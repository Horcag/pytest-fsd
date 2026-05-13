# src/pytest_fsd/rules/no_reserved_folder_names/__init__.py
"""
[Rule: no-reserved-folder-names] (optional)
Forbid subfolders in segments that have the same name
as other conventional segments (ui, model, api, lib, config).
"""

import os
from typing import List

from ..._lib.fs_utils import STANDARD_SEGMENTS, get_canonical_layer
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-reserved-folder-names"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that segment subfolders don't use reserved segment names."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    # Проверяем все слои (включая shared)
    for layer in config.layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        canonical = get_canonical_layer(layer)
        if canonical == "shared":
            # В shared сегменты — прямые дочерние папки
            _check_segments_subfolders(layer_path, layer, violations)
        elif canonical != "app":
            # В слайсовых слоях сегменты лежат внутри слайсов
            for slice_name in os.listdir(layer_path):
                slice_path = os.path.join(layer_path, slice_name)
                if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                    continue
                _check_segments_subfolders(
                    slice_path, f"{layer}/{slice_name}", violations
                )

    return violations


def _check_segments_subfolders(
    parent_path: str, context: str, violations: List[Violation]
) -> None:
    """Check subfolders of segments inside a given parent path recursively."""
    for segment_name in os.listdir(parent_path):
        segment_path = os.path.join(parent_path, segment_name)
        if not os.path.isdir(segment_path) or segment_name.startswith("_"):
            continue

        # Если имя папки является стандартным сегментом, проверяем все ее подпапки
        if segment_name in STANDARD_SEGMENTS:
            for root_dir, dirs, _ in os.walk(segment_path):
                # Игнорируем скрытые папки
                dirs[:] = [d for d in dirs if not d.startswith("_")]

                for subfolder in dirs:
                    if subfolder in STANDARD_SEGMENTS:
                        subfolder_path = os.path.join(root_dir, subfolder)
                        violations.append(
                            Violation(
                                rule=RULE_NAME,
                                file_path=subfolder_path,
                                message=f"Subfolder '{subfolder}' inside segment "
                                f"'{context}/{segment_name}' uses a reserved segment name. "
                                f"This may cause confusion about the segment structure.",
                            )
                        )
