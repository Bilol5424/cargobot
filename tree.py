from pathlib import Path

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    ".idea",
    ".vscode",
    "node_modules",
}

def print_tree(
    path: Path,
    prefix: str = "",
    is_last: bool = True,
    root: bool = False
):
    if not root:
        connector = "└── " if is_last else "├── "
        print(prefix + connector + path.name)

    if path.is_dir():
        children = sorted(
            [p for p in path.iterdir() if p.name not in EXCLUDE_DIRS],
            key=lambda x: (x.is_file(), x.name.lower())
        )

        for index, child in enumerate(children):
            last = index == len(children) - 1
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(child, new_prefix, last)

if __name__ == "__main__":
    root_dir = Path(".").resolve()
    print(f"{root_dir.name}/")
    print_tree(root_dir, root=True)
