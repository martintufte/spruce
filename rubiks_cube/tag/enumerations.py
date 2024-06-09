from enum import Enum


class Step(Enum):
    inspection = "inspection"
    rotation = "rotation"
    skip = "skip"
    cancelation = "cancelation"
    finish = "finish"
    auf = "auf"


class CFOP(Enum):
    cross = "cross"
    x_cross = "x-cross"
    xx_cross_adjacent = "xx-cross-adjacent"
    xx_cross_diagonal = "xx-cross-diagonal"
    xx_cross = "xx-cross"
    xxx_cross = "xxx-cross"
    f2l = "f2l"
    f2l_1 = "f2l-1"
    f2l_eo = "f2l-eo"
    oll = "oll"
    pll = "pll"
    zbll = "zbll"
    vls = "vls"
    coll = "coll"
    epll = "epll"
    cpll = "cpll"
    wv = "winter-variation"
    # other building blocks
    face = "face"
    layer = "layer"


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


class Progress(Enum):
    solved = "solved"
    draft = "draft"
    skeleton = "skeleton"
    insertion = "insertion"
    rewrite = "rewrite"


class FewestMoves(Enum):
    solved_corners = "solved-corners"
    solved_edges = "solved-edges"
    co = "co"
    co_fb = "co-fb"
    co_lr = "co-lr"
    co_ud = "co-ud"
    eo = "eo"
    eo_fb = "eo-fb"
    eo_lr = "eo-lr"
    eo_ud = "eo-ud"
    dr = "dr"
    dr_fb = "dr-fb"
    dr_lr = "dr-lr"
    dr_ud = "dr-ud"
    drm = "drm"
    drm_4c4e = "drm-4c4e"
    drm_4c2e = "drm-4c2e"
    drm_3c2e = "drm-3c2e"
    htr = "htr"
    htr_fake = "fake-htr"
    floppy = "floppy"
    floppy_fb = "floppy-fb"
    floppy_lr = "floppy-lr"
    floppy_ud = "floppy-ud"
    leave_slice_m = "layer-m-slice"
    leave_slice_s = "layer-s-slice"
    leave_slice_e = "layer-e-slice"
    leave_slice = "leave-slice"
    block_1x2x2 = "1x2x2-block"
    block_1x2x3 = "1x2x3-block"
    block_2x2x2 = "2x2x2-block"
    block_2x2x3 = "2x2x3-block"
    block_2x3x3 = "2x3x3-block"
