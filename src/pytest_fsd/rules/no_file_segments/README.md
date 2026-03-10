# `no-file-segments`

> ⚡ **Optional rule.** Enable via `extra_rules = ["no-file-segments"]` in `pyproject.toml`.

Discourage using file-based segments (e.g., `model.py` directly in a slice) and suggest folder-based segments (e.g., `model/`) instead.

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
