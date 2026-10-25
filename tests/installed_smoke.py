"""Acceptance controls for an installed wheel, run with `python -I`."""

import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from pytest_fsd import validate_fsd_architecture


def main():
    assert version("pytest-fsd") == sys.argv[1]
    cases = [
        ("features/auth/api/router.py", "from src.features.tables import value\n", "no-cross-imports"),
        ("shared/lib/source.py", "from src.features.tables import value\n", "forbidden-imports"),
        ("features/auth/api/router.py", "from src.shared.lib import value\n", None),
    ]
    for source_path, source, expected_rule in cases:
        with tempfile.TemporaryDirectory(prefix="pytest-fsd-wheel-") as directory:
            root = Path(directory)
            files = {
                "features/auth/__init__.py": "__all__ = []\n",
                "features/tables/__init__.py": "from .model.value import value\n__all__ = ['value']\n",
                "features/tables/model/value.py": "raise RuntimeError('project must not execute')\nvalue = 1\n",
                "shared/lib/__init__.py": "value = 1\n",
                source_path: source,
            }
            for relative, body in files.items():
                path = root / "src" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
            try:
                validate_fsd_architecture(directory)
            except AssertionError as error:
                assert expected_rule and "[" + expected_rule + "]" in str(error), str(error)
            else:
                assert expected_rule is None, "Installed wheel missed " + str(expected_rule)
            print("PASS installed control:", expected_rule or "permitted import")


if __name__ == "__main__":
    main()
