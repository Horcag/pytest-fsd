import os

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # For older Pythons
    except ImportError:
        tomllib = None

from dataclasses import dataclass, field


@dataclass
class FsdConfig:
    """Configuration for pytest-fsd, read from [tool.pytest_fsd] in pyproject.toml."""

    base_path: str = "src"
    layers: list[str] = field(
        default_factory=lambda: [
            "app",
            "pages",
            "widgets",
            "features",
            "entities",
            "shared",
        ]
    )
    ignore_paths: list[str] = field(default_factory=list)
    extra_rules: list[str] = field(default_factory=list)


# Доступные дополнительные правила
AVAILABLE_EXTRA_RULES = {
    "excessive-slicing",
    "shared-lib-grouping",
    "no-file-segments",
    "no-reserved-folder-names",
}


def load_config(root_dir: str) -> FsdConfig:
    """Загружает настройки [tool.pytest_fsd] из pyproject.toml."""
    pyproject_path = os.path.join(root_dir, "pyproject.toml")

    if not os.path.exists(pyproject_path):
        return FsdConfig()

    if tomllib is None:
        raise ImportError(
            "Для чтения pyproject.toml требуется встроенный модуль 'tomllib' (Python 3.11+) "
            "или установка библиотеки 'tomli' (pip install tomli)."
        )

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    tool_config = data.get("tool", {}).get("pytest_fsd", {})

    config = FsdConfig()
    if "base_path" in tool_config:
        config.base_path = tool_config["base_path"]
    if "layers" in tool_config:
        config.layers = tool_config["layers"]
    if "ignore_paths" in tool_config:
        config.ignore_paths = tool_config["ignore_paths"]
    if "extra_rules" in tool_config:
        config.extra_rules = tool_config["extra_rules"]

    return config
