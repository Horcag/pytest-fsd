# src/pytest_fsd/rules/no_public_api_sidestep/__init__.py
"""
[Rule: no-public-api-sidestep]
Imports from other slices must go through the slice's __init__.py (Public API),
not through internal modules.
"""

import os
from typing import List

from ..._lib.ast_utils import get_imports_from_file
from ..._lib.fs_utils import get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-public-api-sidestep"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that all cross-slice imports go through the slice's Public API."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    base_module = config.base_path.replace(os.sep, ".")

    if not os.path.isdir(base_dir):
        return violations

    sliced_layers = get_sliced_layers(config)

    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            # Определяем слайс текущего файла
            rel_path = os.path.relpath(file_path, base_dir)
            parts = rel_path.split(os.sep)

            current_layer = parts[0] if len(parts) > 0 else None
            current_slice = (
                parts[1] if len(parts) > 1 and current_layer in sliced_layers else None
            )

            imports = get_imports_from_file(file_path)

            for lineno, module_path in imports:
                import_parts = module_path.split(".")

                # Определяем, где в импорте начинается layer/slice
                if module_path.startswith(f"{base_module}."):
                    # Стандартный вариант: "src.features.auth.model.handler"
                    # Пропускаем base_module prefix
                    layer_idx = 1
                elif import_parts[0] in sliced_layers:
                    # Альтернативный вариант: "features.auth.model.handler"
                    # (PYTHONPATH указывает на src/)
                    layer_idx = 0
                else:
                    continue

                remaining = import_parts[layer_idx:]
                if len(remaining) < 2:
                    continue

                target_layer = remaining[0]
                target_slice = remaining[1]

                if target_layer not in sliced_layers:
                    continue

                # Разрешаем импорт внутри одного слайса
                if current_layer == target_layer and current_slice == target_slice:
                    continue

                # Длина > 2 (layer + slice + internal) → глубокий импорт
                if len(remaining) > 2:
                    violations.append(
                        Violation(
                            rule=RULE_NAME,
                            file_path=file_path,
                            line_number=lineno,
                            message=f"Importing internal module '{module_path}' "
                            f"from slice '{target_layer}/{target_slice}'. "
                            f"Import from '{base_module}.{target_layer}.{target_slice}' instead.",
                        )
                    )

    return violations
