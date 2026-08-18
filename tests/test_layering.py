"""Guard the boundary between the search layer and puzzle-specific code.

`spruce.search` is the search layer: it operates on permutation
arrays, pattern arrays and opaque move symbols, and must stay usable for any permutation
puzzle. This test walks its runtime import graph and fails if it reaches anything that
knows about a specific puzzle -- notation, goals, variants, pieces or cube geometry.

Imports guarded by `if TYPE_CHECKING:` are ignored on purpose: they cost nothing at
runtime and cannot create a real dependency.
"""

from __future__ import annotations

import ast
from collections import deque
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "spruce"

# The search layer may reach these, and nothing else.
ALLOWED = frozenset(
    {
        "spruce",
        "spruce.types",
        "spruce.search",
        "spruce.algebra",
        "spruce.algebra.pattern",
        "spruce.algebra.permutation",
    },
)
ALLOWED_PREFIXES = ("spruce.search.",)

GUARDED_ROOTS = ("spruce/search",)


def _module_name(path: Path) -> str:
    relative = path.relative_to(PACKAGE_ROOT.parent).with_suffix("")
    parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
    return ".".join(parts)


def _module_path(module: str) -> Path | None:
    parts = module.split(".")[1:]
    if not parts:
        return PACKAGE_ROOT / "__init__.py"
    relative = Path(*parts)
    for candidate in (
        PACKAGE_ROOT / relative.with_suffix(".py"),
        PACKAGE_ROOT / relative / "__init__.py",
    ):
        if candidate.exists():
            return candidate
    return None


def _runtime_imports(path: Path) -> set[str]:
    """Return the `spruce.*` modules imported outside of a TYPE_CHECKING block."""
    imports: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_If(self, node: ast.If) -> None:
            test = node.test
            is_type_checking = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            for child in node.orelse if is_type_checking else [*node.body, *node.orelse]:
                self.visit(child)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module is not None and node.module.startswith("spruce"):
                imports.add(node.module)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                if alias.name.startswith("spruce"):
                    imports.add(alias.name)

    Visitor().visit(ast.parse(path.read_text()))
    return imports


def _parent_packages(module: str) -> set[str]:
    """Importing a submodule also executes every parent package's `__init__`."""
    parts = module.split(".")
    return {".".join(parts[:index]) for index in range(1, len(parts))}


def _import_chains() -> dict[str, list[str]]:
    """Map each runtime-reachable module to a shortest import chain from a guarded root."""
    roots = sorted(
        _module_name(path)
        for guarded in GUARDED_ROOTS
        for path in (PACKAGE_ROOT.parent / guarded).rglob("*.py")
    )
    assert roots, "found no modules to guard"

    chains: dict[str, list[str]] = {root: [root] for root in roots}
    queue = deque(roots)
    while queue:
        module = queue.popleft()
        path = _module_path(module)
        if path is None:
            continue
        for dependency in sorted(_runtime_imports(path) | _parent_packages(module)):
            if dependency not in chains:
                chains[dependency] = [*chains[module], dependency]
                queue.append(dependency)
    return chains


def test_search_layer_does_not_reach_puzzle_specific_code() -> None:
    violations = {
        module: chain
        for module, chain in _import_chains().items()
        if module not in ALLOWED and not module.startswith(ALLOWED_PREFIXES)
    }

    assert not violations, (
        "The search layer must not depend on puzzle-specific code:\n"
        + "\n".join(f"  {' -> '.join(chain)}" for chain in sorted(violations.values()))
    )
