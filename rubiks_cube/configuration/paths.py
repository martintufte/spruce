from __future__ import annotations

from pathlib import Path
from typing import Final

ROOT_DIR: Final = Path(__file__).resolve().parent.parent
DATA_DIR: Final = ROOT_DIR / "data"
LOGS_PATH: Final = DATA_DIR / "logs" / "rubiks_cube.log"
