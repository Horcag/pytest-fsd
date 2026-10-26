---
name: pytest-fsd
description: Architecture checker for Python projects enforcing Feature-Sliced Design (FSD) rules.
---

# pytest-fsd AI Guidelines / Skill

This guideline defines the architecture strategy and problem-solving mechanisms for AI agents working within Python projects that use `pytest-fsd`.

## Goal and Concept

The `pytest-fsd` library enforces the Feature-Sliced Design (FSD) methodology. It protects codebases from:

1. Circular dependencies and layer violations (enforcing a strict top-to-bottom dependency flow).
2. Tight coupling between features (enforcing complete isolation between horizontal slices).
3. Public API bypasses (preventing direct imports from internal slice structure).

## Inner Workings

The library acts as a facade over static AST and filesystem checks. Import rules inspect absolute and relative imports, public packages, initializers, local-function imports and `TYPE_CHECKING` branches without executing project code. They raise `AssertionError` under pytest and standalone Python. Programmatic imports through importlib and __import__, loader aliases, constant expressions, and literal exec/eval/compile code feed the same rules. Unresolved recognized loader calls, executed code, or escaped loaders fail with dynamic-imports. Recursive expansion is bounded. Unresolved dynamic exports, invalid source and invalid configuration fail explicitly. The checker never executes project code or custom import hooks.

Configuration is centralized in `pyproject.toml` under the section `[tool.pytest_fsd]`.

## Troubleshooting Architectural Violations

When you introduce code or refactor, `pytest-fsd` tests might fail. Here is how you should interpret and fix these errors:

### 1. `must not import layers above it` (AST)

**Trigger**: A lower layer (e.g., `entities`) is trying to import from a higher layer (e.g., `features`).
**Resolution**:
FSD dictates downward dependencies only.

- Relocate the shared code to a lower layer (e.g., `shared`).
- Use Dependency Inversion (DI) via interfaces or protocols to abstract the dependency.

### 2. `must not import sibling slice` (AST)

**Trigger**: A slice (e.g., `features/user_auth`) is importing from another slice on the same layer (e.g., `features/user_cart`).
**Resolution**:
Slices on the same layer must not communicate directly (App and Shared contain segments rather than slices). They must remain isolated.

- Extract the common functionality into a lower layer (`entities` or `shared`).
- Compose the slices together inside a higher-level layer (like `widgets` or `pages`/`windows`).

### 3. `Public API Sidestep: importing internal module...` (AST)

**Trigger**: Code is importing deep internal files of a slice like `from src.features.auth.ui.button import Button`.
**Resolution**:
A slice's internal folder structure is strictly private. Only the root `__init__.py` of the slice exposes the Public API.

1. Add `from .ui.button import Button` to the slice's `__init__.py`.
2. Include `Button` in the slice's explicit `__all__` list.
3. Update the consuming file to import via the Public API: `from src.features.auth import Button`.

### 4. `Layer folder 'X' contains __init__.py` (AST)

**Trigger**: A layer folder (e.g., `src/features/__init__.py`) contains a Python file instead of just subdirectories.
**Resolution**:
In FSD, layer folders (`features`, `entities`, etc.) act strictly as grouping namespaces. They do not have their own Public API. Delete the `__init__.py` file from the layer folder root.

### 5. `Wildcard re-export` (AST, opt-in)

**Trigger**: A public API (`__init__.py`) uses `from .model import *` while `no-wildcard-exports` is enabled in `extra_rules`.
**Resolution**: List the imported names explicitly, then expose them through `__all__`. Explicit imports of modules such as `from . import model as model` are allowed.

## Additional and Unimplemented Rules

The default checks include structure and naming constraints as well as import rules. `excessive-slicing`, `shared-lib-grouping`, `no-file-segments`, `no-reserved-folder-names`, and `no-wildcard-exports` are available through `extra_rules`.

Applicable upstream changes are tracked through Steiger 0.7.0 / FSD plugin 0.8.0. `inconsistent-naming`, `import-locality`, and `insignificant-slice` remain unimplemented. Ruff naming and import rules may cover related Python concerns, but they are not equivalent Steiger checks.
