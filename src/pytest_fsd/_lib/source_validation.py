"""Report source files that cannot be inspected rather than silently passing."""

import ast
import os
import tokenize
from typing import List

from .violations import Violation
from .dynamic_imports import analyze_imports
from .fs_utils import is_ignored_directory
from ..config import FsdConfig


def check_sources(config: FsdConfig, project_root: str) -> List[Violation]:
    base_dir = os.path.join(project_root, config.base_path)
    if not os.path.isdir(base_dir):
        return [Violation(rule="python-source", file_path=base_dir,
                          message="Configured source directory does not exist.")]
    violations = []

    def unreadable(error: OSError) -> None:
        violations.append(Violation(rule="python-source", file_path=str(error.filename),
                                    message=f"Cannot inspect source directory: {error}"))

    try:
        with os.scandir(base_dir) as entries:
            layer_names = {entry.name for entry in entries}
    except OSError as error:
        unreadable(error)
        return violations

    for layer in config.layers:
        layer_dir = os.path.join(base_dir, layer)
        if os.path.islink(layer_dir) or (os.path.exists(layer_dir) and not os.path.isdir(layer_dir)):
            violations.append(Violation(rule="python-source", file_path=layer_dir,
                                        message="Configured layer must be a real directory, not a file or symlink."))
            continue
        if layer not in layer_names:
            continue
        for root, dirs, files in os.walk(layer_dir, onerror=unreadable):
            dirs[:] = sorted(d for d in dirs if not is_ignored_directory(d))
            for name in dirs + files:
                path = os.path.join(root, name)
                if os.path.islink(path):
                    violations.append(Violation(rule="python-source", file_path=path,
                                                message="Symlinks inside configured layers cannot be inspected reliably."))
            for filename in sorted(files):
                if not filename.endswith(".py"):
                    continue
                file_path = os.path.join(root, filename)
                try:
                    with tokenize.open(file_path) as handle:
                        source = handle.read()
                    tree = ast.parse(source, filename=file_path)
                    violations.extend(analyze_imports(source, tree, file_path, base_dir).violations)
                except (OSError, UnicodeError, SyntaxError, ValueError, LookupError, RecursionError) as error:
                    violations.append(Violation(
                        rule="python-source", file_path=file_path,
                        line_number=getattr(error, "lineno", None),
                        message=f"Cannot inspect Python source: {error}",
                    ))
    return violations
