# `no-public-api-sidestep`

Forbid deep imports into other slices. All cross-slice imports must go through the slice's `__init__.py` (its Public API).

## How it works

Uses AST analysis to scan all import statements. If a module imports from another slice with a path deeper than `src.layer.slice` (e.g., `src.features.auth.model.handler`), that's a sidestep violation.

Imports within the same slice are allowed to be deep (internal imports).

## Examples

✅ Pass:

```python
# src/pages/main/ui/page.py
from src.features.auth import login_user        # OK: Public API
from src.features.auth import AuthCommand       # OK: Public API
```

❌ Fail:

```python
# src/pages/main/ui/page.py
from src.features.auth.model.handler import login_user  # VIOLATION: deep import
from src.features.auth.model import AuthCommand         # VIOLATION: deep import
```

## Rationale

The public API rule ensures that the internal structure of a slice can change freely during refactors as long as the public API stays the same. This ensures codebase stability.
