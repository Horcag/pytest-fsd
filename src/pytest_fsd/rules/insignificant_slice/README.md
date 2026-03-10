# `insignificant-slice`

> 🟡 **Manual review only.** This rule requires full import graph analysis which is beyond the scope of `pytest-fsd`.

Detects slices that have no references (unused) or only one reference (can be merged into the layer above).

## Why not automated?

This rule requires building a complete import graph of the project and counting how many other modules reference each slice. This is a complex analysis that:

1. Requires resolving all import paths (including dynamic imports, `__init__.py` re-exports)
2. Cannot be done with simple AST parsing — needs full module resolution
3. Is potentially slow for large projects

## How to check manually

1. Use your IDE's "Find Usages" feature on a slice's `__init__.py`
2. If a slice has 0 imports from other modules — it's dead code, remove it
3. If a slice has exactly 1 import — consider merging it into the importing layer

## Steiger Equivalent

- Slices with **no references** → remove or archive
- Slices with **one reference** → merge into the importing module
- **Exception**: pages are allowed to have just 1 reference (from app/routing)
- **Exception**: slices only used in `app` layer don't count (app shouldn't have UI)
