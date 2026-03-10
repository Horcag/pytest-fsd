# src/pytest_fsd/rules/no_layer_public_api/__init__.py
"""
[Rule: no-layer-public-api]
Sliced layer directories should not contain __init__.py.
They are grouping directories, not packages with their own API.
"""

import os
from typing import List

from ..._lib.fs_utils import get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-layer-public-api"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that sliced layer directories do not have __init__.py files."""
    violations = []
    base_path = os.path.join(project_root, config.base_path)
    sliced_layers = get_sliced_layers(config)

    for layer in sliced_layers:
        layer_path = os.path.join(base_path, layer)
        if not os.path.isdir(layer_path):
            continue

        init_file = os.path.join(layer_path, "__init__.py")
        if os.path.exists(init_file):
            violations.append(
                Violation(
                    rule=RULE_NAME,
                    file_path=init_file,
                    line_number=1,
                    message=f"Layer folder '{layer}' contains __init__.py. "
                    f"Layer directories are grouping folders, not packages.",
                )
            )

    return violations
