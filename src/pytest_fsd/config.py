import os

from dataclasses import dataclass, field
from typing import List

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


@dataclass
class FsdConfig:
    """Configuration for pytest-fsd, read from [tool.pytest_fsd] in pyproject.toml."""

    base_path: str = "src"
    layers: List[str] = field(
        default_factory=lambda: [
            "app",
            "pages",
            "widgets",
            "features",
            "entities",
            "shared",
        ]
    )
    ignore_paths: List[str] = field(default_factory=list)
    extra_rules: List[str] = field(default_factory=list)


# Доступные дополнительные правила
AVAILABLE_EXTRA_RULES = {
    "excessive-slicing",
    "shared-lib-grouping",
    "no-file-segments",
    "no-reserved-folder-names",
    "no-wildcard-exports",
}


def load_config(root_dir: str) -> FsdConfig:
    """Загружает настройки [tool.pytest_fsd] из pyproject.toml."""
    pyproject_path = os.path.join(root_dir, "pyproject.toml")

    if not os.path.exists(pyproject_path):
        return FsdConfig()

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    tool_config = data.get("tool", {}).get("pytest_fsd", {})
    if not isinstance(tool_config, dict):
        raise ValueError("[tool.pytest_fsd] must be a table")
    unknown = set(tool_config) - {"base_path", "layers", "ignore_paths", "extra_rules"}
    if unknown:
        raise ValueError(f"Unknown pytest_fsd settings: {', '.join(sorted(unknown))}")
    if "base_path" in tool_config and (
        not isinstance(tool_config["base_path"], str) or not tool_config["base_path"].strip()
    ):
        raise ValueError("pytest_fsd.base_path must be a nonempty string")
    for name in ("layers", "ignore_paths", "extra_rules"):
        if name in tool_config:
            value = tool_config[name]
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                raise ValueError(f"pytest_fsd.{name} must be a list of nonempty strings")
    if "layers" in tool_config:
        layers = tool_config["layers"]
        if not layers or len(layers) != len(set(layers)):
            raise ValueError("pytest_fsd.layers must be nonempty and contain no duplicates")
        if any(layer in (".", "..") or any(char in layer for char in "/\\.") for layer in layers):
            raise ValueError("pytest_fsd.layers must contain directory names, not paths")
    unknown_rules = set(tool_config.get("extra_rules", [])) - AVAILABLE_EXTRA_RULES
    if unknown_rules:
        raise ValueError(f"Unknown pytest_fsd extra_rules: {', '.join(sorted(unknown_rules))}")

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
