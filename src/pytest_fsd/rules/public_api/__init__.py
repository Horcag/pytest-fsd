# src/pytest_fsd/rules/public_api/__init__.py
"""
[Rule: public-api]
Every slice (and every segment in shared) must have an __init__.py file
that serves as its public API definition.
"""

import os
from typing import List

from ..._lib.fs_utils import get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "public-api"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that every slice and shared segment has a public API (__init__.py)."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    # Проверяем слайсы в слайсовых слоях
    sliced_layers = get_sliced_layers(config)
    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        for slice_name in os.listdir(layer_path):
            slice_path = os.path.join(layer_path, slice_name)
            if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                continue

            init_file = os.path.join(slice_path, "__init__.py")
            if not os.path.exists(init_file):
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=slice_path,
                        message=f"Slice '{slice_name}' in layer '{layer}' is missing "
                        f"__init__.py (Public API). Every slice must declare its public API.",
                    )
                )

    # Проверяем сегменты в shared
    shared_path = os.path.join(base_dir, "shared")
    if os.path.isdir(shared_path):
        for segment_name in os.listdir(shared_path):
            segment_path = os.path.join(shared_path, segment_name)
            if not os.path.isdir(segment_path) or segment_name.startswith("_"):
                continue

            init_file = os.path.join(segment_path, "__init__.py")
            if not os.path.exists(init_file):
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=segment_path,
                        message=f"Segment '{segment_name}' in 'shared' is missing "
                        f"__init__.py (Public API). Every shared segment must declare its public API.",
                    )
                )

    return violations
