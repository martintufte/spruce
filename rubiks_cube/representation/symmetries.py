from __future__ import annotations

from rubiks_cube.configuration.enumeration import Variant


def find_variant_group(variant: Variant) -> dict[Variant, list[str]]:
    """Naive list of rotations for each variant."""
    axis_variants = {
        Variant.ud: [],
        Variant.fb: ["x"],
        Variant.lr: ["z"],
    }
    axis2_variants = {
        Variant.e: [],
        Variant.s: ["x"],
        Variant.m: ["z"],
    }
    face_variants = {
        Variant.up: [],
        Variant.down: ["x2"],
        Variant.front: ["x'"],
        Variant.back: ["x"],
        Variant.left: ["z'"],
        Variant.right: ["z"],
    }
    edge_variants = {
        Variant.ub: [],
        Variant.uf: ["y2"],
        Variant.ul: ["y'"],
        Variant.ur: ["y2"],
        Variant.db: ["z2"],
        Variant.df: ["x2"],
        Variant.dl: ["x2", "y"],
        Variant.dr: ["x2", "y'"],
        Variant.fl: ["x'", "z'"],
        Variant.fr: ["x'", "z"],
        Variant.bl: ["x", "z"],
        Variant.br: ["x", "z'"],
    }
    corner_variants = {
        Variant.ubl: [],
        Variant.ubr: ["y"],
        Variant.ufl: ["y'"],
        Variant.ufr: ["y2"],
        Variant.dbl: ["x"],
        Variant.dbr: ["z2"],
        Variant.dfl: ["x2"],
        Variant.dfr: ["y", "x2"],
    }
    face_corner_variants = {
        Variant.up_bl: [],
        Variant.up_br: ["y"],
        Variant.up_fl: ["y'"],
        Variant.up_fr: ["y2"],
        Variant.down_bl: ["x2", "y"],
        Variant.down_br: ["z2"],
        Variant.down_fl: ["x2"],
        Variant.down_fr: ["x2", "y'"],
        Variant.front_ul: ["x'"],
        Variant.front_ur: ["x'", "z"],
        Variant.front_dl: ["x'", "z'"],
        Variant.front_dr: ["x'", "z2"],
        Variant.back_ul: ["x", "z'"],
        Variant.back_ur: ["x", "z2"],
        Variant.back_dl: ["x"],
        Variant.back_dr: ["x", "z"],
        Variant.left_ub: ["z'", "x'"],
        Variant.left_db: ["z'"],
        Variant.left_uf: ["z'", "x2"],
        Variant.left_df: ["z'", "x"],
        Variant.right_ub: ["z"],
        Variant.right_db: ["z", "x"],
        Variant.right_uf: ["z", "x'"],
        Variant.right_df: ["z", "x2"],
    }
    face_opposite_corners_variants = {
        Variant.up_bl_fr: [],
        Variant.up_br_fl: ["y"],
        Variant.down_bl_fr: ["x2", "y"],
        Variant.down_br_fl: ["x2"],
        Variant.front_ul_dr: ["x'"],
        Variant.front_ur_dl: ["x'", "z"],
        Variant.back_ul_dr: ["x", "z"],
        Variant.back_ur_dl: ["x"],
        Variant.left_ub_df: ["z'", "x"],
        Variant.left_db_uf: ["z'"],
        Variant.right_ub_df: ["z"],
        Variant.right_db_uf: ["z", "x"],
    }
    face_edge_variants = {
        Variant.up_b: [],
        Variant.up_f: ["y2"],
        Variant.up_l: ["y'"],
        Variant.up_r: ["y"],
        Variant.down_b: ["z2"],
        Variant.down_f: ["x2"],
        Variant.down_l: ["x2", "y"],
        Variant.down_r: ["x2", "y'"],
        Variant.front_u: ["x'"],
        Variant.front_d: ["x'", "z2"],
        Variant.front_l: ["x'", "z'"],
        Variant.front_r: ["x'", "z"],
        Variant.back_u: ["x", "z2"],
        Variant.back_d: ["x"],
        Variant.back_l: ["x", "z"],
        Variant.back_r: ["x", "z'"],
        Variant.left_u: ["z'", "x'"],
        Variant.left_d: ["z'", "x"],
        Variant.left_f: ["z'", "x2"],
        Variant.left_b: ["z'"],
        Variant.right_u: ["z", "x'"],
        Variant.right_d: ["z", "x"],
        Variant.right_f: ["z", "x2"],
        Variant.right_b: ["z"],
    }

    if variant in axis_variants:
        return axis_variants
    if variant in axis2_variants:
        return axis2_variants
    if variant in face_variants:
        return face_variants
    if variant in edge_variants:
        return edge_variants
    if variant in corner_variants:
        return corner_variants
    if variant in face_opposite_corners_variants:
        return face_opposite_corners_variants
    if variant in face_corner_variants:
        return face_corner_variants
    if variant in face_edge_variants:
        return face_edge_variants
    raise ValueError(f"Variant {variant} not found.")
