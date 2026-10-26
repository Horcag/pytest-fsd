# `no-public-api-sidestep`

Forbid imports of another slice's internal modules and names outside its explicit `__all__` public API.

Shared uses the same public boundaries as `public-api`: ordinary segments such as `shared/config` expose their root `__init__.py`; each immediate package in `shared/lib` and `shared/ui` exposes its own `__init__.py`. Individual Python modules in `shared/lib` and `shared/ui` are public entrypoints and do not need a package wrapper. The optional root APIs of `shared/lib` and `shared/ui` are not required boundaries.

## How it works

Uses AST analysis to scan all import statements. If a module imports from another slice with a path deeper than `src.layer.slice` (e.g., `src.features.auth.model.handler`), that's a sidestep violation.

Imports within the same slice or Shared API package are allowed to be deep (internal imports). Imports between Shared libraries or segments must use the target's public API.

For example, `from src.shared.lib.dates import today` is allowed when `dates/__init__.py` explicitly exports `today`. Importing `src.shared.lib.dates.internal` from another library or an upper layer is forbidden. `from src.shared.lib.format_date import format_date` remains allowed when `format_date.py` is an individual module.

Package imports such as `import src.features.auth` and `from src.features import auth` are allowed; the package name itself does not need to appear in its `__all__`. Explicit names imported from a public package must appear in a statically resolvable `__all__`. A wildcard import also requires a known export list. Supported declarations include lists, tuples, annotations, concatenation, `+=`, `append`, and `extend`; unknown or escaped export lists produce a diagnostic. Missing public API files are handled by `public-api`.

Relative imports, nested source roots, configured layer prefixes, conditional imports, resolvable programmatic imports and literal executed code are checked without executing project modules. Sources in unconfigured layers, hidden directories and `__pycache__` are excluded. Underscore-prefixed Python packages remain in scope.

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
