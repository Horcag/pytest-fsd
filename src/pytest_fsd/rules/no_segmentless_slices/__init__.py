# src/pytest_fsd/rules/no_segmentless_slices/__init__.py
"""
[Rule: no-segmentless-slices]
Every slice must contain at least one standard FSD segment
(as a folder or a .py file), e.g. ui, model, api, lib, config.
"""

import os
from typing import List

from ..._lib.fs_utils import STANDARD_SEGMENTS, get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-segmentless-slices"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that every slice contains at least one standard FSD segment."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    sliced_layers = get_sliced_layers(config)

    if not os.path.isdir(base_dir):
        return violations

    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        for slice_name in os.listdir(layer_path):
            slice_path = os.path.join(layer_path, slice_name)
            if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                continue

            has_segments = False
            try:
                entries = os.listdir(slice_path)
            except OSError:
                continue

            for entry in entries:
                if entry in STANDARD_SEGMENTS:
                    has_segments = True
                    break
                if entry.endswith(".py") and entry[:-3] in STANDARD_SEGMENTS:
                    has_segments = True
                    break

            if not has_segments:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=slice_path,
                        message=f"Slice '{slice_name}' in layer '{layer}' does not contain any "
                        f"standard FSD segments ({', '.join(STANDARD_SEGMENTS)}). "
                        f"A slice without segments is usually an architectural smell.",
                    )
                )

    return violations
