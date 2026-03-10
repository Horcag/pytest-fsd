# `no-ui-in-app`

Forbid direct imports of UI frameworks (tkinter, PyQt, PySide, etc.) in the `app` layer.

The `app` layer is meant for application initialization: providers, routing, store configuration. UI components should live in `pages`, `windows`, or `widgets` layers.

## Checked UI frameworks

`tkinter`, `PyQt5`, `PyQt6`, `PySide2`, `PySide6`, `ttkbootstrap`, `customtkinter`

## Examples

✅ Pass:

```python
# src/app/main.py
from src.pages.main import MainPage  # OK: app uses a page, doesn't build UI itself

app = MainPage()
app.mainloop()
```

❌ Fail:

```python
# src/app/main.py
import tkinter as tk  # ❌ UI framework in app layer

root = tk.Tk()
root.mainloop()
```

## Rationale

Mixing initialization logic with UI creation leads to monolithic app layers. UI components should be decomposed into slices in appropriate layers like `pages` or `widgets`.
