# pytest-fsd

Linter архитектуры [Feature-Sliced Design (FSD)](https://feature-sliced.design/) для Python. Вдохновлен TS-линтером [Steiger](https://github.com/feature-sliced/steiger).

## Отличия от Steiger

В `pytest-fsd` портированы только **ядерные правила** изоляции слоев и Public API (защита от запутанных зависимостей).
Остальные стилистические правила Steiger (размеры файлов, тире в названиях папок, `repetitive-naming`, `inconsistent-naming` и т.д.) **нужно переносить и настраивать самостоятельно** с помощью классических Python-линтеров (например, `Ruff`).

## Установка

```bash
uv add --dev pytest-fsd
```

## Использование (Zero-boilerplate)

Создайте 1 тест-файл `tests/test_architecture.py`:

```python
from pytest_fsd import validate_fsd_architecture

def test_project_architecture():
    validate_fsd_architecture()
```

Настройте ваши слои в `pyproject.toml` (если не подходят стандартные веб-слои):

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
```

Запуск: `pytest tests/test_architecture.py`

## Что проверяет под капотом

1. `forbidden-imports`: слой импортирует код только _снизу_.
2. `no-cross-imports`: слайсы одного слоя _не_ импортируют друг друга.
3. `no-public-api-sidestep`: глубокие импорты в чужой слайс в обход его `__init__.py` запрещены.
4. `no-layer-public-api`: папки слоев (`features/`, `entities/`) _не содержат_ `__init__.py`.
5. Изоляция тестов: продакшн (`src/`) _не импортирует_ `tests/`.
