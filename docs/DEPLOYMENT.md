# Развёртывание функционала массовой загрузки

## Необходимые зависимости

Все зависимости уже установлены в проекте:

```
openpyxl>=3.1.0  # Работа с Excel файлами
```

## Структура новых файлов

```
cargobot/
├── services/
│   ├── bulk_import.py          # Сервис массовой загрузки
│   └── excel_template.py       # Генератор шаблонов
├── handlers/admin/
│   └── bulk_import.py          # Обработчики Telegram
├── docs/
│   ├── BULK_IMPORT.md          # Техническая документация
│   ├── ADMIN_GUIDE_RU.md       # Руководство администратора
│   └── DEPLOYMENT.md           # Эта инструкция
├── temp/                       # Временные файлы (создаётся автоматически)
├── templates/                  # Шаблоны Excel (создаётся автоматически)
└── reports/                    # Отчёты (уже существует)
```

## Шаги развёртывания

### 1. Создание директорий

```bash
cd /c/Users/Manu_1411/PycharmProjects/cargobot

# Создать необходимые директории
mkdir -p temp templates reports docs
```

### 2. Генерация шаблонов Excel

```bash
# Генерация шаблонов для скачивания администраторами
python3 -c "from services.excel_template import generate_import_template; \
    generate_import_template('ru'); \
    generate_import_template('tj')"
```

Это создаст файлы:
- `templates/import_template_ru.xlsx`
- `templates/import_template_tj.xlsx`

### 3. Обновление .gitignore

Убедитесь, что временные файлы не попадают в git:

```bash
# Добавить в .gitignore если ещё нет
echo "temp/" >> .gitignore
echo "templates/*.xlsx" >> .gitignore
```

### 4. Проверка регистрации роутера

Убедитесь, что роутер зарегистрирован в `bot.py`:

```python
from handlers.admin.bulk_import import bulk_import_router

# В функции main():
dp.include_router(bulk_import_router)
```

### 5. Проверка прав доступа

```bash
# Убедитесь, что бот может писать в директории
chmod 755 temp templates reports
```

### 6. Запуск бота

```bash
python bot.py
```

## Проверка работоспособности

### Тест 1: Ручной ввод трек-кода

1. Откройте бота
2. Перейдите в админ-панель
3. **📥 Массовая загрузка** → **✍️ Ручной ввод**
4. Введите: `TEST12345`
5. Проверьте, что товар создан в БД

### Тест 2: Список трек-кодов

1. **📥 Массовая загрузка** → **📝 Список трек-кодов**
2. Введите:
   ```
   TEST001, TEST002, TEST003
   ```
3. Проверьте отчёт

### Тест 3: Excel файл

1. **📥 Массовая загрузка** → **📥 Скачать шаблон**
2. Откройте файл, заполните несколько строк
3. **📄 Excel файл** → Отправьте файл
4. Проверьте отчёт

### Тест 4: Уведомления

1. От имени клиента добавьте pending трек-код
2. От имени админа загрузите этот трек-код
3. Проверьте, что клиент получил уведомление

## Мониторинг

### Логи

Проверьте логи на наличие ошибок:

```bash
# Поиск ошибок импорта
grep "bulk_import" bot.log | grep "ERROR"

# Успешные импорты
grep "Успешно импортирован" bot.log

# Уведомления пользователей
grep "Уведомлено пользователей" bot.log
```

### Мониторинг директорий

```bash
# Проверка временных файлов
ls -lh temp/

# Проверка шаблонов
ls -lh templates/

# Размер директории temp (должна периодически очищаться)
du -sh temp/
```

### Очистка временных файлов

Создайте cron job для автоматической очистки:

```bash
# Удалять файлы старше 24 часов
0 0 * * * find /path/to/cargobot/temp -type f -mtime +1 -delete
```

## Обновление

При обновлении функционала:

1. Остановите бота
2. Обновите код
3. Пересоздайте шаблоны (если изменилась структура)
4. Запустите бота
5. Проверьте работу через тесты

## Откат изменений

Если возникли проблемы:

```bash
# 1. Остановить бота
pkill -f bot.py

# 2. Откатить изменения в git
git revert <commit_hash>

# 3. Удалить новые файлы (опционально)
rm -rf temp templates
rm services/bulk_import.py
rm services/excel_template.py
rm handlers/admin/bulk_import.py

# 4. Запустить бота
python bot.py
```

## Масштабирование

### Для большого количества трек-кодов

1. **Увеличьте timeout для async операций**
2. **Добавьте пагинацию в отчётах** (уже реализовано — показываются первые 10)
3. **Используйте bulk_insert** для больших объёмов:

```python
# В BulkImportService добавить:
async def bulk_create_products(self, products_data: List[dict]):
    """Массовое создание товаров за одну транзакцию"""
    products = [Product(**data) for data in products_data]
    self.product_repo.session.add_all(products)
    await self.product_repo.session.commit()
```

### Для высоконагруженных систем

1. Добавьте очередь (Celery + Redis)
2. Асинхронная обработка больших файлов
3. Прогресс-бар для длительных операций

## Безопасность

### Проверка прав доступа

```python
# Всегда проверяйте admin права
if not settings.is_admin(user_id):
    return
```

### Лимиты

Текущие ограничения:
- Размер Excel файла: 10 MB
- Timeout: стандартный async_session

Для изменения лимитов отредактируйте `handlers/admin/bulk_import.py`:

```python
# Изменить максимальный размер файла
if document.file_size > 20 * 1024 * 1024:  # 20 MB
    await message.answer("❌ Файл слишком большой")
```

## Troubleshooting

### Ошибка: "No module named 'openpyxl'"

```bash
pip install openpyxl
```

### Ошибка: "Permission denied: temp/"

```bash
chmod 755 temp
# или
chown your_user:your_group temp
```

### Ошибка: "InvalidFileException"

- Убедитесь, что файл действительно .xlsx
- Попробуйте пересохранить файл в Excel
- Проверьте, не повреждён ли файл

### Шаблон не скачивается

```bash
# Проверьте наличие файла
ls -l templates/import_template_ru.xlsx

# Пересоздайте шаблон
python3 -c "from services.excel_template import generate_import_template; generate_import_template('ru')"
```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f bot.log | grep bulk_import`
2. Проверьте права на директории
3. Убедитесь, что все зависимости установлены
4. Проверьте версию Python (должна быть 3.8+)

## Контрольный список развёртывания

- [ ] Создана директория `temp/`
- [ ] Создана директория `templates/`
- [ ] Создана директория `docs/`
- [ ] Сгенерированы шаблоны Excel
- [ ] Обновлён `.gitignore`
- [ ] Зарегистрирован `bulk_import_router` в `bot.py`
- [ ] Проверены права на директории
- [ ] Выполнены все тесты
- [ ] Настроен мониторинг логов
- [ ] Настроена очистка временных файлов
