[English](README.md)

# pytest-fsd

[![PyPI](https://img.shields.io/pypi/v/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![Python](https://img.shields.io/pypi/pyversions/pytest-fsd)](https://pypi.org/project/pytest-fsd/)
[![CI](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml/badge.svg)](https://github.com/Horcag/pytest-fsd/actions/workflows/ci.yml)

Проверка архитектуры Python-проекта по [Feature-Sliced Design (FSD)](https://feature-sliced.design/) через pytest. Правила адаптированы из [FSD-плагина Steiger](https://github.com/feature-sliced/steiger); там, где необходимо, добавлены проверки для Python. Это самостоятельный пакет, а не официальный порт Steiger.

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
]
```

`no-file-segments` — опция этого Python-пакета: в реестре правил FSD-плагина Steiger 0.7.0 она отсутствует. `no-cross-imports` здесь по умолчанию включено для совместимости, а в Steiger по умолчанию отключено. Это осознанные различия.

Примеры и подробности находятся в [документации правил](src/pytest_fsd/rules/).

## Ограничения

- `forbidden-imports` и `no-cross-imports` используют [pytest-archon](https://pypi.org/project/pytest-archon/). Импорты под `if TYPE_CHECKING:` не видны этим проверкам во время выполнения.
- `no-public-api-sidestep` анализирует синтаксис Python и явные списки `__all__`. Динамически собранные экспорты могут давать ложные срабатывания.
- Прямых аналогов Steiger `inconsistent-naming` и `import-locality` здесь нет. Для именования Python и относительных импортов можно использовать правила Ruff `N` и `TID`; их поведение не совпадает полностью с правилами Steiger.
- `insignificant-slice` требует анализа графа импортов и не реализовано. Устаревший слой `processes` пакет не создаёт — не указывайте его в `layers`.
- Пакет проверяет Python-файлы и структуру каталогов. Он не реализует все правила Steiger и все соглашения JavaScript.

История выпусков Steiger — в [журнале изменений FSD-плагина](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/CHANGELOG.md).

## Лицензия

MIT. См. [LICENSE](LICENSE).
