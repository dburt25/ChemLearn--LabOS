"""Static import checks to enforce modular boundaries."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Set


FORBIDDEN_IN_CORE: tuple[str, ...] = ("labos.ui", "labos.modules")
FORBIDDEN_IN_MODULES: tuple[str, ...] = ("labos.ui",)


def _collect_import_targets(path: Path) -> Set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _find_violations(root: Path, forbidden_prefixes: Iterable[str]) -> list[tuple[Path, str]]:
    violations: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*.py")):
        for imported in _collect_import_targets(path):
            if any(imported.startswith(prefix) for prefix in forbidden_prefixes):
                violations.append((path, imported))
    return violations


def test_core_avoids_ui_and_modules_imports() -> None:
    core_root = Path("labos/core")
    violations = _find_violations(core_root, FORBIDDEN_IN_CORE)
    assert not violations, f"Core must not import UI or module internals: {violations}"


def test_modules_do_not_import_ui() -> None:
    modules_root = Path("labos/modules")
    violations = _find_violations(modules_root, FORBIDDEN_IN_MODULES)
    assert not violations, f"Modules must not import UI: {violations}"
