# import matplotlib.pyplot as plt

from rubiks_cube.solver.heuristics import average_distance_to_goal


def test_main() -> None:
    df = average_distance_to_goal()
    df["Prob"] = df["Count"] / sum(df["Count"])

    # Mean
    mu = sum(df["Distance"] * df["Prob"])

    # Variance
    var = sum(df["Prob"] * (df["Distance"] - mu) ** 2)
    assert var >= 0

    # Generate a histogram
    # plt.plot(df["Distance"], df["Count"], "o")
    # plt.yscale("log")
    # plt.show()

    # Generate a bar plot
    # plt.bar(df["Distance"], df["Prob"])
    # plt.yscale("log")
    # plt.show()
