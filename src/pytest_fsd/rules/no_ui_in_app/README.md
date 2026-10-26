# `no-ui-in-app`

Reject an `app/ui` directory. This matches the [Steiger FSD rule](https://github.com/feature-sliced/steiger/tree/master/packages/steiger-plugin-fsd/src/no-ui-in-app): the app layer should configure and compose the application, while UI components belong in pages or widgets.

This Python package also rejects direct imports of these desktop GUI modules anywhere under `app`: `tkinter`, `PyQt5`, `PyQt6`, `PySide2`, `PySide6`, `ttkbootstrap`, and `customtkinter`. This extra check is specific to `pytest-fsd`.

```text
src/app/ui/              # violation
src/pages/home/ui/       # allowed
```

```python
# src/app/main.py
import tkinter            # violation in pytest-fsd
```

The import check covers static imports, resolvable programmatic imports and literal executed code without executing project modules. It applies to the configured App layer, including ordering prefixes. Relative local imports such as `from .tkinter import settings` are allowed. Hidden directories and `__pycache__` are excluded; underscore-prefixed Python packages remain in scope. The framework list is explicit and does not cover every GUI toolkit.
