from __future__ import annotations

import json
from typing import TYPE_CHECKING

import attrs

from spruce.search.beam import CompiledStep

if TYPE_CHECKING:
    from pathlib import Path

    import cattrs


@attrs.frozen
class ResourceHandler:
    """Manage resources related to solving permutation search problems."""

    resource_dir: Path
    converter: cattrs.Converter

    def __attrs_post_init__(self) -> None:
        try:
            self.resource_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise RuntimeError(f"Failed to create session directory {self.resource_dir}") from exc

    @property
    def config_path(self) -> Path:
        return self.resource_dir / "config.json"

    def save_config(self, config: object) -> None:
        data = self.converter.unstructure(config)
        self.config_path.write_text(json.dumps(data, indent=2))

    @property
    def step_contexts_path(self) -> Path:
        return self.resource_dir / "step_contexts.json"

    def save_step_contexts(self, contexts: list[CompiledStep]) -> None:
        data = self.converter.unstructure(contexts)
        self.step_contexts_path.write_text(json.dumps(data, indent=2))

    def load_step_contexts(self) -> list[CompiledStep]:
        data = json.loads(self.step_contexts_path.read_text())
        return self.converter.structure(data, list[CompiledStep])
