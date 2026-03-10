# src/pytest_fsd/rules/no_public_api_sidestep/__init__.py
"""
[Rule: no-public-api-sidestep]
Imports from other slices must go through the slice's __init__.py (Public API),
not through internal modules.
"""

import os
from typing import List

from ..._lib.ast_utils import get_exported_names, get_imports_from_file
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

            for lineno, module_path, level, imported_names in imports:
                if level > 0:
                    # Разрешаем относительные импорты
                    file_dir_parts = parts[:-1]  # Убираем имя файла

                    if level > len(file_dir_parts):
                        # Возврат за пределы src/ (или base_path), вне области FSD
                        continue

                    # Вычисляем путь назначения
                    resolved_parts = file_dir_parts[: len(file_dir_parts) - level + 1]
                    if module_path:
                        resolved_parts.extend(module_path.split("."))

                    import_parts = resolved_parts
                    layer_idx = 0
                else:
                    if not module_path:
                        continue

                    import_parts = module_path.split(".")

                    # Определяем, где в импорте начинается layer/slice
                    if module_path.startswith(f"{base_module}."):
                        # Стандартный вариант: "src.features.auth.model.handler"
                        layer_idx = 1
                    elif import_parts[0] in sliced_layers:
                        # Альтернативный вариант: "features.auth.model.handler"
                        # Проверка физического существования (защита от коллизий с PyPI-библиотеками)
                        layer_path = os.path.join(base_dir, import_parts[0])
                        if not os.path.isdir(layer_path):
                            continue

                        if len(import_parts) > 1:
                            target_slice_path = os.path.join(
                                layer_path, import_parts[1]
                            )
                            # Слайс может быть папкой или .py файлом
                            if not os.path.isdir(
                                target_slice_path
                            ) and not os.path.isfile(f"{target_slice_path}.py"):
                                continue

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
                else:
                    # Длина == 2 (layer + slice) -> Обращение к __init__.py слайса
                    # Проверяем, что импортируемые имена действительно экспортируются в __all__ (Blind Spot 1)
                    if imported_names:
                        target_init_path = os.path.join(
                            base_dir, target_layer, target_slice, "__init__.py"
                        )
                        if os.path.isfile(target_init_path):
                            exported_names = get_exported_names(target_init_path)
                            if exported_names is None:
                                violations.append(
                                    Violation(
                                        rule=RULE_NAME,
                                        file_path=file_path,
                                        line_number=lineno,
                                        message=f"Slice '{target_layer}/{target_slice}' does not define `__all__` in its __init__.py. "
                                        f"Public API exports must be explicit to prevent encapsulation bypass.",
                                    )
                                )
                            else:
                                for name in imported_names:
                                    if name not in exported_names and name != "*":
                                        violations.append(
                                            Violation(
                                                rule=RULE_NAME,
                                                file_path=file_path,
                                                line_number=lineno,
                                                message=f"Name '{name}' is not explicitly exported in "
                                                f"'{target_layer}/{target_slice}/__init__.py'. "
                                                f"Add it to `__all__` to make it part of the Public API.",
                                            )
                                        )

    return violations
