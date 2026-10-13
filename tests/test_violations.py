from pytest_fsd._lib.violations import Violation


def test_violation_format_without_location():
    assert Violation("rule", "path.py", "message").format() == (
        " - [rule] path.py -> message"
    )


def test_violation_format_preserves_line_only_locations():
    assert Violation("rule", "path.py", "message", 3).format() == (
        " - [rule] path.py:3 -> message"
    )
