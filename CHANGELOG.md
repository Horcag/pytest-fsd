# Changelog

## 0.6.0

- Analyze `importlib.import_module`, `importlib.__import__`, and built-in `__import__` using the same layer, slice, public API, and app/UI rules as ordinary imports.
- Resolve imported/assigned loader aliases, literal names, constant bindings, concatenation, f-strings, joins, relative packages, and `__import__` fromlists without executing project code.
- Inspect literal `exec`/`eval` code and literal `compile` inputs, including nested dynamic imports. Report violations at the original call site.
- Fail with `dynamic-imports` when a recognized loader target, package, fromlist, executed code, or escaped loader cannot be inspected. Unknown values never count as proof that a recognized dynamic import is valid.
- Respect function/lambda parameter shadowing, class/method lookup, comprehensions and conditional bindings; preserve possible loader provenance across branches.
- Bound recursive code expansion and diagnostics to prevent generated code from making inspection unbounded.
- Add dynamic import, namespace, scope, no-execution, subprocess and installed-wheel regression controls. Custom import hooks and arbitrary runtime behavior are not executed by the checker.

## 0.5.0

- Replace runtime import checks with static AST analysis. Forbidden layer and sibling-slice imports now fail both under pytest and in standalone Python, without importing project code or requiring pytest-archon.
- Detect public-package, relative, aliased, source-root, nested-source-root, local-function, and `TYPE_CHECKING` imports; include package initializers. App and Shared segments remain free to import each other within their own layer.
- Repair public API checking for plain module imports, parent-package imports, nested roots, relative imports, and static `__all__` declarations and updates.
- Reject invalid configuration, unknown extra rules, missing source roots, and uninspectable Python files instead of silently passing. Respect Python encoding declarations and UTF-8 BOMs.
- Fix structural checks for fake API files, invalid segment filesystem types, names colliding with Shared segments, and reserved names inside custom segments. Avoid false GUI-import violations for relative modules.
- Add standalone/pytest regression controls and installed-wheel verification. Dynamic imports and dynamically computed exports remain outside static resolution.

## 0.4.0

- Adapt the applicable changes from Steiger 0.7.0 / FSD plugin 0.8.0, published September 25, 2026.
- Add the opt-in `no-wildcard-exports` rule for `from module import *` in Python public APIs (`__init__.py`). It is disabled by default, matching upstream.
- Include character columns in AST import diagnostics and retain start/end positions on violations. Existing violations without column information keep their previous format.
- Select and verify the actual Python interpreter in each CI matrix job.
- Update development pytest to 9.1.1 on Python 3.10+, keeping pytest 8 on Python 3.8/3.9; refresh the dependency lock and build backend.

Steiger's language server, file watching, Node.js requirements, and JavaScript dependency-resolution cache do not apply to this pytest-based Python package. This release does not add those features.

Upstream references: [FSD plugin changelog](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/CHANGELOG.md), [Steiger changelog](https://github.com/feature-sliced/steiger/blob/master/packages/steiger/CHANGELOG.md).
