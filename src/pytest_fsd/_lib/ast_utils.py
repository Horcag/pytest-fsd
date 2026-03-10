# src/pytest_fsd/_lib/ast_utils.py
"""Shared AST parsing utilities used by multiple rules."""

import ast
from typing import List, Tuple


def get_imports_from_file(filepath: str) -> List[Tuple[int, str]]:
    """Return list of (line_number, full_module_path) for all imports in a file."""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.lineno, node.module))

    return imports
