from __future__ import annotations

import logging
import statistics
import time
from typing import TYPE_CHECKING
from typing import Callable
from typing import Final

import numpy as np
from tqdm import tqdm

from rubiks_cube.formatting.regex import canonical_key
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.scrambler import scramble_generator
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.solver.actions import get_action_space
from rubiks_cube.solver.bidirectional.alpha import bidirectional_solver_v4
from rubiks_cube.solver.bidirectional.alpha import bidirectional_solver_v5
from rubiks_cube.solver.bidirectional.alpha import bidirectional_solver_v6
from rubiks_cube.solver.bidirectional.alpha import bidirectional_solver_v7
from rubiks_cube.solver.bidirectional.alpha import bidirectional_solver_v8
from rubiks_cube.solver.bidirectional.beta import bidirectional_solver
from rubiks_cube.solver.optimizers import DtypeOptimizer
from rubiks_cube.solver.optimizers import IndexOptimizer
from rubiks_cube.tag import get_rubiks_cube_pattern

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation

LOGGER: Final = logging.getLogger(__name__)


class AlphaSolver:
    def __init__(
        self,
        fn: Callable[
            [CubePermutation, dict[str, CubePermutation], CubePattern, int, int, float],
            list[list[str]] | None,
        ],
    ) -> None:
        self.fn = fn


class BetaSolver:
    def __init__(
        self,
        fn: Callable[
            [CubePermutation, dict[str, CubePermutation], CubePattern, int, int, BoolArray, float],
            list[list[str]] | None,
        ],
    ) -> None:
        self.fn = fn


def verify_solution(
    solution: list[str],
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
) -> bool:
    """Verify that a solution actually solves the cube."""
    try:
        current_perm = initial_permutation.copy()

        # Apply each move in the solution
        for move in solution:
            if move in actions:
                current_perm = current_perm[actions[move]]
            else:
                print(f"Warning: Unknown move '{move}' in solution")
                return False

        # Check if the final state matches the pattern (solved state)
        identity = np.arange(len(current_perm))
        target_pattern = pattern[identity]
        result_pattern = pattern[current_perm]

        return np.array_equal(target_pattern, result_pattern)
    except Exception as e:
        print(f"Error verifying solution: {e}")
        return False


def benchmark_solver(
    solver: AlphaSolver | BetaSolver,
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    canonical_matrix: BoolArray,
    max_depth: int = 10,
    n_solutions: int = 1,
    max_time: int = 15,
    n_trials: int = 10,
) -> tuple[float, float, float, list[list[str]]]:
    """Benchmark a single solver function."""
    times: list[float] = []
    solutions_found: list[int] = []
    solution_lengths: list[int] = []
    all_solutions: list[list[str]] = []

    for _ in range(n_trials):
        start_time = time.perf_counter()
        try:
            if isinstance(solver, AlphaSolver):
                solutions = solver.fn(
                    initial_permutation,
                    actions,
                    pattern,
                    max_depth,
                    n_solutions,
                    max_time,
                )
            elif isinstance(solver, BetaSolver):
                solutions = solver.fn(
                    initial_permutation,
                    actions,
                    pattern,
                    canonical_matrix,
                    max_depth,
                    n_solutions,
                    max_time,
                )
            else:
                raise ValueError("Unknown solver type")

            end_time = time.perf_counter()
            elapsed = end_time - start_time
            times.append(elapsed)

            if solutions is not None:
                solutions_found.append(True)
                # Count moves in solution
                solution_length = len(solutions[0])
                solution_lengths.append(solution_length)
                all_solutions.append(solutions[0])

                # Verify solution
                if not verify_solution(solutions[0], initial_permutation, actions, pattern):
                    print(f"❌ Invalid solution: {solutions[0]}")
            else:
                solutions_found.append(False)
                solution_lengths.append(0)
                all_solutions.append([])

        except Exception as e:
            print(f"Error in solver: {e}")
            times.append(float("inf"))
            solutions_found.append(False)
            solution_lengths.append(0)
            all_solutions.append([])

    avg_time = statistics.mean([t for t in times if t != float("inf")])
    success_rate = sum(solutions_found) / len(solutions_found)
    avg_solution_length = (
        statistics.mean([length for length in solution_lengths if length > 0])
        if any(length > 0 for length in solution_lengths)
        else 0
    )

    return avg_time, success_rate, avg_solution_length, all_solutions


def run_benchmark(
    solvers: dict[str, AlphaSolver | BetaSolver],
    min_scramble_length: int = 5,
    max_scramble_length: int = 8,
    n_trials: int = 100,
    max_depth: int = 10,
    seed: int = 42,
) -> dict[str, dict[str, list[float]]]:
    """Run comprehensive benchmark comparing all solvers.

    Args:
        solvers (dict[str, AlphaSolver | BetaSolver]): Dictionary mapping solver names to solver functions.
        min_scramble_length (int): Minimum scramble length to test.
        max_scramble_length (int): Maximum scramble length to test.
        n_trials (int): Number of trials per scramble length.
        max_depth (int): Maximum search depth for solvers.
        seed (int): Random seed for reproducibility.

    Returns:
        dict[str, dict[str, list[float]]] Dictionary containing benchmark results for each solver.
    """
    LOGGER.info(f"🧩 Starting benchmark with {len(solvers)} solvers")
    LOGGER.info(f"Scramble lengths: {min_scramble_length}-{max_scramble_length}")
    LOGGER.info(f"Trials per length: {n_trials}")
    LOGGER.info(f"Max search depth: {max_depth}")

    # Set seeds for reproducibility
    rng = np.random.default_rng(seed=42)
    cube_size = 3

    solver_names = list(solvers.keys())
    results: dict[str, dict[str, list[float]]] = {}

    # Setup solver actions
    generator = MoveGenerator("<L, R, U, D, F, B>")
    actions = get_action_space(generator=generator, cube_size=cube_size)
    pattern = get_rubiks_cube_pattern(tag="solved", cube_size=cube_size)

    # Apply index optimization to permutations
    index_optimizer = IndexOptimizer(cube_size=cube_size)
    actions = index_optimizer.fit_transform(actions=actions)
    pattern = index_optimizer.transform_pattern(pattern)

    # Apply dtpye optimization to pattern
    dtype_optimizer = DtypeOptimizer()
    pattern = dtype_optimizer.fit_transform(pattern)

    # Optimize canonical move order based on action space
    actions = {name: actions[name] for name in sorted(actions.keys(), key=canonical_key)}
    n_actions = len(actions)
    closed_perms: set[tuple[int, ...]] = {tuple(np.arange(pattern.size))}
    closed_perms |= {tuple(perm) for perm in actions.values()}

    canonical_matrix = np.ones((n_actions, n_actions), dtype=bool)
    for i, perm_i in enumerate(actions.values()):
        for j, perm_j in enumerate(actions.values()):
            perm_ji = tuple(perm_j[perm_i])
            if perm_ji in closed_perms or (i > j and perm_ji == tuple(perm_i[perm_j])):
                canonical_matrix[i, j] = False

    # Initialize results structure
    for solver_name in solver_names:
        results[solver_name] = {
            "times": [],
            "success_rates": [],
            "solution_lengths": [],
        }

    # Run benchmark for each scramble length
    for scramble_length in range(min_scramble_length, max_scramble_length + 1):
        LOGGER.info(f"📊 Testing scramble length: {scramble_length}")

        # Setup scramble generator
        scrambles = scramble_generator(
            length=scramble_length,
            generator=MoveGenerator("<L, R, U, D, F, B>"),
            cube_size=cube_size,
            n_scrambles=n_trials,
            rng=rng,
        )

        # Track performance for this scramble length
        length_results: dict[str, dict[str, list[float]]] = {}
        for solver_name in solver_names:
            length_results[solver_name] = {"times": [], "success": [], "solution_lengths": []}

        with tqdm(total=n_trials, desc=f"Length {scramble_length}", unit="trial") as pbar:
            for i, scramble in enumerate(scrambles):
                LOGGER.debug(f"Processing scramble {i+1}/{n_trials}: {scramble}")

                try:
                    # Prepare solver inputs
                    initial_permutation = get_rubiks_cube_state(
                        sequence=scramble, cube_size=cube_size
                    )
                    initial_permutation = index_optimizer.transform_permutation(initial_permutation)

                    # Test each solver on this scramble
                    for solver_name, solver in solvers.items():
                        avg_time, success_rate, avg_sol_len, _ = benchmark_solver(
                            solver=solver,
                            initial_permutation=initial_permutation,
                            actions=actions,
                            pattern=pattern,
                            canonical_matrix=canonical_matrix,
                            max_depth=max_depth,
                            n_solutions=1,
                            n_trials=1,
                        )

                        length_results[solver_name]["times"].append(avg_time)
                        length_results[solver_name]["success"].append(success_rate)
                        length_results[solver_name]["solution_lengths"].append(avg_sol_len)

                except Exception as e:
                    LOGGER.error(f"Error preparing scramble {scramble}: {e}")
                    # Add error entries for all solvers
                    for solver_name in solver_names:
                        length_results[solver_name]["times"].append(float("inf"))
                        length_results[solver_name]["success"].append(0.0)
                        length_results[solver_name]["solution_lengths"].append(0.0)

                pbar.update(1)

        # Calculate statistics for this scramble length
        for solver_name in solver_names:
            valid_times = [t for t in length_results[solver_name]["times"] if t != float("inf")]
            avg_time = statistics.mean(valid_times) if valid_times else float("inf")
            avg_success = statistics.mean(length_results[solver_name]["success"])
            valid_lengths = [
                length for length in length_results[solver_name]["solution_lengths"] if length > 0
            ]
            avg_length = statistics.mean(valid_lengths) if valid_lengths else 0.0

            results[solver_name]["times"].append(avg_time)
            results[solver_name]["success_rates"].append(avg_success)
            results[solver_name]["solution_lengths"].append(avg_length)

            LOGGER.info(
                f"  {solver_name}: {avg_time:.4f}s avg, {avg_success:.1%} success, {avg_length:.1f} moves avg"
            )

    # Print summary and calculate performance gains
    print_benchmark_summary(results, solver_names, min_scramble_length, max_scramble_length)

    return results


def print_benchmark_summary(
    results: dict[str, dict[str, list[float]]],
    solver_names: list[str],
    min_length: int,
    max_length: int,
) -> None:
    """Print comprehensive benchmark summary with performance comparisons."""
    LOGGER.info("📋 Generating benchmark summary")

    print("\n" + "=" * 100)
    print("🧩 RUBIK'S CUBE SOLVER BENCHMARK SUMMARY")
    print("=" * 100)

    # Build header
    header_parts = ["Length"]
    for name in solver_names:
        header_parts.extend([f"{name} Time", f"{name} Success", f"{name} Moves"])

    if len(solver_names) > 1:
        baseline = solver_names[0]
        header_parts.extend([f"{name}/{baseline}" for name in solver_names[1:]])

    # Print header
    col_width = 12
    header_format = "{:<8} " + " ".join([f"{{:<{col_width}}}"] * (len(header_parts) - 1))
    print(header_format.format(*header_parts))
    print("-" * (8 + col_width * (len(header_parts) - 1) + len(header_parts) - 1))

    # Print results for each scramble length
    overall_speedups: dict[str, list[float]] = {name: [] for name in solver_names[1:]}

    for i, length in enumerate(range(min_length, max_length + 1)):
        row_data = [str(length)]

        # Add performance data for each solver
        baseline_time = results[solver_names[0]]["times"][i] if solver_names else 0

        for name in solver_names:
            time_val = results[name]["times"][i]
            success_val = results[name]["success_rates"][i]
            moves_val = results[name]["solution_lengths"][i]

            row_data.extend(
                [
                    f"{time_val:.4f}s" if time_val != float("inf") else "∞",
                    f"{success_val:.1%}",
                    f"{moves_val:.1f}",
                ]
            )

        # Add speedup ratios if multiple solvers
        if len(solver_names) > 1:
            for name in solver_names[1:]:
                current_time = results[name]["times"][i]
                if current_time > 0 and baseline_time > 0 and current_time != float("inf"):
                    speedup = baseline_time / current_time
                    row_data.append(f"{speedup:.2f}x")
                    overall_speedups[name].append(speedup)
                else:
                    row_data.append("N/A")

        # Print row
        print(f"{row_data[0]:<8} ", end="")
        for _j, data in enumerate(row_data[1:], 1):
            print(f"{data:<{col_width}} ", end="")
        print()

    # Print overall performance summary
    if len(solver_names) > 1:
        print("-" * (8 + col_width * (len(header_parts) - 1) + len(header_parts) - 1))
        print("\n🚀 OVERALL PERFORMANCE GAINS:")

        baseline_name = solver_names[0]
        best_performer = baseline_name
        best_average_speedup = 1.0

        for name in solver_names[1:]:
            if overall_speedups[name]:
                avg_speedup = statistics.mean(overall_speedups[name])
                median_speedup = statistics.median(overall_speedups[name])

                print(f"   {name} vs {baseline_name}:")
                print(f"     Average speedup: {avg_speedup:.2f}x")
                print(f"     Median speedup:  {median_speedup:.2f}x")
                print(f"     Best speedup:    {max(overall_speedups[name]):.2f}x")

                if avg_speedup > best_average_speedup:
                    best_average_speedup = avg_speedup
                    best_performer = name

                LOGGER.info(f"{name} shows {avg_speedup:.2f}x average speedup over {baseline_name}")

        print(
            f"\n🏆 WINNER: {best_performer} with {best_average_speedup:.2f}x average performance gain!"
        )
        LOGGER.info(f"Benchmark complete. Best performer: {best_performer}")

    print("=" * 100)


def get_available_solvers() -> dict[str, AlphaSolver | BetaSolver]:
    """Get all available solver functions."""
    solvers: dict[str, AlphaSolver | BetaSolver] = {}

    solvers["a4"] = AlphaSolver(fn=bidirectional_solver_v4)
    solvers["a5"] = AlphaSolver(fn=bidirectional_solver_v5)
    solvers["a6"] = AlphaSolver(fn=bidirectional_solver_v6)
    solvers["a7"] = AlphaSolver(fn=bidirectional_solver_v7)
    solvers["a8"] = AlphaSolver(fn=bidirectional_solver_v8)
    solvers["b1"] = BetaSolver(fn=bidirectional_solver)

    return solvers


def main(
    solver_versions: list[str] | None = None,
    min_scramble_length: int = 5,
    max_scramble_length: int = 8,
    n_trials: int = 100,
    max_depth: int = 10,
    seed: int = 42,
    log_level: str = "INFO",
) -> None:
    """Run configurable solver benchmarks.

    Args:
        solver_versions: List of solver versions to test (e.g., ["v4", "v6", "v7"])
        min_scramble_length: Minimum scramble length to test
        max_scramble_length: Maximum scramble length to test
        n_trials: Number of trials per scramble length
        max_depth: Maximum search depth for solvers
        seed: Random seed for reproducibility
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    LOGGER.info("🚀 Starting Rubik's Cube Solver Benchmark")

    # Get available solvers
    available_solvers = get_available_solvers()
    LOGGER.info(f"Available solvers: {list(available_solvers.keys())}")

    # Select solvers to test
    if solver_versions is None:
        solver_versions = list(available_solvers.keys())
        LOGGER.info("No specific solvers requested, testing all available solvers")
    else:
        # Validate requested solvers
        invalid_solvers = [v for v in solver_versions if v not in available_solvers]
        if invalid_solvers:
            LOGGER.error(f"Invalid solver versions: {invalid_solvers}")
            LOGGER.error(f"Available versions: {list(available_solvers.keys())}")
            return

    # Build solver dictionary
    solvers_to_test = {
        version: available_solvers[version]
        for version in solver_versions
        if version in available_solvers
    }

    if not solvers_to_test:
        LOGGER.error("No valid solvers to test!")
        return

    LOGGER.info(f"Testing solvers: {list(solvers_to_test.keys())}")

    # Run benchmark
    _results = run_benchmark(
        solvers=solvers_to_test,
        min_scramble_length=min_scramble_length,
        max_scramble_length=max_scramble_length,
        n_trials=n_trials,
        max_depth=max_depth,
        seed=seed,
    )

    LOGGER.info("✅ Benchmark completed successfully!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Rubik's Cube solvers")
    parser.add_argument("solvers", nargs="*", default=["c1"], help="Solver versions to benchmark")
    parser.add_argument("--min-length", type=int, default=5, help="Minimum scramble length")
    parser.add_argument("--max-length", type=int, default=7, help="Maximum scramble length")
    parser.add_argument(
        "--n-trials", type=int, default=100, help="Number of trials per configuration"
    )
    parser.add_argument("--max-depth", type=int, default=10, help="Maximum search depth")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()

    main(
        solver_versions=args.solvers,
        min_scramble_length=args.min_length,
        max_scramble_length=args.max_length,
        n_trials=args.n_trials,
        max_depth=args.max_depth,
        seed=args.seed,
        log_level=args.log_level,
    )
