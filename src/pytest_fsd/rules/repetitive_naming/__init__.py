# src/pytest_fsd/rules/repetitive_naming/__init__.py
"""
[Rule: repetitive-naming]
File names within a slice should not duplicate the slice name.
For example, inside features/user there should be no user_model.py.
"""

import os
from typing import List

from ..._lib.fs_utils import get_sliced_layers
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "repetitive-naming"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that files inside slices don't repeat the slice name."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    sliced_layers = get_sliced_layers(config)

    if not os.path.isdir(base_dir):
        return violations

    for layer in sliced_layers:
        layer_path = os.path.join(base_dir, layer)
        if not os.path.isdir(layer_path):
            continue

        for slice_name in os.listdir(layer_path):
            slice_path = os.path.join(layer_path, slice_name)
            if not os.path.isdir(slice_path) or slice_name.startswith("_"):
                continue

            for root, _, files in os.walk(slice_path):
                for file in files:
                    if not file.endswith(".py") or file == "__init__.py":
                        continue

                    file_body = file[:-3]

                    if file_body == slice_name or file_body.startswith(
                        slice_name + "_"
                    ):
                        violations.append(
                            Violation(
                                rule=RULE_NAME,
                                file_path=os.path.join(root, file),
                                message=f"File '{file}' contains the slice name '{slice_name}'. "
                                f"Use simpler names inside the slice context "
                                f"(e.g., 'model.py' or 'handler.py').",
                            )
                        )

    return violations
