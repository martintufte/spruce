from __future__ import annotations

from enum import Enum
from enum import unique


@unique
class Variant(Enum):
    none = "none"
    # Face
    left = "left"
    right = "right"
    front = "front"
    back = "back"
    up = "up"
    down = "down"
    # Corners
    ubl = "ubl"
    ubr = "ubr"
    ufl = "ufl"
    ufr = "ufr"
    dbl = "dbl"
    dbr = "dbr"
    dfl = "dfl"
    dfr = "dfr"
    # Edges
    ul = "ul"
    ur = "ur"
    uf = "uf"
    ub = "ub"
    dl = "dl"
    dr = "dr"
    df = "df"
    db = "db"
    fl = "fl"
    fr = "fr"
    bl = "bl"
    br = "br"
    # Axis
    lr = "lr"
    fb = "fb"
    ud = "ud"
    # Face + corner
    up_bl = "up-bl"
    up_br = "up-br"
    up_fl = "up-fl"
    up_fr = "up-fr"
    down_bl = "down-bl"
    down_br = "down-br"
    down_fl = "down-fl"
    down_fr = "down-fr"
    left_ub = "left-ub"
    left_db = "left-db"
    left_uf = "left-uf"
    left_df = "left-df"
    right_ub = "right-ub"
    right_db = "right-db"
    right_uf = "right-uf"
    right_df = "right-df"
    front_ul = "front-ul"
    front_ur = "front-ur"
    front_dl = "front-dl"
    front_dr = "front-dr"
    back_ul = "back-ul"
    back_ur = "back-ur"
    back_dl = "back-dl"
    back_dr = "back-dr"
    # Face + opposite corners
    up_bl_fr = "up-bl+fr"
    up_br_fl = "up-br+fl"
    down_bl_fr = "down-bl+fr"
    down_br_fl = "down-br+fl"
    left_ub_df = "left-ub+df"
    left_db_uf = "left-db+uf"
    right_ub_df = "right-ub+df"
    right_db_uf = "right-db+uf"
    front_ul_dr = "front-ul+dr"
    front_ur_dl = "front-ur+dl"
    back_ul_dr = "back-ul+dr"
    back_ur_dl = "back-ur+dl"
    # Face + edge
    up_l = "up-l"
    up_r = "up-r"
    up_f = "up-f"
    up_b = "up-b"
    down_l = "down-l"
    down_r = "down-r"
    down_f = "down-f"
    down_b = "down-b"
    left_u = "left-u"
    left_d = "left-d"
    left_f = "left-f"
    left_b = "left-b"
    right_u = "right-u"
    right_d = "right-d"
    right_f = "right-f"
    right_b = "right-b"
    front_u = "front-u"
    front_d = "front-d"
    front_l = "front-l"
    front_r = "front-r"
    back_u = "back-u"
    back_d = "back-d"
    back_l = "back-l"
    back_r = "back-r"


def find_variant_group(variant: Variant) -> dict[Variant, tuple[str, ...]]:
    """Naive rotation word for each variant."""
    axis_variants = {
        Variant.ud: (),
        Variant.fb: ("x",),
        Variant.lr: ("z",),
    }
    face_variants = {
        Variant.up: (),
        Variant.down: ("x2",),
        Variant.front: ("x'",),
        Variant.back: ("x",),
        Variant.left: ("z'",),
        Variant.right: ("z",),
    }
    edge_variants = {
        Variant.ub: (),
        Variant.uf: ("y2",),
        Variant.ul: ("y'",),
        Variant.ur: ("y",),
        Variant.db: ("z2",),
        Variant.df: ("x2",),
        Variant.dl: ("x2", "y"),
        Variant.dr: ("x2", "y'"),
        Variant.fl: ("x'", "z'"),
        Variant.fr: ("x'", "z"),
        Variant.bl: ("x", "z"),
        Variant.br: ("x", "z'"),
    }
    corner_variants = {
        Variant.ubl: (),
        Variant.ubr: ("y",),
        Variant.ufl: ("y'",),
        Variant.ufr: ("y2",),
        Variant.dbl: ("x",),
        Variant.dbr: ("z2",),
        Variant.dfl: ("x2",),
        Variant.dfr: ("y", "x2"),
    }
    face_corner_variants = {
        Variant.up_bl: (),
        Variant.up_br: ("y",),
        Variant.up_fl: ("y'",),
        Variant.up_fr: ("y2",),
        Variant.down_bl: ("x2", "y"),
        Variant.down_br: ("z2",),
        Variant.down_fl: ("x2",),
        Variant.down_fr: ("x2", "y'"),
        Variant.front_ul: ("x'",),
        Variant.front_ur: ("x'", "z"),
        Variant.front_dl: ("x'", "z'"),
        Variant.front_dr: ("x'", "z2"),
        Variant.back_ul: ("x", "z'"),
        Variant.back_ur: ("x", "z2"),
        Variant.back_dl: ("x",),
        Variant.back_dr: ("x", "z"),
        Variant.left_ub: ("z'", "x'"),
        Variant.left_db: ("z'",),
        Variant.left_uf: ("z'", "x2"),
        Variant.left_df: ("z'", "x"),
        Variant.right_ub: ("z",),
        Variant.right_db: ("z", "x"),
        Variant.right_uf: ("z", "x'"),
        Variant.right_df: ("z", "x2"),
    }
    face_opposite_corners_variants = {
        Variant.up_bl_fr: (),
        Variant.up_br_fl: ("y",),
        Variant.down_bl_fr: ("x2", "y"),
        Variant.down_br_fl: ("x2",),
        Variant.front_ul_dr: ("x'",),
        Variant.front_ur_dl: ("x'", "z"),
        Variant.back_ul_dr: ("x", "z"),
        Variant.back_ur_dl: ("x",),
        Variant.left_ub_df: ("z'", "x"),
        Variant.left_db_uf: ("z'",),
        Variant.right_ub_df: ("z",),
        Variant.right_db_uf: ("z", "x"),
    }
    face_edge_variants = {
        Variant.up_b: (),
        Variant.up_f: ("y2",),
        Variant.up_l: ("y'",),
        Variant.up_r: ("y",),
        Variant.down_b: ("z2",),
        Variant.down_f: ("x2",),
        Variant.down_l: ("x2", "y"),
        Variant.down_r: ("x2", "y'"),
        Variant.front_u: ("x'",),
        Variant.front_d: ("x'", "z2"),
        Variant.front_l: ("x'", "z'"),
        Variant.front_r: ("x'", "z"),
        Variant.back_u: ("x", "z2"),
        Variant.back_d: ("x",),
        Variant.back_l: ("x", "z"),
        Variant.back_r: ("x", "z'"),
        Variant.left_u: ("z'", "x'"),
        Variant.left_d: ("z'", "x"),
        Variant.left_f: ("z'", "x2"),
        Variant.left_b: ("z'",),
        Variant.right_u: ("z", "x'"),
        Variant.right_d: ("z", "x"),
        Variant.right_f: ("z", "x2"),
        Variant.right_b: ("z",),
    }

    if variant in axis_variants:
        return axis_variants
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
