[🇷🇺 Читать на русском](README.ru.md)

# pytest-fsd

**FSD Architecture Validation for Python Projects.**

`pytest-fsd` automatically checks your Python project's architecture for compliance with the [Feature-Sliced Design](https://feature-sliced.design/) methodology.

It uses a hybrid approach: dynamic checks via [pytest-archon](https://pypi.org/project/pytest-archon/) + static AST analysis + file structure verification.

## Installation

```bash
pip install pytest-fsd
# or
uv add --dev pytest-fsd
```

## Usage

### 1. Configure `pyproject.toml`

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
```

### 2. Create a test

```python
# tests/test_architecture.py
from pytest_fsd import validate_fsd_architecture

def test_project_architecture():
    validate_fsd_architecture()
```

### 3. Run

```bash
pytest tests/test_architecture.py -vv
```

## Library Architecture

Each rule is a folder inside `src/pytest_fsd/rules/<rule_name>/` containing:

- `__init__.py` — verification logic (the function `check(config, project_root) -> List[Violation]`)
- `README.md` — rule description, examples, and rationale

```
src/pytest_fsd/
  __init__.py           # Facade: validate_fsd_architecture()
  config.py             # Reads [tool.pytest_fsd] from pyproject.toml
  _lib/                 # Shared utilities
    violations.py       # Unified Violation dataclass
    ast_utils.py        # AST parsing for imports
    fs_utils.py         # File utilities, segment constants
  rules/
    forbidden_imports/          # pytest-archon: layers only import from layers below
    no_cross_imports/           # pytest-archon: slices within the same layer are independent
    no_public_api_sidestep/     # AST: importing from another slice is only allowed via its __init__.py
    no_layer_public_api/        # FS: layer folders must not contain __init__.py
    no_ui_in_app/               # AST: forbids importing UI frameworks directly into app
    repetitive_naming/          # FS: files do not duplicate the slice name
    no_segmentless_slices/      # FS: a slice must contain at least one standard segment
    segments_by_purpose/        # FS: forbids utils/helpers/components/hooks
    ambiguous_slice_names/      # FS: slice names must not match segment names in shared
    no_segments_on_sliced_layers/ # FS: sliced layers must not contain segments directly
    public_api/                 # FS: every slice must have an __init__.py
```

---

## Steiger Rules Coverage Matrix

Full list of rules from the [Steiger FSD Plugin](https://github.com/feature-sliced/steiger) and their status in `pytest-fsd`:

| #   | Steiger Rule                                    | pytest-fsd Status      | Description                                                                               |
| --- | ----------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------- |
| 1   | `forbidden-imports` / `no-higher-level-imports` | ✅ **Complete**       | Layers only import from layers below them                                                 |
| 2   | `no-cross-imports`                              | ✅ **Complete**       | Slices within the same layer are independent of each other                                |
| 3   | `no-public-api-sidestep`                        | ✅ **Complete**       | Importing from another slice is only allowed via `__init__.py`                            |
| 4   | `public-api`                                    | ✅ **Complete**       | Every slice and shared segment must have an `__init__.py`                                 |
| 5   | `no-layer-public-api`                           | ✅ **Complete**       | Layer folders (`features/`, `entities/`) must not contain `__init__.py`                   |
| 6   | `segments-by-purpose`                           | ✅ **Complete**       | Forbids `utils`, `helpers`, `hooks`, `components`, `modals`, `types`, `constants`, etc.   |
| 7   | `no-segmentless-slices`                         | ✅ **Complete**       | A slice must contain at least one standard segment                                        |
| 8   | `repetitive-naming`                             | ✅ **Complete**       | Files do not duplicate the slice name (`user/user_model.py` → `user/model.py`)            |
| 9   | `no-ui-in-app`                                  | ✅ **Complete**       | The `app` layer must not import UI frameworks                                             |
| 10  | `ambiguous-slice-names`                         | ✅ **Complete**       | Slice names must not match segment names in `shared/`                                     |
| 11  | `no-segments-on-sliced-layers`                  | ✅ **Complete**       | Sliced layers do not have direct segment folders                                          |
| 12  | `inconsistent-naming`                           | 🔶 **Ruff**            | Enforced by the `N` (pep8-naming) plugin in `Ruff`                                        |
| 13  | `import-locality`                               | 🔶 **Ruff**            | Enforced by the `TID` (flake8-tidy-imports) plugin in `Ruff`                              |
| 14  | `typo-in-layer-name`                            | ✅ **Complete**       | Forbids unknown layer folders (e.g., `fietures` instead of `features`) in the root        |
| 15  | `no-processes`                                  | 🔶 **Configuration**   | The `processes` layer is deprecated; simply do not include it in `layers`                 |
| 16  | `excessive-slicing`                             | ⚡ **Optional**        | More than 20 slices in one layer (threshold: 20)                                          |
| 17  | `insignificant-slice`                           | 🟡 **Manual check**    | Requires import graph analysis to determine "insignificant" slices                        |
| 18  | `no-file-segments`                              | ⚡ **Optional**        | A segment as a file (`model.py`) instead of a folder (`model/`)                           |
| 19  | `shared-lib-grouping`                           | ⚡ **Optional**        | More than 15 ungrouped files in `shared/lib`                                              |
| 20  | `no-reserved-folder-names`                      | ⚡ **Optional**        | Subfolders in segments must not match segment names                                       |

### Legend

| Status                     | Meaning                                                                                             |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| ✅ **Complete**           | The rule is fully automated and runs every time `pytest` is executed                                |
| ⚡ **Optional**         | The rule is automated but is enabled via `extra_rules` in `pyproject.toml`                          |
| 🔶 **Ruff / Configuration** | Covered by external tools (`Ruff`) or `pyproject.toml` configuration                                |
| 🟡 **Manual check**     | Requires subjective evaluation or complex analysis better suited for manual code review             |

---

## Enabling Optional Rules

Add to `pyproject.toml`:

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
extra_rules = [
    "excessive-slicing",       # ≤ 20 slices per layer
    "shared-lib-grouping",     # ≤ 15 files in shared/lib
    "no-file-segments",        # Segments must be folders, not files
    "no-reserved-folder-names" # Segment subfolders cannot be named ui/model/api/lib/config
]
```

Each rule is described in detail in `src/pytest_fsd/rules/<rule_name>/README.md`.

---

## Configuring Ruff for Related Rules

For full coverage of FSD rules that Steiger checks at the linting level (which `pytest-fsd` does not duplicate), add to `pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["N", "TID"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"
```

| Ruff Plugin                 | Steiger Rule          | What it checks                                  |
| --------------------------- | --------------------- | ----------------------------------------------- |
| `N` (pep8-naming)           | `inconsistent-naming` | `snake_case` for modules, variables, functions  |
| `TID` (flake8-tidy-imports) | `import-locality`     | Forbids relative imports from parent packages   |

Detailed descriptions and configuration examples: `src/pytest_fsd/rules/inconsistent_naming/README.md` and `src/pytest_fsd/rules/import_locality/README.md`.

## Known Limitations

- **`TYPE_CHECKING` imports**: Rules using `pytest-archon` (e.g., `forbidden-imports` and `no-cross-imports`) work based on dynamic import graph analysis at runtime. Imports inside `if TYPE_CHECKING:` blocks are not executed when the module loads and are therefore **not visible to these rules**.
- **Relative imports**: The `ast_utils.py` module supports relative paths for checking `no-public-api-sidestep`, however, `Ruff` (the `TID` plugin) is still better at controlling relative imports outside of slices.
- **Dynamic `__all__`**: The `no-public-api-sidestep` rule uses static AST analysis to extract `__all__` from the `__init__.py` file. If the export list is formed dynamically (e.g., `__all__ = a + b`), the static analyzer will not be able to read it, and the tool may yield false positive violations. Exports in `__all__` must be defined as an explicit list or tuple.
- **Minimum Python Version**: The library supports Python **3.8+**. For Python `<3.11`, backward compatibility is provided via the `tomli` package, and on Python `3.11+` the built-in `tomllib` is used.

## License

MIT