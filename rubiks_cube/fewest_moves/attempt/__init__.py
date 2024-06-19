from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import unniss
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_state
from rubiks_cube.state.tag import autotag_state
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
        return_string = f"Scramble: {self.scramble}\n\n"
        for step in self.steps:
            return_string += f"{str(step)}\n"
        return_string += f"\nFinal Solution: {str(self.final_solution)}"
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


if __name__ == "__main__":
    scramble_input = """
    R' U' F D R F2 D L F  D2 F2 L' U R' L2 D' R2 F2 R2 D L2 U2 R' U' F
    """
    attempt_input = """
    U B' L2 F  // eo
    R  // drm
    U' R2 L2 D2 B2 D' F2 D U2 R  // dr
    (U' R2 D)  // htr
    (F2 R2 L2 D2 R2 [F2 D2])  // leave-slice (25)
    [] = U' D R2 U D  // solved (28)
    """

    attempt = FewestMovesAttempt.from_string(scramble_input, attempt_input)

    print(attempt)
