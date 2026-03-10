# `no-reserved-folder-names`

> ⚡ **Optional rule.** Enable via `extra_rules = ["no-reserved-folder-names"]` in `pyproject.toml`.

Forbid subfolders within segments that have the same name as conventional segment names (`ui`, `model`, `api`, `lib`, `config`).

## Configuration

```toml
[tool.pytest_fsd]
extra_rules = ["no-reserved-folder-names"]
```

## Examples

✅ Pass:

```text
📂 shared/
  📂 ui/
    📄 __init__.py
    📄 button.py
```

❌ Fail:

```text
📂 shared/
  📂 ui/
    📄 __init__.py
    📂 lib/            # ❌ reserved segment name used as subfolder
      📄 helpers.py
```

## Rationale

Conventional segment names like `ui`, `model`, `api`, `lib`, `config` are well-known in FSD. Seeing them as subfolders inside another segment may mislead developers into thinking they are looking at slice segments rather than implementation details.
