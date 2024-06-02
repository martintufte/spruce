# Code from:
# https://gist.github.com/jacklee1792/45cbcabd9cdaf192f1458e752423af82
# This code is a Python implementation of the slice solver by Jack Lee.
# TODO: Understand this implementation

import os
import argparse
import random
import subprocess

from tools.nissy.nissy import execute_nissy


SUBSET_ALGS = {
    "0c0": "",
    "0c3": "R B2 R2 D2 R' B2 R2 B2 D2 R",
    "0c4": "U' R2 U R2 U2 B2 U B2 U",
    "2c3": "U F2 U2 R2 F2 U' F2 R2 U",
    "2c4": "U2 R2 U L2 U R2 U' L2 U",
    "2c5": "U L2 U R2 U' R2 U R2 U",
    "4a1": "U R2 L2 U F2 B2 D",
    "4a2": "U R2 U2 F2 U' F2 U F2 U2 R2 U",
    "4a3": "U' F2 R2 U L2 U2 B2 D",
    "4a4": "U R2 U' F2 U R2 F2 U B2 U' F2 U",
    "4b2": "U R2 F2 R2 F2 U",
    "4b3": "U R2 U2 B2 U' F2 L2 D",
    "4b4": "U R2 U' R2 F2 U2 F2 U' F2 U",
    "4b5": "U B2 U B2 U' F2 U F2 U",
}

EDGE_ALGS = {
    "0e": "",
    "2e": "U R2 F2 R2 U",
    "4e": "U L2 R2 D",
    "6e": "U L2 R2 B2 L2 B2 D",
    "8e": "U R2 L2 F2 B2 U",
}


def main(subset, edge_count):
    if subset not in SUBSET_ALGS:
        valid_subsets = ", ".join(SUBSET_ALGS.keys())
        print(f"Bad subset \"{subset}\", expected one of {valid_subsets}")
        return
    if edge_count not in EDGE_ALGS:
        valid_edge_counts = ", ".join(EDGE_ALGS.keys())
        print(f"Bad edge count \"{edge_count}\", expected one of {valid_edge_counts}")  # noqa E501
        return

    # add some random half turns
    half_turns = random.choices("U2 D2 L2 R2 F2 B2".split(), k=20)
    scramble = SUBSET_ALGS[subset] + " " + EDGE_ALGS[edge_count] + " ".join(half_turns)  # noqa E501

    # let nissy do all the hard work to clean it up
    inv = execute_nissy(f"solve -p htr {scramble}")
    htr_scramble = execute_nissy(f"invert {inv}")

    print(inv)
    print(f"HTR-scramble: {htr_scramble}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(description="Generate scrambles for HTR subsets")  # noqa E501
    parser.add_argument("subset", type=str, help="The HTR subset")
    parser.add_argument("edge_count", type=str, help="The number of bad edges")

    args = parser.parse_args()
    main(args.subset, args.edge_count)
