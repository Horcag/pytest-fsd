"""Slices within a layer must be independent; App and Shared have no slices."""

from typing import List

from ..._lib.fs_utils import get_sliced_layers
from ..._lib.imports import iter_imports
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-cross-imports"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Reject imports of sibling slices, including their public packages."""
    violations = []
    sliced_layers = get_sliced_layers(config)
    for path, source, target, location in iter_imports(config, project_root):
        if (len(source) >= 3 and len(target) >= 2
                and source[0] in sliced_layers and source[0] == target[0]
                and source[1] != target[1]):
            violations.append(Violation(
                rule=RULE_NAME, file_path=path, **location,
                message=f"Slice '{source[0]}/{source[1]}' must not import sibling slice '{target[0]}/{target[1]}'.",
            ))
    return violations
