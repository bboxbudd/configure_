import sys
import os
import argparse
import csv
import base64

class VFS:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.fs = {}  # путь -> {'type': 'file'/'dir', 'content': base64 или none}
        self._load_from_csv()

    def _load_from_csv(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"vfs не найден: {self.csv_path}")
        
        self.fs["/"] = {"type": "dir", "content": None}

        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row['path']
                type_ = row['type']
                content = row.get('content', '')

                # нормализуем путь: только прямые слэши, без дублей
                if not path.startswith('/'):
                    path = '/' + path
                path = path.replace('\\', '/').rstrip('/')
                while '//' in path:
                    path = path.replace('//', '/')

                # сохраняем файл или папку
                self.fs[path] = {
                    'type': type_,
                    'content': content if type_ == 'file' else None
                }

                # создаём все родительские директории
                if path != '/':
                    parts = path.split('/')[1:]  # убираем первый пустой элемент
                    for i in range(1, len(parts)):
                        parent_path = '/' + '/'.join(parts[:i])
                        if parent_path not in self.fs:
                            self.fs[parent_path] = {'type': 'dir', 'content': None}

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
        # нормализуем путь вручную
        if not path.startswith('/'):
            path = '/' + path
        path = path.replace('\\', '/').rstrip('/')
        while '//' in path:
            path = path.replace('//', '/')
        if path == '':
            path = '/'
        return self.fs.get(path)

    def list_dir(self, path):
        """возвращает список элементов в директории"""
        if not path.startswith('/'):
            path = '/' + path
        path = path.replace('\\', '/').rstrip('/')
        if path != '/':
            path += '/'
        
        items = []
        for p in self.fs:
            if p.startswith(path):
                rel = p[len(path):]
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

    def _normalize_path(self, path):
        """нормализует путь с использованием только '/' (unix-style)"""
        if path.startswith('/'):
            # абсолютный путь
            parts = path.split('/')
        else:
            # относительный путь
            current_parts = self.current_dir.split('/')
            input_parts = path.split('/')
            parts = current_parts + input_parts

        # обрабатываем '.' и '..'
        result = []
        for part in parts:
            if part == '' or part == '.':
                continue
            elif part == '..':
                if result:
                    result.pop()
            else:
                result.append(part)
        
        normalized = '/' + '/'.join(result)
        return normalized if normalized != '' else '/'

    def cmd_cd(self, args):
        if not args:
            print("cd: отсутствует аргумент")
            return

        target = args[0]
        new_path = self._normalize_path(target)

        # проверяем, существует ли путь
        if not self.vfs.get(new_path):
            print(f"cd: нет такого файла или директории: {target}")
            return

        if not self.vfs.is_dir(new_path):
            print(f"cd: не является директорией: {target}")
            return

        self.current_dir = new_path

    def cmd_ls(self, args):
        if args:
            # поддержка ls с аргументом (путь)
            target = args[0]
            path_to_list = self._normalize_path(target)
        else:
            # без аргумента — текущая директория
            path_to_list = self.current_dir

        if not self.vfs.get(path_to_list):
            print(f"ls: нет такого файла или директории: {args[0] if args else '.'}")
            return

        if self.vfs.is_file(path_to_list):
            # если указали файл — просто выводим его имя
            print(os.path.basename(path_to_list))
            return

        # иначе — директория
        items = self.vfs.list_dir(path_to_list)
        if items:
            print("  ".join(sorted(items)))
        # если пусто — ничего не выводим (как в настоящем ls)

    def cmd_cat(self, args):
        if not args:
            print("cat: отсутствует аргумент")
            return

        target = args[0]
        file_path = self._normalize_path(target)

        if not self.vfs.is_file(file_path):
            if not self.vfs.get(file_path):
                print(f"cat: нет такого файла: {target}")
            else:
                print(f"cat: это директория: {target}")
            return

        # получаем base64-содержимое
        content_b64 = self.vfs.fs[file_path]['content']
        if not content_b64:
            return  # пустой файл

        try:
            # декодируем из base64 в байты, затем в строку utf-8
            content_bytes = base64.b64decode(content_b64)
            content_str = content_bytes.decode('utf-8')
            print(content_str, end='')  # end='', чтобы не добавлять лишний \n
        except Exception as e:
            print(f"cat: ошибка чтения файла {target}: {e}")

    def cmd_uniq(self, args):
        if not args:
            print("uniq: отсутствует аргумент")
            return

        target = args[0]
        file_path = self._normalize_path(target)

        if not self.vfs.is_file(file_path):
            if not self.vfs.get(file_path):
                print(f"uniq: нет такого файла: {target}")
            else:
                print(f"uniq: это директория: {target}")
            return

        content_b64 = self.vfs.fs[file_path]['content']
        if not content_b64:
            return

        try:
            content_bytes = base64.b64decode(content_b64)
            lines = content_bytes.decode('utf-8').splitlines(keepends=True)
        except Exception as e:
            print(f"uniq: ошибка чтения файла {target}: {e}")
            return

        # выводим только уникальные последовательные строки (как в unix uniq)
        prev = None
        for line in lines:
            if line != prev:
                print(line, end='')
                prev = line

    def cmd_cp(self, args):
        if len(args) < 2:
            print("cp: требуется два аргумента (источник и назначение)")
            return

        src = self._normalize_path(args[0])
        dst = self._normalize_path(args[1])

        # Проверяем, что источник существует
        if not self.vfs.is_file(src):
            if not self.vfs.get(src):
                print(f"cp: нет такого файла: {args[0]}")
            else:
                print(f"cp: '{args[0]}' — это директория")
            return

        # Получаем содержимое файла
        content_b64 = self.vfs.fs[src]['content']

        # Если dst — существующая директория, копируем внутрь неё
        if self.vfs.is_dir(dst):
            filename = os.path.basename(src)
            dst = dst.rstrip('/') + '/' + filename

        # Проверяем, не является ли путь некорректным
        parent_dir = os.path.dirname(dst)
        if parent_dir == '':
            parent_dir = '/'
        if not self.vfs.is_dir(parent_dir):
            print(f"cp: каталог назначения не существует: {parent_dir}")
            return

        # Копируем (создаём или перезаписываем)
        self.vfs.fs[dst] = {
            'type': 'file',
            'content': content_b64
        }

        print(f"файл '{src}' скопирован в '{dst}'")

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
            'cat': self.cmd_cat,
            'uniq': self.cmd_uniq,
            'exit': self.cmd_exit,
            'vfs-save': self.cmd_vfs_save,
            'cp': self.cmd_cp,
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