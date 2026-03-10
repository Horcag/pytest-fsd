# `typo-in-layer-name`

> 🔶 **Covered by configuration.** This rule is enforced by the `[tool.pytest_fsd].layers` section in `pyproject.toml`.

Ensure that all layer directories are named correctly without typos.

## How it works

When you explicitly list your layers in `pyproject.toml`, `pytest-fsd` only recognizes those exact names. Any typo in a layer folder name (e.g., `fietures` instead of `features`) simply won't be checked — and the `no-segmentless-slices` rule will flag the content as unstructured.

## Configuration

```toml
[tool.pytest_fsd]
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
#         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#         Only these exact names are recognized as valid FSD layers.
#         A directory "fietures" would be ignored entirely.
```

## Steiger Equivalent

```text
📂 shraed/     # ❌ typo — Steiger would flag this
📂 fietures/   # ❌ typo
📂 entities/   # ✅ correct
```

In `pytest-fsd`, if `fietures/` is not in the `layers` list, it is unseen by the tool. Running `pytest-fsd` with the correct `layers` config implicitly enforces proper naming.
