import os
import ast
from dataclasses import dataclass
from typing import List, Tuple
from .config import FsdConfig


@dataclass
class AstViolation:
    file_path: str
    line_number: int
    message: str


def check_no_layer_public_api(
    config: FsdConfig, project_root: str
) -> List[AstViolation]:
    """
    [Rule: no-layer-public-api]
    Папки слоев (кроме, возможно, shared/app, но по FSD обычно для всех sliced-слоев)
    не должны содержать __init__.py. Это директории группировки.
    """
    violations = []
    base_path = os.path.join(project_root, config.base_path)

    # Слои, в которых лежат слайсы (sliced layers)
    sliced_layers = [
        layer_name
        for layer_name in config.layers
        if layer_name not in ("app", "shared")
    ]

    for layer in sliced_layers:
        layer_path = os.path.join(base_path, layer)
        if not os.path.isdir(layer_path):
            continue

        init_file = os.path.join(layer_path, "__init__.py")
        if os.path.exists(init_file):
            violations.append(
                AstViolation(
                    file_path=init_file,
                    line_number=1,
                    message=f"Layer folder '{layer}' contains __init__.py. It should be a plain directory.",
                )
            )

    return violations


def _get_imports_from_file(filepath: str) -> List[Tuple[int, str]]:
    """Возвращает список (строка, полный_модуль_источник) для всех импортов в файле."""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # В случае from . import X, module может быть None, но нас интересуют абсолютные пути FSD
                imports.append((node.lineno, node.module))

    return imports


def check_public_api_sidestep(
    config: FsdConfig, project_root: str
) -> List[AstViolation]:
    """
    [Rule: no-public-api-sidestep]
    Проверяет, что импорты слайсов из других модулей идут ТОЛЬКО через Public API слайса.
    Пример: from src.features.auth import login_user (OK)
    Пример: from src.features.auth.internal.utils import ... (VIOLATION)
    """
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    base_module = config.base_path.replace(os.sep, ".")

    if not os.path.isdir(base_dir):
        return violations

    sliced_layers = [
        layer_name
        for layer_name in config.layers
        if layer_name not in ("app", "shared")
    ]

    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            # Определяем, к какому слайсу принадлежит текущий файд (чтобы разрешить внутренние импорты)
            rel_path = os.path.relpath(file_path, base_dir)
            parts = rel_path.split(os.sep)

            current_layer = parts[0] if len(parts) > 0 else None
            current_slice = (
                parts[1] if len(parts) > 1 and current_layer in sliced_layers else None
            )

            # Парсим AST
            imports = _get_imports_from_file(file_path)

            for lineno, module_path in imports:
                # Нас интересуют только абсолютные импорты, начинающиеся с base_module (например, src.)
                if not module_path.startswith(f"{base_module}."):
                    continue

                import_parts = module_path.split(".")
                if len(import_parts) < 3:
                    continue  # src.layer - это еще не слайс

                target_layer = import_parts[1]
                target_slice = import_parts[2]

                if target_layer not in sliced_layers:
                    continue  # Игнорируем shared и app, у них нет строгих слайсов в понимании FSD

                # Разрешаем импорт внутри одного слайса
                if current_layer == target_layer and current_slice == target_slice:
                    continue

                # Импорт идет из другого слайса. Проверяем, что нет sidestep.
                # Длина import_parts должна быть ровно 3 (src.layer.slice)
                if len(import_parts) > 3:
                    violations.append(
                        AstViolation(
                            file_path=file_path,
                            line_number=lineno,
                            message=f"Public API Sidestep: importing internal module '{module_path}' "
                            f"from slice '{target_layer}/{target_slice}'. "
                            f"Import from '{base_module}.{target_layer}.{target_slice}' instead.",
                        )
                    )

    return violations
