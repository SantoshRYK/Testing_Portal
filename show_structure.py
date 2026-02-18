from pathlib import Path

def print_tree(directory, out, prefix="", ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv'}
    entries = [p for p in sorted(Path(directory).iterdir(), key=lambda x: (x.is_file(), x.name))
               if not (p.name in ignore_dirs or p.name.startswith('.'))]
    for i, path in enumerate(entries):
        is_last = i == len(entries) - 1
        out.write(f"{prefix}{'└── ' if is_last else '├── '}{path.name}\n")
        if path.is_dir():
            extension = "    " if is_last else "│   "
            print_tree(path, out, prefix + extension, ignore_dirs)

if __name__ == "__main__":
    with open("tree_structure.txt", "w", encoding="utf-8") as f:
        print_tree(".", f)