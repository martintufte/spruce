from pathlib import Path
from typing import Final

# Define directories as Path objects
CONFIGURATION_DIR: Final = Path(__file__).resolve().parent
ROOT_DIR: Final = CONFIGURATION_DIR.parent

DATA_DIR: Final = ROOT_DIR / "data"
LOGS_PATH: Final = DATA_DIR / "logs" / "rubiks_cube.log"
RESOURCES_DIR: Final = DATA_DIR / "resources"
