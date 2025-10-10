import sys
import os
import argparse

class ShellEmulator:
    def __init__(self, vfs_path, script_path=None):
        # извлекаем имя vfs из пути (без завершающих слэшей)
        self.vfs_name = os.path.basename(vfs_path.rstrip("/\\"))
        # сохраняем исходный путь к виртуальной файловой системе
        self.vfs_path = vfs_path
        # путь к стартовому скрипту (может быть none)
        self.script_path = script_path
        # флаг работы эмулятора
        self.running = True
        # текущая директория (всегда корень, так как логика cd не реализована)
        self.current_dir = "/"
        # флаг: сейчас выполняется скрипт или интерактивный ввод
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

    def execute_command(self, command, args):
        # словарь поддерживаемых команд
        command_methods = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit,
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