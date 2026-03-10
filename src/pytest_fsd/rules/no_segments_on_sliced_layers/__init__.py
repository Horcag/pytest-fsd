# src/pytest_fsd/rules/no_segments_on_sliced_layers/__init__.py
"""
[Rule: no-segments-on-sliced-layers]
Sliced layers (features, entities, pages, widgets) must contain only slices,
not direct segment folders like ui/, api/, model/.
"""

import os
from typing import List

from ..._lib.fs_utils import STANDARD_SEGMENTS, get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-segments-on-sliced-layers"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that sliced layers don't contain segment folders as direct children."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    sliced_layers = get_sliced_layers(config)

    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        for child_name in os.listdir(layer_path):
            child_path = os.path.join(layer_path, child_name)
            if not os.path.isdir(child_path) or child_name.startswith("_"):
                continue

            # Если имя папки совпадает с именем стандартного сегмента — это нарушение
            if child_name in STANDARD_SEGMENTS:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=child_path,
                        message=f"Layer '{layer}' contains a segment folder '{child_name}' "
                        f"as a direct child. Sliced layers should only contain slices, "
                        f"not segments. Move this code into a slice.",
                    )
                )

    return violations
