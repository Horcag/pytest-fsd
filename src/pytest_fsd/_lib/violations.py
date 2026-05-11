# src/pytest_fsd/_lib/violations.py
"""Unified violation dataclass for all FSD rules."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Violation:
    """Represents a single FSD architecture violation."""

    rule: str
    file_path: str
    message: str
    line_number: Optional[int] = None

    def format(self) -> str:
        """Format the violation as a human-readable string."""
        location = self.file_path
        if self.line_number is not None:
            location += f":{self.line_number}"
        return f" - [{self.rule}] {location} -> {self.message}"
