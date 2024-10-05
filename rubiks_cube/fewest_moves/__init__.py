from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Generator

from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import unniss
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.tag import autotag_state
from rubiks_cube.state.tag import autotag_step
from rubiks_cube.utils.parsing import parse_attempt
from rubiks_cube.utils.parsing import parse_scramble


class FewestMovesAttempt:
    def __init__(
        self,
        scramble: MoveSequence,
        steps: list[MoveSequence],
        datetime: str = "2022-01-01 00:00:00",
        wca_id: str = "2022NONE01",
        cube_size: int = 3,
        time_limit: str = "1:00:00",
        metric: Metric = Metric.HTM,
    ) -> None:
        self.scramble = scramble
        self.steps = steps
        self.datetime = datetime
        self.wca_id = wca_id
        self.cube_size = cube_size
        self.time_limit = time_limit
        self.metric = metric

        self.tags = [""] * len(steps)
        self.cancellations = [0] * len(steps)
        self.step_lengths = [len(step) for step in steps]

    @property
    @lru_cache(maxsize=1)
    def final_solution(self) -> MoveSequence:
        """The final solution of the attempt."""
        combined = sum(self.steps, start=MoveSequence())
        return cleanup(unniss(combined))

    @property
    def result(self) -> str:
        state = get_rubiks_cube_state(
            sequence=self.scramble + self.final_solution,
            orientate_after=True,
        )
        if autotag_state(state) == "solved":
            return str(len(self.final_solution))
        return "DNF"

    @classmethod
    def from_string(cls, scramble_input: str, attempt_input: str) -> FewestMovesAttempt:
        """Create a fewest moves attempt from a string."""
        scramble = parse_scramble(scramble_input)
        steps = parse_attempt(attempt_input)
        return cls(
            scramble=scramble,
            steps=steps,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def compile(self) -> None:
        """Compile the steps in the attempt.
        - Tag each step
        - Count the number of cancellations
        - Count the number of moves in each step
        """

        scramble_state = get_rubiks_cube_state(sequence=self.scramble, orientate_after=True)

        tags = []
        cancellations: list[int] = []
        for i in range(len(self.steps)):

            # Initial sequence and state
            initial_sequence = sum(self.steps[:i], start=MoveSequence())
            initial_state = get_rubiks_cube_state(
                sequence=initial_sequence,
                initial_state=scramble_state,
                orientate_after=True,
            )

            # Final sequence and state (unniss if solved)
            final_sequence = sum(self.steps[: i + 1], start=MoveSequence())
            final_state = get_rubiks_cube_state(
                sequence=final_sequence,
                initial_state=scramble_state,
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


if __name__ == "__main__":

    # Example Fewest Moves attempt
    scramble_input = """
    R' U' F L U B' D' L F2 U2 D' B U R2 D F2 R2 F2 L2 D' F2 D2 R' U' F
    """
    attempt_input = """
    B' (F2 R' F)
    (L')
    R2 L2 F2 D' B2 D B2 U' R'
    U F2 * U2 B2 R2 U'
    * = L2
    B2 L2 D2 R2 D2 L2
    """

    attempt = FewestMovesAttempt.from_string(scramble_input, attempt_input)
    attempt.compile()

    print()
    print(attempt)
    print()

    for step, tag, subset, moves, cancels, total in attempt:
        if cancels > 0:
            print(f"{step}  // {tag} ({moves}-{cancels}/{total})")
        else:
            print(f"{step}  // {tag} ({moves}/{total})")

    # Example CFOP solve
    scramble_input = """
    D R' U2 F2 D U' B2 R2 L' F U' B2 U2 F L F' D'
    """
    attempt_input = """
    x2
    R' D2 R' D L' U L D R' U' R D
    L U' L'
    U' R U R' y' U R' U' R
    r' U' R U' R' U2 r
    U
    """
    attempt = FewestMovesAttempt.from_string(scramble_input, attempt_input)
    attempt.compile()

    print()
    print(attempt)
    print()
