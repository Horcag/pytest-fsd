# Changelog

## 0.4.0

- Adapt the applicable changes from Steiger 0.7.0 / FSD plugin 0.8.0, published September 25, 2026.
- Add the opt-in `no-wildcard-exports` rule for `from module import *` in Python public APIs (`__init__.py`). It is disabled by default, matching upstream.
- Include character columns in AST import diagnostics and retain start/end positions on violations. Existing violations without column information keep their previous format.
- Select and verify the actual Python interpreter in each CI matrix job.
- Update development pytest to 9.1.1 on Python 3.10+, keeping pytest 8 on Python 3.8/3.9; refresh the dependency lock and build backend.

Steiger's language server, file watching, Node.js requirements, and JavaScript dependency-resolution cache do not apply to this pytest-based Python package. This release does not add those features.

Upstream references: [FSD plugin changelog](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/CHANGELOG.md), [Steiger changelog](https://github.com/feature-sliced/steiger/blob/master/packages/steiger/CHANGELOG.md).
