# `no-processes`

> 🔶 **Covered by configuration.** Simply do not include `"processes"` in the `layers` list in `pyproject.toml`.

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

In `pytest-fsd`, an unlisted layer is simply ignored by all rules. If you keep `processes` out of the `layers` config, its existence won't affect the checks, but its contents also won't be validated.
