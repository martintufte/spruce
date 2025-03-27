import pandas as pd


def average_distance_to_goal() -> pd.DataFrame:
    """Get average distance to goal.

    Returns:
        pd.DataFrame: Pandas DataFrame.
    """
    data = {
        "Distance": list(range(21)),
        "Count": [
            1,
            18,
            243,
            3_240,
            43_239,
            574_908,
            7_618_438,
            100_803_036,
            1_332_343_288,
            17_596_479_795,
            232_248_063_316,
            3_063_288_809_012,
            40_374_425_656_248,
            531_653_418_284_628,
            6_989_320_578_825_358,
            91_365_146_187_124_313,
            1_100_000_000_000_000_000,
            12_000_000_000_000_000_000,
            29_000_000_000_000_000_000,
            1_500_000_000_000_000_000,
            490_000_000,
        ],
    }

    df = pd.DataFrame(data)

    return df
