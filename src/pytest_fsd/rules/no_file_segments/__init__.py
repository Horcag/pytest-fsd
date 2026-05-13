# src/pytest_fsd/rules/no_file_segments/__init__.py
"""
[Rule: no-file-segments] (optional)
Discourage using file-based segments (e.g., model.py) instead of
folder-based segments (e.g., model/ directory).
"""

import os
from typing import List

from ..._lib.fs_utils import STANDARD_SEGMENTS, get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-file-segments"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that segments are folders, not files."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    sliced_layers = get_sliced_layers(config)

    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        for slice_name in os.listdir(layer_path):
            slice_path = os.path.join(layer_path, slice_name)
            if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                continue

            for file in os.listdir(slice_path):
                if not file.endswith(".py") or file == "__init__.py":
                    continue
                file_body = file[:-3]
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=os.path.join(slice_path, file),
                        message=f"Segment '{file_body}' in slice '{slice_name}' is a file "
                        f"('{file}'). Use a folder '{file_body}/' instead for better "
                        f"long-term growth potential.",
                    )
                )

    # Проверяем sliceless слои (например, shared)
    for layer in config.layers:
        if layer in sliced_layers:
            continue
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue
            
        for file in os.listdir(layer_path):
            if not file.endswith(".py") or file == "__init__.py":
                continue
            file_body = file[:-3]
            violations.append(
                Violation(
                    rule=RULE_NAME,
                    file_path=os.path.join(layer_path, file),
                    message=f"Segment '{file_body}' in layer '{layer}' is a file ('{file}'). "
                    f"Use a folder '{file_body}/' instead.",
                )
            )

    return violations
