from pytest_fsd.config import load_config
from pytest_fsd.rules.public_api import RULE_NAME, check


def test_public_api_no_errors_on_valid_project(create_project):
    """Test that no errors are reported when all slices have public APIs."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
          📂 posts
            📂 ui
            📄 __init__.py
        📂 features
          📂 comments
            📂 ui
            📄 __init__.py
        📂 windows
          📂 editor
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_public_api_errors_on_missing_api(create_project):
    """Test that errors are reported when slices or shared segments lack a public API."""
    project_root = create_project(
        """
        📂 shared
          📂 config
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
          📂 posts
            📂 ui
        📂 features
          📂 comments
            📂 ui
        📂 windows
          📂 editor
            📂 ui
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))

    # Expecting 4 violations: shared/config, entities/posts, features/comments, windows/editor
    assert len(violations) == 4

    messages = sorted([v.message for v in violations])
    assert any("Segment 'config' in 'shared' is missing __init__.py" in msg for msg in messages)
    assert any("Slice 'posts' in layer 'entities' is missing __init__.py" in msg for msg in messages)
    assert any("Slice 'comments' in layer 'features' is missing __init__.py" in msg for msg in messages)
    assert any("Slice 'editor' in layer 'windows' is missing __init__.py" in msg for msg in messages)
    assert all(v.rule == RULE_NAME for v in violations)


def test_public_api_shared_ui_lib_exceptions(create_project):
    """Test that shared/ui and shared/lib don't need __init__.py at root, but their subfolders do."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 styles.py
            📄 button.py
            📂 complex_widget
          📂 lib
            📄 utils.py
            📂 async_helpers
              📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))

    # Expecting 1 violation: shared/ui/complex_widget is missing __init__.py
    assert len(violations) == 1
    assert "Subfolder 'complex_widget' in 'shared/ui' is missing __init__.py" in violations[0].message
