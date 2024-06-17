from enum import Enum
from enum import unique


@unique
class Face(Enum):
    up = "Up"
    front = "Front"
    right = "Right"
    blue = "Back"
    left = "Left"
    down = "Down"


@unique
class Piece(Enum):
    corner = "Corner"
    edge = "Edge"
    center = "Center"


@unique
class Metric(Enum):
    HTM = "Half Turn Metric"
    STM = "Slice Turn Metric"
    QTM = "Quarter Turn Metric"
    ETM = "Execution Turn Metric"


@unique
class Pattern(Enum):
    empty = "Empty"
    mask = "Mask"
    relative_mask = "Relative Mask"
    orientation = "Orientation"


@unique
class State(Enum):
    layer = "layer"
    line = "line"
    block_1x1x3 = "1x1x3"
    block_1x2x2 = "1x2x2"
    block_1x2x3 = "1x2x3"
    block_2x2x2 = "2x2x2"
    block_2x2x3 = "2x2x3"
    two_blocks = "two-blocks"
    centers = "centers"
    corners = "corners"
    cross = "cross"
    edges = "edges"
    co = "co"
    co_face = "co-face"
    co_fb = "co-fb"
    co_lr = "co-lr"
    co_ud = "co-ud"
    co_htr = "co-htr"
    cp_layer = "cp-layer"
    dr = "dr"
    dr_fb = "dr-fb"
    dr_lr = "dr-lr"
    dr_ud = "dr-ud"
    eo = "eo"
    eo_cross = "eo-cross"  # not supported yet
    eo_face = "eo-face"
    eo_fb = "eo-fb"
    eo_lr = "eo-lr"
    eo_ud = "eo-ud"
    eo_fb_lr = "eo-fb-lr"
    eo_fb_ud = "eo-fb-ud"
    eo_lr_ud = "eo-lr-ud"
    eo_line = "eo-line"  # not supported yet
    eo_floppy_fb = "eo-floppy-fb"
    eo_floppy_lr = "eo-floppy-lr"
    eo_floppy_ud = "eo-floppy-ud"
    eo_htr = "eo-htr"
    ep_layer = "ep-layer"
    face = "face"
    f2l = "f2l"
    f2l_co = "f2l-co"
    f2l_cp = "f2l-cp"
    f2l_eo = "f2l-eo"
    f2l_ep = "f2l-ep"
    f2l_ep_co = "f2l-ep-co"
    f2l_eo_cp = "f2l-eo-cp"
    f2l_face = "f2l-face"
    f2l_layer = "f2l-layer"
    floppy = "floppy"
    floppy_fb = "floppy-fb"
    floppy_lr = "floppy-lr"
    floppy_ud = "floppy-ud"
    floppy_col = "floppy-columns"
    floppy_fb_col = "floppy-fb-columns"
    floppy_lr_col = "floppy-lr-columns"
    floppy_ud_col = "floppy-ud-columns"
    htr = "htr"  # not supported yet
    htr_like = "htr-like"
    minus_slice = "minus-slice"
    minus_slice_e = "minus-slice-e"
    minus_slice_m = "minus-slice-m"
    minus_slice_s = "minus-slice-s"
    leave_slice = "leave-slice"
    leave_slice_e = "leave-slice-e"
    leave_slice_m = "leave-slice-m"
    leave_slice_s = "leave-slice-s"
    xo_fb = "xo-fb"
    xo_lr = "xo-lr"
    xo_ud = "xo-ud"
    xo_htr = "xo-htr"
    xp_face = "xp-face"
    x_cross = "x-cross"
    xx_cross_adjacent = "xx-cross-adjacent"
    xx_cross_diagonal = "xx-cross-diagonal"
    xx_cross = "xx-cross"
    xxx_cross = "xxx-cross"


@unique
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
    oll = "oll"
    pll = "pll"
    drm = "drm"
    drm_4c4e = "drm-4c4e"
    drm_4c2e = "drm-4c2e"
    drm_3c2e = "drm-3c2e"


@unique
class RouxStep(Enum):
    fb = "fb"
    sb = "sb"
    cmll = "cmll"
    lse = "lse"


@unique
class ZZStep(Enum):
    zz_f2l = "zz-f2l"
    ll = "last-layer"


@unique
class Progress(Enum):
    draft = "draft"
    solved = "solved"
    skeleton = "skeleton"
    insertion = "insertion"
    rewrite = "rewrite"
    blocks = "blocks"


@unique
class Patterns(Enum):
    superflip = "superflip"
    checkerboard = "checkerboard"
    cube_in_cube = "cube-in-cube"
    cube_in_cube_in_cube = "cube-in-cube-in-cube"
