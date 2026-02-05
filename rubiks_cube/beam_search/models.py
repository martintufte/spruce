from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import Sequence

from attrs import frozen

from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.generator import MoveGenerator

if TYPE_CHECKING:
    from rubiks_cube.move.algorithm import MoveAlgorithm


def _parse_goal(value: Goal | str) -> Goal:
    if isinstance(value, Goal):
        return value
    try:
        return Goal(value)
    except ValueError:
        try:
            return Goal[value]
        except KeyError as exc:
            raise ValueError(f"Unknown goal: {value}") from exc


def _parse_generator(value: MoveGenerator | str | None) -> MoveGenerator | None:
    if value is None:
        return None
    if isinstance(value, MoveGenerator):
        return value
    if isinstance(value, str):
        return MoveGenerator.from_str(value)
    raise TypeError("Generator must be a MoveGenerator, string, or None.")


@frozen
class TransitionSpec:
    allowed_prev_goals: dict[Goal, list[Goal]] | None = None
    generator_by_prev_goal: dict[Goal, MoveGenerator] | None = None

    def allowed_prev_goals_for(self, goal: Goal) -> list[Goal] | None:
        if self.allowed_prev_goals is None:
            return None
        return self.allowed_prev_goals.get(goal)

    def generator_for_prev_goal(
        self, prev_goal: Goal | None, fallback: MoveGenerator | None
    ) -> MoveGenerator | None:
        if prev_goal is None or self.generator_by_prev_goal is None:
            return fallback
        return self.generator_by_prev_goal.get(prev_goal, fallback)


@frozen
class BeamStep:
    name: str
    goals: list[Goal]
    subset: str | None = None
    subset_filters: list[str] | None = None
    transition: TransitionSpec | None = None
    generator: MoveGenerator | None = None
    algorithms: list[MoveAlgorithm] | None = None
    min_search_depth: int = 0
    max_search_depth: int = 10
    n_solutions: int = 1
    search_solutions: int | None = None
    max_time: float | None = None

    def allowed_subsets(self) -> list[str] | None:
        if self.subset_filters is None:
            return None
        if not self.subset_filters:
            raise ValueError("BeamStep subset_filters cannot be empty.")
        return list(self.subset_filters)

    def solver_n_solutions(self) -> int:
        if self.search_solutions is None:
            return self.n_solutions
        return max(self.n_solutions, self.search_solutions)


@frozen
class BeamPlan:
    steps: list[BeamStep]
    name: str | None = None

    @classmethod
    def from_steps(cls, steps: Sequence[BeamStep], name: str | None = None) -> BeamPlan:
        return cls(steps=list(steps), name=name)

    @classmethod
    def from_dict(cls, data: Mapping[str, Mapping[str, Any]], name: str | None = None) -> BeamPlan:
        steps: list[BeamStep] = []

        for step_name, raw in data.items():
            if not isinstance(raw, Mapping):
                raise TypeError("Each step spec must be a mapping of settings.")

            goals_raw = raw.get("goals", raw.get("goal", step_name))
            if isinstance(goals_raw, Sequence) and not isinstance(goals_raw, str):
                goals = [_parse_goal(item) for item in goals_raw]
            else:
                goals = [_parse_goal(goals_raw)]
            if not goals:
                raise ValueError("BeamStep goals cannot be empty.")
            subset = raw.get("subset")
            subset_filters = raw.get("subset_filters")
            if subset_filters is None and "subset_filter" in raw:
                subset_filters = [raw.get("subset_filter")]
            if subset_filters is not None:
                if isinstance(subset_filters, str):
                    raise TypeError("subset_filters must be a list, not a string.")
                if not isinstance(subset_filters, Sequence):
                    raise TypeError("subset_filters must be a list of strings.")
                subset_filters = [str(item) for item in subset_filters]
            generator = _parse_generator(raw.get("generator"))
            transition_data = raw.get("transition")
            if transition_data is not None and not isinstance(transition_data, Mapping):
                raise TypeError("transition must be a mapping of transition settings.")

            generator_by_prev_goal = raw.get("generator_by_prev_goal")
            allowed_prev_goals = raw.get("allowed_prev_goals")
            if transition_data is not None and (
                generator_by_prev_goal is not None or allowed_prev_goals is not None
            ):
                raise ValueError(
                    "Use transition or generator_by_prev_goal/allowed_prev_goals, not both."
                )

            if transition_data is not None:
                generator_by_prev_goal = transition_data.get("generator_by_prev_goal")
                allowed_prev_goals = transition_data.get("allowed_prev_goals")

            transition: TransitionSpec | None = None
            if generator_by_prev_goal is not None or allowed_prev_goals is not None:
                if generator_by_prev_goal is not None:
                    if not isinstance(generator_by_prev_goal, Mapping):
                        raise TypeError("generator_by_prev_goal must be a mapping.")
                    parsed_generators: dict[Goal, MoveGenerator] = {}
                    for key, value in generator_by_prev_goal.items():
                        parsed_goal = _parse_goal(key)
                        parsed_generator = _parse_generator(value)
                        if parsed_generator is None:
                            raise ValueError("generator_by_prev_goal values cannot be None.")
                        parsed_generators[parsed_goal] = parsed_generator
                    generator_by_prev_goal = parsed_generators

                if allowed_prev_goals is not None:
                    if not isinstance(allowed_prev_goals, Mapping):
                        raise TypeError("allowed_prev_goals must be a mapping.")
                    parsed_allowed: dict[Goal, list[Goal]] = {}
                    for key, value in allowed_prev_goals.items():
                        parsed_goal = _parse_goal(key)
                        if isinstance(value, str) or not isinstance(value, Sequence):
                            raise TypeError("allowed_prev_goals values must be lists of goals.")
                        parsed_allowed[parsed_goal] = [_parse_goal(item) for item in value]
                    allowed_prev_goals = parsed_allowed

                transition = TransitionSpec(
                    allowed_prev_goals=allowed_prev_goals,
                    generator_by_prev_goal=generator_by_prev_goal,
                )
            algorithms = raw.get("algorithms")

            min_search_depth = int(raw.get("min_search_depth", raw.get("min_depth", 0)))
            max_search_depth = int(raw.get("max_search_depth", raw.get("max_length", 10)))
            n_solutions = int(raw.get("n_solutions", raw.get("max_solutions", 1)))
            search_solutions = raw.get("search_solutions")
            if search_solutions is not None:
                search_solutions = int(search_solutions)
            max_time = raw.get("max_time", raw.get("time_limit"))

            steps.append(
                BeamStep(
                    name=step_name,
                    goals=goals,
                    subset=subset,
                    subset_filters=subset_filters,
                    transition=transition,
                    generator=generator,
                    algorithms=algorithms,
                    min_search_depth=min_search_depth,
                    max_search_depth=max_search_depth,
                    n_solutions=n_solutions,
                    search_solutions=search_solutions,
                    max_time=max_time,
                )
            )

        return cls(steps=steps, name=name)
