import os
from typing import Final

CONFIGURATION_DIR: Final = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR: Final = os.path.dirname(CONFIGURATION_DIR)
DATA_DIR: Final = os.path.join(ROOT_DIR, "data")
RESOURCES_DIR: Final = os.path.join(DATA_DIR, "resources")
