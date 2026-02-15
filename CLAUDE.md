# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CargoBot is a Telegram bot for cargo/package management between China and Tajikistan. It supports two languages (Russian, Tajik) and role-based access: clients, China warehouse admins (`admin_cn`), and Tajikistan warehouse admins (`admin_tj`).

## Commands

```bash
# Run the bot
python bot.py

# Initialize database tables manually
python create_tables.py

# Run with Docker
docker-compose up -d
```

No test suite exists. No linter is configured.

## Architecture

**Framework:** Aiogram 3.x with async/await throughout. FSM (Finite State Machine) drives multi-step conversations.

**Key layers:**

- `bot.py` — Entry point. Creates Bot/Dispatcher, registers all routers, starts polling. Admin handler files in `handlers/` are dynamically discovered and loaded.
- `config.py` — `Settings` class loads from `.env`. Admin IDs use format `telegram_id:role` (comma-separated). Singleton `settings` instance used everywhere.
- `database/session.py` — Async SQLAlchemy engine and session factory. `Base` for ORM models is defined here (not in models.py). Tables auto-created on bot startup via `create_tables()`.
- `database/models.py` — Two models: `User` and `Product`. Imports `Base` from `session.py`. Enums: `UserRole`, `ProductStatus`, `DoorDeliveryStatus`, `ProductCategory`.
- `database/repository.py` — Repository pattern for data access (`UserRepository`, `ProductRepository`).
- `handlers/` — Router-based handlers split by role and feature. Each module exposes a router variable (e.g., `common_router`, `track_codes_router`).
- `handlers/common.py` — `/start` command and language selection.
- `handlers/client/` — Client features: track codes, profile, address, calculator, door delivery, etc.
- `handlers/admin/` — Structured admin handlers (main menu, update status, reports, profile).
- `handlers/admin_china.py`, `admin_tajikistan.py`, `admin_export.py` — Legacy admin handlers loaded dynamically.
- `keyboards/` — Telegram keyboard builders, language-aware. Separate modules for client, admin, calculator, products.
- `services/` — Business logic: delivery cost calculator, Excel export (openpyxl), track code generation.
- `utils/states.py` — All FSM state groups: `AdminStates`, `ClientState`, `AdminChinaState`, `AdminTajikistanState`, `AdminState`, `TrackCodeStates`, `LanguageState`.
- `locales/ru.json`, `locales/tj.json` — Translation dictionaries for bilingual UI.

**Product lifecycle statuses:** CREATED → CHINA_WAREHOUSE → IN_TRANSIT → TAJIKISTAN_WAREHOUSE → DELIVERED → COMPLETED

## Conventions

- All user-facing strings go through locale JSON files (`locales/ru.json`, `locales/tj.json`), keyed by user's `language` field.
- Handler modules export a single `Router` instance. Router registration happens in `bot.py`.
- Database sessions are obtained via `async_session_maker()` from `database/session.py`. All DB operations are async.
- Admin access is controlled by `ADMIN_IDS` env var and checked via `settings.is_admin()` / `settings.get_admin_role()`.
- Comments and variable names in code are a mix of Russian and English.

## Environment Variables

Configured in `.env` (gitignored):

- `BOT_TOKEN` — Telegram bot API token
- `DB_URL` — SQLAlchemy connection string (default: `sqlite+aiosqlite:///database.db`)
- `ADMIN_IDS` — Comma-separated `telegram_id:role` pairs (e.g., `123456:admin_cn,789012:admin_tj`)
- `LOG_LEVEL` — Logging level (default: `INFO`)

## Database

SQLite for development (`database.db`), MySQL 8.0 available via Docker Compose. SQLAlchemy 2.0 async ORM with `aiosqlite` driver. No Alembic migrations are set up yet — schema changes require manual table recreation or migration scripts.
