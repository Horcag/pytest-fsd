# src/pytest_fsd/rules/excessive_slicing/__init__.py
"""
[Rule: excessive-slicing] (optional)
Forbid having too many slices in a single layer.
Default threshold: 20 slices per layer.
"""

import os
from typing import List

from ..._lib.fs_utils import get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "excessive-slicing"
DEFAULT_THRESHOLD = 20


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that no layer contains too many slices."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    sliced_layers = get_sliced_layers(config)

    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        slices = [
            d
            for d in os.listdir(layer_path)
            if os.path.isdir(os.path.join(layer_path, d)) and not d.startswith("_")
        ]

        if len(slices) > DEFAULT_THRESHOLD:
            violations.append(
                Violation(
                    rule=RULE_NAME,
                    file_path=layer_path,
                    message=f"Layer '{layer}' contains {len(slices)} slices "
                    f"(threshold: {DEFAULT_THRESHOLD}). Too many slices make navigation "
                    f"difficult. Consider grouping related slices.",
                )
            )

    return violations
