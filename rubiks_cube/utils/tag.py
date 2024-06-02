from enum import Enum


class StepSpeedSolve(Enum):
    inspection = "inspection"
    rotation = "rotation"
    skip = "skip"
    finish = "finish"


class StepCFOP(Enum):
    cross = "cross"
    x_cross = "x-cross"
    xx_cross = "xx-cross"
    xxx_cross = "xxx-cross"
    f2l_minus_1 = "f2l-1"
    f2l = "f2l"
    oll = "oll"
    pll = "pll"
    auf = "auf"


class StepCFOPExtra(Enum):
    zbll = "zbll"
    vls = "vls"
    coll = "coll"
    epll = "epll"
    cpll = "cpll"
    wv = "winter-variation"


class StepRoux(Enum):
    fb = "fb"
    sb = "sb"
    cmll = "cmll"
    lse = "lse"


class StepZZ(Enum):
    EOLine = "eo-line"
    EOCross = "eo-cross"
    ZZF2L = "zz-f2l"
    LL = "last-layer"


class StepFewestMoves(Enum):
    insert = "insert"
    rewrite = "rewrite"


class StepHTR(Enum):
    eo = "eo"
    dr = "dr"
    drm = "drm"
    htr = "htr"


class StepBlockbuilding(Enum):
    two_by_one = "2x1"
    two_by_two = "2x2"
    two_by_three = "2x3"


class Progress(Enum):
    draft = "draft"
    skeleton = "skeleton"
    solved = "solved"
