[English](README.md)

# pytest-fsd

[![PyPI](https://img.shields.io/pypi/v/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![Python](https://img.shields.io/pypi/pyversions/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![CI](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml/badge.svg)](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml)

Проверка архитектуры Python-проекта по [Feature-Sliced Design (FSD)](https://feature-sliced.design/) через pytest. Правила адаптированы из [FSD-плагина Steiger](https://github.com/feature-sliced/steiger); там, где необходимо, добавлены проверки для Python. Это самостоятельный пакет, а не официальный порт Steiger.

Учтены применимые изменения до Steiger 0.7.0 / FSD-плагина 0.8.0. Адаптации для Python описаны в [журнале изменений](CHANGELOG.md).

## Установка

```bash
pip install pytest-fsd
# или
uv add --dev pytest-fsd
```

Поддерживается Python 3.8–3.14.

## Использование

Укажите слои проекта в `pyproject.toml` от верхнего к нижнему:

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "pages", "widgets", "features", "entities", "shared"]
# ignore_paths = ["my_non_fsd_package"]
```

Создайте архитектурный тест:

```python
# tests/test_architecture.py
from pytest_fsd import validate_fsd_architecture


def test_architecture():
    validate_fsd_architecture()
```

Запустите `pytest tests/test_architecture.py`. Нарушения выводятся как ошибки теста с именем правила и путём. Если исходный код лежит в другом каталоге, измените `base_path`. Валидатор читает `[tool.pytest_fsd]` из корня проекта; параметр `validate_fsd_architecture(project_root="...")` позволяет проверить другой проект.

Самостоятельный запуск тоже вызывает `AssertionError` при нарушениях и завершается с ненулевым кодом:

```bash
python -c "from pytest_fsd import validate_fsd_architecture; validate_fsd_architecture()"
```

Неизвестные настройки и дополнительные правила вызывают `ValueError`. Отсутствующий каталог исходников, симлинки внутри настроенных слоёв и Python-файлы, которые невозможно разобрать, приводят к ошибке проверки. `ignore_paths` исключает посторонние каталоги из проверки имён слоёв, но не отключает проверку импортов настроенных слоёв.

## Правила

По умолчанию проверяются направление импортов между слоями (`forbidden-imports`), независимость слайсов (`no-cross-imports`), публичные API (`public-api`, `no-public-api-sidestep`, `no-layer-public-api`), структура (`no-segmentless-slices`, `no-segments-on-sliced-layers`, `typo-in-layer-name`, `ambiguous-slice-names`), именование (`segments-by-purpose`, `repetitive-naming`) и `no-ui-in-app`.

`segments-by-purpose` включает общие имена из FSD-плагина Steiger 0.7.0: `schemas`, `handlers`, `fixtures`, `middlewares`, `validators`, `resolvers`, `mutations`, `assets` и другие. Они проверяются в роли FSD-сегментов. Пакет также проверяет сегменты-файлы, поэтому `fixtures.py` внутри слайса будет отмечен.

`no-ui-in-app` запрещает каталог `app/ui`, как и Steiger. Дополнительно сохранена Python-проверка прямых импортов распространённых GUI-библиотек из слоя `app`.

При необходимости включите дополнительные проверки:

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "pages", "widgets", "features", "entities", "shared"]
extra_rules = [
    "excessive-slicing",        # Более 20 слайсов в слое
    "shared-lib-grouping",      # Более 15 отдельных Python-файлов в shared/lib
    "no-file-segments",         # Сегменты должны быть каталогами
    "no-reserved-folder-names", # Без вложенных имён сегментов вроде model/model
    "no-wildcard-exports",      # Без `from module import *` в __init__.py
]
```

`no-wildcard-exports` появилось в FSD-плагине Steiger 0.8.0 и по умолчанию отключено в обоих пакетах. Проверяются файлы `__init__.py` на всех указанных слоях, включая вложенные пакеты. Явные импорты модулей вроде `from . import model as model` допустимы в Python. Диагностика AST-проверок импортов теперь включает номер строки и позицию символа.

`no-file-segments` — опция этого Python-пакета: в реестре правил FSD-плагина Steiger 0.8.0 она отсутствует. `no-cross-imports` здесь по умолчанию включено для совместимости, а в Steiger по умолчанию отключено. Это осознанные различия.

Примеры и подробности находятся в [документации правил](src/pytest_fsd/rules/).

## Ограничения

- Правила импортов статически разбирают Python, включая относительные импорты, `__init__.py`, импорты внутри функций и ветки `if TYPE_CHECKING:`. Код проекта не исполняется. Программные импорты через `importlib.import_module`, `importlib.__import__` и встроенный `__import__` тоже проверяются. Поддерживаются алиасы загрузчиков, литералы, переменные с константными значениями, конкатенация, f-строки, `join`, относительные пакеты и `fromlist`. Строки `exec`/`eval` и константные входы `compile` разбираются рекурсивно с ограничением объёма анализа. Неразрешённые вызовы известных загрузчиков и строки исполняемого кода завершаются ошибкой `[dynamic-imports]`, а не пропускаются. Произвольные пользовательские загрузчики и код проекта не исполняются.
- `no-public-api-sidestep` анализирует синтаксис Python и явные списки `__all__`. Динамически собранные экспорты могут давать ложные срабатывания.
- Прямых аналогов Steiger `inconsistent-naming` и `import-locality` здесь нет. Для именования Python и относительных импортов можно использовать правила Ruff `N` и `TID`; их поведение не совпадает полностью с правилами Steiger.
- `insignificant-slice` требует анализа графа импортов и не реализовано. Устаревший слой `processes` пакет не создаёт — не указывайте его в `layers`.
- Пакет проверяет Python-файлы и структуру каталогов. Он не реализует все правила Steiger и все соглашения JavaScript.

История выпусков Steiger — в [журнале изменений FSD-плагина](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/CHANGELOG.md).

## Лицензия

MIT. См. [LICENSE](LICENSE).

Вызов `importlib.import_module(f"src.{layer}.tables")` проверяется, если значение `layer` известно. Если имя приходит только во время исполнения, проверка выдаёт `[dynamic-imports]`: замените такой вызов явным выбором между известными импортами. Чекер проверяет архитектуру и не является интерпретатором произвольного Python-кода или средством изоляции исполнения.

Полная [матрица аудита правил](docs/RULE-AUDIT.md) связывает все 17 реализованных правил и две входные проверки с допустимыми и запрещёнными примерами, включением правил и проверкой установленного пакета.

Публичные API Shared тоже проверяются: для обычных сегментов это `__init__.py` сегмента, для `shared/ui` и `shared/lib` — API отдельных пакетов компонентов/библиотек либо самостоятельные Python-модули. Внутри одной границы импорты свободны. Каталоги служебных данных с точкой в начале имени и `__pycache__` исключаются из сканирования; пакеты `_private` и `__private` проверяются как обычный код.
