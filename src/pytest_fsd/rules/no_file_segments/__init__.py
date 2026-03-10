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

            # Ищем .py файлы, чьё имя совпадает со стандартным сегментом
            for file in os.listdir(slice_path):
                if not file.endswith(".py") or file == "__init__.py":
                    continue
                file_body = file[:-3]
                if file_body in STANDARD_SEGMENTS:
                    # Проверяем, что одноимённая папка НЕ существует
                    folder_path = os.path.join(slice_path, file_body)
                    if not os.path.isdir(folder_path):
                        violations.append(
                            Violation(
                                rule=RULE_NAME,
                                file_path=os.path.join(slice_path, file),
                                message=f"Segment '{file_body}' in slice '{slice_name}' is a file "
                                f"('{file}'). Use a folder '{file_body}/' instead for better "
                                f"long-term growth potential.",
                            )
                        )

    # Проверяем shared так же
    shared_path = os.path.join(base_dir, "shared")
    if os.path.isdir(shared_path):
        for file in os.listdir(shared_path):
            if not file.endswith(".py") or file == "__init__.py":
                continue
            file_body = file[:-3]
            if file_body in STANDARD_SEGMENTS:
                folder_path = os.path.join(shared_path, file_body)
                if not os.path.isdir(folder_path):
                    violations.append(
                        Violation(
                            rule=RULE_NAME,
                            file_path=os.path.join(shared_path, file),
                            message=f"Segment '{file_body}' in 'shared' is a file ('{file}'). "
                            f"Use a folder '{file_body}/' instead.",
                        )
                    )

    return violations
