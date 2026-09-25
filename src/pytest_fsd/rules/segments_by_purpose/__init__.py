# src/pytest_fsd/rules/segments_by_purpose/__init__.py
"""
[Rule: segments-by-purpose]
Segment names should describe their purpose (ui, model, api, lib),
not their nature (utils, helpers, components, hooks).
"""

import os
from typing import List

from ..._lib.fs_utils import get_canonical_layer
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "segments-by-purpose"

# Список запрещенных имен сегментов из Steiger
BANNED_SEGMENT_NAMES = {
    "utils",
    "util",
    "helpers",
    "helper",
    "hooks",
    "hook",
    "modals",
    "modal",
    "components",
    "component",
    "types",
    "type",
    "interfaces",
    "interface",
    "containers",
    "container",
    "services",
    "service",
    "constants",
    "constant",
    "consts",
    "const",
    "stores",
    "store",
    "functions",
    "function",
    "classes",
    "class",
    "enums",
    "enum",
    "decorators",
    "decorator",
    "schemas",
    "schema",
    "handlers",
    "handler",
    "fixtures",
    "fixture",
    "middlewares",
    "middleware",
    "validators",
    "validator",
    "validations",
    "validation",
    "resolvers",
    "resolver",
    "mutations",
    "mutation",
    "assets",
    "asset",
}


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that segment names describe purpose, not nature."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    if not os.path.isdir(base_dir):
        return violations

    ignored_layers = ("app",)

    for layer in config.layers:
        canonical = get_canonical_layer(layer)
        if canonical in ignored_layers:
            continue

        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        if canonical == "shared":
            # В shared сегменты лежат прямо в корне слоя
            _check_entries_in_dir(layer_path, layer, violations)
        else:
            # Для остальных слоев сегменты лежат внутри слайсов
            for slice_name in os.listdir(layer_path):
                slice_path = os.path.join(layer_path, slice_name)
                if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                    continue
                _check_entries_in_dir(slice_path, slice_name, violations)

    return violations


def _check_entries_in_dir(
    parent_path: str, context: str, violations: List[Violation]
) -> None:
    """Check both directories and .py files against BANNED_SEGMENT_NAMES at depth=1."""
    try:
        entries = os.listdir(parent_path)
    except OSError:
        return

    for entry in entries:
        if entry.startswith("_"):
            continue

        entry_path = os.path.join(parent_path, entry)

        # Checking directories
        if os.path.isdir(entry_path):
            if entry in BANNED_SEGMENT_NAMES:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=entry_path,
                        message=f"Segment '{entry}' in '{context}' describes what its "
                        f"contents ARE, not their PURPOSE. "
                        f"Use 'lib', 'ui', 'api', 'model', or 'config' instead.",
                    )
                )
        # Checking .py files (acting as segments)
        elif entry.endswith(".py"):
            file_stem = entry[:-3]
            if file_stem in BANNED_SEGMENT_NAMES:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=entry_path,
                        message=f"File '{entry}' in '{context}' uses a banned segment name "
                        f"'{file_stem}'. Rename to describe purpose, not nature "
                        f"(e.g., 'lib/', 'model/', 'config/').",
                    )
                )
