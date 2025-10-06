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
from rubiks_cube.solver.bidirectional_solver import bidirectional_solver_v2
from rubiks_cube.solver.bidirectional_solver import bidirectional_solver_v3
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


def benchmark_solver(
    solver_func: Callable[
        [
            CubePermutation,
            dict[str, CubePermutation],
            CubePattern,
            int,
        ],
        list[str] | None,
    ],
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_depth: int = 8,
    n_trials: int = 5,
) -> tuple[float, float, float]:
    """Benchmark a single solver function."""
    times = []
    solutions_found = []
    solution_lengths = []

    for _ in range(n_trials):
        start_time = time.perf_counter()
        try:
            solutions = solver_func(
                initial_permutation,
                actions,
                pattern,
                max_depth,
            )

            end_time = time.perf_counter()
            elapsed = end_time - start_time
            times.append(elapsed)

            if solutions:
                solutions_found.append(True)
                # Count moves in solution
                solution_length = len(solutions[0].split())
                solution_lengths.append(solution_length)
            else:
                solutions_found.append(False)
                solution_lengths.append(0)

        except Exception as e:
            print(f"Error in solver: {e}")
            times.append(float("inf"))
            solutions_found.append(False)
            solution_lengths.append(0)

    avg_time = statistics.mean([t for t in times if t != float("inf")])
    success_rate = sum(solutions_found) / len(solutions_found)
    avg_solution_length = (
        statistics.mean([l for l in solution_lengths if l > 0])
        if any(l > 0 for l in solution_lengths)
        else 0
    )

    return avg_time, success_rate, avg_solution_length


def run_benchmark() -> None:
    """Run comprehensive benchmark comparing both solvers."""
    print("🧩 Rubik's Cube Solver Benchmark")
    print("=" * 50)
    print("Comparing bidirectional_solver vs new_solver")
    print("Scramble lengths: 1-7 moves")
    print("Trials per scramble length: 10")
    print("Max search depth: 10")
    print()

    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    results = []

    for scramble_length in range(1, 8):
        print(f"📊 Testing scramble length: {scramble_length}")

        # Generate test scrambles
        scrambles = [generate_scramble(scramble_length) for _ in range(10)]

        old_times = []
        new_times = []
        old_success = []
        new_success = []
        old_solutions = []
        new_solutions = []

        for i, scramble in enumerate(scrambles):
            print(f"  Trial {i+1}/10: {scramble}", end=" -> ")

            try:
                # Prepare solver inputs
                initial_perm, actions, pattern = prepare_solver_inputs(scramble)

                # Benchmark old solver
                old_time, old_succ, old_sol_len = benchmark_solver(
                    bidirectional_solver_v2,
                    initial_perm,
                    actions,
                    pattern,
                    max_depth=10,
                    n_trials=1,
                )

                # Benchmark new solver
                new_time, new_succ, new_sol_len = benchmark_solver(
                    bidirectional_solver_v3,
                    initial_perm,
                    actions,
                    pattern,
                    max_depth=10,
                    n_trials=1,
                )

                old_times.append(old_time)
                new_times.append(new_time)
                old_success.append(old_succ)
                new_success.append(new_succ)
                old_solutions.append(old_sol_len)
                new_solutions.append(new_sol_len)

                # Calculate speedup
                if old_time > 0 and new_time > 0:
                    speedup = old_time / new_time
                    print(f"Speedup: {speedup:.2f}x")
                else:
                    print("N/A")

            except Exception as e:
                print(f"Error: {e}")
                old_times.append(float("inf"))
                new_times.append(float("inf"))
                old_success.append(0)
                new_success.append(0)
                old_solutions.append(0)
                new_solutions.append(0)

        # Calculate statistics for this scramble length
        valid_old_times = [t for t in old_times if t != float("inf")]
        valid_new_times = [t for t in new_times if t != float("inf")]

        if valid_old_times and valid_new_times:
            avg_old_time = statistics.mean(valid_old_times)
            avg_new_time = statistics.mean(valid_new_times)
            avg_speedup = avg_old_time / avg_new_time
        else:
            avg_old_time = avg_new_time = avg_speedup = 0

        avg_old_success = statistics.mean(old_success)
        avg_new_success = statistics.mean(new_success)

        results.append(
            {
                "length": scramble_length,
                "old_time": avg_old_time,
                "new_time": avg_new_time,
                "speedup": avg_speedup,
                "old_success": avg_old_success,
                "new_success": avg_new_success,
            }
        )

        print(f"  📈 Average speedup: {avg_speedup:.2f}x")
        print(f"  ✅ Success rates: Old={avg_old_success:.1%}, New={avg_new_success:.1%}")
        print()

    # Print summary
    print("📋 BENCHMARK SUMMARY")
    print("=" * 50)
    print(
        f"{'Length':<8} {'Old Time':<12} {'New Time':<12} {'Speedup':<10} {'Old Success':<12} {'New Success':<12}"
    )
    print("-" * 70)

    total_speedup = []

    for result in results:
        print(
            f"{result['length']:<8} "
            f"{result['old_time']:<12.4f} "
            f"{result['new_time']:<12.4f} "
            f"{result['speedup']:<10.2f}x "
            f"{result['old_success']:<12.1%} "
            f"{result['new_success']:<12.1%}"
        )

        if result["speedup"] > 0:
            total_speedup.append(result["speedup"])

    if total_speedup:
        overall_speedup = statistics.mean(total_speedup)
        print("-" * 70)
        print(f"🚀 Overall Average Speedup: {overall_speedup:.2f}x")

        if overall_speedup >= 1.5:
            print("✅ SUCCESS: Achieved target 1.5x speed improvement!")
        else:
            print("⚠️  Target not fully achieved, but some improvement observed.")


if __name__ == "__main__":
    run_benchmark()
