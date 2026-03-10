# `shared-lib-grouping`

> ⚡ **Optional rule.** Enable via `extra_rules = ["shared-lib-grouping"]` in `pyproject.toml`.

Forbid having too many ungrouped modules in `shared/lib`.

**Threshold: 15 files** (as per Steiger defaults).

## Configuration

```toml
[tool.pytest_fsd]
extra_rules = ["shared-lib-grouping"]
```

## Examples

✅ Pass:

```text
📂 shared/
  📂 lib/
    📄 __init__.py
    📄 dates.py
    📄 collections.py
```

❌ Fail:

```text
📂 shared/
  📂 lib/            # ❌ 16+ ungrouped files
    📄 __init__.py
    📄 dates.py
    📄 collections.py
    📄 utils.py
    📄 helpers.py
    📄 constants.py
    📄 types.py
    📄 api.py
    📄 ... (16+ files)
```

## Rationale

`shared/lib` is a high-risk candidate for becoming a dump folder. When it grows beyond 15 modules, the developer should create subfolders to group related functionality (e.g., `shared/lib/date_utils/`, `shared/lib/http/`).
