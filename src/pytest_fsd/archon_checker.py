import os
from pytest_archon import archrule
from .config import FsdConfig


def get_slices(layer: str, base_path: str) -> list[str]:
    """Возвращает список папок (слайсов) внутри указанного слоя FSD."""
    path = os.path.join(base_path, layer)
    if not os.path.isdir(path):
        return []
    return [
        d
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d)) and not d.startswith("_")
    ]


def check_layer_dependencies(config: FsdConfig, project_root: str):
    """
    [Rule: no-higher-level-imports]
    Слои могут импортировать только из нижележащих слоев.
    """
    base_path = config.base_path
    layers = config.layers

    for i, current_layer in enumerate(layers):
        layer_path = os.path.join(project_root, base_path, current_layer)
        if not os.path.isdir(layer_path):
            continue

        # Проверяем наличие .py файлов
        has_python_files = False
        for _, _, files in os.walk(layer_path):
            if any(f.endswith(".py") and f != "__init__.py" for f in files):
                has_python_files = True
                break

        if not has_python_files:
            continue

        forbidden_layers = layers[:i]
        if forbidden_layers:
            forbidden_modules = [f"{base_path}.{layer}.*" for layer in forbidden_layers]
            (
                archrule(f"[{current_layer.upper()}] must not import layers above it")
                .match(f"{base_path}.{current_layer}.*")
                .should_not_import(*forbidden_modules)
                .check(base_path)
            )


def check_slices_are_independent(config: FsdConfig, project_root: str):
    """
    [Rule: no-cross-imports]
    Слайсы внутри одного слоя не могут импортировать друг друга (кроме Shared).
    """
    base_path = config.base_path

    for layer in config.layers:
        if layer == "shared":
            continue  # В shared слайсы обычно могут зависеть друг от друга, или это настраивается отдельно

        slices = get_slices(layer, os.path.join(project_root, base_path))
        if not slices:
            continue

        for slice_name in slices:
            other_slices = [
                f"{base_path}.{layer}.{s}.*" for s in slices if s != slice_name
            ]
            if other_slices:
                (
                    archrule(f"[{layer.upper()}] Slice '{slice_name}' is independent")
                    .match(f"{base_path}.{layer}.{slice_name}.*")
                    .should_not_import(*other_slices)
                    .check(base_path)
                )


def check_production_code_cross_boundary(
    config: FsdConfig, project_root: str, tests_path: str = "tests"
):
    """Проверяет изоляцию production-кода от тестов."""
    base_path = config.base_path
    (
        archrule("Production code is isolated from tests")
        .match(f"{base_path}.*")
        .should_not_import(f"{tests_path}.*")
        .check(base_path)
    )
