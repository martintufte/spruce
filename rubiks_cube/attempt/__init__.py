from __future__ import annotations

from functools import lru_cache
from typing import Generator
from typing import Literal

from rubiks_cube.configuration import ATTEMPT_TYPE
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import unniss
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.tag import autotag_state
from rubiks_cube.tag import autotag_step
from rubiks_cube.utils.parsing import parse_attempt
from rubiks_cube.utils.parsing import parse_scramble


class Attempt:
    def __init__(
        self,
        scramble: MoveSequence,
        steps: list[MoveSequence],
        type: Literal["fewest_moves", "speedsolve"] = ATTEMPT_TYPE,
    ) -> None:
        """Initialize a fewest moves attempt.

        Args:
            scramble (MoveSequence): Scramble of the attempt.
            steps (list[MoveSequence]): Steps of the attempt.
            type (Literal["fewest_moves", "speedsolve"], optional): Type of the attempt.
        """
        self.scramble = scramble
        self.steps = steps
        self.type = type

        self.tags = [""] * len(steps)
        self.cancellations = [0] * len(steps)
        self.step_lengths = [len(step) for step in steps]

    @property
    @lru_cache(maxsize=1)
    def final_solution(self) -> MoveSequence:
        """The final solution of the attempt.

        Returns:
            MoveSequence: Final solution of the attempt.
        """
        combined = sum(self.steps, start=MoveSequence())
        if self.type == "fewest_moves":
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
        if autotag_state(state) == "solved":
            return str(len(self.final_solution))
        return "DNF"

    @classmethod
    def from_string(cls, scramble_input: str, attempt_input: str) -> Attempt:
        """Create a fewest moves attempt from a string.

        Args:
            scramble_input (str): Scramble of the attempt.
            attempt_input (str): The steps of the attempt.

        Returns:
            Attempt: Fewest moves attempt.
        """
        return cls(
            scramble=parse_scramble(scramble_input),
            steps=parse_attempt(attempt_input),
        )

    def compile(self) -> None:
        """Compile the steps in the attempt.
        - Tag each step.
        - Count the number of cancellations.
        - Count the number of moves in each step.
        """

        scramble_state = get_rubiks_cube_state(sequence=self.scramble, orientate_after=True)

        tags = []
        cancellations: list[int] = []
        for i in range(len(self.steps)):

            # Initial sequence and state
            initial_sequence = sum(self.steps[:i], start=MoveSequence())
            initial_state = get_rubiks_cube_state(
                sequence=initial_sequence,
                initial_permutation=scramble_state,
                orientate_after=True,
            )

            # Final sequence and state (unniss if solved)
            final_sequence = sum(self.steps[: i + 1], start=MoveSequence())
            final_state = get_rubiks_cube_state(
                sequence=final_sequence,
                initial_permutation=scramble_state,
                orientate_after=True,
            )
            if autotag_state(final_state) == "solved":
                final_sequence = unniss(final_sequence)

            # Autotag the step
            tag = autotag_step(initial_state, final_state)
            if i == 0 and tag == "rotation":
                tag = "inspection"
            tags.append(tag)

            # Number of cancellations
            cancellations.append(
                len(initial_sequence)
                + len(self.steps[i])
                - len(cleanup(final_sequence))
                - sum(cancellations)
            )

        self.tags = tags
        self.cancellations = cancellations

    def __str__(self) -> str:
        """String representation of the attempt.

        Returns:
            str: Representation of the attempt.
        """
        return_string = f"Scramble: {self.scramble}\n"
        cumulative_length = 0
        if self.steps:
            max_step_ch = max(len(str(step)) for step in self.steps)
        else:
            max_step_ch = 0

        for step, tag, cancellation in zip(self.steps, self.tags, self.cancellations):
            return_string += f"\n{str(step).ljust(max_step_ch)}"
            if tag != "":
                return_string += f"  // {tag} ({len(step)}"
            if cancellation > 0:
                return_string += f"-{cancellation}"
            cumulative_length += len(step) - cancellation
            return_string += f"/{cumulative_length})"

        return_string += f"\n\nFinal ({self.result}): {str(self.final_solution)}"
        return return_string

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

        cumulative_length = 0
        for step, tag, can in zip(self.steps, self.tags, self.cancellations):
            subset = ""
            cumulative_length += len(step) - can
            yield (
                str(step).ljust(max_step_ch),
                tag,
                subset,
                len(step),
                can,
                cumulative_length,
            )

    def __next__(self) -> tuple[str, str, str, int, int, int]:
        return next(self)

    def __len__(self) -> int:
        return len(self.steps)
