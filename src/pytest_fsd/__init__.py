# src/pytest_fsd/__init__.py
"""
pytest-fsd: FSD Architecture Validation for Python Projects.

Provides validate_fsd_architecture() — a single facade function
that runs all FSD rules configured in pyproject.toml.
"""

from typing import List

from ._lib.violations import Violation
from .config import load_config
from .rules import (
    ambiguous_slice_names,
    forbidden_imports,
    no_cross_imports,
    no_layer_public_api,
    no_public_api_sidestep,
    no_segmentless_slices,
    no_segments_on_sliced_layers,
    no_ui_in_app,
    public_api,
    repetitive_naming,
    segments_by_purpose,
)
from .rules import (
    excessive_slicing,
    no_file_segments,
    no_reserved_folder_names,
    shared_lib_grouping,
)

# Базовые правила — всегда активны
CORE_RULES = [
    forbidden_imports,
    no_cross_imports,
    no_public_api_sidestep,
    no_layer_public_api,
    no_ui_in_app,
    repetitive_naming,
    no_segmentless_slices,
    segments_by_purpose,
    ambiguous_slice_names,
    no_segments_on_sliced_layers,
    public_api,
]

# Дополнительные правила — включаются через extra_rules в pyproject.toml
EXTRA_RULES = {
    "excessive-slicing": excessive_slicing,
    "shared-lib-grouping": shared_lib_grouping,
    "no-file-segments": no_file_segments,
    "no-reserved-folder-names": no_reserved_folder_names,
}


def validate_fsd_architecture(project_root: str = ".") -> None:
    """
    Validate the project architecture against FSD rules.

    Reads configuration from pyproject.toml -> [tool.pytest_fsd].
    Runs all core rules + any extra_rules specified in config.
    Raises AssertionError if any violations are found.
    """
    config = load_config(project_root)
    all_violations: List[Violation] = []

    # Запускаем базовые правила
    for rule_module in CORE_RULES:
        all_violations.extend(rule_module.check(config, project_root))

    # Запускаем дополнительные правила, если они включены в конфиге
    for extra_rule_name in config.extra_rules:
        rule_module = EXTRA_RULES.get(extra_rule_name)
        if rule_module is not None:
            all_violations.extend(rule_module.check(config, project_root))

    if all_violations:
        error_msg = "FSD Architecture Validation failed:\n"
        for v in all_violations:
            error_msg += v.format() + "\n"
        raise AssertionError(error_msg)
