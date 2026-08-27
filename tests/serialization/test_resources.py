from __future__ import annotations

import json
from typing import TYPE_CHECKING

import cattrs
import pytest

from spruce.configuration import AppConfig
from spruce.puzzle.cube.metrics import Metric
from spruce.puzzle.cube.spec import Puzzle
from spruce.serialization.resources import ResourceHandler

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def handler(tmp_path: Path) -> ResourceHandler:
    return ResourceHandler(resource_dir=tmp_path, converter=cattrs.Converter())


class TestResourceHandler:
    """The handler only writes the config; these check the file it writes is complete.

    Nothing reads `config.json` back, so the assertion goes through the converter rather
    than a `load_config` method the app would never call.
    """

    @staticmethod
    def _read_back(handler: ResourceHandler) -> AppConfig:
        data = json.loads(handler.config_path.read_text())
        return handler.converter.structure(data, AppConfig)

    def test_default_config_written_completely(self, handler: ResourceHandler) -> None:
        config = AppConfig()
        handler.save_config(config)

        assert self._read_back(handler) == config

    def test_custom_config_written_completely(self, handler: ResourceHandler) -> None:
        config = AppConfig(puzzle=Puzzle._4x4x4, metric=Metric.QTM, layout="wide", log_level="info")
        handler.save_config(config)

        assert self._read_back(handler) == config

    def test_config_written_to_session_dir(self, handler: ResourceHandler) -> None:
        handler.save_config(AppConfig())
        assert handler.config_path.exists()
        assert handler.config_path.parent == handler.resource_dir
