# src/pytest_fsd/rules/no_cross_imports/__init__.py
"""
[Rule: no-cross-imports]
Slices within the same layer must not import from each other.
Uses pytest-archon for dynamic runtime checking.
"""

import os
from typing import List

from pytest_archon import archrule

from ..._lib.fs_utils import get_slices
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-cross-imports"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that slices within the same layer do not import from each other."""
    violations = []
    base_path = config.base_path

    for layer in config.layers:
        # В shared слайсы могут зависеть друг от друга
        if layer == "shared":
            continue

        slices = get_slices(layer, os.path.join(project_root, base_path))
        if not slices:
            continue

        for slice_name in slices:
            other_slices = [
                f"{base_path}.{layer}.{s}.*" for s in slices if s != slice_name
            ]
            if other_slices:
                try:
                    (
                        archrule(
                            f"[{layer.upper()}] Slice '{slice_name}' is independent"
                        )
                        .match(f"{base_path}.{layer}.{slice_name}.*")
                        .should_not_import(*other_slices)
                        .check(base_path)
                    )
                except AssertionError as e:
                    violations.append(
                        Violation(
                            rule=RULE_NAME,
                            file_path=f"{layer}/{slice_name}",
                            message=str(e).strip(),
                        )
                    )

    return violations
