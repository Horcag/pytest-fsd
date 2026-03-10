# `no-segmentless-slices`

Require every slice to contain at least one standard FSD segment.

Standard segments: `ui`, `model`, `api`, `lib`, `config`.

A segment can be either a **folder** (e.g., `features/auth/model/`) or a **file** (e.g., `features/auth/model.py`).

## Examples

✅ Pass:

```
📂 features/
  📂 auth/
    📂 model/         # ← standard segment
      📄 handler.py
    📄 __init__.py
```

❌ Fail:

```
📂 features/
  📂 auth/
    📄 handler.py     # ❌ no standard segment folder or file
    📄 __init__.py
```

## Rationale

A slice without standard segments is usually an architectural smell — it suggests that the code is not properly decomposed into purpose-driven groups.
