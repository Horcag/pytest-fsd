from pathlib import Path

import pytest


def parse_steiger_tree(base_path: Path, tree_str: str) -> None:
    """
    Parses a string representing a file tree (using Steiger's syntax)
    and creates it on disk.

    Example Steiger syntax:
    📂 shared
      📂 ui
        📄 index.ts
    """
    lines = [line for line in tree_str.splitlines() if line.strip()]
    if not lines:
        return

    # Find base indent
    base_indent = len(lines[0]) - len(lines[0].lstrip())

    path_stack = [(base_path, base_indent - 1)]

    for line in lines:
        indent = len(line) - len(line.lstrip())
        content = line.strip()

        # Pop from stack until we find the parent directory based on indentation
        while path_stack and path_stack[-1][1] >= indent:
            path_stack.pop()

        parent_path = path_stack[-1][0]

        if content.startswith("📂"):
            folder_name = content.replace("📂", "").strip()
            new_dir = parent_path / folder_name
            new_dir.mkdir(parents=True, exist_ok=True)
            path_stack.append((new_dir, indent))
        elif content.startswith("📄"):
            file_name = content.replace("📄", "").strip()
            new_file = parent_path / file_name
            new_file.parent.mkdir(parents=True, exist_ok=True)
            new_file.touch()


@pytest.fixture
def create_project(tmp_path: Path):
    """
    Fixture to create a temporary FSD project structure.
    Returns a function that takes a tree string and optional extra pyproject.toml content.
    """
    def _create_project(tree_str: str, extra_rules: list[str] | None = None) -> Path:
        src_dir = tmp_path / "src"
        src_dir.mkdir(exist_ok=True)

        # Create the pyproject.toml
        toml_content = [
            "[tool.pytest_fsd]",
            'base_path = "src"',
            'layers = ["app", "windows", "widgets", "features", "entities", "shared"]',
        ]
        
        if extra_rules:
            rules_str = ", ".join(f'"{r}"' for r in extra_rules)
            toml_content.append(f"extra_rules = [{rules_str}]")

        (tmp_path / "pyproject.toml").write_text("\n".join(toml_content), encoding="utf-8")

        parse_steiger_tree(src_dir, tree_str)
        
        # Add tmp_path to sys.path so pytest_archon can import the modules
        import sys
        sys.path.insert(0, str(tmp_path))
        
        return tmp_path

    yield _create_project
    
    # Cleanup sys.path after tests (approximate cleanup)
    import sys
    if str(tmp_path) in sys.path:
        sys.path.remove(str(tmp_path))
