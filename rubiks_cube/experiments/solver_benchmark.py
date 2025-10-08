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
from rubiks_cube.solver.bidirectional_solver import bidirectional_solver_v5b
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
    print("🧩 Rubik's Cube Solver Benchmark: V4 vs V5 vs V5b")
    print("=" * 60)
    print("V4:  Original bidirectional solver")
    print("V5:  Integer encoding + pruning optimizations")
    print("V5b: Optimized backtracking (memory efficient)")
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
        scrambles = [generate_scramble(scramble_length) for _ in range(300)]

        v4_times = []
        v5_times = []
        v5b_times = []
        v4_success = []
        v5_success = []
        v5b_success = []
        v4_solution_lengths = []
        v5_solution_lengths = []
        v5b_solution_lengths = []

        for i, scramble in enumerate(scrambles):
            print(f"  Trial {i+1}/300: {scramble}", end=" -> ")

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

                # Benchmark V5b solver
                v5b_time, v5b_succ, v5b_sol_len, v5b_solutions = benchmark_solver(
                    bidirectional_solver_v5b,
                    initial_perm,
                    actions,
                    pattern,
                    max_depth=10,
                    n_trials=1,
                )

                v4_times.append(v4_time)
                v5_times.append(v5_time)
                v5b_times.append(v5b_time)
                v4_success.append(v4_succ)
                v5_success.append(v5_succ)
                v5b_success.append(v5b_succ)
                v4_solution_lengths.append(v4_sol_len)
                v5_solution_lengths.append(v5_sol_len)
                v5b_solution_lengths.append(v5b_sol_len)

                # Calculate speedups
                v5_speedup = v4_time / v5_time if v5_time > 0 else float("inf")
                v5b_speedup = v4_time / v5b_time if v5b_time > 0 else float("inf")
                print(f"V5: {v5_speedup:.2f}x, V5b: {v5b_speedup:.2f}x")

            except Exception as e:
                print(f"Error: {e}")
                v4_times.append(float("inf"))
                v5_times.append(float("inf"))
                v5b_times.append(float("inf"))
                v4_success.append(0)
                v5_success.append(0)
                v5b_success.append(0)
                v4_solution_lengths.append(0)
                v5_solution_lengths.append(0)
                v5b_solution_lengths.append(0)

        # Calculate statistics for this scramble length
        valid_v4_times = [t for t in v4_times if t != float("inf")]
        valid_v5_times = [t for t in v5_times if t != float("inf")]
        valid_v5b_times = [t for t in v5b_times if t != float("inf")]

        if valid_v4_times and valid_v5_times and valid_v5b_times:
            avg_v4_time = statistics.mean(valid_v4_times)
            avg_v5_time = statistics.mean(valid_v5_times)
            avg_v5b_time = statistics.mean(valid_v5b_times)
            avg_v5_speedup = avg_v4_time / avg_v5_time
            avg_v5b_speedup = avg_v4_time / avg_v5b_time
        else:
            avg_v4_time = avg_v5_time = avg_v5b_time = avg_v5_speedup = avg_v5b_speedup = 0

        avg_v4_success = statistics.mean(v4_success)
        avg_v5_success = statistics.mean(v5_success)
        avg_v5b_success = statistics.mean(v5b_success)

        results.append(
            {
                "length": scramble_length,
                "v4_time": avg_v4_time,
                "v5_time": avg_v5_time,
                "v5b_time": avg_v5b_time,
                "v5_speedup": avg_v5_speedup,
                "v5b_speedup": avg_v5b_speedup,
                "v4_success": avg_v4_success,
                "v5_success": avg_v5_success,
                "v5b_success": avg_v5b_success,
            }
        )

        print(f"  📈 Average speedups: V5={avg_v5_speedup:.2f}x, V5b={avg_v5b_speedup:.2f}x")
        print(
            f"  ✅ Success rates: V4={avg_v4_success:.1%}, V5={avg_v5_success:.1%}, V5b={avg_v5b_success:.1%}"
        )
        print()

    # Print summary
    print("📋 BENCHMARK SUMMARY")
    print("=" * 85)
    print(
        f"{'Length':<8} {'V4 Time':<10} {'V5 Time':<10} {'V5b Time':<10} {'V5/V4':<8} {'V5b/V4':<8} {'V4 Succ':<8} {'V5 Succ':<8} {'V5b Succ':<8}"
    )
    print("-" * 85)

    total_v5_speedup = []
    total_v5b_speedup = []

    for result in results:
        print(
            f"{result['length']:<8} "
            f"{result['v4_time']:<10.4f} "
            f"{result['v5_time']:<10.4f} "
            f"{result['v5b_time']:<10.4f} "
            f"{result['v5_speedup']:<8.2f}x "
            f"{result['v5b_speedup']:<8.2f}x "
            f"{result['v4_success']:<8.1%} "
            f"{result['v5_success']:<8.1%} "
            f"{result['v5b_success']:<8.1%}"
        )

        if result["v5_speedup"] > 0:
            total_v5_speedup.append(result["v5_speedup"])
        if result["v5b_speedup"] > 0:
            total_v5b_speedup.append(result["v5b_speedup"])

    if total_v5_speedup and total_v5b_speedup:
        overall_v5_speedup = statistics.mean(total_v5_speedup)
        overall_v5b_speedup = statistics.mean(total_v5b_speedup)
        print("-" * 85)
        print(f"🚀 Overall V5 Average Speedup: {overall_v5_speedup:.2f}x")
        print(f"🚀 Overall V5b Average Speedup: {overall_v5b_speedup:.2f}x")

        if overall_v5b_speedup > overall_v5_speedup:
            print("🏆 V5b WINS! Optimized backtracking is the fastest!")
        elif overall_v5_speedup > overall_v5b_speedup:
            print("🏆 V5 WINS! Integer encoding approach is fastest!")
        else:
            print("🤝 TIE! Both approaches show excellent performance!")


def run_comprehensive_comparison() -> None:
    """Run comprehensive comparison of V4, V5, and V5b solvers."""
    print("🧩 COMPREHENSIVE SOLVER COMPARISON: V4 vs V5 vs V5b")
    print("=" * 70)
    print("V4:  Original bidirectional solver")
    print("V5:  Integer encoding + pruning optimizations")
    print("V5b: Optimized backtracking (memory efficient)")
    print()

    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    # Setup
    generator = MoveGenerator("<L, R, U, D, F, B>")
    actions = get_action_space(generator=generator, cube_size=3)
    pattern = get_rubiks_cube_pattern(tag="solved", cube_size=3)

    # Apply index optimization (consistent for all solvers)
    optimizer = IndexOptimizer(cube_size=3)
    actions = optimizer.fit_transform(actions=actions)
    pattern = optimizer.transform_pattern(pattern)

    # Test cases with increasing complexity
    test_cases = [
        (["R", "U"], "Simple (2 moves)"),
        (["R", "U", "F"], "Easy (3 moves)"),
        (["R", "U", "F", "D"], "Medium (4 moves)"),
        (["R", "U", "F", "D", "L"], "Complex (5 moves)"),
        (["R", "U", "F", "D", "L", "B"], "Hard (6 moves)"),
    ]

    solvers = [
        (bidirectional_solver_v4, "V4"),
        (bidirectional_solver_v5, "V5"),
        (bidirectional_solver_v5b, "V5b"),
    ]

    print(
        f'{"Test":<18} {"V4 Time":<10} {"V5 Time":<10} {"V5b Time":<10} {"V5/V4":<8} {"V5b/V4":<8} {"V5b/V5":<8}'
    )
    print("-" * 85)

    total_times = [0.0, 0.0, 0.0]  # V4, V5, V5b

    for scramble_moves, description in test_cases:
        scramble = MoveSequence(scramble_moves)
        initial_perm = get_rubiks_cube_state(sequence=scramble, cube_size=3)
        initial_perm = optimizer.transform_permutation(initial_perm)

        times = []
        solutions = []

        # Test each solver
        for solver_func, solver_name in solvers:
            start = time.perf_counter()
            solution = solver_func(initial_perm, actions, pattern, 8, 1, 5.0)
            solve_time = time.perf_counter() - start

            times.append(solve_time)
            solutions.append(solution)

        total_times[0] += times[0]
        total_times[1] += times[1]
        total_times[2] += times[2]

        # Calculate speedups
        v5_speedup = times[0] / times[1] if times[1] > 0 else float("inf")
        v5b_speedup = times[0] / times[2] if times[2] > 0 else float("inf")
        v5b_vs_v5 = times[1] / times[2] if times[2] > 0 else float("inf")

        print(
            f"{description:<18} {times[0]:<10.4f} {times[1]:<10.4f} {times[2]:<10.4f} {v5_speedup:<8.2f}x {v5b_speedup:<8.2f}x {v5b_vs_v5:<8.2f}x"
        )

    # Summary
    print("-" * 85)
    overall_v5_speedup = total_times[0] / total_times[1] if total_times[1] > 0 else float("inf")
    overall_v5b_speedup = total_times[0] / total_times[2] if total_times[2] > 0 else float("inf")
    overall_v5b_vs_v5 = total_times[1] / total_times[2] if total_times[2] > 0 else float("inf")

    print(
        f'{"TOTAL":<18} {total_times[0]:<10.4f} {total_times[1]:<10.4f} {total_times[2]:<10.4f} {overall_v5_speedup:<8.2f}x {overall_v5b_speedup:<8.2f}x {overall_v5b_vs_v5:<8.2f}x'
    )

    print()
    print("🚀 FINAL RESULTS:")
    print(f"✅ V5 overall speedup vs V4: {overall_v5_speedup:.2f}x")
    print(f"✅ V5b overall speedup vs V4: {overall_v5b_speedup:.2f}x")
    print(f"✅ V5b overall speedup vs V5: {overall_v5b_vs_v5:.2f}x")
    print()
    print("🎯 CONCLUSION:")
    if overall_v5b_speedup > overall_v5_speedup:
        print("🏆 V5b WINS! Optimized backtracking is the fastest approach!")
        print("   ✅ Best of both worlds: speed + memory efficiency")
    elif overall_v5_speedup > overall_v5b_speedup:
        print("🏆 V5 WINS! Integer encoding with direct storage is fastest!")
        print("   ✅ Speed-optimized approach for current use cases")
    else:
        print("🤝 TIE! Both V5 and V5b show excellent performance!")


if __name__ == "__main__":
    run_benchmark()
