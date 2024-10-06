import matplotlib.pyplot as plt
import numpy as np

from rubiks_cube.heuristics import average_distance_to_goal


def test_main() -> None:
    df = average_distance_to_goal()
    df["Prob"] = df["Count"] / sum(df["Count"])

    # Mean
    mu = sum(df["Distance"] * df["Prob"])
    print(mu)

    # Variance
    var = sum(df["Prob"] * (df["Distance"] - mu) ** 2)
    print(var)

    # Standard deviation
    std = np.sqrt(var)
    print(std)

    # Generate a histogram
    plt.plot(df["Distance"], df["Count"], "o")
    plt.yscale("log")
    plt.show()

    # Generate a bar plot
    plt.bar(df["Distance"], df["Prob"])
    plt.yscale("log")
    plt.show()
