"""Guard the boundary between the puzzle-agnostic core and puzzle-specific code.

`spruce.algebra` and `spruce.search` operate on permutation arrays, pattern arrays and
opaque move symbols, so they must stay usable for any permutation puzzle. Every module in
them is checked here, and since that set is closed, checking direct imports is enough: a
core module can only reach cube code through an import this test can see.

Imports guarded by `if TYPE_CHECKING:` are ignored on purpose -- they cost nothing at
runtime and cannot create a real dependency.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "spruce"

CORE = ("spruce.algebra", "spruce.search")
ALSO_ALLOWED = frozenset({"spruce", "spruce.types"})


def _runtime_imports(path: Path) -> set[str]:
    """Return the `spruce.*` modules imported outside of a TYPE_CHECKING block."""
    imports: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_If(self, node: ast.If) -> None:
            test = node.test
            type_checking = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            for child in node.orelse if type_checking else [*node.body, *node.orelse]:
                self.visit(child)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module is not None and node.module.startswith("spruce"):
                imports.add(node.module)

        def visit_Import(self, node: ast.Import) -> None:
            imports.update(alias.name for alias in node.names if alias.name.startswith("spruce"))

    Visitor().visit(ast.parse(path.read_text()))
    return imports


def _is_allowed(module: str) -> bool:
    return module in ALSO_ALLOWED or module.startswith(CORE)


def test_core_does_not_import_puzzle_specific_code() -> None:
    paths = sorted(
        path for package in CORE for path in (PACKAGE_ROOT / package.split(".")[-1]).rglob("*.py")
    )
    assert paths, "found no core modules to guard"

    violations = [
        f"  {path.relative_to(PACKAGE_ROOT.parent)} imports {module}"
        for path in paths
        for module in sorted(_runtime_imports(path))
        if not _is_allowed(module)
    ]

    assert not violations, "The core must not depend on puzzle-specific code:\n" + "\n".join(
        violations,
    )


def test_types_module_stays_dependency_free() -> None:
    """`spruce.types` is allowed above, so it has to be clean for that to be sound."""
    assert not _runtime_imports(PACKAGE_ROOT / "types.py")
