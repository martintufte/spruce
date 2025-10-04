"""Benchmarking script for the Rubik's Cube Solver - 3x3 Cross solving focus."""

from __future__ import annotations

import logging
import random
import statistics

import attrs
import numpy as np

from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.logging import configure_logging
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver import solve_step

# Setup logging
configure_logging()
LOGGER = logging.getLogger(__name__)


@attrs.define
class BenchmarkConfig:
    """Configuration for a benchmark test."""

    name: str
    cube_size: int = 3
    tag: str = "cross"
    max_search_depth: int = 8
    scramble_length: int = 20
    n_runs: int = 10


@attrs.define
class BenchmarkResult:
    """Results from a benchmark test."""

    config_name: str
    success_rate: float
    mean_walltime: float
    mean_solution_length: float
    n_runs: int
    successful_runs: int


class SolverBenchmark:
    """Main benchmarking class for the Rubik's cube solver."""

    def __init__(self) -> None:
        """Initialize the benchmark suite."""
        # Set random seeds for reproducibility
        random.seed(42)
        np.random.seed(42)

    def generate_scramble(self, length: int) -> MoveSequence:
        """Generate a random scramble sequence for 3x3 cube."""
        standard_moves = [
            "U",
            "R",
            "F",
            "L",
            "B",
            "D",
            "U'",
            "R'",
            "F'",
            "L'",
            "B'",
            "D'",
            "U2",
            "R2",
            "F2",
            "L2",
            "B2",
            "D2",
        ]

        # Generate moves avoiding consecutive same face moves
        scramble_moves: list[str] = []
        last_move = "I"  # Identity move

        for _ in range(length):
            available_moves = [move for move in standard_moves if not move.startswith(last_move[0])]
            last_move = random.choice(available_moves)
            scramble_moves.append(last_move)

        return MoveSequence(scramble_moves)

    def run_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run a complete benchmark for a given configuration."""
        LOGGER.info(f"Running benchmark with config: {config.name}")

        generator = MoveGenerator("<L, R, U, D, F, B>")
        walltimes: list[float] = []
        solution_lengths: list[int] = []
        successful_runs = 0

        for i in range(config.n_runs):
            scramble = self.generate_scramble(config.scramble_length)

            try:
                solutions, search_summary = solve_step(
                    sequence=scramble,
                    generator=generator,
                    tag=config.tag,
                    max_search_depth=config.max_search_depth,
                    cube_size=config.cube_size,
                )

                if search_summary.status == Status.Success and solutions:
                    successful_runs += 1
                    walltimes.append(search_summary.walltime)
                    solution_lengths.append(len(solutions[0].moves))

            except Exception as e:
                LOGGER.debug(f"Run {i + 1} failed: {e}")

        success_rate = successful_runs / config.n_runs if config.n_runs > 0 else 0.0
        mean_walltime = statistics.mean(walltimes) if walltimes else 0.0
        mean_solution_length = statistics.mean(solution_lengths) if solution_lengths else 0.0

        result = BenchmarkResult(
            config_name=config.name,
            success_rate=success_rate,
            mean_walltime=mean_walltime,
            mean_solution_length=mean_solution_length,
            n_runs=config.n_runs,
            successful_runs=successful_runs,
        )

        LOGGER.info(f"Completed: {success_rate:.1%} success, {mean_walltime:.3f}s avg")
        return result


def get_cross_config(n_runs: int = 10) -> BenchmarkConfig:
    """Get the default 3x3 cross solving configuration."""
    return BenchmarkConfig(
        name="3x3_cross",
        n_runs=n_runs,
    )


def main() -> None:
    """Main entry point - benchmarks 3x3 cross solving."""
    benchmark = SolverBenchmark()
    config = get_cross_config()
    result = benchmark.run_benchmark(config)

    print(f"\n3x3 Cross Solving Benchmark:")
    print(f"Success Rate: {result.success_rate:.1%}")
    print(f"Average Time: {result.mean_walltime:.3f}s")
    print(f"Average Moves: {result.mean_solution_length:.1f}")


if __name__ == "__main__":
    main()
