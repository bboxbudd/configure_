from Prac1 import VFS, ShellEmulator


class OutputManager:
    """Простой класс вывода"""
    def __init__(self):
        self.buffer = []

    def write(self, text):
        self.buffer.append(text)

    def flush(self):
        out = "".join(self.buffer)
        self.buffer.clear()
        return out


import sys
import os
from Prac1 import VFS, ShellEmulator


class OutputManager:
    """Простой класс вывода"""
    def __init__(self):
        self.buffer = []

    def write(self, text):
        self.buffer.append(text)

    def flush(self):
        out = "".join(self.buffer)
        self.buffer.clear()
        return out


def main():
    # Проверяем, указан ли путь к VFS
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python vfs_shell_main.py <путь_к_vfs.csv>\n")
        sys.exit(1)

    vfs_path = sys.argv[1]

    if not os.path.exists(vfs_path):
        print(f"Ошибка: файл '{vfs_path}' не найден.")
        sys.exit(1)

    # Загружаем виртуальную ФС
    vfs = VFS(vfs_path)
    shell = ShellEmulator(vfs)
    out = OutputManager()

    print(f"[debug] Загружена VFS: {os.path.abspath(vfs_path)}\n")

    while shell.running:
        cmd = input(f"{shell.current_dir}$ ").strip()
        if not cmd:
            continue
        parts = cmd.split()
        command, args = parts[0], parts[1:]
        result = shell.execute(command, args)
        out.write(result)
        print(out.flush(), end='')


if __name__ == "__main__":
    main()
