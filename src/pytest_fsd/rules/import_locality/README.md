# `import-locality`

> 🔶 **Covered by Ruff.** This rule is NOT part of `pytest-fsd` core checks, but is fully enforceable via Ruff's `TID` (flake8-tidy-imports) plugin.

Require that imports **within the same slice** be relative, and imports **from another slice** be absolute.

## Ruff Configuration

```toml
[tool.ruff.lint]
select = ["TID"]  # flake8-tidy-imports

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"  # Запрет relative imports из родительских пакетов
```

### What `TID` covers

| Rule     | Description                                      |
| -------- | ------------------------------------------------ |
| `TID251` | Banned imports (configurable)                    |
| `TID252` | Relative imports from parent packages are banned |

## How it maps to FSD

```python
# src/entities/user/ui/avatar.py

# ✅ Relative import within the same slice — OK
from .styles import avatar_styles

# ✅ Absolute import from another slice — OK
from src.shared.ui import Button

# ❌ Absolute self-import — wasteful
from src.entities.user.ui.styles import avatar_styles

# ❌ Relative import from another slice — fragile
from ...shared.ui import Button
```

## Rationale

Imports between slices should be absolute to stay stable during refactors. Imports within a slice should be relative to keep them short and because the public API should not need to expose internal modules.
