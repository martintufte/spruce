from rubiks_cube.solver.heuristics import average_distance_to_goal


def test_main() -> None:
    df = average_distance_to_goal()
    df["Prob"] = df["Count"] / sum(df["Count"])

    # Mean
    mu = sum(df["Distance"] * df["Prob"])

    # Variance
    var = sum(df["Prob"] * (df["Distance"] - mu) ** 2)
    assert var >= 0
