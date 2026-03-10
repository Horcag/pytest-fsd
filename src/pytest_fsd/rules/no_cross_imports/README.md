# `no-cross-imports`

Forbid imports between slices on the same layer. Slices within the same layer must be independent of each other.

## How it works

Uses `pytest-archon` to dynamically verify that each slice in a layer does not import from any other slice in the same layer.

The `shared` layer is excluded from this check, as segments in `shared` may depend on each other.

## Examples

✅ Pass:

```python
# src/features/auth/model/handler.py
from src.entities.user import User     # OK: different layer
from src.shared.lib import hash_pw     # OK: shared layer
```

❌ Fail:

```python
# src/features/auth/model/handler.py
from src.features.profile import Profile  # VIOLATION: same layer (features)
```

## Rationale

Cross-imports between slices create tight coupling, which makes it difficult to refactor or move slices independently. If two slices need to share code, that code should be extracted to a lower layer (e.g., `entities` or `shared`).
