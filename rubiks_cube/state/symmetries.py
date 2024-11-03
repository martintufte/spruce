from rubiks_cube.configuration.enumeration import Subset


def find_symmetry_subset(subset: Subset) -> dict[Subset, list[str]]:
    """Naive list of symmetries for each subset."""
    axis_subset: dict[Subset, list[str]] = {
        Subset.ud: [],
        Subset.fb: ["x"],
        Subset.lr: ["z"],
    }
    face_subset: dict[Subset, list[str]] = {
        Subset.up: [],
        Subset.down: ["x2"],
        Subset.front: ["x'"],
        Subset.back: ["x"],
        Subset.left: ["z'"],
        Subset.right: ["z"],
    }
    edge_subset: dict[Subset, list[str]] = {
        Subset.ub: [],
        Subset.uf: ["y2"],
        Subset.ul: ["y'"],
        Subset.ur: ["y2"],
        Subset.db: ["z2"],
        Subset.df: ["x2"],
        Subset.dl: ["x2", "y"],
        Subset.dr: ["x2", "y'"],
        Subset.fl: ["x'", "z'"],
        Subset.fr: ["x'", "z"],
        Subset.bl: ["x", "z"],
        Subset.br: ["x", "z'"],
    }
    corner_subset: dict[Subset, list[str]] = {
        Subset.ubl: [],
        Subset.ubr: ["y"],
        Subset.ufl: ["y'"],
        Subset.ufr: ["y2"],
        Subset.dbl: ["x"],
        Subset.dbr: ["z2"],
        Subset.dfl: ["x2"],
        Subset.dfr: ["y", "x2"],
    }
    face_corner_subset: dict[Subset, list[str]] = {
        Subset.up_bl: [],
        Subset.up_br: ["y"],
        Subset.up_fl: ["y'"],
        Subset.up_fr: ["y2"],
        Subset.down_bl: ["x2", "y"],
        Subset.down_br: ["z2"],
        Subset.down_fl: ["x2"],
        Subset.down_fr: ["x2", "y'"],
        Subset.front_ul: ["x'"],
        Subset.front_ur: ["x'", "z"],
        Subset.front_dl: ["x'", "z'"],
        Subset.front_dr: ["x'", "z2"],
        Subset.back_ul: ["x", "z'"],
        Subset.back_ur: ["x", "z2"],
        Subset.back_dl: ["x"],
        Subset.back_dr: ["x", "z"],
        Subset.left_ub: ["z'", "x'"],
        Subset.left_db: ["z'"],
        Subset.left_uf: ["z'", "x2"],
        Subset.left_df: ["z'", "x"],
        Subset.right_ub: ["z"],
        Subset.right_db: ["z", "x"],
        Subset.right_uf: ["z", "x'"],
        Subset.right_df: ["z", "x2"],
    }
    face_edge_subset: dict[Subset, list[str]] = {
        Subset.up_b: [],
        Subset.up_f: ["y2"],
        Subset.up_l: ["y'"],
        Subset.up_r: ["y"],
        Subset.down_b: ["z2"],
        Subset.down_f: ["x2"],
        Subset.down_l: ["x2", "y"],
        Subset.down_r: ["x2", "y'"],
        Subset.front_u: ["x'"],
        Subset.front_d: ["x'", "z2"],
        Subset.front_l: ["x'", "z'"],
        Subset.front_r: ["x'", "z"],
        Subset.back_u: ["x", "z2"],
        Subset.back_d: ["x"],
        Subset.back_l: ["x", "z"],
        Subset.back_r: ["x", "z'"],
        Subset.left_u: ["z'", "x'"],
        Subset.left_d: ["z'", "x"],
        Subset.left_f: ["z'", "x2"],
        Subset.left_b: ["z'"],
        Subset.right_u: ["z", "x'"],
        Subset.right_d: ["z", "x"],
        Subset.right_f: ["z", "x2"],
        Subset.right_b: ["z"],
    }

    if subset in axis_subset:
        return axis_subset
    elif subset in face_subset:
        return face_subset
    elif subset in edge_subset:
        return edge_subset
    elif subset in corner_subset:
        return corner_subset
    elif subset in face_corner_subset:
        return face_corner_subset
    elif subset in face_edge_subset:
        return face_edge_subset
    raise ValueError(f"Subset {subset} not found.")
