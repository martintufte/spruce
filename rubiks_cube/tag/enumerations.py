from enum import Enum


class Step(Enum):
    inspection = "inspection"
    rotation = "rotation"
    skip = "skip"
    cancelation = "cancelation"
    finish = "finish"
    auf = "auf"
    coll = "coll"
    eoll = "eoll"
    cpll = "cpll"
    epll = "epll"
    zbll = "zbll"


class Progress(Enum):
    solved = "solved"
    draft = "draft"
    skeleton = "skeleton"
    insertion = "insertion"
    rewrite = "rewrite"
    trigger = "trigger"
    blocks = "blocks"
    drm = "drm"
    drm_4c4e = "drm-4c4e"
    drm_4c2e = "drm-4c2e"
    drm_3c2e = "drm-3c2e"


class Basic(Enum):
    face = "face"
    eo_face = "eo-face"
    co_face = "co-face"
    xp_face = "xp-face"
    layer = "layer"
    ep_layer = "ep-layer"
    cp_layer = "cp-layer"
    line = "line"


class CFOP(Enum):
    cross = "cross"
    x_cross = "x-cross"
    xx_cross_adjacent = "xx-cross-adjacent"
    xx_cross_diagonal = "xx-cross-diagonal"
    xx_cross = "xx-cross"
    xxx_cross = "xxx-cross"
    f2l = "f2l"
    f2l_eo = "f2l-eo"
    f2l_co = "f2l-co"
    f2l_ep = "f2l-ep"
    f2l_cp = "f2l-cp"
    oll = "oll"
    pll = "pll"  # not implemented yet


class FewestMoves(Enum):
    corners = "corners"
    edges = "edges"
    centers = "centers"
    xo_fb = "xo-fb"
    xo_lr = "xo-lr"
    xo_ud = "xo-ud"
    xo_htr = "xo-htr"
    co = "co"
    co_fb = "co-fb"
    co_lr = "co-lr"
    co_ud = "co-ud"
    co_htr = "co-htr"
    eo = "eo"
    eo_fb = "eo-fb"
    eo_lr = "eo-lr"
    eo_ud = "eo-ud"
    eo_fb_lr = "eo-fb-lr"
    eo_fb_ud = "eo-fb-ud"
    eo_lr_ud = "eo-lr-ud"
    eo_floppy_fb = "eo-floppy-fb"
    eo_floppy_lr = "eo-floppy-lr"
    eo_floppy_ud = "eo-floppy-ud"
    eo_htr = "eo-htr"
    dr = "dr"
    dr_fb = "dr-fb"
    dr_lr = "dr-lr"
    dr_ud = "dr-ud"
    htr_like = "htr-like"
    htr = "htr"  # not implemented yet
    floppy = "floppy"  # not implemented yet
    floppy_fb = "floppy-fb"
    floppy_lr = "floppy-lr"
    floppy_ud = "floppy-ud"
    floppy_fb_col = "floppy-fb-col"
    floppy_lr_col = "floppy-lr-col"
    floppy_ud_col = "floppy-ud-col"
    minus_slice_m = "minus-slice-m"
    minus_slice_s = "minus-slice-s"
    minus_slice_e = "minus-slice-e"
    minus_slice = "minus-slice"
    leave_slice_m = "leave-slice-m"
    leave_slice_s = "leave-slice-s"
    leave_slice_e = "leave-slice-e"
    leave_slice = "leave-slice"
    block_1x1x3 = "1x1x3-block"
    block_1x2x2 = "1x2x2-block"
    block_1x2x3 = "1x2x3-block"
    block_2x2x2 = "2x2x2-block"
    block_2x2x3 = "2x2x3-block"


# Additional patterns that can be implementated later:
class Roux(Enum):
    fb = "fb"
    sb = "sb"
    cmll = "cmll"
    lse = "lse"
    two_blocks = "two-blocks"


class ZZ(Enum):
    eo_line = "eo-line"
    eo_cross = "eo-cross"
    zz_f2l = "zz-f2l"
    ll = "last-layer"


class Petrus(Enum):
    pass


class Patterns(Enum):
    superflip = "superflip"
    checkerboard = "checkerboard"
    cube_in_cube = "cube-in-cube"
    cube_in_cube_in_cube = "cube-in-cube-in-cube"
