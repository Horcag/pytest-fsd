# `no-cross-imports`

Forbid imports between slices on the same layer. Slices within the same layer must be independent of each other.

## How it works

Statically analyzes Python imports without executing project modules. Includes public packages, relative imports, package initializers and `TYPE_CHECKING` branches; works under pytest and standalone Python.

The `app` and `shared` layers are excluded: they contain segments, which may depend on each other within the same layer.

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
