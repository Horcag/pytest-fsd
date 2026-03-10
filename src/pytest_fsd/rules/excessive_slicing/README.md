# `excessive-slicing`

> ⚡ **Optional rule.** Enable via `extra_rules = ["excessive-slicing"]` in `pyproject.toml`.

Forbid having too many ungrouped slices in a single layer.

**Threshold: 20 slices per layer** (as per Steiger defaults).

## Configuration

```toml
[tool.pytest_fsd]
extra_rules = ["excessive-slicing"]
```

## Examples

✅ Pass:

```text
📂 features/
  📂 auth/
  📂 profile/
  📂 settings/
  # ... up to 20 slices is fine
```

❌ Fail:

```text
📂 features/        # ❌ 21+ slices
  📂 comments/
  📂 posts/
  📂 users/
  📂 cars/
  📂 ... (21+ directories)
```

## Rationale

Having too many slices in a layer makes it harder to discover features in a project and promotes excessive decomposition. Consider grouping related slices into nested folders.
