from __future__ import annotations

import logging
import textwrap
from typing import TYPE_CHECKING
from typing import Self

import attrs
import numpy as np

from spruce.move.sequence import MoveSequence
from spruce.move.sequence import cleanup
from spruce.move.sequence import measure
from spruce.move.sequence import unniss
from spruce.representation import get_permutation
from spruce.representation.utils import get_identity

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Sequence

    from spruce.autotagger import PatternTagger
    from spruce.move.meta import MoveMeta
    from spruce.puzzle.cube.metrics import Metric


LOGGER = logging.getLogger(__name__)


def _combine_parts(
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
        outer_separator (str, optional): How to separate outer parts. Defaults to "\n\n".

    Returns:
        str: Combined parts.
    """
    return outer_separator.join(
        [
            inner_separator.join([textwrap.fill(string, width=width) for string in part])
            for part in parts
        ],
    )


@attrs.mutable
class Attempt:
    scramble: MoveSequence
    steps: list[MoveSequence]
    move_meta: MoveMeta
    tags: list[str]
    cancellations: list[int]
    step_lengths: list[int]

    metric: Metric
    cleanup_final: bool = True

    @classmethod
    def from_scramble_and_steps(
        cls,
        scramble: MoveSequence,
        steps: list[MoveSequence],
        move_meta: MoveMeta,
        metric: Metric,
        cleanup_final: bool = True,
    ) -> Self:
        """Create an attempt from scramble and steps.

        Args:
            scramble (MoveSequence): Scramble of the attempt.
            steps (list[MoveSequence]): Steps of the attempt.
            move_meta (MoveMeta): Move meta configuration.
            metric (Metric, optional): Metric of the attempt.
                Defaults to DEFAULT_METRIC.
            cleanup_final (bool, optional): Cleanup the final solution. Defaults to True.
        """
        return cls(
            scramble=scramble,
            steps=steps,
            move_meta=move_meta,
            tags=[""] * len(steps),
            cancellations=[0] * len(steps),
            step_lengths=[measure(step, metric=metric) for step in steps],
            metric=metric,
            cleanup_final=cleanup_final,
        )

    def get_final_solution(self) -> MoveSequence:
        combined = sum(self.steps, start=MoveSequence())
        if self.cleanup_final:
            return cleanup(unniss(combined, self.move_meta), self.move_meta)
        return combined

    def compile(self, autotagger: PatternTagger, width: int = 80) -> str:
        """Compile the steps in the attempt.

        Args:
            width (int): Width to wrap lines.

        Returns:
            str: Compiled string with scramble, steps, and final solution.
        """
        scramble_permutation = get_permutation(
            sequence=self.scramble,
            move_meta=self.move_meta,
            orientate_after=True,
        )

        self.tags = []
        self.cancellations = []
        self.step_lengths = []

        current_sequence = MoveSequence()
        initial_permutation = scramble_permutation
        cumulative_raw = 0
        cumulative_cancellations = 0

        for i, step in enumerate(self.steps):
            # Final sequence and permutation
            final_sequence = current_sequence + step
            final_permutation = get_permutation(
                sequence=final_sequence,
                move_meta=self.move_meta,
                initial_permutation=scramble_permutation,
                orientate_after=True,
            )
            if np.array_equal(final_permutation, get_identity(self.move_meta.size)):
                final_sequence = unniss(final_sequence, self.move_meta)

            tag = autotagger.tag_step(initial_permutation, final_permutation)
            if i == 0 and tag == "rotation":
                tag = "inspection"
            self.tags.append(tag)

            # Number of cancellations
            step_measure = measure(step, metric=self.metric)
            cancellation = (
                cumulative_raw
                + step_measure
                - measure(cleanup(final_sequence, self.move_meta), metric=self.metric)
                - cumulative_cancellations
            )
            self.cancellations.append(cancellation)
            self.step_lengths.append(step_measure)
            cumulative_raw += step_measure
            cumulative_cancellations += cancellation
            current_sequence = final_sequence
            initial_permutation = final_permutation

        cumulative_length = 0
        max_step_ch = max(len(str(step)) for step in self.steps) if self.steps else 0
        step_lines = []
        for step, tag, cancellation, step_length in zip(
            self.steps,
            self.tags,
            self.cancellations,
            self.step_lengths,
            strict=False,
        ):
            step_line = f"{str(step).ljust(max_step_ch)}"
            if tag != "":
                step_line += f"  // {tag} ({step_length}"
            if cancellation > 0:
                step_line += f"-{cancellation}"
            cumulative_length += step_length - cancellation
            step_line += f"/{cumulative_length})"
            step_lines.append(step_line)

        final_solution = self.get_final_solution()

        permutation = get_permutation(
            sequence=self.scramble + final_solution,
            move_meta=self.move_meta,
            orientate_after=True,
        )
        if np.array_equal(permutation, get_identity(self.move_meta.size)):
            result = str(measure(final_solution, self.metric))
        else:
            result = "DNF"

        # Wrap parts together
        scramble_line = f"Scramble: {self.scramble}"
        final_line = f"Final ({result}): {final_solution}"

        return _combine_parts(
            parts=[[scramble_line], step_lines, [final_line]],
            width=width,
            inner_separator="\n",
            outer_separator="\n\n",
        )

    def __iter__(self) -> Generator[tuple[str, str, str, int, int, int]]:
        """Iterate through the steps of the attempt.

        Yields:
            Iterator[tuple[str, str, str, int, int, int]]: The move sequence
                for the step, the auto pattern, and subset if applicable, the
                number of moves, cancellations, and cumulative length.
        """
        max_step_ch = max(len(str(step)) for step in self.steps) if self.steps else 0

        cumulative = 0
        for step, pattern, cancel, step_length in zip(
            self.steps,
            self.tags,
            self.cancellations,
            self.step_lengths,
            strict=False,
        ):
            subset = ""
            cumulative += step_length - cancel
            yield (
                str(step).ljust(max_step_ch),
                pattern,
                subset,
                step_length,
                cancel,
                cumulative,
            )

    def __len__(self) -> int:
        return len(self.steps)
