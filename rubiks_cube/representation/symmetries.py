from __future__ import annotations

from rubiks_cube.configuration.enumeration import Symmetry


def find_symmetry_groups(subset: Symmetry) -> dict[Symmetry, list[str]]:
    """Naive list of symmetries for each subset."""
    axis_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.ud: [],
        Symmetry.fb: ["x"],
        Symmetry.lr: ["z"],
    }
    face_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.up: [],
        Symmetry.down: ["x2"],
        Symmetry.front: ["x'"],
        Symmetry.back: ["x"],
        Symmetry.left: ["z'"],
        Symmetry.right: ["z"],
    }
    edge_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.ub: [],
        Symmetry.uf: ["y2"],
        Symmetry.ul: ["y'"],
        Symmetry.ur: ["y2"],
        Symmetry.db: ["z2"],
        Symmetry.df: ["x2"],
        Symmetry.dl: ["x2", "y"],
        Symmetry.dr: ["x2", "y'"],
        Symmetry.fl: ["x'", "z'"],
        Symmetry.fr: ["x'", "z"],
        Symmetry.bl: ["x", "z"],
        Symmetry.br: ["x", "z'"],
    }
    corner_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.ubl: [],
        Symmetry.ubr: ["y"],
        Symmetry.ufl: ["y'"],
        Symmetry.ufr: ["y2"],
        Symmetry.dbl: ["x"],
        Symmetry.dbr: ["z2"],
        Symmetry.dfl: ["x2"],
        Symmetry.dfr: ["y", "x2"],
    }
    face_corner_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.up_bl: [],
        Symmetry.up_br: ["y"],
        Symmetry.up_fl: ["y'"],
        Symmetry.up_fr: ["y2"],
        Symmetry.down_bl: ["x2", "y"],
        Symmetry.down_br: ["z2"],
        Symmetry.down_fl: ["x2"],
        Symmetry.down_fr: ["x2", "y'"],
        Symmetry.front_ul: ["x'"],
        Symmetry.front_ur: ["x'", "z"],
        Symmetry.front_dl: ["x'", "z'"],
        Symmetry.front_dr: ["x'", "z2"],
        Symmetry.back_ul: ["x", "z'"],
        Symmetry.back_ur: ["x", "z2"],
        Symmetry.back_dl: ["x"],
        Symmetry.back_dr: ["x", "z"],
        Symmetry.left_ub: ["z'", "x'"],
        Symmetry.left_db: ["z'"],
        Symmetry.left_uf: ["z'", "x2"],
        Symmetry.left_df: ["z'", "x"],
        Symmetry.right_ub: ["z"],
        Symmetry.right_db: ["z", "x"],
        Symmetry.right_uf: ["z", "x'"],
        Symmetry.right_df: ["z", "x2"],
    }
    face_opposite_corners_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.up_bl_fr: [],
        Symmetry.up_br_fl: ["y"],
        Symmetry.down_bl_fr: ["x2", "y"],
        Symmetry.down_br_fl: ["x2"],
        Symmetry.front_ul_dr: ["x'"],
        Symmetry.front_ur_dl: ["x'", "z"],
        Symmetry.back_ul_dr: ["x", "z"],
        Symmetry.back_ur_dl: ["x"],
        Symmetry.left_ub_df: ["z'", "x"],
        Symmetry.left_db_uf: ["z'"],
        Symmetry.right_ub_df: ["z"],
        Symmetry.right_db_uf: ["z", "x"],
    }
    face_edge_symmetries: dict[Symmetry, list[str]] = {
        Symmetry.up_b: [],
        Symmetry.up_f: ["y2"],
        Symmetry.up_l: ["y'"],
        Symmetry.up_r: ["y"],
        Symmetry.down_b: ["z2"],
        Symmetry.down_f: ["x2"],
        Symmetry.down_l: ["x2", "y"],
        Symmetry.down_r: ["x2", "y'"],
        Symmetry.front_u: ["x'"],
        Symmetry.front_d: ["x'", "z2"],
        Symmetry.front_l: ["x'", "z'"],
        Symmetry.front_r: ["x'", "z"],
        Symmetry.back_u: ["x", "z2"],
        Symmetry.back_d: ["x"],
        Symmetry.back_l: ["x", "z"],
        Symmetry.back_r: ["x", "z'"],
        Symmetry.left_u: ["z'", "x'"],
        Symmetry.left_d: ["z'", "x"],
        Symmetry.left_f: ["z'", "x2"],
        Symmetry.left_b: ["z'"],
        Symmetry.right_u: ["z", "x'"],
        Symmetry.right_d: ["z", "x"],
        Symmetry.right_f: ["z", "x2"],
        Symmetry.right_b: ["z"],
    }

    if subset in axis_symmetries:
        return axis_symmetries
    if subset in face_symmetries:
        return face_symmetries
    if subset in edge_symmetries:
        return edge_symmetries
    if subset in corner_symmetries:
        return corner_symmetries
    if subset in face_opposite_corners_symmetries:
        return face_opposite_corners_symmetries
    if subset in face_corner_symmetries:
        return face_corner_symmetries
    if subset in face_edge_symmetries:
        return face_edge_symmetries
    raise ValueError(f"Symmetry {subset} not found.")
