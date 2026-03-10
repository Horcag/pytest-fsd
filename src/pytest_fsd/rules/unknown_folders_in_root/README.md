# `unknown-folders-in-root`

Warn about directories inside `base_path` (e.g., `src/`) that are not listed in `[tool.pytest_fsd].layers`.

This catches typos like `fietures/` (instead of `features/`), or stale layer folders that were renamed but not cleaned up.

## Examples

✅ Pass (all directories are known layers):

```text
📂 src/
  📂 app/         # ← in layers
  📂 features/    # ← in layers
  📂 shared/      # ← in layers
```

❌ Fail:

```text
📂 src/
  📂 app/
  📂 fietures/    # ❌ typo — not in layers
  📂 shared/
```

## How to fix

- If a typo: rename the directory to the correct layer name.
- If intentional (non-FSD directory): add it to `ignore_paths` in `pyproject.toml`:

```toml
[tool.pytest_fsd]
ignore_paths = ["scripts", "migrations"]
```
