# `no-file-segments`

> ⚡ **Optional rule.** Enable via `extra_rules = ["no-file-segments"]` in `pyproject.toml`.

Discourage using file-based segments (e.g., `model.py` directly in a slice) and suggest folder-based segments (e.g., `model/`) instead.

Every direct Python file except `__init__.py` is treated as a file segment, regardless of its name. The same check applies directly inside the sliceless `app` and `shared` layers. Files inside a folder segment are implementation modules and are allowed. A directory whose name ends in `.py` is not a file segment.

## Configuration

```toml
[tool.pytest_fsd]
extra_rules = ["no-file-segments"]
```

## Examples

✅ Pass:

```text
📂 features/
  📂 auth/
    📂 model/          # ← folder segment
      📄 handler.py
    📄 __init__.py
```

❌ Fail:

```text
📂 features/
  📂 auth/
    📄 model.py        # ❌ file segment
    📄 __init__.py
```

## Rationale

File segments are limited in growth potential — everything has to be in one file. Folder segments allow adding adjacent files in the future (e.g., `model/types.py`, `model/validators.py`). Folders are better for long-term project growth.

> **Note:** This rule is optional because in Python small slices with a single `model.py` are common and acceptable.

## Scope

Configured layer names and source roots are supported, including numeric ordering prefixes. Ordinary underscore-prefixed package directories are checked. Dot-hidden directories and `__pycache__` are metadata and are skipped. Checks apply at the documented slice or segment boundary, not recursively to implementation packages.
