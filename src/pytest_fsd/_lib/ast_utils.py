# src/pytest_fsd/_lib/ast_utils.py
"""Shared AST parsing utilities used by multiple rules."""

import ast
from typing import List, Tuple, Optional


def get_imports_from_file(
    filepath: str,
) -> List[Tuple[int, Optional[str], int, List[str]]]:
    """Return list of (line_number, full_module_path, level, imported_names).

    Level represents relative imports:
    0 = absolute import (e.g. `import foo` or `from foo import bar`)
    1 = current directory (`from . import bar` -> module=None, level=1)
    2 = parent directory (`from ..foo import bar` -> module='foo', level=2)
    """
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name, 0, [alias.name]))
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            imports.append((node.lineno, node.module, node.level, names))

    return imports


def get_exported_names(filepath: str) -> Optional[List[str]]:
    """Return the list of names exported in __all__ if defined, or None if not defined."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        return [
                            elt.value
                            for elt in node.value.elts
                            if getattr(elt, "value", None) is not None
                        ]
    return None
