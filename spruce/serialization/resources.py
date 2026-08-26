from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import TypeVar

import attrs

from spruce.search.beam import CompiledStep
from spruce.search.transform.pipeline import Pipeline

if TYPE_CHECKING:
    from pathlib import Path

    import cattrs

T = TypeVar("T")


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

    def load_config(self, config_type: type[T]) -> T:
        data = json.loads(self.config_path.read_text())
        return self.converter.structure(data, config_type)

    @property
    def pipeline_path(self) -> Path:
        return self.resource_dir / "preprocess_pipeline.json"

    def save_preprocess_pipeline(self, pipeline: Pipeline) -> None:
        data = self.converter.unstructure(pipeline)
        self.pipeline_path.write_text(json.dumps(data, indent=2))

    def load_preprocess_pipeline(self) -> Pipeline:
        data = json.loads(self.pipeline_path.read_text())
        return self.converter.structure(data, Pipeline)

    @property
    def plan_name_path(self) -> Path:
        return self.resource_dir / "plan_name.json"

    def save_plan_name(self, plan_name: str) -> None:
        self.plan_name_path.write_text(json.dumps({"plan_name": plan_name}))

    def load_plan_name(self) -> str:
        data = json.loads(self.plan_name_path.read_text())
        return str(data["plan_name"])

    @property
    def step_contexts_path(self) -> Path:
        return self.resource_dir / "step_contexts.json"

    def save_step_contexts(self, contexts: list[CompiledStep]) -> None:
        data = self.converter.unstructure(contexts)
        self.step_contexts_path.write_text(json.dumps(data, indent=2))

    def load_step_contexts(self) -> list[CompiledStep]:
        data = json.loads(self.step_contexts_path.read_text())
        return self.converter.structure(data, list[CompiledStep])
