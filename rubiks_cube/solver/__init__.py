from rubiks_cube.solver.bidirectional_solver import solve_step

__all__ = ["solve_step"]


# TODO: Optimizations for the bidirectional solver

# Permutation indecies optimizations:
# - Remove indecies not affected by the action space (DONE)
# - Remove indecies of conserved orientations of edges and corners (DONE)
# - Remove indecies from pieces that are not in the pattern (DONE)
# - Remvoe indecies of pieces that are always relatively solved wrt each other (DONE)  # noqa: E501

# Action space / solver optimazations:
# - Find the terminal actions and use them for the first branching
# - Use the last moves to determine the next moves
# - Make use of action groupings to reduce the effective branching factor
# - Remove identity actions and combine equivalent actions

# Bidirectional search optimizations:
# - Search a given depth (burn = n) from one side before initial switch
# - Give a message to the user if no solution is reachable with infinite depth
# - Return state="solved" with no solutions if the cube is already solved
# - Investigate and implementing simple pruning techniques
# - Deep action space pruning to reduce branching factor further
