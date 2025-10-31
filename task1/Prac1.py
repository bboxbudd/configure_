import os
import csv
import base64
import sys


class VFS:
    """Виртуальная файловая система, не производящая вывода"""
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.fs = {}
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
                if not path.startswith('/'):
                    path = '/' + path
                path = path.replace('\\', '/').rstrip('/')
                while '//' in path:
                    path = path.replace('//', '/')
                self.fs[path] = {
                    'type': type_,
                    'content': content if type_ == 'file' else None
                }
                # создаём родительские директории
                if path != '/':
                    parts = path.split('/')[1:]
                    for i in range(1, len(parts)):
                        parent = '/' + '/'.join(parts[:i])
                        if parent not in self.fs:
                            self.fs[parent] = {'type': 'dir', 'content': None}

    def save_to_csv(self, output_path):
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['path', 'type', 'content'])
            for path in sorted(self.fs.keys()):
                if path == '/':
                    continue
                meta = self.fs[path]
                content = meta['content'] if meta['type'] == 'file' else ''
                writer.writerow([path, meta['type'], content])

    def get(self, path):
        if not path.startswith('/'):
            path = '/' + path
        path = path.replace('\\', '/').rstrip('/')
        while '//' in path:
            path = path.replace('//', '/')
        if path == '':
            path = '/'
        return self.fs.get(path)

    def list_dir(self, path):
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
    """Эмулятор shell, не использующий print(), возвращает вывод строками"""
    def __init__(self, vfs):
        self.vfs = vfs
        self.current_dir = "/"
        self.running = True

    def _normalize_path(self, path):
        if path.startswith('/'):
            parts = path.split('/')
        else:
            current_parts = self.current_dir.split('/')
            input_parts = path.split('/')
            parts = current_parts + input_parts
        result = []
        for part in parts:
            if part == '' or part == '.':
                continue
            elif part == '..':
                if result:
                    result.pop()
            else:
                result.append(part)
        return '/' + '/'.join(result)

    def execute(self, command, args):
        """Основной диспетчер команд — возвращает текст"""
        commands = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'cat': self.cmd_cat,
            'uniq': self.cmd_uniq,
            'cp': self.cmd_cp,
            'exit': self.cmd_exit,
            'vfs-save': self.cmd_vfs_save,
        }
        if command in commands:
            return commands[command](args)
        return f"Команда '{command}' не найдена\n"

    # --- Команды ---
    def cmd_ls(self, args):
        path = args[0] if args else self.current_dir
        path = self._normalize_path(path)
        if not self.vfs.get(path):
            return f"ls: нет такого файла или директории: {path}\n"
        if self.vfs.is_file(path):
            return os.path.basename(path) + "\n"
        items = self.vfs.list_dir(path)
        return "  ".join(sorted(items)) + "\n"

    def cmd_cd(self, args):
        if not args:
            return "cd: отсутствует аргумент\n"
        new_path = self._normalize_path(args[0])
        if not self.vfs.get(new_path):
            return f"cd: нет такого файла или директории: {args[0]}\n"
        if not self.vfs.is_dir(new_path):
            return f"cd: не является директорией: {args[0]}\n"
        self.current_dir = new_path
        return ""

    def cmd_cat(self, args):
        if not args:
            return "cat: отсутствует аргумент\n"
        path = self._normalize_path(args[0])
        if not self.vfs.is_file(path):
            if not self.vfs.get(path):
                return f"cat: нет такого файла: {args[0]}\n"
            return f"cat: это директория: {args[0]}\n"
        content_b64 = self.vfs.fs[path]['content']
        if not content_b64:
            return ""
        try:
            content_bytes = base64.b64decode(content_b64)
            return content_bytes.decode('utf-8')
        except Exception as e:
            return f"cat: ошибка чтения файла {args[0]}: {e}\n"

    def cmd_uniq(self, args):
        if not args:
            return "uniq: отсутствует аргумент\n"
        path = self._normalize_path(args[0])
        if not self.vfs.is_file(path):
            if not self.vfs.get(path):
                return f"uniq: нет такого файла: {args[0]}\n"
            return f"uniq: это директория: {args[0]}\n"
        content_b64 = self.vfs.fs[path]['content']
        if not content_b64:
            return ""
        try:
            content_bytes = base64.b64decode(content_b64)
            lines = content_bytes.decode('utf-8').splitlines(keepends=True)
            prev = None
            output = []
            for line in lines:
                if line != prev:
                    output.append(line)
                    prev = line
            return "".join(output)
        except Exception as e:
            return f"uniq: ошибка чтения файла {args[0]}: {e}\n"

    def cmd_cp(self, args):
        if len(args) < 2:
            return "cp: требуется два аргумента\n"
        src = self._normalize_path(args[0])
        dst = self._normalize_path(args[1])
        if not self.vfs.is_file(src):
            if not self.vfs.get(src):
                return f"cp: нет такого файла: {args[0]}\n"
            return f"cp: '{args[0]}' — это директория\n"
        content_b64 = self.vfs.fs[src]['content']
        if self.vfs.is_dir(dst):
            filename = os.path.basename(src)
            dst = dst.rstrip('/') + '/' + filename
        parent_dir = os.path.dirname(dst) or '/'
        if not self.vfs.is_dir(parent_dir):
            return f"cp: каталог назначения не существует: {parent_dir}\n"
        self.vfs.fs[dst] = {'type': 'file', 'content': content_b64}
        return f"файл '{src}' скопирован в '{dst}'\n"

    def cmd_vfs_save(self, args):
        if not args:
            return "vfs-save: укажите путь для сохранения\n"
        try:
            self.vfs.save_to_csv(args[0])
            return f"vfs сохранён в '{args[0]}'\n"
        except Exception as e:
            return f"ошибка сохранения vfs: {e}\n"

    def cmd_exit(self, args):
        self.running = False
        return "Выход из эмулятора.\n"
