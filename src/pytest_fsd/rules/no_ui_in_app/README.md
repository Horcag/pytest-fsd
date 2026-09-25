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

The import check looks at static `import` and `from ... import ...` syntax. It does not detect dynamic imports or every possible GUI framework.
