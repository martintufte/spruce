from __future__ import annotations

import random
import statistics
import time
from typing import Callable

import numpy as np

from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.solver.actions import get_action_space
from rubiks_cube.solver.bidirectional_solver import bidirectional_solver_v4
from rubiks_cube.solver.bidirectional_solver import bidirectional_solver_v5
from rubiks_cube.solver.bidirectional_solver import bidirectional_solver_v6
from rubiks_cube.solver.optimizers import IndexOptimizer
from rubiks_cube.tag import get_rubiks_cube_pattern


def generate_scramble(length: int) -> MoveSequence:
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


def prepare_solver_inputs(
    scramble: MoveSequence,
) -> tuple[CubePermutation, dict[str, CubePermutation], CubePattern]:
    """Prepare the inputs needed for both solvers."""
    generator = MoveGenerator("<L, R, U, D, F, B>")
    actions = get_action_space(generator=generator, cube_size=3)
    pattern = get_rubiks_cube_pattern(tag="solved", cube_size=3)

    initial_permutation = get_rubiks_cube_state(sequence=scramble, cube_size=3)

    # Apply index optimization
    optimizer = IndexOptimizer(cube_size=3)
    actions = optimizer.fit_transform(actions=actions)
    initial_permutation = optimizer.transform_permutation(initial_permutation)
    pattern = optimizer.transform_pattern(pattern)

    return initial_permutation, actions, pattern


def verify_solution(
    solution_str: str,
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
) -> bool:
    """Verify that a solution actually solves the cube."""
    try:
        current_perm = initial_permutation.copy()
        moves = solution_str.split()

        # Apply each move in the solution
        for move in moves:
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
    solver_func: Callable[
        [
            CubePermutation,
            dict[str, CubePermutation],
            CubePattern,
            int,
        ],
        list[list[str]] | list[str] | None,
    ],
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_depth: int = 10,
    n_trials: int = 10,
) -> tuple[float, float, float, list[str]]:
    """Benchmark a single solver function."""
    times = []
    solutions_found = []
    solution_lengths = []
    all_solutions = []

    for _ in range(n_trials):
        start_time = time.perf_counter()
        try:
            solutions = solver_func(
                initial_permutation,
                actions,
                pattern,
                max_depth,
            )
            if isinstance(solutions, list) and all(isinstance(sol, list) for sol in solutions):
                # Flatten list of lists to count moves
                solutions = [" ".join(sol) for sol in solutions]

            end_time = time.perf_counter()
            elapsed = end_time - start_time
            times.append(elapsed)

            if solutions is not None:
                assert isinstance(solutions[0], str)
                solutions_found.append(True)
                # Count moves in solution
                solution_length = len(solutions[0].split())
                solution_lengths.append(solution_length)
                all_solutions.append(solutions[0])

                # Verify solution
                if not verify_solution(solutions[0], initial_permutation, actions, pattern):
                    print(f"❌ Invalid solution: {solutions[0]}")
            else:
                solutions_found.append(False)
                solution_lengths.append(0)
                all_solutions.append("")

        except Exception as e:
            print(f"Error in solver: {e}")
            times.append(float("inf"))
            solutions_found.append(False)
            solution_lengths.append(0)
            all_solutions.append("")

    avg_time = statistics.mean([t for t in times if t != float("inf")])
    success_rate = sum(solutions_found) / len(solutions_found)
    avg_solution_length = (
        statistics.mean([l for l in solution_lengths if l > 0])
        if any(l > 0 for l in solution_lengths)
        else 0
    )

    return avg_time, success_rate, avg_solution_length, all_solutions


def run_benchmark() -> None:
    """Run comprehensive benchmark comparing all solvers."""
    print("🧩 Rubik's Cube Solver Benchmark: V4 vs V5 vs V6")
    print("=" * 60)
    print("V4:  Original bidirectional solver")
    print("V5:  Integer encoding + pruning optimizations")
    print("V6:  Correctness and performance improvements")
    print("Scramble lengths: 5-8 moves")
    print("Trials per scramble length: 100")
    print("Max search depth: 10")
    print()

    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    results = []

    for scramble_length in range(5, 9):
        print(f"📊 Testing scramble length: {scramble_length}")

        # Generate test scrambles
        scrambles = [generate_scramble(scramble_length) for _ in range(100)]

        v4_times = []
        v5_times = []
        v6_times = []
        v4_success = []
        v5_success = []
        v6_success = []
        v4_solution_lengths = []
        v5_solution_lengths = []
        v6_solution_lengths = []

        for i, scramble in enumerate(scrambles):
            print(f"  Trial {i+1}/100: {scramble}", end=" -> ")

            try:
                # Prepare solver inputs
                initial_perm, actions, pattern = prepare_solver_inputs(scramble)

                # Benchmark V4 solver
                v4_time, v4_succ, v4_sol_len, v4_solutions = benchmark_solver(
                    bidirectional_solver_v4,
                    initial_perm,
                    actions,
                    pattern,
                    max_depth=10,
                    n_trials=1,
                )

                # Benchmark V5 solver
                v5_time, v5_succ, v5_sol_len, v5_solutions = benchmark_solver(
                    bidirectional_solver_v5,
                    initial_perm,
                    actions,
                    pattern,
                    max_depth=10,
                    n_trials=1,
                )

                # Benchmark V6 solver
                v6_time, v6_succ, v6_sol_len, v6_solutions = benchmark_solver(
                    bidirectional_solver_v5,
                    initial_perm,
                    actions,
                    pattern,
                    max_depth=10,
                    n_trials=1,
                )

                v4_times.append(v4_time)
                v5_times.append(v5_time)
                v6_times.append(v6_time)
                v4_success.append(v4_succ)
                v5_success.append(v5_succ)
                v6_success.append(v6_succ)
                v4_solution_lengths.append(v4_sol_len)
                v5_solution_lengths.append(v5_sol_len)
                v6_solution_lengths.append(v6_sol_len)

                # Calculate speedups
                v5_speedup = v4_time / v5_time if v5_time > 0 else float("inf")
                v6_speedup = v4_time / v6_time if v6_time > 0 else float("inf")
                print(f"V5: {v5_speedup:.2f}x, V6: {v6_speedup:.2f}x")

            except Exception as e:
                print(f"Error: {e}")
                v4_times.append(float("inf"))
                v5_times.append(float("inf"))
                v6_times.append(float("inf"))
                v4_success.append(0)
                v5_success.append(0)
                v6_success.append(0)
                v4_solution_lengths.append(0)
                v5_solution_lengths.append(0)
                v6_solution_lengths.append(0)

        # Calculate statistics for this scramble length
        valid_v4_times = [t for t in v4_times if t != float("inf")]
        valid_v5_times = [t for t in v5_times if t != float("inf")]
        valid_v6_times = [t for t in v6_times if t != float("inf")]

        if valid_v4_times and valid_v5_times and valid_v6_times:
            avg_v4_time = statistics.mean(valid_v4_times)
            avg_v5_time = statistics.mean(valid_v5_times)
            avg_v6_time = statistics.mean(valid_v6_times)
            avg_v5_speedup = avg_v4_time / avg_v5_time
            avg_v6_speedup = avg_v4_time / avg_v6_time
        else:
            avg_v4_time = avg_v5_time = avg_v6_time = avg_v5_speedup = avg_v6_speedup = 0

        avg_v4_success = statistics.mean(v4_success)
        avg_v5_success = statistics.mean(v5_success)
        avg_v6_success = statistics.mean(v6_success)

        results.append(
            {
                "length": scramble_length,
                "v4_time": avg_v4_time,
                "v5_time": avg_v5_time,
                "v6_time": avg_v6_time,
                "v5_speedup": avg_v5_speedup,
                "v6_speedup": avg_v6_speedup,
                "v4_success": avg_v4_success,
                "v5_success": avg_v5_success,
                "v6_success": avg_v6_success,
            }
        )

        print(f"  📈 Average speedups: V5={avg_v5_speedup:.2f}x, V6={avg_v6_speedup:.2f}x")
        print(
            f"  ✅ Success rates: V4={avg_v4_success:.1%}, V5={avg_v5_success:.1%}, V6={avg_v6_success:.1%}"
        )
        print()

    # Print summary
    print("📋 BENCHMARK SUMMARY")
    print("=" * 85)
    print(
        f"{'Length':<8} {'V4 Time':<10} {'V5 Time':<10} {'V6 Time':<10} {'V5/V4':<8} {'V6/V4':<8} {'V4 Succ':<8} {'V5 Succ':<8} {'V6 Succ':<8}"
    )
    print("-" * 85)

    total_v5_speedup = []
    total_v6_speedup = []

    for result in results:
        print(
            f"{result['length']:<8} "
            f"{result['v4_time']:<10.4f} "
            f"{result['v5_time']:<10.4f} "
            f"{result['v6_time']:<10.4f} "
            f"{result['v5_speedup']:<8.2f}x "
            f"{result['v6_speedup']:<8.2f}x "
            f"{result['v4_success']:<8.1%} "
            f"{result['v5_success']:<8.1%} "
            f"{result['v6_success']:<8.1%}"
        )

        if result["v5_speedup"] > 0:
            total_v5_speedup.append(result["v5_speedup"])
        if result["v6_speedup"] > 0:
            total_v6_speedup.append(result["v6_speedup"])

    if total_v5_speedup and total_v6_speedup:
        overall_v5_speedup = statistics.mean(total_v5_speedup)
        overall_v6_speedup = statistics.mean(total_v6_speedup)
        print("-" * 85)
        print(f"🚀 Overall V5 Average Speedup: {overall_v5_speedup:.2f}x")
        print(f"🚀 Overall V6 Average Speedup: {overall_v6_speedup:.2f}x")

        if overall_v6_speedup > overall_v5_speedup:
            print("🏆 V6 WINS! Optimized backtracking is the fastest!")
        elif overall_v5_speedup > overall_v6_speedup:
            print("🏆 V5 WINS! Integer encoding approach is fastest!")
        else:
            print("🤝 TIE! Both approaches show excellent performance!")


if __name__ == "__main__":
    run_benchmark()
