import re
from typing import Final

MOVE_REGEX: Final[str] = r"^[Ii]?$|^[3456789]?[LRFBUD][w][2']?$|^[LRFBUDxyzMES][2']?$"

ROTATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([ixyz])([2']?)$")
SINGLE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([LRFBUD])([2']?)$")
SLICE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([MES])([2']?)$")
WIDE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([3456789]?)([LRFBUD])w([2']?)$")

DOUBLE_ROTATION_SEARCH: Final[re.Pattern[str]] = re.compile(r"[ixyz]2")
DOUBLE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[2]")
DOUBLE_SLICE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[MES]2")
ROTATION_SEARCH: Final[re.Pattern[str]] = re.compile(r"[ixyz]")
SLICE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[MES]")
