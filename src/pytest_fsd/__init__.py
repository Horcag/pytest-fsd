from .config import load_config
from .archon_checker import (
    check_layer_dependencies,
    check_slices_are_independent,
    check_production_code_cross_boundary,
)
from .ast_checker import check_no_layer_public_api, check_public_api_sidestep


def validate_fsd_architecture(project_root: str = "."):
    """
    Фасадная функция для валидации архитектуры проекта на соответствие FSD.
    Сочетает динамические (pytest-archon) и статические (AST) проверки.
    Конфигурация считывается из pyproject.toml -> [tool.pytest_fsd].
    """
    config = load_config(project_root)

    # 1. Запуск динамических проверок (archon)
    # Исключения архитекутрных нарушений Archon выбросит сам
    check_production_code_cross_boundary(config, project_root)
    check_layer_dependencies(config, project_root)
    check_slices_are_independent(config, project_root)

    # 2. Запуск статических AST-проверок
    ast_violations = []

    # no-layer-public-api
    ast_violations.extend(check_no_layer_public_api(config, project_root))

    # no-public-api-sidestep
    ast_violations.extend(check_public_api_sidestep(config, project_root))

    if ast_violations:
        error_msg = "AST Validation failed with the following FSD violations:\n"
        for v in ast_violations:
            error_msg += f" - {v.file_path}:{v.line_number} -> {v.message}\n"
        raise AssertionError(error_msg)
