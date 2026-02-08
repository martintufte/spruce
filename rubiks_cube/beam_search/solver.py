from __future__ import annotations

import time
from enum import Enum
from typing import TYPE_CHECKING
from typing import Callable
from typing import Sequence
from typing import TypeAlias

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
from rubiks_cube.move.utils import niss_move
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.permutation import apply_moves_to_permutation
from rubiks_cube.representation.utils import invert
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.bidirectional import BidirectionalSolver

if TYPE_CHECKING:
    from rubiks_cube.beam_search.interface import BeamPlan
    from rubiks_cube.beam_search.interface import BeamStep

BeamHeuristic: TypeAlias = Callable[[CubePermutation, Sequence["_StepOptions"]], float]


class SearchSide(str, Enum):
    normal = "normal"
    inverse = "inverse"

    def toggle(self) -> SearchSide:
        if self == SearchSide.normal:
            return SearchSide.inverse
        return SearchSide.normal


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
class BeamCandidate:
    sequence: MoveSequence
    steps: list[MoveSequence]
    permutation: CubePermutation
    cost: int
    last_goal: Goal | None
    side: SearchSide


def _step_sides(candidate: BeamCandidate, step: BeamStep) -> tuple[SearchSide, ...]:
    transition = step.transition
    if transition is None or transition.side_mode == "same":
        return (candidate.side,)
    if transition.side_mode == "normal":
        return (SearchSide.normal,)
    if transition.side_mode == "inverse":
        return (SearchSide.inverse,)
    if transition.side_mode == "switch":
        return (candidate.side.toggle(),)
    return (candidate.side, candidate.side.toggle())


def _search_permutation(permutation: CubePermutation, side: SearchSide) -> CubePermutation:
    if side is SearchSide.normal:
        return permutation
    return invert(permutation)


def _sequence_for_side(solution: MoveSequence, side: SearchSide) -> MoveSequence:
    if side is SearchSide.normal:
        return solution
    return MoveSequence([niss_move(move) for move in solution])


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


def select_top_k(candidates: list[BeamCandidate], k: int) -> list[BeamCandidate]:
    scored = [(candidate, candidate.cost) for candidate in candidates]
    scored.sort(key=lambda item: (item[1], item[0].cost))
    return [candidate for candidate, _score in scored[:k]]


def _insert_solution(
    best_solutions: list[BeamSolution],
    candidate: BeamCandidate,
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
            actions = get_actions(generator=generator, cube_size=cube_size)
            goal_contexts: list[_StepContext] = []
            for goal in step.goals:
                pattern = get_rubiks_cube_pattern(goal=goal, cube_size=cube_size)
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
) -> BeamSearchSummary:
    if not plan.steps:
        raise ValueError("Beam plan must contain at least one step.")
    if beam_width < 1:
        raise ValueError("Beam width must be at least 1.")
    if n_solutions < 1:
        raise ValueError("Number of solutions must be at least 1.")

    contexts = _build_step_contexts(plan=plan, cube_size=cube_size)
    start_time = time.perf_counter()

    initial_permutation = get_rubiks_cube_state(sequence=sequence, cube_size=cube_size)
    beam: list[BeamCandidate] = [
        BeamCandidate(
            sequence=MoveSequence(),
            steps=[],
            permutation=initial_permutation,
            cost=0,
            last_goal=None,
            side=SearchSide.normal,
        )
    ]

    best_solutions: list[BeamSolution] = []

    timed_out = False

    for step_index, step_options in enumerate(contexts):
        next_beam: list[BeamCandidate] = []

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
                for side in _step_sides(candidate, step_options.step):
                    permutation_to_solve = _search_permutation(candidate.permutation, side)
                    solutions = context.solver.search(
                        permutation=permutation_to_solve,
                        n_solutions=step_options.step.n_solutions,
                        min_search_depth=step_options.step.min_search_depth,
                        max_search_depth=step_options.step.max_search_depth,
                        max_time=step_time,
                    )
                    sequences = _normalize_solutions(solutions, metric=metric)
                    if sequences is None:
                        continue

                    for solution in sequences:
                        solved_permutation = apply_moves_to_permutation(
                            permutation_to_solve, solution, cube_size=cube_size
                        )
                        if side is SearchSide.normal:
                            new_permutation = solved_permutation
                        else:
                            new_permutation = invert(solved_permutation)

                        allowed_subsets = step_options.step.allowed_subsets(context.goal)
                        if not _passes_subset_filter(
                            permutation=solved_permutation,
                            goal=context.goal,
                            allowed_subsets=allowed_subsets,
                        ):
                            continue

                        step_solution = _sequence_for_side(solution, side)
                        new_steps = [*candidate.steps, step_solution]
                        new_sequence = candidate.sequence + step_solution
                        new_cost = candidate.cost + measure(solution, metric=metric)

                        new_candidate = BeamCandidate(
                            sequence=new_sequence,
                            steps=new_steps,
                            permutation=new_permutation,
                            cost=new_cost,
                            last_goal=context.goal,
                            side=side,
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

        beam = select_top_k(candidates=next_beam, k=beam_width)

    status = Status.Success if best_solutions else Status.Failure
    return BeamSearchSummary(
        solutions=best_solutions,
        walltime=time.perf_counter() - start_time,
        status=status,
    )
