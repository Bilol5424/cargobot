import os

# ===== НАСТРОЙКИ =====
OUTPUT_FILE = "project_dump.txt"

EXCLUDE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build"
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".exe",
    ".dll",
    ".so",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".mp4",
    ".mp3"
}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def is_text_file(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return False
    return True


def export_project(root_dir: str):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                file_path = os.path.join(root, file)

                if not is_text_file(file_path):
                    continue

                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    output.write(
                        f"\n===== FILE: {file_path} =====\n"
                        f"[SKIPPED: file is larger than {MAX_FILE_SIZE // 1024} KB]\n"
                    )
                    continue

                output.write(f"\n===== FILE: {file_path} =====\n")

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        output.write(f.read())
                except Exception as e:
                    output.write(f"[ERROR READING FILE: {e}]\n")


if __name__ == "__main__":
    project_root = os.getcwd()
    export_project(project_root)
    print(f"Готово. Содержимое проекта сохранено в '{OUTPUT_FILE}'")
