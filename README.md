# My Expenses

> Record your expenses in 5 seconds!

A minimalist Telegram bot for quick expense tracking with a smart LLM-powered parser, category selection, and date navigation — all powered by FastAPI and PostgreSQL.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Features

### Core Functionality
- ⚡ **Record Expenses** — enter amount (or a description + amount like `lunch 300`) and pick a category
- 📋 **Today's Expenses** — view all expenses for today with a running total
- 🗑 **Delete Last Expense** — remove the most recent entry with one click
- 📅 **Date Navigation** — browse expenses by date, jumping only to days that have entries
- 💾 **Persistent Storage** — all data stored in PostgreSQL

### Smart Input
- **Classic Mode** — type a number, then select a category
- **LLM-Powered Mode** — type natural language like `taxi to airport 1200` and the bot parses it, shows a preview, and asks for confirmation

### Categories
- 🍔 **Food** — meals, groceries, snacks
- 🚗 **Transport** — taxi, bus, fuel, parking
- 📦 **Other** — everything else

## Quick Start

### Prerequisites
- Docker & Docker Compose
- A Telegram bot token (get one from [@BotFather](https://t.me/botfather))

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/my-expenses.git
cd my-expenses
```

### 2. Configure Environment
```bash
cp .env.bot.secret .env.bot
```

Edit `.env.bot` and set your bot token:
```env
BOT_TOKEN=your_token_from_botfather
API_BASE_URL=http://localhost:8000
API_KEY=my-expenses-secret-key
```

(Optional) Configure LLM integration for smart parsing:
```env
LLM_API_BASE_URL=http://localhost:8080
LLM_API_KEY=your_llm_key
LLM_MODEL=coder-model
```

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```

This starts three services:
| Service | Description | Port |
|---|---|---|
| **postgres** | PostgreSQL 16 (Alpine) | 5432 |
| **api** | FastAPI backend | 8000 |
| **bot** | Telegram bot | — |

### 4. Open the Bot
Start a chat with your bot in Telegram and send `/start`.

## Development Setup

### Install Dependencies
```bash
uv pip install -e ".[dev]"
```

### Run API Server
```bash
poe dev-api
# or: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Bot
```bash
poe dev-bot
# or: python -m bot.main
```

> Make sure PostgreSQL is running before starting the API server. For local dev you can run `docker compose up -d postgres`.

### Available Poe Tasks
```bash
poe dev-api        # Start FastAPI with hot reload
poe dev-bot        # Start the Telegram bot
poe check          # Run linter + type checker
poe format         # Format code with Ruff
poe lint           # Lint with Ruff
poe typecheck      # Type check with Pyright
```

## Usage Guide

### Commands
| Command | Description |
|---|---|
| `/start` | Welcome message with main menu |
| `/help` | List all available commands |
| `/record` | Start recording a new expense |
| `/today` | View all expenses for today |
| `/deletelast` | Delete the most recent expense |

### Recording an Expense

**Classic flow:**
1. Send `/record` or tap "📝 Record Expense"
2. Enter the amount (e.g., `300`)
3. Tap a category button (Food / Transport / Other)
4. Done — confirmation is shown

**Smart flow (LLM-powered):**
1. Send `/record` or tap "📝 Record Expense"
2. Type a description with amount (e.g., `lunch at cafe 500`)
3. Bot parses and shows a preview with detected category and amount
4. Confirm or cancel

### Viewing Expenses
- `/today` — shows all expenses for today (Moscow time, UTC+3) with total
- Inline "📋 Today's Expenses" button — same as `/today`
- Date picker — browse by date, skipping days with no entries using `←` / `→` buttons

### Deleting an Expense
- `/deletelast` or tap "🗑 Delete Last" — removes the most recent expense and shows what was deleted

## Architecture

```
User <--(Telegram)--> [Bot (aiogram 3.x)]
                           |
                    HTTP (httpx)
                    Authorization: Bearer <API_KEY>
                           |
                           v
                    [API (FastAPI)] <--(asyncpg)--> [PostgreSQL]
```

### Services

| Service | Tech | Role |
|---|---|---|
| **Telegram Bot** | aiogram 3.x | User interface, FSM-based conversation flows |
| **FastAPI API** | FastAPI + SQLModel | REST API for all CRUD operations |
| **PostgreSQL** | PostgreSQL 16 | Persistent data storage |

### Project Structure
```
my-expenses/
├── bot/                          # Telegram Bot (aiogram)
│   ├── main.py                   # Entry point, dispatcher setup
│   ├── config.py                 # BotSettings (token, API, LLM config)
│   ├── Dockerfile
│   ├── handlers/
│   │   ├── commands.py           # /start, /help, /record, /today, /deletelast
│   │   ├── expense.py            # FSM expense recording flow + callbacks
│   │   └── keyboards.py          # Inline keyboard builders
│   └── services/
│       ├── expenses_api.py       # HTTP client to FastAPI backend
│       └── llm_parser.py         # Keyword + LLM expense parser
│
├── api/                          # FastAPI Backend
│   ├── main.py                   # FastAPI app, CORS, health check
│   ├── config.py                 # Pydantic Settings (DB, API key)
│   ├── database.py               # Async SQLAlchemy engine + sessions
│   ├── auth.py                   # HTTP Bearer API key verification
│   ├── Dockerfile
│   ├── models/
│   │   └── expense.py            # SQLModel ORM models + DTOs
│   ├── routers/
│   │   └── expenses.py           # API endpoint definitions
│   └── db/
│       └── expenses.py           # CRUD operations (async queries)
│
├── database/
│   └── init.sql                  # PostgreSQL schema (table + indexes)
│
├── docker-compose.yml            # Service orchestration
├── pyproject.toml                # Dependencies + tool config
└── README.md                     # This file
```

## API Reference

All endpoints are prefixed with `/api` and require Bearer token authentication:
```
Authorization: Bearer <API_KEY>
```

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/expenses/` | Create a new expense |
| `GET` | `/api/expenses/last/{telegram_user_id}` | Get last expense |
| `DELETE` | `/api/expenses/last/{telegram_user_id}` | Delete last expense |
| `GET` | `/api/expenses/today/{telegram_user_id}` | Get today's expenses |
| `GET` | `/api/expenses/total-today/{telegram_user_id}` | Get today's total |
| `GET` | `/api/expenses/date/{telegram_user_id}/{target_date}` | Get expenses by date |
| `GET` | `/api/expenses/dates/{telegram_user_id}` | Get all dates with expenses |
| `GET` | `/api/expenses/prev-date/{telegram_user_id}/{current_date}` | Get previous date |
| `GET` | `/api/expenses/next-date/{telegram_user_id}/{current_date}` | Get next date |
| `GET` | `/health` | Health check (no auth required) |

### Request Body (POST /api/expenses/)
```json
{
  "telegram_user_id": 123456789,
  "amount": 150.50,
  "category": "food",
  "description": "Lunch at cafe"
}
```

## Database Schema

```sql
CREATE TABLE expense (
    id                SERIAL PRIMARY KEY,
    telegram_user_id  BIGINT       NOT NULL,
    amount            NUMERIC(10,2) NOT NULL,
    category          VARCHAR(50)   NOT NULL,
    description       TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_expense_user_id     ON expense(telegram_user_id);
CREATE INDEX idx_expense_created_at ON expense(created_at);
```

All timestamps are stored in UTC. Day-level queries use Moscow time (UTC+3).

## Environment Variables

### Bot (`.env.bot`)
| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | **Yes** | — | Telegram bot token from BotFather |
| `API_BASE_URL` | No | `http://localhost:8000` | FastAPI backend URL |
| `API_KEY` | No | `my-expenses-secret-key` | Shared secret for API auth |
| `LLM_API_BASE_URL` | No | `http://localhost:8080` | LLM API base URL |
| `LLM_API_KEY` | No | `""` | LLM API key |
| `LLM_MODEL` | No | `coder-model` | LLM model name |

### API
| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_HOST` | No | `localhost` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |
| `DB_NAME` | No | `my_expenses` | Database name |
| `DB_USER` | No | `postgres` | Database user |
| `DB_PASSWORD` | No | `postgres` | Database password |
| `API_KEY` | No | `my-expenses-secret-key` | Must match bot's API_KEY |
| `DEBUG` | No | `false` | Enable SQL echo logging |

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Bot Framework | aiogram 3.x |
| Web Framework | FastAPI |
| ORM | SQLModel (SQLAlchemy 2.0 + Pydantic) |
| Database | PostgreSQL 16 |
| DB Driver | asyncpg |
| HTTP Client | httpx |
| ASGI Server | Uvicorn |
| Config | pydantic-settings |
| Package Manager | uv |
| Linting | Ruff |
| Type Checking | Pyright |
| Testing | pytest + pytest-asyncio |
| Containerization | Docker + Docker Compose |

## License

MIT
