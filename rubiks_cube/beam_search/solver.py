from __future__ import annotations

import asyncio
import math
import time
from typing import TYPE_CHECKING
from typing import Callable
from typing import Sequence
from typing import TypeAlias

import numpy as np
from attrs import frozen

from rubiks_cube.autotagger import get_rubiks_cube_pattern
from rubiks_cube.autotagger.subset import get_subset_label
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import measure
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.permutation import apply_moves_to_permutation
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.bidirectional import BidirectionalSolver

if TYPE_CHECKING:
    from rubiks_cube.beam_search.models import BeamPlan
    from rubiks_cube.beam_search.models import BeamStep

BeamHeuristic: TypeAlias = Callable[[CubePermutation, Sequence["_StepOptions"]], float]


@frozen
class BeamSolution:
    sequence: MoveSequence
    steps: list[MoveSequence]
    cost: int


@frozen
class BeamSearchSummary:
    solutions: list[BeamSolution]
    walltime: float
    status: Status


@frozen
class _BeamCandidate:
    sequence: MoveSequence
    steps: list[MoveSequence]
    permutation: CubePermutation
    cost: int
    last_goal: Goal | None


@frozen
class _StepContext:
    step: BeamStep
    solver: BidirectionalSolver
    pattern: CubePattern
    goal: Goal


@frozen
class _StepOptions:
    step: BeamStep
    contexts_by_generator: dict[str, list[_StepContext]]
    default_generator_key: str

    def contexts_for_prev_goal(self, prev_goal: Goal | None) -> list[_StepContext]:
        if self.step.transition is not None:
            generator = self.step.transition.generator_for_prev_goal(prev_goal, self.step.generator)
            if generator is not None:
                return self.contexts_by_generator.get(str(generator), [])
        return self.contexts_by_generator.get(self.default_generator_key, [])


def _pattern_mismatch_count(permutation: CubePermutation, pattern: CubePattern) -> int:
    mask = pattern != 0
    if not np.any(mask):
        return 0
    permuted = pattern[permutation]
    return int(np.count_nonzero(permuted[mask] != pattern[mask]))


def _estimate_remaining_depth(
    permutation: CubePermutation,
    remaining_steps: Sequence[_StepOptions],
    mismatch_divisor: int,
) -> float:
    if not remaining_steps:
        return 0.0

    min_depth = sum(step.step.min_search_depth for step in remaining_steps)
    final_patterns: list[CubePattern] = []
    for contexts in remaining_steps[-1].contexts_by_generator.values():
        final_patterns.extend(context.pattern for context in contexts)
    mismatch = min(_pattern_mismatch_count(permutation, pattern) for pattern in final_patterns)
    mismatch_estimate = math.ceil(mismatch / mismatch_divisor) if mismatch else 0

    return float(min_depth + mismatch_estimate)


def _default_heuristic(mismatch_divisor: int) -> BeamHeuristic:
    def estimate(permutation: CubePermutation, remaining_steps: Sequence[_StepOptions]) -> float:
        return _estimate_remaining_depth(
            permutation=permutation,
            remaining_steps=remaining_steps,
            mismatch_divisor=mismatch_divisor,
        )

    return estimate


def _normalize_solutions(
    solutions: list[list[str]] | None,
    metric: Metric,
) -> list[MoveSequence] | None:
    if solutions is None:
        return None
    if len(solutions) == 0:
        return [MoveSequence()]

    sequences = [MoveSequence(solution) for solution in solutions]
    return sorted(sequences, key=lambda seq: measure(seq, metric=metric))


def _select_top_k(
    candidates: list[_BeamCandidate],
    beam_width: int,
    heuristic: BeamHeuristic,
    remaining_steps: Sequence[_StepOptions],
) -> list[_BeamCandidate]:
    scored = [
        (
            candidate,
            candidate.cost + heuristic(candidate.permutation, remaining_steps),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (item[1], item[0].cost))
    return [candidate for candidate, _score in scored[:beam_width]]


def _insert_solution(
    best_solutions: list[BeamSolution],
    candidate: _BeamCandidate,
    n_solutions: int,
) -> None:
    best_solutions.append(
        BeamSolution(sequence=candidate.sequence, steps=candidate.steps, cost=candidate.cost)
    )
    best_solutions.sort(key=lambda solution: solution.cost)
    del best_solutions[n_solutions:]


def _build_step_contexts(plan: BeamPlan, cube_size: int) -> list[_StepOptions]:
    default_generator = MoveGenerator.from_str(DEFAULT_GENERATOR)
    contexts: list[_StepOptions] = []

    for step in plan.steps:
        base_generator = step.generator or default_generator
        generator_map: dict[str, MoveGenerator] = {str(base_generator): base_generator}
        if step.transition is not None and step.transition.generator_by_prev_goal is not None:
            for generator in step.transition.generator_by_prev_goal.values():
                generator_map.setdefault(str(generator), generator)

        contexts_by_generator: dict[str, list[_StepContext]] = {}
        for generator_key, generator in generator_map.items():
            actions = get_actions(
                generator=generator, algorithms=step.algorithms, cube_size=cube_size
            )
            goal_contexts: list[_StepContext] = []
            for goal in step.goals:
                pattern = get_rubiks_cube_pattern(
                    goal=goal, subset=step.subset, cube_size=cube_size
                )
                solver = BidirectionalSolver.from_actions_and_pattern(
                    actions=actions,
                    pattern=pattern,
                    cube_size=cube_size,
                    optimize_indices=False,
                )
                goal_contexts.append(
                    _StepContext(step=step, solver=solver, pattern=pattern, goal=goal)
                )
            contexts_by_generator[generator_key] = goal_contexts

        contexts.append(
            _StepOptions(
                step=step,
                contexts_by_generator=contexts_by_generator,
                default_generator_key=str(base_generator),
            )
        )

    return contexts


def _passes_subset_filter(
    permutation: CubePermutation,
    goal: Goal,
    allowed_subsets: list[str] | None,
) -> bool:
    if allowed_subsets is None:
        return True
    subset = get_subset_label(goal.value, permutation)
    return subset in allowed_subsets


def _passes_prev_goal_filter(
    prev_goal: Goal | None,
    allowed_prev_goals: list[Goal] | None,
) -> bool:
    if allowed_prev_goals is None:
        return True
    if prev_goal is None:
        return False
    return prev_goal in allowed_prev_goals


def beam_search(
    sequence: MoveSequence,
    plan: BeamPlan,
    beam_width: int,
    n_solutions: int = 1,
    max_time: float = 60.0,
    cube_size: int = CUBE_SIZE,
    metric: Metric = DEFAULT_METRIC,
    heuristic: BeamHeuristic | None = None,
    mismatch_divisor: int = 8,
) -> BeamSearchSummary:
    if not plan.steps:
        raise ValueError("Beam plan must contain at least one step.")
    if beam_width < 1:
        raise ValueError("Beam width must be at least 1.")
    if n_solutions < 1:
        raise ValueError("Number of solutions must be at least 1.")
    if mismatch_divisor < 1:
        raise ValueError("Mismatch divisor must be at least 1.")

    search_heuristic = heuristic or _default_heuristic(mismatch_divisor)
    contexts = _build_step_contexts(plan=plan, cube_size=cube_size)
    start_time = time.perf_counter()

    initial_permutation = get_rubiks_cube_state(sequence=sequence, cube_size=cube_size)
    beam: list[_BeamCandidate] = [
        _BeamCandidate(
            sequence=MoveSequence(),
            steps=[],
            permutation=initial_permutation,
            cost=0,
            last_goal=None,
        )
    ]

    best_solutions: list[BeamSolution] = []

    timed_out = False

    for step_index, step_options in enumerate(contexts):
        remaining_steps = contexts[step_index + 1 :]
        allowed_subsets = step_options.step.allowed_subsets()
        next_beam: list[_BeamCandidate] = []

        for candidate in beam:
            elapsed = time.perf_counter() - start_time
            if elapsed >= max_time:
                timed_out = True
                break

            remaining_time = max_time - elapsed
            if remaining_time <= 0:
                timed_out = True
                break
            step_time = remaining_time
            if step_options.step.max_time is not None:
                step_time = min(step_time, step_options.step.max_time)

            step_contexts = step_options.contexts_for_prev_goal(candidate.last_goal)
            for context in step_contexts:
                allowed_prev = None
                if step_options.step.transition is not None:
                    allowed_prev = step_options.step.transition.allowed_prev_goals_for(context.goal)
                if not _passes_prev_goal_filter(
                    prev_goal=candidate.last_goal,
                    allowed_prev_goals=allowed_prev,
                ):
                    continue
                solutions = context.solver.search(
                    permutation=candidate.permutation,
                    n_solutions=step_options.step.solver_n_solutions(),
                    min_search_depth=step_options.step.min_search_depth,
                    max_search_depth=step_options.step.max_search_depth,
                    max_time=step_time,
                )
                sequences = _normalize_solutions(solutions, metric=metric)
                if sequences is None:
                    continue

                for solution in sequences:
                    new_permutation = apply_moves_to_permutation(
                        candidate.permutation, solution, cube_size=cube_size
                    )
                    new_steps = [*candidate.steps, solution]
                    new_sequence = candidate.sequence + solution
                    new_cost = candidate.cost + measure(solution, metric=metric)
                    if not _passes_subset_filter(
                        permutation=new_permutation,
                        goal=context.goal,
                        allowed_subsets=allowed_subsets,
                    ):
                        continue

                    new_candidate = _BeamCandidate(
                        sequence=new_sequence,
                        steps=new_steps,
                        permutation=new_permutation,
                        cost=new_cost,
                        last_goal=context.goal,
                    )

                    if step_index == len(contexts) - 1:
                        _insert_solution(best_solutions, new_candidate, n_solutions=n_solutions)
                    else:
                        next_beam.append(new_candidate)

        if timed_out:
            break

        if step_index == len(contexts) - 1:
            break

        if not next_beam:
            break

        beam = _select_top_k(
            candidates=next_beam,
            beam_width=beam_width,
            heuristic=search_heuristic,
            remaining_steps=remaining_steps,
        )

    status = Status.Success if best_solutions else Status.Failure
    return BeamSearchSummary(
        solutions=best_solutions,
        walltime=time.perf_counter() - start_time,
        status=status,
    )


async def beam_search_async(
    sequence: MoveSequence,
    plan: BeamPlan,
    beam_width: int,
    n_solutions: int = 1,
    max_time: float = 60.0,
    cube_size: int = CUBE_SIZE,
    metric: Metric = DEFAULT_METRIC,
    heuristic: BeamHeuristic | None = None,
    mismatch_divisor: int = 8,
) -> BeamSearchSummary:
    if not plan.steps:
        raise ValueError("Beam plan must contain at least one step.")
    if beam_width < 1:
        raise ValueError("Beam width must be at least 1.")
    if n_solutions < 1:
        raise ValueError("Number of solutions must be at least 1.")
    if mismatch_divisor < 1:
        raise ValueError("Mismatch divisor must be at least 1.")

    search_heuristic = heuristic or _default_heuristic(mismatch_divisor)
    contexts = _build_step_contexts(plan=plan, cube_size=cube_size)
    start_time = time.perf_counter()

    initial_permutation = get_rubiks_cube_state(sequence=sequence, cube_size=cube_size)
    beam: list[_BeamCandidate] = [
        _BeamCandidate(
            sequence=MoveSequence(),
            steps=[],
            permutation=initial_permutation,
            cost=0,
            last_goal=None,
        )
    ]

    best_solutions: list[BeamSolution] = []

    timed_out = False

    for step_index, step_options in enumerate(contexts):
        remaining_steps = contexts[step_index + 1 :]
        allowed_subsets = step_options.step.allowed_subsets()
        next_beam: list[_BeamCandidate] = []

        for candidate in beam:
            elapsed = time.perf_counter() - start_time
            if elapsed >= max_time:
                timed_out = True
                break

            remaining_time = max_time - elapsed
            if remaining_time <= 0:
                timed_out = True
                break
            step_time = remaining_time
            if step_options.step.max_time is not None:
                step_time = min(step_time, step_options.step.max_time)

            step_contexts = step_options.contexts_for_prev_goal(candidate.last_goal)
            for context in step_contexts:
                allowed_prev = None
                if step_options.step.transition is not None:
                    allowed_prev = step_options.step.transition.allowed_prev_goals_for(context.goal)
                if not _passes_prev_goal_filter(
                    prev_goal=candidate.last_goal,
                    allowed_prev_goals=allowed_prev,
                ):
                    continue
                solutions = context.solver.search(
                    permutation=candidate.permutation,
                    n_solutions=step_options.step.solver_n_solutions(),
                    min_search_depth=step_options.step.min_search_depth,
                    max_search_depth=step_options.step.max_search_depth,
                    max_time=step_time,
                )
                sequences = _normalize_solutions(solutions, metric=metric)
                if sequences is None:
                    continue

                for solution in sequences:
                    new_permutation = apply_moves_to_permutation(
                        candidate.permutation, solution, cube_size=cube_size
                    )
                    new_steps = [*candidate.steps, solution]
                    new_sequence = candidate.sequence + solution
                    new_cost = candidate.cost + measure(solution, metric=metric)
                    if not _passes_subset_filter(
                        permutation=new_permutation,
                        goal=context.goal,
                        allowed_subsets=allowed_subsets,
                    ):
                        continue

                    new_candidate = _BeamCandidate(
                        sequence=new_sequence,
                        steps=new_steps,
                        permutation=new_permutation,
                        cost=new_cost,
                        last_goal=context.goal,
                    )

                    if step_index == len(contexts) - 1:
                        _insert_solution(best_solutions, new_candidate, n_solutions=n_solutions)
                    else:
                        next_beam.append(new_candidate)

            await asyncio.sleep(0)

        if timed_out:
            break

        if step_index == len(contexts) - 1:
            break

        if not next_beam:
            break

        beam = _select_top_k(
            candidates=next_beam,
            beam_width=beam_width,
            heuristic=search_heuristic,
            remaining_steps=remaining_steps,
        )
        await asyncio.sleep(0)

    status = Status.Success if best_solutions else Status.Failure
    return BeamSearchSummary(
        solutions=best_solutions,
        walltime=time.perf_counter() - start_time,
        status=status,
    )
