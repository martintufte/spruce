from __future__ import annotations

import logging
import time
from enum import Enum
from typing import TYPE_CHECKING
from typing import Callable
from typing import Sequence
from typing import TypeAlias

from attrs import frozen

from rubiks_cube.autotagger import get_rubiks_cube_patterns
from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.autotagger.subset import distinguish_htr
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.configuration.types import SolutionValidator
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.steps import MoveSteps
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.bidirectional import BidirectionalSolver

if TYPE_CHECKING:
    from rubiks_cube.beam_search.interface import BeamPlan
    from rubiks_cube.beam_search.interface import BeamStep

BeamHeuristic: TypeAlias = Callable[[CubePermutation, Sequence["_StepOptions"]], float]
LOGGER = logging.getLogger(__name__)


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
    steps: MoveSteps
    cost: int


@frozen
class BeamSearchSummary:
    solutions: list[BeamSolution]
    walltime: float
    status: Status


@frozen
class BeamCandidate:
    sequence: MoveSequence
    steps: MoveSteps
    permutation: CubePermutation
    cost: int
    side: SearchSide
    last_goal: Goal


def _step_sides(candidate: BeamCandidate, step: BeamStep) -> tuple[SearchSide, ...]:
    if step.transition.search_side == "prev":
        return (candidate.side,)
    if step.transition.search_side == "normal":
        return (SearchSide.normal,)
    if step.transition.search_side == "inverse":
        return (SearchSide.inverse,)
    if step.transition.search_side == "switch":
        return (candidate.side.toggle(),)
    return (candidate.side, candidate.side.toggle())


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
    allowed_prev_goals_by_goal: dict[Goal, frozenset[Goal]] | None = None

    def contexts_for_prev_goal(self, prev_goal: Goal = Goal.none) -> list[_StepContext]:
        generator = self.step.transition.generator_map.get(prev_goal, self.step.generator)
        if generator is not None:
            return self.contexts_by_generator.get(str(generator), [])
        return self.contexts_by_generator.get(self.default_generator_key, [])

    def allowed_prev_goals_for(self, goal: Goal) -> frozenset[Goal] | None:
        if self.allowed_prev_goals_by_goal is None:
            return None
        return self.allowed_prev_goals_by_goal.get(goal)


def select_top_k(candidates: list[BeamCandidate], k: int) -> list[BeamCandidate]:
    scored = [(candidate, candidate.cost) for candidate in candidates]
    scored.sort(key=lambda item: (item[1], item[0].cost))
    return [candidate for candidate, _score in scored[:k]]


def _insert_solution(
    best_solutions: list[BeamSolution],
    candidate: BeamCandidate,
    max_solutions: int,
) -> None:
    best_solutions.append(
        BeamSolution(sequence=candidate.sequence, steps=candidate.steps, cost=candidate.cost)
    )
    best_solutions.sort(key=lambda solution: solution.cost)
    del best_solutions[max_solutions:]


def _build_step_contexts(plan: BeamPlan, cube_size: int) -> list[_StepOptions]:
    default_generator = MoveGenerator.from_str(DEFAULT_GENERATOR)
    cubexes = get_cubexes(cube_size=cube_size)
    contexts: list[_StepOptions] = []
    prev_goals: tuple[Goal, ...] = ()

    for step in plan.steps:
        base_generator = step.generator or default_generator
        generator_map: dict[str, MoveGenerator] = {str(base_generator): base_generator}
        for generator in step.transition.generator_map.values():
            generator_map.setdefault(str(generator), generator)

        contexts_by_generator: dict[str, list[_StepContext]] = {}
        for generator_key, generator in generator_map.items():
            actions = get_actions(generator=generator, cube_size=cube_size)
            goal_contexts: list[_StepContext] = []
            for goal in step.goals:
                patterns = get_rubiks_cube_patterns(goal=goal, cube_size=cube_size)
                assert len(patterns) == 1, "Only support one pattern for now"
                pattern = patterns[0]

                solution_validator: SolutionValidator | None = None
                if goal == Goal.htr:

                    def _is_real_htr(permutation: CubePermutation) -> bool:
                        return distinguish_htr(permutation) == "real"

                    solution_validator = _is_real_htr

                solver = BidirectionalSolver.from_actions_and_pattern(
                    actions=actions,
                    pattern=pattern,
                    cube_size=cube_size,
                    optimize_indices=False,
                    solution_validator=solution_validator,
                )
                goal_contexts.append(
                    _StepContext(step=step, solver=solver, pattern=pattern, goal=goal)
                )
            contexts_by_generator[generator_key] = goal_contexts

        allowed_prev_goals_by_goal: dict[Goal, frozenset[Goal]] | None = None
        if step.transition.check_contained and len(prev_goals) > 0:
            allowed_prev_goals_by_goal = {}
            for goal in step.goals:
                goal_cubex = cubexes[goal]
                allowed_prev_goals_by_goal[goal] = frozenset(
                    prev_goal for prev_goal in prev_goals if cubexes[prev_goal] in goal_cubex
                )

        contexts.append(
            _StepOptions(
                step=step,
                contexts_by_generator=contexts_by_generator,
                default_generator_key=str(base_generator),
                allowed_prev_goals_by_goal=allowed_prev_goals_by_goal,
            )
        )
        prev_goals = tuple(step.goals)

    return contexts


def _passes_prev_goal_filter(
    prev_goal: Goal | None,
    allowed_prev_goals: frozenset[Goal] | None,
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
    max_solutions: int = 1,
    max_time: float = 60.0,
    cube_size: int = CUBE_SIZE,
    metric: Metric = DEFAULT_METRIC,
) -> BeamSearchSummary:
    if not plan.steps:
        raise ValueError("Beam plan must contain at least one step.")
    if beam_width < 1:
        raise ValueError("Beam width must be at least 1.")
    if max_solutions < 1:
        raise ValueError("Maximum number of solutions must be at least 1.")

    LOGGER.info(f"Running beam search with plan '{plan.name}'..")

    contexts = _build_step_contexts(plan=plan, cube_size=cube_size)
    start_time = time.perf_counter()

    beam: list[BeamCandidate] = [
        BeamCandidate(
            sequence=MoveSequence(),
            steps=MoveSteps(),
            permutation=get_rubiks_cube_permutation(sequence=sequence, cube_size=cube_size),
            cost=0,
            side=SearchSide.normal,
            last_goal=Goal.none,
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

            step_contexts = step_options.contexts_for_prev_goal(candidate.last_goal)
            for context in step_contexts:
                if not _passes_prev_goal_filter(
                    prev_goal=candidate.last_goal,
                    allowed_prev_goals=step_options.allowed_prev_goals_for(context.goal),
                ):
                    continue

                for side in _step_sides(candidate, step_options.step):
                    search_summary = context.solver.search(
                        permutation=candidate.permutation,
                        max_solutions=step_options.step.max_solutions,
                        min_search_depth=step_options.step.min_search_depth,
                        max_search_depth=step_options.step.max_search_depth,
                        max_time=step_time,
                        search_inverse=side is SearchSide.inverse,
                    )

                    if search_summary.status is Status.Failure:
                        continue

                    step_solutions = search_summary.solutions
                    if len(step_solutions) == 0:
                        step_solutions = [MoveSequence()]
                    else:
                        step_solutions = sorted(
                            step_solutions,
                            key=lambda seq: measure(seq, metric=metric),
                        )

                    for solution in step_solutions:
                        new_permutation = get_rubiks_cube_permutation(
                            sequence=solution,
                            initial_permutation=candidate.permutation,
                            cube_size=cube_size,
                        )

                        new_steps = candidate.steps.with_step(solution)
                        new_sequence = candidate.sequence + solution
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
                            _insert_solution(
                                best_solutions, new_candidate, max_solutions=max_solutions
                            )
                        else:
                            next_beam.append(new_candidate)

        if timed_out:
            break

        if step_index == len(contexts) - 1:
            break

        if not next_beam:
            break

        beam = select_top_k(candidates=next_beam, k=beam_width)

    walltime = time.perf_counter() - start_time
    status = Status.Success if best_solutions else Status.Failure

    LOGGER.info(f"Beam search found {len(best_solutions)} solutions. " f"Walltime: {walltime:.2f}s")

    return BeamSearchSummary(
        solutions=best_solutions,
        walltime=walltime,
        status=status,
    )
