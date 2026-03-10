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

    # Собираем имена компонентов (слайсов) внутри сегментов shared
    # Например: shared/ui/button -> регистрируем 'button' (внутри сегмента 'ui')
    shared_slices: dict[str, str] = {}
    for segment in os.listdir(shared_path):
        segment_path = os.path.join(shared_path, segment)
        if not os.path.isdir(segment_path) or segment.startswith("_"):
            continue

        for shared_slice in os.listdir(segment_path):
            if os.path.isdir(
                os.path.join(segment_path, shared_slice)
            ) and not shared_slice.startswith("_"):
                shared_slices[shared_slice] = segment

    if not shared_slices:
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

            if slice_name in shared_slices:
                conflict_segment = shared_slices[slice_name]
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=slice_path,
                        message=f"Slice '{slice_name}' in layer '{layer}' has the same name as "
                        f"component 'shared/{conflict_segment}/{slice_name}'. This creates ambiguity about "
                        f"where new code should be placed.",
                    )
                )

    return violations
