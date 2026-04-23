from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from attrs import frozen

from rubiks_cube.autotagger.pattern import get_patterns
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.configuration.enumeration import SearchSide
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.steps import MoveSteps
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.pattern import pattern_implies
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.bidirectional import BidirectionalSolver

if TYPE_CHECKING:
    from rubiks_cube.beam_search.interface import BeamPlan
    from rubiks_cube.beam_search.interface import BeamStep
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.move.generator import MoveGenerator

LOGGER = logging.getLogger(__name__)


@frozen
class BeamSolution:
    steps: MoveSteps
    cost: int

    @property
    def sequence(self) -> MoveSequence:
        return self.steps.to_sequence()


@frozen
class BeamSearchSummary:
    solutions: list[BeamSolution]
    walltime: float
    status: Status


@frozen
class BeamCandidate:
    permutation: PermutationArray
    steps: MoveSteps
    side: SearchSide
    goal_history: tuple[Goal, ...]
    variant_history: tuple[Variant, ...]
    cost: int


def search_sides(candidate: BeamCandidate, step: BeamStep) -> tuple[SearchSide, ...]:
    if step.transition.search_side == "prev":
        return (candidate.side,)
    if step.transition.search_side == "normal":
        return (SearchSide.normal,)
    if step.transition.search_side == "inverse":
        return (SearchSide.inverse,)
    if step.transition.search_side == "switch":
        return (candidate.side.toggle(),)
    if step.transition.search_side == "both":
        return (candidate.side, candidate.side.toggle())
    raise ValueError(f"Unknown search_side: {step.transition.search_side!r}")


def _generator_key(generator: MoveGenerator) -> frozenset[str]:
    return frozenset(str(seq) for seq in generator.generator)


@frozen
class CompiledVariant:
    goal: Goal
    variant: Variant
    step: BeamStep
    solver: BidirectionalSolver
    pattern: PatternArray


@frozen
class CompiledStep:
    step: BeamStep
    contexts_by_generator: dict[frozenset[str], list[CompiledVariant]]
    allowed_prev_variants_by_variant: dict[Variant, frozenset[Variant]] | None = None

    def transition_prev_variant(self, candidate: BeamCandidate) -> Variant:
        idx = self.step.transition.prev_goal_index
        return candidate.variant_history[idx]

    def contexts_for_prev_variant(self, prev_variant: Variant) -> list[CompiledVariant]:
        generator = self.step.transition.generator_map.get(prev_variant)
        if generator is None:
            return []
        return self.contexts_by_generator.get(_generator_key(generator), [])

    def allowed_prev_variants_for(self, variant: Variant) -> frozenset[Variant] | None:
        if self.allowed_prev_variants_by_variant is None:
            return None
        return self.allowed_prev_variants_by_variant.get(variant)

    def allowed_variant_for_prev_variant(self, prev_variant: Variant) -> frozenset[Variant] | None:
        allowed = self.step.transition.allowed_variants_by_prev_variant
        if allowed is None:
            return None
        return allowed.get(prev_variant)


def select_top_k(candidates: list[BeamCandidate], k: int) -> list[BeamCandidate]:
    candidates.sort(key=lambda c: c.cost)
    return candidates[:k]


def _insert_solution(
    best_solutions: list[BeamSolution],
    candidate: BeamCandidate,
    max_solutions: int,
) -> None:
    best_solutions.append(BeamSolution(steps=candidate.steps, cost=candidate.cost))
    best_solutions.sort(key=lambda solution: solution.cost)
    del best_solutions[max_solutions:]


def build_step_contexts(plan: BeamPlan, move_meta: MoveMeta) -> list[CompiledStep]:
    patterns = get_patterns(cube_size=move_meta.cube_size)
    contexts: list[CompiledStep] = []

    prev_goal: Goal = Goal.none
    prev_variants: tuple[Variant, ...] = ()

    for step in plan.steps:
        generator_map: dict[frozenset[str], MoveGenerator] = {}
        for generator in step.transition.generator_map.values():
            generator_map.setdefault(_generator_key(generator), generator)

        contexts_by_generator: dict[frozenset[str], list[CompiledVariant]] = {}
        for generator_key, generator in generator_map.items():
            actions = get_actions(move_meta=move_meta, generator=generator)
            goal_contexts: list[CompiledVariant] = []

            pattern = patterns[step.goal]
            validator_key = step.goal.value if pattern.validator is not None else None
            for variant, cube_pattern in pattern.variants.items():
                if variant not in step.variants:
                    continue
                solver = BidirectionalSolver.from_actions_and_pattern(
                    actions=actions,
                    pattern=cube_pattern,
                    validator=pattern.validator,
                    validator_key=validator_key,
                    optimize_indices=True,
                    debug=False,
                )
                goal_contexts.append(
                    CompiledVariant(
                        goal=step.goal,
                        variant=variant,
                        step=step,
                        solver=solver,
                        pattern=cube_pattern,
                    )
                )
            contexts_by_generator[generator_key] = goal_contexts
            if len(goal_contexts) == 0:
                continue

        allowed_prev_variants_by_variant: dict[Variant, frozenset[Variant]] | None = None
        if step.transition.check_contained and len(prev_variants) > 0:
            allowed_prev_variants_by_variant = {}

            goal_pattern = patterns[step.goal]
            for variant in step.variants:
                allowed_prev_variants_by_variant[variant] = frozenset(
                    prev_variant
                    for prev_variant in prev_variants
                    if pattern_implies(goal_pattern[variant], patterns[prev_goal][prev_variant])
                )

        contexts.append(
            CompiledStep(
                step=step,
                contexts_by_generator=contexts_by_generator,
                allowed_prev_variants_by_variant=allowed_prev_variants_by_variant,
            )
        )
        prev_goal = step.goal
        prev_variants = tuple(step.variants)

    return contexts


def beam_search(
    sequence: MoveSequence,
    plan: BeamPlan,
    beam_width: int,
    max_solutions: int = 1,
    max_time: float = 60.0,
    metric: Metric = DEFAULT_METRIC,
    contexts: list[CompiledStep] | None = None,
) -> BeamSearchSummary:
    """Solve using the beam search algorithm.

    Args:
        sequence (MoveSequence): Sequence to scramble the cube.
        plan (BeamPlan): Beam plan containing steps.
        beam_width (int): How many solutions to keep from one step to the next.
        max_solutions (int, optional): Maximum number of solutions. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.
        metric (Metric, optional): Metric to calculate cost. Defaults to DEFAULT_METRIC.
        contexts (list[CompiledStep] | None, optional): Pre-built step contexts. When provided,
            skips the expensive build step so the solver can be reused across scrambles.

    Raises:
        ValueError: Beam plan must contain at least one step.
        ValueError: Beam width must be at least 1.
        ValueError: Maximum number of solutions must be at least one.

    Returns:
        BeamSearchSummary: Summary of the beam search.
    """
    if not plan.steps:
        raise ValueError("Beam plan must contain at least one step.")
    if beam_width < 1:
        raise ValueError("Beam width must be at least 1.")
    if max_solutions < 1:
        raise ValueError("Maximum number of solutions must be at least 1.")

    LOGGER.info(f"Running beam search with plan '{plan.name}'..")
    LOGGER.debug(f"Sequence: {sequence}")

    move_meta = MoveMeta.from_cube_size(cube_size=plan.cube_size)

    if contexts is None:
        build_start_time = time.perf_counter()
        contexts = build_step_contexts(plan=plan, move_meta=move_meta)
        build_walltime = time.perf_counter() - build_start_time
        LOGGER.debug(f"Build walltime: {build_walltime:.2f}s")

    permutation = get_rubiks_cube_permutation(sequence=sequence, move_meta=move_meta)
    beam: list[BeamCandidate] = [
        BeamCandidate(
            permutation=permutation,
            steps=MoveSteps(),
            side=SearchSide.normal,
            goal_history=(Goal.none,),
            variant_history=(Variant.none,),
            cost=0,
        )
    ]

    best_solutions: list[BeamSolution] = []
    timed_out = False
    start_time = time.perf_counter()

    for step_index, step_options in enumerate(contexts):
        next_beam: list[BeamCandidate] = []

        for candidate in beam:
            elapsed = time.perf_counter() - start_time
            if elapsed >= max_time:
                timed_out = True
                break

            transition_variant = step_options.transition_prev_variant(candidate)
            step_contexts = step_options.contexts_for_prev_variant(transition_variant)
            allowed_goals = step_options.allowed_variant_for_prev_variant(transition_variant)
            prev_variant = candidate.variant_history[-1]

            for context in step_contexts:
                if allowed_goals is not None and context.goal not in allowed_goals:
                    continue

                if (
                    allowed_prev_variants := step_options.allowed_prev_variants_for(context.variant)
                ) is not None:
                    if prev_variant not in allowed_prev_variants:
                        continue

                for side in search_sides(candidate=candidate, step=step_options.step):
                    elapsed = time.perf_counter() - start_time
                    if elapsed >= max_time:
                        timed_out = True
                        break

                    search_summary = context.solver.search(
                        permutations=[candidate.permutation],
                        max_solutions_per_permutation=step_options.step.max_solutions,
                        max_search_depth=step_options.step.max_search_depth,
                        max_time=max_time - elapsed,
                        side=side,
                    )

                    if search_summary.status is Status.Failure:
                        continue

                    rooted_solutions = sorted(
                        search_summary.solutions,
                        key=lambda rooted: measure(rooted.sequence, metric=metric),
                    )

                    for rooted_solution in rooted_solutions:
                        solution = rooted_solution.sequence
                        new_permutation = get_rubiks_cube_permutation(
                            sequence=solution,
                            move_meta=move_meta,
                            initial_permutation=candidate.permutation,
                        )
                        new_candidate = BeamCandidate(
                            permutation=new_permutation,
                            steps=candidate.steps.with_step(solution),
                            side=side,
                            goal_history=(*candidate.goal_history, context.goal),
                            variant_history=(*candidate.variant_history, context.variant),
                            cost=candidate.cost + measure(solution, metric=metric),
                        )
                        if step_index == len(contexts) - 1:
                            _insert_solution(
                                best_solutions, new_candidate, max_solutions=max_solutions
                            )
                        else:
                            next_beam.append(new_candidate)

                if timed_out:
                    break

            if timed_out:
                break

        if timed_out:
            break

        if step_index == len(contexts) - 1:
            break

        if not next_beam:
            break

        beam = select_top_k(candidates=next_beam, k=beam_width)

    walltime = time.perf_counter() - start_time
    status = Status.Success if best_solutions else Status.Failure

    LOGGER.info(f"Beam search found {len(best_solutions)} solutions in {walltime:.2f}s")

    return BeamSearchSummary(
        solutions=best_solutions,
        walltime=walltime,
        status=status,
    )
