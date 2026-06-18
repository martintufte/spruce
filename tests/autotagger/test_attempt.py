from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

from spruce.autotagger import PatternTagger
from spruce.autotagger.attempt import Attempt
from spruce.configuration.enumeration import Metric
from spruce.configuration.enumeration import Puzzle
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.parsing import parse_scramble
from spruce.parsing import parse_steps

if TYPE_CHECKING:
    from spruce.autotagger.interface import PermutationTagger

LOGGER: Final = logging.getLogger(__name__)


class TestAttempt:
    move_meta: MoveMeta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)
    autotagger: PermutationTagger = PatternTagger.from_move_meta(move_meta=move_meta)

    def test1(self) -> None:
        scramble_input = """
        R' U' F L U B' D' L F2 U2 D' B U R2 D F2 R2 F2 L2 D' F2 D2 R' U' F
        """
        steps_input = """
        B' (F2 R' F)
        (L')
        R2 L2 F2 D' B2 D B2 U' R'
        U F2 L2 U2 B2 R2 U'
        B2 L2 D2 R2 D2 L2
        """

        attempt = Attempt.from_scramble_and_steps(
            scramble=parse_scramble(scramble_input),
            steps=parse_steps(steps_input),
            move_meta=self.move_meta,
            metric=Metric.HTM,
        )
        attempt.compile(self.autotagger)

        assert isinstance(attempt.get_final_solution(), MoveSequence)

    def test2(self) -> None:
        scramble_input = """
        D R' U2 F2 D U' B2 R2 L' F U' B2 U2 F L F' D'
        """
        steps_input = """
        x2
        R' D2 R' D L' U L D R' U' R D
        L U' L'
        U' R U R' y' U R' U' R
        r' U' R U' R' U2 r
        U
        """
        attempt = Attempt.from_scramble_and_steps(
            scramble=parse_scramble(scramble_input),
            steps=parse_steps(steps_input),
            move_meta=self.move_meta,
            metric=Metric.HTM,
        )
        attempt.compile(self.autotagger)

        assert isinstance(attempt.get_final_solution(), MoveSequence)
