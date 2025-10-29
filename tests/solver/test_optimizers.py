from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.optimizers import ActionOptimizer
from rubiks_cube.solver.optimizers import IndexOptimizer


class TestIndexOptimizer:
    def test_standard(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<L, R, U, D, F, B>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions)
        assert sum(optimizer.affected_mask) == 48
        assert sum(optimizer.isomorphic_mask) == 48

    def test_2gen(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<R, U>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 32
        assert sum(optimizer.isomorphic_mask) == 25

    def test_3gen_adjasent(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<R, U, F>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 39
        assert sum(optimizer.isomorphic_mask) == 39

    def test_3gen_opposite(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<R, U, D>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 44
        assert sum(optimizer.isomorphic_mask) == 34

    def test_dr(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<L2, R2, U, D, F2, B2>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 48
        assert sum(optimizer.isomorphic_mask) == 20

    def test_htr(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<L2, R2, U2, D2, F2, B2>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 48
        assert sum(optimizer.isomorphic_mask) == 20

    def test_roux(self) -> None:
        cube_size = 3
        generator = MoveGenerator("<M, U>")

        actions = get_actions(generator=generator, cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 28
        assert sum(optimizer.isomorphic_mask) == 20

    def test_tperm(self) -> None:
        tperm = MoveAlgorithm("T-perm", "R U R' U' R' F R2 U' R' U' R U R' F'")
        cube_size = 3

        actions = get_actions(algorithms=[tperm], cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 10
        assert sum(optimizer.isomorphic_mask) == 2

    def test_uperm(self) -> None:
        uperm = MoveAlgorithm("Ua-perm", "M2 U M U2 M' U M2")
        cube_size = 3

        actions = get_actions(algorithms=[uperm], cube_size=cube_size)
        optimizer = IndexOptimizer(cube_size=cube_size)
        optimizer.fit_transform(actions=actions)

        assert sum(optimizer.affected_mask) == 6
        assert sum(optimizer.isomorphic_mask) == 3


if __name__ == "__main__":
    cube_size = 3
    generator = MoveGenerator("<L, R, U, D, F, B, x, y, z>")
    actions = get_actions(generator=generator, cube_size=cube_size)
    action_optimizer = ActionOptimizer()

    actions_optimized = action_optimizer.fit_transform(actions=actions)
    adj_matrix = action_optimizer.get_adj_matrix()

    import pandas as pd

    df_adj = pd.DataFrame(
        data=adj_matrix, index=actions_optimized.keys(), columns=actions_optimized.keys(), dtype=int
    )

    print("Actions:", actions_optimized)
    print("Adjacency Matrix:\n", df_adj)

    print("Adjacency Matrix last 9:\n", df_adj.iloc[-9:, -9:])
