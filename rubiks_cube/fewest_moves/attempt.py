from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from rubiks_cube.configuration import ATTEMPT_TYPE
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import unniss
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_state
from rubiks_cube.state.tag import autotag_state
from rubiks_cube.state.tag import autotag_step
from rubiks_cube.utils.enumerations import AttemptType
from rubiks_cube.utils.enumerations import Metric
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
        state = get_state(sequence=self.scramble + self.final_solution)
        tag = autotag_state(state)
        if tag == "solved":
            return str(len(self.final_solution))
        return "DNF"

    def __str__(self) -> str:
        return_string = f"Scramble: {self.scramble}\n"
        cumulative_length = 0
        cumulative_cancelation = 0
        for step, tag, cancelation in zip(self.steps, self.tags, self.cancellations):  # noqa: E501
            return_string += f"\n{str(step)}"
            if tag != "":
                return_string += f"  // {tag} ({len(step)}"
            if cancelation != cumulative_cancelation:
                return_string += f"-{cancelation - cumulative_cancelation}"
                cumulative_cancelation += cancelation
            cumulative_length += len(step) - cumulative_cancelation
            return_string += f"/{cumulative_length})"
        if ATTEMPT_TYPE is AttemptType.fewest_moves:
            return_string += f"\n\nFinal ({self.result}): {str(self.final_solution)}"  # noqa: E501
        return return_string

    @classmethod
    def from_string(
        cls,
        scramble_input: str,
        attempt_input: str
    ) -> FewestMovesAttempt:
        """Create a fewest moves attempt from a string."""
        scramble = parse_scramble(scramble_input)
        steps = parse_attempt(attempt_input)
        return cls(
            scramble=scramble,
            steps=steps,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def tag_step(self) -> None:
        """Tag the steps of the attempt and the cancellations."""
        auto_tags = []
        auto_cancellations = []
        scramble_state = get_state(self.scramble, orientate_after=True)
        for i in range(len(self.steps)):
            initial_sequence = sum(self.steps[: i], start=MoveSequence())
            initial_state = get_state(
                initial_sequence,
                initial_state=scramble_state,
                orientate_after=True,
            )
            final_sequence = sum(self.steps[: i + 1], start=MoveSequence())
            final_state = get_state(
                final_sequence,
                initial_state=scramble_state,
                orientate_after=True,
            )
            auto_tags.append(
                autotag_step(
                    initial_state=initial_state,
                    final_state=final_state,
                    length=len(self.steps[i]),
                    step_number=i,
                )
            )
            if autotag_state(final_state) == "solved":
                len_end = len(cleanup(unniss(final_sequence)))
            else:
                len_end = len(cleanup(final_sequence))
            auto_cancellations.append(
                (len(initial_sequence) + len(self.steps[i])) - len_end
            )

        self.tags = auto_tags
        self.cancellations = auto_cancellations


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
    attempt.tag_step()

    print()
    print(attempt)
    print()

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
    attempt.tag_step()

    print()
    print(attempt)
    print()
