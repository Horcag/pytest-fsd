"""Forbid wildcard imports in Python public API files (__init__.py)."""

import ast
import os
import tokenize
from typing import List

from ..._lib.ast_utils import get_node_location
from ..._lib.dynamic_imports import analyze_imports
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-wildcard-exports"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Check package APIs on configured layers without executing their imports."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    for layer in config.layers:
        for root, _, files in os.walk(os.path.join(base_dir, layer)):
            if "__init__.py" not in files:
                continue
            file_path = os.path.join(root, "__init__.py")
            try:
                with tokenize.open(file_path) as api:
                    source = api.read()
                tree = ast.parse(source, filename=file_path)
            except (OSError, UnicodeError, SyntaxError, ValueError, LookupError) as error:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=file_path,
                        message=f"Cannot inspect public API: {error}",
                        line_number=getattr(error, "lineno", None),
                    )
                )
                continue

            for node in analyze_imports(source, tree, file_path, base_dir).imports:
                if not isinstance(node, ast.ImportFrom):
                    continue
                if not any(alias.name == "*" for alias in node.names):
                    continue
                module = "." * node.level + (node.module or "")
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=file_path,
                        message=f"Wildcard re-export from '{module}' does not define an explicit public API. "
                        "Prefer explicit named imports.",
                        **get_node_location(node, source),
                    )
                )

    return violations
