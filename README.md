[Русская версия](README.ru.md)

# pytest-fsd

[![PyPI](https://img.shields.io/pypi/v/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![Python](https://img.shields.io/pypi/pyversions/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![CI](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml/badge.svg)](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml)

Validate [Feature-Sliced Design (FSD)](https://feature-sliced.design/) architecture in a Python project using pytest. The rules are adapted from the [Steiger FSD plugin](https://github.com/feature-sliced/steiger), with Python-specific checks where appropriate. This is an independent Python package, not an official Steiger port.

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
]
```

`no-file-segments` is a Python package option; it is not registered as a rule in Steiger FSD plugin 0.7.0. `no-cross-imports` is enabled here for compatibility, whereas the upstream plugin does not enable it by default. These choices are intentionally different from Steiger.

See the [rule documentation](src/pytest_fsd/rules/) for examples and details.

## Scope and limitations

- `forbidden-imports` and `no-cross-imports` use [pytest-archon](https://pypi.org/project/pytest-archon/). Imports guarded by `if TYPE_CHECKING:` are invisible to these runtime checks.
- `no-public-api-sidestep` analyzes Python syntax and explicit `__all__` lists. Dynamically assembled exports may be reported incorrectly.
- Steiger's `inconsistent-naming` and `import-locality` have no direct equivalent here. Consider Ruff's `N` and `TID` rules for Python naming and relative imports; their behavior is not identical to Steiger's rules.
- Steiger's `insignificant-slice` needs an import graph and is not implemented. The deprecated `processes` layer is not created by this package; omit it from `layers`.
- This package checks Python files and filesystem structure. It does not implement every Steiger rule or every JavaScript-specific convention.

See the [upstream FSD plugin changelog](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/CHANGELOG.md) for Steiger's release history.

## License

MIT. See [LICENSE](LICENSE).
