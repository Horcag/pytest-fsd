# `no-wildcard-exports`

Reject `from module import *` in public API files (`__init__.py`) on configured FSD layers, including App, Shared, and nested packages. Wildcard imports in other Python files are outside this rule's scope.

Adapted from [Steiger FSD plugin 0.8.0](https://github.com/feature-sliced/steiger/tree/master/packages/steiger-plugin-fsd/src/no-wildcard-exports). The check is disabled by default. Enable it in `pyproject.toml`:

```toml
[tool.pytest_fsd]
extra_rules = ["no-wildcard-exports"]
```

Prefer explicit names:

```python
# entities/user/__init__.py
from .model import User, get_user

__all__ = ["User", "get_user"]
```

This public API fails the check, even with an explicit `__all__`:

```python
from .model import *

__all__ = ["User"]
```

The rule examines import syntax without executing modules. It reports each wildcard statement with one-based line and character column positions and an exclusive end position. Conditional imports, including `if TYPE_CHECKING:`, are checked too. Unreadable files and files with invalid Python syntax produce a diagnostic with the underlying error.

Python's `from . import model as model` explicitly imports one module and is allowed. It does not copy all of that module's names into the package namespace, so it is not treated as JavaScript's `export * as model`.

Resolvable programmatic imports with a wildcard fromlist and literal executed wildcard imports are checked at their original call locations. Hidden directories and `__pycache__` are excluded; underscore-prefixed Python packages remain in scope.
