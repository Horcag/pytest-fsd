# src/pytest_fsd/rules/shared_lib_grouping/__init__.py
"""
[Rule: shared-lib-grouping] (optional)
Forbid having too many ungrouped modules in shared/lib.
Default threshold: 15 files.
"""

import os
from typing import List

from ..._lib.fs_utils import get_layer_by_canonical_name
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "shared-lib-grouping"
DEFAULT_THRESHOLD = 15


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that shared/lib doesn't have too many ungrouped files."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    shared_layer = get_layer_by_canonical_name(config, "shared")
    if not shared_layer:
        return violations

    lib_path = os.path.join(base_dir, shared_layer, "lib")

    if not os.path.isdir(lib_path):
        return violations

    # Считаем только .py файлы (не папки и не __init__.py)
    py_files = [
        f
        for f in os.listdir(lib_path)
        if f.endswith(".py")
        and f != "__init__.py"
        and os.path.isfile(os.path.join(lib_path, f))
    ]

    if len(py_files) > DEFAULT_THRESHOLD:
        violations.append(
            Violation(
                rule=RULE_NAME,
                file_path=lib_path,
                message=f"'shared/lib' contains {len(py_files)} ungrouped files "
                f"(threshold: {DEFAULT_THRESHOLD}). Consider grouping related "
                f"modules into subfolders to prevent it from becoming a dump.",
            )
        )

    return violations
