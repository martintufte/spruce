from __future__ import annotations

from math import factorial

from spruce.autotagger.pattern import Pattern
from spruce.autotagger.pattern import get_patterns
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.puzzle.cube.goals import Goal
from spruce.puzzle.cube.patterns import generate_pattern_variants
from spruce.puzzle.cube.patterns import pattern_combinations
from spruce.puzzle.cube.spec import Puzzle
from spruce.puzzle.cube.variants import Variant


class TestPatternCombinations:
    puzzle = Puzzle._3x3x3
    move_meta: MoveMeta = MoveMeta.from_puzzle(puzzle=puzzle)
    patterns = get_patterns(puzzle=puzzle)

    def test_pattern_combinations_solved(self) -> None:
        pattern = self.patterns.get(Goal.solved)
        assert pattern is not None
        n_combinations = pattern_combinations(
            pattern=pattern.variants[Variant.none],
            move_meta=self.move_meta,
        )
        assert n_combinations == 1

    def test_pattern_combinations_none(self) -> None:
        pattern = self.patterns.get(Goal.none)
        assert pattern is not None
        n_combinations = pattern_combinations(
            pattern=pattern.variants[Variant.none],
            move_meta=self.move_meta,
        )
        assert n_combinations == factorial(8) * 3**7 * factorial(12) * 2**11 / 2

    def test_pattern_combinations_eo(self) -> None:
        pattern = self.patterns.get(Goal.eo)
        assert pattern is not None
        n_combinations = pattern_combinations(
            pattern=pattern.variants[Variant.fb],
            move_meta=self.move_meta,
        )
        assert n_combinations == factorial(8) * 3**7 * factorial(12) / 2

    def test_pattern_combinations_dr(self) -> None:
        pattern = self.patterns.get(Goal.dr)
        assert pattern is not None
        n_combinations = pattern_combinations(
            pattern=pattern.variants[Variant.ud],
            move_meta=self.move_meta,
        )
        assert n_combinations == factorial(8) * factorial(8) * factorial(4) / 2

    def test_pattern_combinations_cross(self) -> None:
        pattern = self.patterns.get(Goal.cross)
        assert pattern is not None
        n_combinations = pattern_combinations(
            pattern=pattern.variants[Variant.down],
            move_meta=self.move_meta,
        )
        assert n_combinations == factorial(8) * 3**7 * factorial(8) * 2**7 / 2


class TestGeneratePatternsVariations:
    def test_generate_patterns_from_subset(self) -> None:
        move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)
        pattern = Pattern.from_settings(
            move_meta=move_meta,
            variant=Variant.down,
            fixed_sequence=MoveSequence.from_str("R L U2 R2 L2 U2 R L U"),
        )

        variants = generate_pattern_variants(
            pattern=pattern.variants[Variant.down],
            initial_variant=Variant.down,
            move_meta=move_meta,
        )

        assert len(variants) == 6
