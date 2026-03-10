# src/pytest_fsd/rules/ambiguous_slice_names/__init__.py
"""
[Rule: ambiguous-slice-names]
Slice names should not match segment names in the shared layer.
For example, if shared/i18n exists, having features/i18n is confusing.
"""

import os
from typing import List

from ..._lib.fs_utils import get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "ambiguous-slice-names"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that slice names don't collide with shared segment names."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    # Собираем имена сегментов из shared
    shared_path = os.path.join(base_dir, "shared")
    if not os.path.isdir(shared_path):
        return violations

    shared_segment_names = {
        d
        for d in os.listdir(shared_path)
        if os.path.isdir(os.path.join(shared_path, d)) and not d.startswith("_")
    }

    if not shared_segment_names:
        return violations

    # Проверяем слайсы во всех слоях
    sliced_layers = get_sliced_layers(config)

    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        for slice_name in os.listdir(layer_path):
            slice_path = os.path.join(layer_path, slice_name)
            if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                continue

            if slice_name in shared_segment_names:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=slice_path,
                        message=f"Slice '{slice_name}' in layer '{layer}' has the same name as "
                        f"segment 'shared/{slice_name}'. This creates ambiguity about "
                        f"where new code should be placed.",
                    )
                )

    return violations
