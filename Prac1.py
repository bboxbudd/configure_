import sys
import os
import argparse
import csv
import base64
import json
from collections import defaultdict

class VFS:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.fs = {}  # путь -> {'type': 'file'/'dir', 'content': base64 или none}
        self._load_from_csv()

    def _load_from_csv(self):
        """загружает vfs из csv-файла в память"""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"vfs не найден: {self.csv_path}")
        
        # корень всегда существует
        self.fs["/"] = {"type": "dir", "content": None}

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row['path']
                type_ = row['type']
                content = row.get('content', '')

                # нормализуем путь: всегда начинается с /
                if not path.startswith('/'):
                    path = '/' + path
                path = os.path.normpath(path)

                self.fs[path] = {
                    'type': type_,
                    'content': content if type_ == 'file' else None
                }

                # автоматически создаём родительские директории
                parent = os.path.dirname(path)
                while parent != '/' and parent not in self.fs:
                    self.fs[parent] = {'type': 'dir', 'content': None}
                    parent = os.path.dirname(parent)

    def save_to_csv(self, output_path):
        """сохраняет текущее состояние vfs в csv"""
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['path', 'type', 'content'])
            for path in sorted(self.fs.keys()):
                if path == '/':
                    continue  # корень не сохраняем
                meta = self.fs[path]
                content = meta['content'] if meta['type'] == 'file' else ''
                writer.writerow([path, meta['type'], content])

    def get(self, path):
        """возвращает метаданные по пути или none"""
        norm_path = os.path.normpath(path)
        return self.fs.get(norm_path)

    def list_dir(self, path):
        """возвращает список элементов в директории (для будущего ls)"""
        norm_path = os.path.normpath(path)
        if norm_path != '/' and not norm_path.endswith('/'):
            norm_path += '/'
        items = []
        for p in self.fs:
            if p.startswith(norm_path):
                rel = p[len(norm_path):]
                if '/' not in rel and rel:
                    items.append(rel)
        return items

    def is_dir(self, path):
        meta = self.get(path)
        return meta and meta['type'] == 'dir'

    def is_file(self, path):
        meta = self.get(path)
        return meta and meta['type'] == 'file'
    
class ShellEmulator:
    def __init__(self, vfs_path, script_path=None):
        self.vfs = VFS(vfs_path)  # создаём vfs из csv
        self.vfs_name = os.path.basename(vfs_path.rstrip("/\\"))
        self.script_path = script_path
        self.running = True
        self.current_dir = "/"
        self.stdin_from_script = False

    def print_prompt(self):
        # выводим приглашение только в интерактивном режиме
        if not self.stdin_from_script:
            print(f"{self.vfs_name}:{self.current_dir}$ ", end="", flush=True)

    def parse_input(self, user_input):
        # разбиваем ввод на части по пробелам, убирая лишние пробелы
        parts = user_input.strip().split()
        # если ввод пустой — возвращаем none и пустой список
        if not parts:
            return None, []
        # первое слово — команда, остальное — аргументы
        command = parts[0]
        args = parts[1:]
        return command, args

    def cmd_ls(self, args):
        # заглушка для команды ls: выводим фиксированный список файлов
        print("файл1.txt  папка1  README.md")

    def cmd_cd(self, args):
        # заглушка для cd: не меняем директорию, просто выводим сообщение
        if args:
            print(f"cd: переход в '{args[0]}' (не реализовано)")
        else:
            print("cd: отсутствует аргумент")

    def cmd_exit(self, args):
        # при выходе из скрипта не выводим сообщение, иначе — выводим
        if not self.stdin_from_script:
            print("завершение работы")
        # устанавливаем флаг остановки
        self.running = False

    def cmd_vfs_save(self, args):
        if not args:
            print("vfs-save: укажите путь для сохранения")
            return
        output_path = args[0]
        try:
            self.vfs.save_to_csv(output_path)
            print(f"vfs сохранён в '{output_path}'")
        except Exception as e:
            print(f"ошибка сохранения vfs: {e}")

    def execute_command(self, command, args):
        # словарь поддерживаемых команд
        command_methods = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit,
            'vfs-save': self.cmd_vfs_save,  
        }

        # если команда известна — вызываем соответствующий метод
        if command in command_methods:
            command_methods[command](args)
        else:
            # иначе — ошибка
            print(f"команда '{command}' не найдена")

    def run_script(self):
        # если скрипт не задан — ничего не делаем
        if not self.script_path:
            return False

        # проверяем, существует ли файл скрипта
        if not os.path.isfile(self.script_path):
            print(f"ошибка: скрипт '{self.script_path}' не найден.", file=sys.stderr)
            return False

        # включаем режим выполнения скрипта
        self.stdin_from_script = True
        # отладочный вывод пути к скрипту
        print(f"[debug] выполнение скрипта: {self.script_path}\n")

        # читаем скрипт построчно
        with open(self.script_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                # пропускаем пустые строки и комментарии (начинаются с #)
                if not stripped or stripped.startswith('#'):
                    continue

                # имитируем ввод пользователя: выводим команду как в терминале
                print(f"{self.vfs_name}:{self.current_dir}$ {stripped}", flush=True)

                # парсим команду
                command, args = self.parse_input(stripped)
                if command is None:
                    continue

                # выполняем команду
                self.execute_command(command, args)
                # если была команда exit — выходим из цикла
                if not self.running:
                    break
                # добавляем пустую строку для читаемости (как в тз)
                print()

        # выключаем режим скрипта
        self.stdin_from_script = False
        return True

    def run_interactive(self):
        # основной цикл интерактивного режима
        while self.running:
            self.print_prompt()
            try:
                user_input = input()
            except (EOFError, KeyboardInterrupt):
                # обработка ctrl+d или ctrl+c
                print("\nзавершение работы")
                break

            # пропускаем пустой ввод
            if not user_input.strip():
                continue

            # парсим ввод
            command, args = self.parse_input(user_input)
            if command is None:
                continue

            # выполняем команду
            self.execute_command(command, args)
            # добавляем пустую строку после вывода
            print()

    def run(self):
        # если задан скрипт — запускаем его, иначе — интерактивный режим
        if self.script_path:
            self.run_script()
        else:
            self.run_interactive()


def main():
    # настраиваем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="эмулятор shell с виртуальной фс")
    parser.add_argument("--vfs", required=True, help="путь к виртуальной файловой системе")
    parser.add_argument("--script", help="путь к стартовому скрипту")

    # получаем аргументы
    args = parser.parse_args()

    # отладочный вывод параметров запуска
    print("[debug] запуск эмулятора с параметрами:")
    print(f"  --vfs    = {os.path.abspath(args.vfs)}")
    if args.script:
        print(f"  --script = {os.path.abspath(args.script)}")
    else:
        print("  --script = (не задан)")

    # проверяем существование vfs
    if not os.path.exists(args.vfs):
        print(f"ошибка: vfs по пути '{args.vfs}' не существует.", file=sys.stderr)
        sys.exit(1)

    # создаём и запускаем эмулятор
    shell = ShellEmulator(vfs_path=args.vfs, script_path=args.script)
    shell.run()


# точка входа в программу
if __name__ == "__main__":
    main()