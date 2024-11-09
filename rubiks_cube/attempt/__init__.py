from __future__ import annotations

import logging
from functools import lru_cache
from typing import Generator

import numpy as np

from rubiks_cube.configuration import METRIC
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.sequence import unniss
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import get_identity_permutation
from rubiks_cube.tag import autotag_step

LOGGER = logging.getLogger(__name__)


class Attempt:
    def __init__(
        self,
        scramble: MoveSequence,
        steps: list[MoveSequence],
        metric: Metric = METRIC,
        include_scramble: bool = True,
        include_steps: bool = True,
        include_final: bool = True,
        cleanup_final: bool = True,
    ) -> None:
        """Initialize an attempt.

        Args:
            scramble (MoveSequence): Scramble of the attempt.
            steps (list[MoveSequence]): Steps of the attempt.
            metric (Metric, optional): Metric of the attempt.
                Defaults to METRIC.
            include_scramble (bool, optional): Include the scramble in the output.
                Defaults to True.
            include_steps (bool, optional): Include the steps in the output.
                Defaults to True.
            include_final (bool, optional): Include the final solution in the output.
                Defaults to True.
        """
        self.metric = metric
        self.include_scramble = include_scramble
        self.include_steps = include_steps
        self.include_final = include_final
        self.cleanup_final = cleanup_final

        self.scramble = scramble
        self.steps = steps
        self.tags = [""] * len(steps)
        self.cancellations = [0] * len(steps)
        self.step_lengths = [measure(step, metric=self.metric) for step in steps]

    @property
    @lru_cache(maxsize=1)
    def final_solution(self) -> MoveSequence:
        """The final solution of the attempt.

        Returns:
            MoveSequence: Final solution of the attempt.
        """
        combined = sum(self.steps, start=MoveSequence())
        if self.cleanup_final:
            return cleanup(unniss(combined))
        return combined

    @property
    def result(self) -> str:
        """The length of the final solution, or DNF if not solved.

        Returns:
            str: String representation of the result.
        """
        state = get_rubiks_cube_state(
            sequence=self.scramble + self.final_solution,
            orientate_after=True,
        )
        if np.array_equal(state, get_identity_permutation()):
            return str(measure(self.final_solution, self.metric))
        return "DNF"

    def compile(self) -> None:
        """Compile the steps in the attempt."""

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

            # Autotag the step
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

    def __str__(self) -> str:
        """String representation of the attempt.

        Returns:
            str: Representation of the attempt.
        """
        lines = []

        if self.include_scramble:
            lines.append(f"Scramble: {self.scramble}")

        if self.include_steps:
            cumulative_length = 0
            max_step_ch = max(len(str(step)) for step in self.steps) if self.steps else 0
            step_lines = []
            for step, tag, cancellation in zip(self.steps, self.tags, self.cancellations):
                step_line = f"{str(step).ljust(max_step_ch)}"
                if tag != "":
                    step_line += f"  // {tag} ({measure(step, metric=self.metric)}"
                if cancellation > 0:
                    step_line += f"-{cancellation}"
                cumulative_length += measure(step, metric=self.metric) - cancellation
                step_line += f"/{cumulative_length})"
                step_lines.append(step_line)
            lines.append("\n".join(step_lines))

        if self.include_final:
            lines.append(f"Final ({self.result}): {self.final_solution}")

        return "\n\n".join(lines)

    def __iter__(self) -> Generator[tuple[str, str, str, int, int, int], None]:
        """Iterate through the steps of the attempt.

        Yields:
            Iterator[tuple[str, str, str, int, int, int]]: The move sequence
                for the step, the auto tag, and subset if applicable, the
                number of moves, cancellations, and cumulative length.
        """
        if self.steps:
            max_step_ch = max(len(str(step)) for step in self.steps)
        else:
            max_step_ch = 0

        cumulative = 0
        for step, tag, cancel in zip(self.steps, self.tags, self.cancellations):
            subset = ""
            cumulative += measure(step, metric=self.metric) - cancel
            yield (
                str(step).ljust(max_step_ch),
                tag,
                subset,
                measure(step, metric=self.metric),
                cancel,
                cumulative,
            )

    def __next__(self) -> tuple[str, str, str, int, int, int]:
        return next(self)

    def __len__(self) -> int:
        return len(self.steps)
