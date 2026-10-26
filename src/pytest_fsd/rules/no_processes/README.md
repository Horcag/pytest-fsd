# `no-processes`

> 🔶 **Not a separately registered rule.** Simply do not include `"processes"` in the `layers` list in `pyproject.toml`.

The Processes layer was deprecated from FSD because there weren't enough use cases to justify its existence.

## Configuration

```toml
[tool.pytest_fsd]
# Notice: no "processes" here — it is omitted intentionally
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
```

If your project has a `processes` layer, consider moving the code into `app` or `features`.

## Steiger Equivalent

```text
📂 processes/   # ❌ deprecated layer
  📂 cart/
```

An unlisted `processes` directory is reported by `typo-in-layer-name`, unless explicitly listed in `ignore_paths`. Its contents are outside the configured-layer checks. If you explicitly add `processes` to `layers`, it is treated as a custom sliced layer; there is no separate deprecation check.
