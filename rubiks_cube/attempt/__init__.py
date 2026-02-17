from __future__ import annotations

import logging
import textwrap
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Generator
from typing import Sequence

import numpy as np

from rubiks_cube.autotagger import autotag_step
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.sequence import unniss
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.permutation import get_identity_permutation

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Metric
    from rubiks_cube.move.meta import MoveMeta
    from rubiks_cube.move.steps import MoveSteps


LOGGER = logging.getLogger(__name__)


def combine_parts(
    parts: Sequence[Sequence[str]],
    width: int,
    inner_separator: str = "\n",
    outer_separator: str = "\n\n",
) -> str:
    """Combine the parts into a single string.

    Args:
        parts (Sequence[str]): Sequence of parts to combine.
        width (int): Maximum line length.
        inner_separator (str, optional): How to separate inner parts. Defaults to "\n".
        outer_seperator (str, optional): How to separate outer parts. Defaults to "\n\n".

    Returns:
        str: Combined parts.
    """
    return outer_separator.join(
        [
            inner_separator.join([textwrap.fill(string, width=width) for string in part])
            for part in parts
        ]
    )


class Attempt:
    def __init__(
        self,
        scramble: MoveSequence,
        steps: MoveSteps,
        move_meta: MoveMeta,
        metric: Metric = DEFAULT_METRIC,
        cleanup_final: bool = True,
    ) -> None:
        """Initialize an attempt.

        Args:
            scramble (MoveSequence): Scramble of the attempt.
            steps (MoveSteps): Steps of the attempt.
            move_meta (MoveMeta): Move meta configuration.
            metric (Metric, optional): Metric of the attempt.
                Defaults to DEFAULT_METRIC.
            cleanup_final (bool, optional): Cleanup the final solution. Defaults to True.
        """
        self.metric = metric
        self.cleanup_final = cleanup_final

        self.scramble = scramble
        self.steps = steps
        self.move_meta = move_meta
        self.tags = [""] * len(steps)
        self.cancellations = [0] * len(steps)
        self.step_lengths = [measure(step, metric=self.metric) for step in steps]

    @property
    @lru_cache(maxsize=1)
    def final_solution(self) -> MoveSequence:
        """Get the final solution of the attempt.

        Returns:
            MoveSequence: Final solution of the attempt.
        """
        combined = sum(self.steps, start=MoveSequence())
        if self.cleanup_final:
            return cleanup(unniss(combined), self.move_meta)
        return combined

    @property
    def result(self) -> str:
        """Get the length of the final solution, or DNF if not solved.

        Returns:
            str: String representation of the result.
        """
        permutation = get_rubiks_cube_permutation(
            sequence=self.scramble + self.final_solution,
            orientate_after=True,
        )
        if np.array_equal(permutation, get_identity_permutation()):
            return str(measure(self.final_solution, self.metric))
        return "DNF"

    def compile(self, width: int = 80) -> str:
        """Compile the steps in the attempt.

        Args:
            width (int): Width to wrap lines.

        Returns:
            str: Compiled string with scramble, steps, and final solution.
        """
        scramble_permutation = get_rubiks_cube_permutation(
            sequence=self.scramble, orientate_after=True
        )

        self.tags = []
        self.cancellations = []

        for i in range(len(self.steps)):

            # Initial sequence and permutation
            initial_sequence = sum(self.steps[:i], start=MoveSequence())
            initial_permutation = get_rubiks_cube_permutation(
                sequence=initial_sequence,
                initial_permutation=scramble_permutation,
                orientate_after=True,
            )

            # Final sequence and permutation
            final_sequence = sum(self.steps[: i + 1], start=MoveSequence())
            final_permutation = get_rubiks_cube_permutation(
                sequence=final_sequence,
                initial_permutation=scramble_permutation,
                orientate_after=True,
            )
            if np.array_equal(final_permutation, get_identity_permutation()):
                final_sequence = unniss(final_sequence)

            tag = autotag_step(initial_permutation, final_permutation)
            if i == 0 and tag == "rotation":
                tag = "inspection"
            self.tags.append(tag)

            # Number of cancellations
            self.cancellations.append(
                measure(initial_sequence, metric=self.metric)
                + measure(self.steps[i], metric=self.metric)
                - measure(cleanup(final_sequence, self.move_meta), metric=self.metric)
                - sum(self.cancellations)
            )

        cumulative_length = 0
        max_step_ch = max(len(str(step)) for step in self.steps) if self.steps else 0
        step_lines = []
        for step, tag, cancellation in zip(self.steps, self.tags, self.cancellations, strict=False):
            step_line = f"{str(step).ljust(max_step_ch)}"
            if tag != "":
                step_line += f"  // {tag} ({measure(step, metric=self.metric)}"
            if cancellation > 0:
                step_line += f"-{cancellation}"
            cumulative_length += measure(step, metric=self.metric) - cancellation
            step_line += f"/{cumulative_length})"
            step_lines.append(step_line)

        # Wrap parts together
        scramble_line = f"Scramble: {self.scramble}"
        final_line = f"Final ({self.result}): {self.final_solution}"

        return combine_parts(
            parts=[[scramble_line], step_lines, [final_line]],
            width=width,
            inner_separator="\n",
            outer_separator="\n\n",
        )

    def __iter__(self) -> Generator[tuple[str, str, str, int, int, int], None]:
        """Iterate through the steps of the attempt.

        Yields:
            Iterator[tuple[str, str, str, int, int, int]]: The move sequence
                for the step, the auto pattern, and subset if applicable, the
                number of moves, cancellations, and cumulative length.
        """
        max_step_ch = max(len(str(step)) for step in self.steps) if self.steps else 0

        cumulative = 0
        for step, pattern, cancel in zip(self.steps, self.tags, self.cancellations, strict=False):
            subset = ""
            cumulative += measure(step, metric=self.metric) - cancel
            yield (
                str(step).ljust(max_step_ch),
                pattern,
                subset,
                measure(step, metric=self.metric),
                cancel,
                cumulative,
            )

    def __next__(self) -> tuple[str, str, str, int, int, int]:
        return next(self)

    def __len__(self) -> int:
        return len(self.steps)
