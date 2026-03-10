# src/pytest_fsd/_lib/fs_utils.py
"""Shared filesystem utilities used by multiple rules."""

import os
from typing import List

from ..config import FsdConfig

# Стандартные сегменты FSD для Python-проектов
STANDARD_SEGMENTS = ("ui", "model", "api", "lib", "config")


def get_sliced_layers(config: FsdConfig) -> List[str]:
    """Return layers that contain slices (excluding app and shared)."""
    return [
        layer_name
        for layer_name in config.layers
        if layer_name not in ("app", "shared")
    ]


def get_slices(layer: str, base_path: str) -> List[str]:
    """Return list of slice directory names inside a given layer."""
    path = os.path.join(base_path, layer)
    if not os.path.isdir(path):
        return []
    return [
        d
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d)) and not d.startswith("_")
    ]
