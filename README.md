[Русская версия](README.ru.md)

# pytest-fsd

[![PyPI](https://img.shields.io/pypi/v/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![Python](https://img.shields.io/pypi/pyversions/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![CI](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml/badge.svg)](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml)

Validate [Feature-Sliced Design (FSD)](https://feature-sliced.design/) architecture in a Python project using pytest. The rules are adapted from the [Steiger FSD plugin](https://github.com/feature-sliced/steiger), with Python-specific checks where appropriate. This is an independent Python package, not an official Steiger port.

The applicable upstream changes are tracked through Steiger 0.7.0 / FSD plugin 0.8.0. See the [changelog](CHANGELOG.md) for Python adaptations.

## Install

```bash
pip install pytest-fsd
# or
uv add --dev pytest-fsd
```

Python 3.8–3.14 is supported.

## Use

Add the layers used by your project, from highest to lowest, to `pyproject.toml`:

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "pages", "widgets", "features", "entities", "shared"]
# ignore_paths = ["my_non_fsd_package"]
```

Create an architecture test:

```python
# tests/test_architecture.py
from pytest_fsd import validate_fsd_architecture


def test_architecture():
    validate_fsd_architecture()
```

Run `pytest tests/test_architecture.py`. Violations appear as assertion failures with a rule name and path. If your source root is different, set `base_path` accordingly. The validator reads `[tool.pytest_fsd]` from the project root; `validate_fsd_architecture(project_root="...")` can target another project.

Standalone checks also raise `AssertionError` on violations and return a nonzero exit status:

```bash
python -c "from pytest_fsd import validate_fsd_architecture; validate_fsd_architecture()"
```

Unknown configuration keys/rules and invalid settings raise `ValueError`. A missing source root, uninspectable Python file, or symlink inside configured layers fails validation. `ignore_paths` excludes non-FSD top-level directories from the layer-name check; it does not suppress imports in configured layers.

## Rules

The default checks cover layer import direction (`forbidden-imports`), slice independence (`no-cross-imports`), public APIs (`public-api`, `no-public-api-sidestep`, `no-layer-public-api`), structure (`no-segmentless-slices`, `no-segments-on-sliced-layers`, `typo-in-layer-name`, `ambiguous-slice-names`), naming (`segments-by-purpose`, `repetitive-naming`), and `no-ui-in-app`.

`segments-by-purpose` includes the generic names added in Steiger's FSD plugin 0.7.0, such as `schemas`, `handlers`, `fixtures`, `middlewares`, `validators`, `resolvers`, `mutations`, and `assets`. These names are checked when used as FSD segments. Python `fixtures.py` in a slice is also flagged because this package checks file segments as well as directories.

`no-ui-in-app` rejects an `app/ui` directory, as in Steiger. It also retains the Python-specific check for direct imports of common desktop GUI frameworks from the app layer.

Enable additional checks only when they suit your project:

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "pages", "widgets", "features", "entities", "shared"]
extra_rules = [
    "excessive-slicing",        # More than 20 slices per layer
    "shared-lib-grouping",      # More than 15 loose Python files in shared/lib
    "no-file-segments",         # Segments must be directories
    "no-reserved-folder-names", # No nested segment names such as model/model
    "no-wildcard-exports",      # No `from module import *` in __init__.py
]
```

`no-wildcard-exports` was added in Steiger FSD plugin 0.8.0 and is disabled by default in both packages. It checks `__init__.py` files on every configured layer, including nested packages. Explicit module imports such as `from . import model as model` remain valid in Python. AST import diagnostics include line and character column numbers.

`no-file-segments` is a Python package option; it is not registered as a rule in Steiger FSD plugin 0.8.0. `no-cross-imports` is enabled here for compatibility, whereas the upstream plugin does not enable it by default. These choices are intentionally different from Steiger.

See the [rule documentation](src/pytest_fsd/rules/) for examples and details. The [complete rule audit](docs/RULE-AUDIT.md) maps all 17 implemented rules and both input guards to positive/negative, activation, threshold and installed-package checks.

## Scope and limitations

- Import rules statically inspect Python syntax, including relative imports, package initializers, function-local imports and `if TYPE_CHECKING:` branches. They do not execute project code. Programmatic imports through `importlib.import_module`, `importlib.__import__`, and built-in `__import__` are analyzed too. Loader aliases, literal names, constant bindings, concatenation, f-strings, joins, relative packages and fromlists are supported. Literal `exec`/`eval` strings and literal `compile` inputs are inspected recursively, with bounded expansion. Unresolved recognized loader calls or executed code fail with `[dynamic-imports]`; they do not silently pass. Arbitrary user-defined import hooks and runtime code are not executed.
- Shared APIs are enforced too: other segments use their root `__init__.py`; `shared/ui` and `shared/lib` expose individual component/library package APIs or standalone Python modules. Imports within the same boundary remain valid.
- Dot-hidden metadata directories and `__pycache__` are excluded from scans. Underscore-prefixed packages such as `_private` are ordinary code and are checked.
- `no-public-api-sidestep` supports static `__all__` lists/tuples, concatenation, annotations, `+=`, `append` and `extend`. Unresolved dynamic exports are reported as unknown.
- Steiger's `inconsistent-naming` and `import-locality` have no direct equivalent here. Consider Ruff's `N` and `TID` rules for Python naming and relative imports; their behavior is not identical to Steiger's rules.
- Steiger's `insignificant-slice` needs an import graph and is not implemented. The deprecated `processes` layer is not created by this package; omit it from `layers`.
- This package checks Python files and filesystem structure. It does not implement every Steiger rule or every JavaScript-specific convention.

For example, this computed sibling import is rejected:

```python
import importlib

layer = "features"
importlib.import_module(f"src.{layer}.other_slice")
```

If the target comes from runtime input (`importlib.import_module(requested_module)`), validation fails with `[dynamic-imports]` because the target cannot be proven valid. Replace it with an explicit dispatch between statically known imports. The checker is an architecture linter; it does not emulate arbitrary Python execution or serve as an execution sandbox.

See the [upstream FSD plugin changelog](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/CHANGELOG.md) for Steiger's release history.

## License

MIT. See [LICENSE](LICENSE).
