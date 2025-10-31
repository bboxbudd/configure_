
# Переменные
PYTHON = C:\Users\1\AppData\Local\Programs\Python\Python313\python.exe
VFS_FILE = vfs_test.csv
MAIN_FILE = output.py
PRAC_FILE = Prac1.py
TEST_BAT = test_vfs_medium.bat

# Цели по умолчанию
.DEFAULT_GOAL := help

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make run       - запустить VFS shell"
	@echo "  make test      - запустить тест через bat файл"
	@echo "  make clean     - очистить временные файлы"
	@echo "  make help      - показать эту справку"

# Запуск VFS shell
run:
	$(PYTHON) $(MAIN_FILE) $(VFS_FILE)

# Запуск теста через bat файл
test:
	./$(TEST_BAT)

# Очистка
clean:
	@echo "Очистка временных файлов..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@find . -name "*.csv" ! -name "$(VFS_FILE)" -delete

# Проверка файлов
check:
	@echo "Проверка наличия необходимых файлов..."
	@test -f $(MAIN_FILE) || echo "Ошибка: $(MAIN_FILE) не найден"
	@test -f $(PRAC_FILE) || echo "Ошибка: $(PRAC_FILE) не найден"
	@test -f $(VFS_FILE) || echo "Ошибка: $(VFS_FILE) не найден"
	@test -f $(TEST_BAT) || echo "Ошибка: $(TEST_BAT) не найден"
	@echo "Проверка завершена"

.PHONY: help run test clean check