from __future__ import annotations

from typing import TYPE_CHECKING

import cattrs
import pytest

from rubiks_cube.configuration import AppConfig
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.serialization.resources import ResourceHandler

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def handler(tmp_path: Path) -> ResourceHandler:
    return ResourceHandler(resource_dir=tmp_path, converter=cattrs.Converter())


class TestResourceHandler:
    def test_roundtrip_default_config(self, handler: ResourceHandler) -> None:
        config = AppConfig()
        handler.save_config(config)
        assert handler.load_config(AppConfig) == config

    def test_roundtrip_custom_config(self, handler: ResourceHandler) -> None:
        config = AppConfig(cube_size=4, metric=Metric.QTM, layout="wide", log_level="info")
        handler.save_config(config)
        assert handler.load_config(AppConfig) == config

    def test_config_written_to_session_dir(self, handler: ResourceHandler) -> None:
        handler.save_config(AppConfig())
        assert handler.config_path.exists()
        assert handler.config_path.parent == handler.resource_dir
