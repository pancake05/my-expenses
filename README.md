# My Expenses - Telegram Bot

Минималистичный Telegram-бот для быстрого учёта расходов. Запишите расход за 5 секунд!

## Возможности

### Основные:
- ⚡ **Запись расхода** — введите сумму + выберите категорию (Еда, Транспорт, Другое)
- 📋 **Последний расход** — показывается сразу после записи
- 🗑 **Удаление последнего расхода** — одним нажатием
- 💾 **Облачное хранение** — данные в PostgreSQL, не пропадут

### Дополнительные:
- 📊 **Список расходов за день** — все расходы за сегодня
- 📈 **Общая сумма за день** — автоматический подсчёт

## Категории
- 🍔 Еда
- 🚗 Транспорт
- 📦 Другое

## Установка и запуск

### 1. Получите токен бота
1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен

### 2. Настройте окружение

```bash
cd my-expenses
cp .env.bot.secret .env.bot
```

Отредактируйте `.env.bot` и вставьте ваш токен:
```
BOT_TOKEN=ваш_токен_от_botfather
API_BASE_URL=http://localhost:8000
API_KEY=my-expenses-secret-key
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL (база данных)
- FastAPI API (бэкенд)
- Telegram Bot (бот)

### 4. Запуск для разработки

**Бэкенд:**
```bash
uv pip install -e ".[dev]"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Бот:**
```bash
uv pip install -e ".[dev]"
python -m bot.main
```

## Использование

1. Откройте вашего бота в Telegram
2. Отправьте `/start`
3. Для записи расхода:
   - Нажмите "📝 Record Expense" или отправьте `/record`
   - Введите сумму (например: `150.50`)
   - Выберите категорию кнопкой
4. Для просмотра расходов за сегодня:
   - Нажмите "📋 Today's Expenses" или отправьте `/today`
5. Для удаления последнего расхода:
   - Нажмите "🗑 Delete Last" или отправьте `/deletelast`

## Архитектура

Проект использует паттерны из лабораторных работ se-toolkit-lab-7 и se-toolkit-lab-8:

- **Telegram Bot** (aiogram 3.x) — интерфейс пользователя
- **FastAPI Backend** — REST API для CRUD операций
- **PostgreSQL** — надёжное облачное хранение
- **SQLModel ORM** — работа с базой данных
- **Docker Compose** — контейнеризация и деплой

### Структура проекта

```
my-expenses/
├── bot/                    # Telegram бот
│   ├── main.py            # Точка входа
│   ├── config.py          # Настройки
│   ├── handlers/          # Обработчики команд и действий
│   │   ├── commands.py    # /start, /help, /record, /today, /deletelast
│   │   ├── expense.py     # Логика записи расхода
│   │   └── keyboards.py   # Inline клавиатуры
│   └── services/          # Сервисы
│       └── expenses_api.py # HTTP клиент к API
├── api/                    # FastAPI бэкенд
│   ├── main.py            # Точка входа
│   ├── config.py          # Настройки
│   ├── database.py        # Подключение к БД
│   ├── auth.py            # Аутентификация
│   ├── models/            # SQLModel модели
│   ├── db/                # CRUD операции
│   └── routers/           # API эндпоинты
├── database/
│   └── init.sql           # Инициализация БД
├── docker-compose.yml     # Оркестрация
└── pyproject.toml         # Зависимости
```

## Технологии

- **Python 3.10+**
- **aiogram 3.x** — Telegram Bot Framework
- **FastAPI** — веб-фреймворк
- **SQLModel** — ORM (SQLAlchemy + Pydantic)
- **asyncpg** — асинхронный драйвер PostgreSQL
- **Docker & Docker Compose** — контейнеризация

## Лицензия

MIT
