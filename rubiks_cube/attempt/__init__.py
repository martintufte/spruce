from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Generator

import numpy as np

from rubiks_cube.autotagger import autotag_step
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.sequence import unniss
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.permutation import get_identity_permutation

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Metric

LOGGER = logging.getLogger(__name__)


class Attempt:
    def __init__(
        self,
        scramble: MoveSequence,
        steps: list[MoveSequence],
        metric: Metric = DEFAULT_METRIC,
        cleanup_final: bool = True,
    ) -> None:
        """Initialize an attempt.

        Args:
            scramble (MoveSequence): Scramble of the attempt.
            steps (list[MoveSequence]): Steps of the attempt.
            metric (Metric, optional): Metric of the attempt.
                Defaults to DEFAULT_METRIC.
            cleanup_final (bool, optional): Cleanup the final solution.
        """
        self.metric = metric
        self.cleanup_final = cleanup_final

        self.scramble = scramble
        self.steps = steps
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
            return cleanup(unniss(combined))
        return combined

    @property
    def result(self) -> str:
        """Get the length of the final solution, or DNF if not solved.

        Returns:
            str: String representation of the result.
        """
        permutation = get_rubiks_cube_state(
            sequence=self.scramble + self.final_solution,
            orientate_after=True,
        )
        if np.array_equal(permutation, get_identity_permutation()):
            return str(measure(self.final_solution, self.metric))
        return "DNF"

    def compile(self) -> tuple[str, str, str]:
        """Compile the steps in the attempt.

        Returns:
            tuple[str, str, str]: Scramble, steps, and final solution.
        """
        scramble_state = get_rubiks_cube_state(sequence=self.scramble, orientate_after=True)

        # Reset state
        self.tags = []
        self.cancellations = []

        for i in range(len(self.steps)):

            # Initial sequence and state
            initial_sequence = sum(self.steps[:i], start=MoveSequence())
            initial_state = get_rubiks_cube_state(
                sequence=initial_sequence,
                initial_permutation=scramble_state,
                orientate_after=True,
            )

            # Final sequence and state
            final_sequence = sum(self.steps[: i + 1], start=MoveSequence())
            final_state = get_rubiks_cube_state(
                sequence=final_sequence,
                initial_permutation=scramble_state,
                orientate_after=True,
            )
            if np.array_equal(final_state, get_identity_permutation()):
                final_sequence = unniss(final_sequence)

            tag = autotag_step(initial_state, final_state)
            if i == 0 and tag == "rotation":
                tag = "inspection"
            self.tags.append(tag)

            # Number of cancellations
            self.cancellations.append(
                measure(initial_sequence, metric=self.metric)
                + measure(self.steps[i], metric=self.metric)
                - measure(cleanup(final_sequence), metric=self.metric)
                - sum(self.cancellations)
            )

        scramble_line = f"Scramble: {self.scramble}"

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
        steps_line = "\n".join(step_lines)

        final_line = f"Final ({self.result}): {self.final_solution}"

        return scramble_line, steps_line, final_line

    def __str__(self) -> str:
        """Get string representation of the attempt.

        Returns:
            str: Representation of the attempt.
        """
        return "\n\n".join(self.compile())

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
