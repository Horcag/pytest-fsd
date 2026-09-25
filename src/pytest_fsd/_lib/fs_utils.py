# src/pytest_fsd/_lib/fs_utils.py
"""Shared filesystem utilities used by multiple rules."""

import os
import re
from typing import List, Optional

from ..config import FsdConfig

# Стандартные сегменты FSD для Python-проектов
STANDARD_SEGMENTS = ("ui", "model", "api", "lib", "config")


def get_canonical_layer(layer_name: str) -> str:
    """Return the layer name without ordering prefixes (e.g., '6_shared' -> 'shared')."""
    # Remove leading digits and underscores
    return re.sub(r"^[0-9_]+", "", layer_name)


def get_layer_by_canonical_name(config: FsdConfig, name: str) -> Optional[str]:
    """Find the actual layer name in config that matches the canonical name."""
    for layer in config.layers:
        if get_canonical_layer(layer) == name:
            return layer
    return None


def get_sliced_layers(config: FsdConfig) -> List[str]:
    """Return layers that contain slices (excluding app and shared)."""
    return [
        layer_name
        for layer_name in config.layers
        if get_canonical_layer(layer_name) not in ("app", "shared")
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
