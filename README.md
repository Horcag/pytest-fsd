# pytest-fsd

**FSD Architecture Validation for Python Projects.**

`pytest-fsd` автоматически проверяет архитектуру вашего Python-проекта на соответствие методологии [Feature-Sliced Design](https://feature-sliced.design/).

Использует гибридный подход: динамические проверки через [pytest-archon](https://pypi.org/project/pytest-archon/) + статический AST-анализ + проверка файловой структуры.

## Установка

```bash
pip install pytest-fsd
# или
uv add --dev pytest-fsd
```

## Использование

### 1. Настройка `pyproject.toml`

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
```

### 2. Создание теста

```python
# tests/test_architecture.py
from pytest_fsd import validate_fsd_architecture

def test_project_architecture():
    validate_fsd_architecture()
```

### 3. Запуск

```bash
pytest tests/test_architecture.py -vv
```

## Архитектура библиотеки

Каждое правило — это папка внутри `src/pytest_fsd/rules/<rule_name>/` с:

- `__init__.py` — логика проверки (функция `check(config, project_root) -> List[Violation]`)
- `README.md` — описание правила, примеры, rationale

```
src/pytest_fsd/
  __init__.py           # Фасад: validate_fsd_architecture()
  config.py             # Чтение [tool.pytest_fsd] из pyproject.toml
  _lib/                 # Общие утилиты
    violations.py       # Единый Violation dataclass
    ast_utils.py        # AST-парсинг импортов
    fs_utils.py         # Файловые утилиты, константы сегментов
  rules/
    forbidden_imports/          # pytest-archon: слои импортируют только нижележащие
    no_cross_imports/           # pytest-archon: слайсы в одном слое независимы
    no_public_api_sidestep/     # AST: импорт только через __init__.py слайса
    no_layer_public_api/        # FS: слоевые папки без __init__.py
    no_ui_in_app/               # AST: запрет UI-фреймворков в app
    repetitive_naming/          # FS: файлы не дублируют имя слайса
    no_segmentless_slices/      # FS: слайс содержит хотя бы один сегмент
    segments_by_purpose/        # FS: запрет utils/helpers/components/hooks
    ambiguous_slice_names/      # FS: имена слайсов ≠ имена сегментов shared
    no_segments_on_sliced_layers/ # FS: в слайсовых слоях не должно быть сегментов напрямую
    public_api/                 # FS: каждый слайс должен иметь __init__.py
```

---

## Матрица покрытия правил Steiger

Полный список правил из [Steiger FSD Plugin](https://github.com/feature-sliced/steiger) и их статус в `pytest-fsd`:

| #   | Steiger Rule                                    | pytest-fsd Status      | Описание                                                                               |
| --- | ----------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------- |
| 1   | `forbidden-imports` / `no-higher-level-imports` | ✅ **Полностью**       | Слои импортируют только нижележащие слои                                               |
| 2   | `no-cross-imports`                              | ✅ **Полностью**       | Слайсы в одном слое независимы друг от друга                                           |
| 3   | `no-public-api-sidestep`                        | ✅ **Полностью**       | Импорт из чужого слайса только через `__init__.py`                                     |
| 4   | `public-api`                                    | ✅ **Полностью**       | Каждый слайс и сегмент shared обязан иметь `__init__.py`                               |
| 5   | `no-layer-public-api`                           | ✅ **Полностью**       | Папки слоев (`features/`, `entities/`) не должны содержать `__init__.py`               |
| 6   | `segments-by-purpose`                           | ✅ **Полностью**       | Запрет `utils`, `helpers`, `hooks`, `components`, `modals`, `types`, `constants` и др. |
| 7   | `no-segmentless-slices`                         | ✅ **Полностью**       | Слайс обязан содержать хотя бы один стандартный сегмент                                |
| 8   | `repetitive-naming`                             | ✅ **Полностью**       | Файлы не дублируют имя слайса (`user/user_model.py` → `user/model.py`)                 |
| 9   | `no-ui-in-app`                                  | ✅ **Полностью**       | Слой `app` не должен импортировать UI-фреймворки                                       |
| 10  | `ambiguous-slice-names`                         | ✅ **Полностью**       | Имена слайсов не совпадают с сегментами `shared/`                                      |
| 11  | `no-segments-on-sliced-layers`                  | ✅ **Полностью**       | В слайсовых слоях нет прямых папок-сегментов                                           |
| 12  | `inconsistent-naming`                           | 🔶 **Ruff**            | Обеспечивается плагином `N` (pep8-naming) в `Ruff`                                     |
| 13  | `import-locality`                               | 🔶 **Ruff**            | Обеспечивается плагином `TID` (flake8-tidy-imports) в `Ruff`                           |
| 14  | `typo-in-layer-name`                            | 🔶 **Конфигурация**    | Покрывается блоком `[tool.pytest_fsd].layers` в `pyproject.toml`                       |
| 15  | `no-processes`                                  | 🔶 **Конфигурация**    | Слой `processes` deprecated; просто не включайте его в `layers`                        |
| 16  | `excessive-slicing`                             | ⚡ **Опционально**     | Более 20 слайсов в одном слое (порог: 20)                                              |
| 17  | `insignificant-slice`                           | 🟡 **Ручная проверка** | Требует анализа графа импортов для определения "незначительных" слайсов                |
| 18  | `no-file-segments`                              | ⚡ **Опционально**     | Сегмент как файл (`model.py`) вместо папки (`model/`)                                  |
| 19  | `shared-lib-grouping`                           | ⚡ **Опционально**     | Более 15 файлов в `shared/lib` без группировки                                         |
| 20  | `no-reserved-folder-names`                      | ⚡ **Опционально**     | Подпапки в сегментах не должны совпадать с именами сегментов                           |

### Легенда

| Статус                     | Значение                                                                                            |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| ✅ **Полностью**           | Правило полностью автоматизировано и выполняется при каждом запуске `pytest`                        |
| ⚡ **Опционально**         | Правило автоматизировано, но включается через `extra_rules` в `pyproject.toml`                      |
| 🔶 **Ruff / Конфигурация** | Покрывается внешними инструментами (`Ruff`) или конфигурацией `pyproject.toml`                      |
| 🟡 **Ручная проверка**     | Требует субъективной оценки или сложного анализа, который лучше производить вручную при code review |

---

## Включение дополнительных правил

Добавьте в `pyproject.toml`:

```toml
[tool.pytest_fsd]
base_path = "src"
layers = ["app", "windows", "widgets", "features", "entities", "shared"]
extra_rules = [
    "excessive-slicing",       # ≤ 20 слайсов на слой
    "shared-lib-grouping",     # ≤ 15 файлов в shared/lib
    "no-file-segments",        # Сегменты должны быть папками, не файлами
    "no-reserved-folder-names" # Подпапки сегментов не могут называться ui/model/api/lib/config
]
```

Каждое правило подробно описано в `src/pytest_fsd/rules/<rule_name>/README.md`.

---

## Настройка Ruff для смежных правил

Для полного покрытия FSD-правил, которые Steiger проверяет на уровне линтинга (и которые `pytest-fsd` не дублирует), добавьте в `pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["N", "TID"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"
```

| Ruff Plugin                 | Steiger Rule          | Что проверяет                                   |
| --------------------------- | --------------------- | ----------------------------------------------- |
| `N` (pep8-naming)           | `inconsistent-naming` | `snake_case` для модулей, переменных, функций   |
| `TID` (flake8-tidy-imports) | `import-locality`     | Запрет relative imports из родительских пакетов |

Подробные описания и примеры конфигурации: `src/pytest_fsd/rules/inconsistent_naming/README.md` и `src/pytest_fsd/rules/import_locality/README.md`.

## Известные ограничения (Known Limitations)

- **`TYPE_CHECKING` импорты**: Правила, использующие `pytest-archon` (например, `forbidden-imports` и `no-cross-imports`), работают на базе динамического анализа графа импортов в рантайме. Импорты, находящиеся внутри блоков `if TYPE_CHECKING:`, не выполняются при загрузке модуля и, следовательно, **не видны для этих правил**.
- **Относительные импорты**: В модуле `ast_utils.py` добавлена поддержка относительных путей для проверки `no-public-api-sidestep`, однако `Ruff` (плагин `TID`) всё равно лучше справляется с контролем относительных импортов за пределами слайсов.
- **Динамический `__all__`**: Правило `no-public-api-sidestep` использует статический AST-анализ для извлечения `__all__` из файла `__init__.py`. Если список экспортов формируется динамически (например, `__all__ = a + b`), статический анализатор не сможет его прочитать, и инструмент может выдать ложноположительные нарушения. Экспорты в `__all__` должны быть заданы как явный список или кортеж.
- **Минимальная версия Python**: Библиотека поддерживает Python **3.8+**. Для Python `<3.11` используется обратная совместимость через пакет `tomli`, а на Python `3.11+` — встроенный `tomllib`.

## Лицензия

MIT
