import re
from typing import Final

MOVE_REGEX: Final[str] = r"^[I]?$|^[3456789]?[LRFBUD][w][2']?$|^[LRFBUDxyzMES][2']?$"
WIDE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([3456789]?)([LRFBUD])w([2']?)$")
SLICE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([MES])([2']?)$")
ROTATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([ixyz])([2']?)$")
