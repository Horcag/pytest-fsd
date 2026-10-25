"""Layers may import only their own layer or layers below them."""

from typing import List

from ..._lib.imports import iter_imports
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "forbidden-imports"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Check all static imports, including package initializers and type hints."""
    violations = []
    ranks = {layer: index for index, layer in enumerate(config.layers)}
    for path, source, target, location in iter_imports(config, project_root):
        if target and target[0] in ranks and ranks[target[0]] < ranks[source[0]]:
            violations.append(Violation(
                rule=RULE_NAME, file_path=path, **location,
                message=f"Layer '{source[0]}' must not import layers above it: '{'.'.join(target)}'.",
            ))
    return violations
