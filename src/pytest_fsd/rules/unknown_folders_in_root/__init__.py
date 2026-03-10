# src/pytest_fsd/rules/unknown_folders_in_root/__init__.py
"""
[Rule: unknown-folders-in-root]
Warn about directories in base_path that are not listed in config.layers
and not in ignore_paths. Catches typos like 'fietures' instead of 'features'.
"""

import os
from typing import List

from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "unknown-folders-in-root"

# Папки, которые всегда следует игнорировать (не FSD-слои)
_ALWAYS_IGNORED = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that all directories in base_path are known FSD layers."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    if not os.path.isdir(base_dir):
        return violations

    known_layers = set(config.layers)
    ignored = _ALWAYS_IGNORED | set(config.ignore_paths)

    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if entry.startswith("_") or entry.startswith("."):
            continue
        if entry in known_layers or entry in ignored:
            continue

        violations.append(
            Violation(
                rule=RULE_NAME,
                file_path=entry_path,
                message=f"Directory '{entry}' in '{config.base_path}/' is not listed "
                f"in [tool.pytest_fsd].layers ({', '.join(config.layers)}). "
                f"Is this a typo? If intentional, add it to 'ignore_paths'.",
            )
        )

    return violations
