# src/pytest_fsd/rules/segments_by_purpose/__init__.py
"""
[Rule: segments-by-purpose]
Segment names should describe their purpose (ui, model, api, lib),
not their nature (utils, helpers, components, hooks).
"""

import os
from typing import List

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
    "consts",
    "const",
}


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that segment names describe purpose, not nature."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    if not os.path.isdir(base_dir):
        return violations

    ignored_layers = ("app",)

    for layer in config.layers:
        if layer in ignored_layers:
            continue

        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        if layer == "shared":
            # В shared сегменты лежат прямо в корне слоя
            for segment_name in os.listdir(layer_path):
                segment_path = os.path.join(layer_path, segment_name)
                if not os.path.isdir(segment_path) or segment_name.startswith("_"):
                    continue
                if segment_name in BANNED_SEGMENT_NAMES:
                    violations.append(
                        Violation(
                            rule=RULE_NAME,
                            file_path=segment_path,
                            message=f"Segment '{segment_name}' in 'shared' describes what its "
                            f"contents ARE, not their PURPOSE. "
                            f"Use 'lib', 'ui', 'api', 'model', or 'config' instead.",
                        )
                    )
        else:
            # Для остальных слоев сегменты лежат внутри слайсов
            for slice_name in os.listdir(layer_path):
                slice_path = os.path.join(layer_path, slice_name)
                if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                    continue

                for segment_name in os.listdir(slice_path):
                    segment_path = os.path.join(slice_path, segment_name)
                    if not os.path.isdir(segment_path) or segment_name.startswith("_"):
                        continue
                    if segment_name in BANNED_SEGMENT_NAMES:
                        violations.append(
                            Violation(
                                rule=RULE_NAME,
                                file_path=segment_path,
                                message=f"Segment '{segment_name}' inside slice '{slice_name}' "
                                f"describes its nature rather than purpose. "
                                f"Use 'ui', 'model', 'api', 'lib', or 'config' instead.",
                            )
                        )

    return violations
