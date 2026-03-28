# CLAUDE.md — Candle

> Crypto market screener and alert system.
> Backend-first. Data integrity over features. No premature optimization.

---

## Project overview

Candle is a crypto market screener that fetches OHLCV data from multiple exchanges,
computes technical indicators, evaluates configurable screening conditions, and
delivers alerts via Telegram. Designed as a portfolio project with a clear path
toward a deployable product.

**Current phase:** Phase 3 — REST API + frontend dashboard
**Completed:**     Phase 1 (backend core) + Phase 2 (alerts + scheduling + Railway deploy)

---

## Absolute rules — never break these

- **Never place real orders on any exchange.** Read-only API keys only. Paper trading
  until this file explicitly states otherwise.
- **Never commit secrets.** All credentials live in `.env`. Never hardcode them.
  Never log them, even partially.
- **Never skip error handling on exchange calls.** Exchanges fail constantly.
  Every ccxt call must handle NetworkError, ExchangeError, and RateLimitExceeded.
- **Never modify the database schema directly.** Use Alembic migrations exclusively.
  No raw ALTER TABLE, no editing models without a migration.
- **Never change the project structure** without updating this file first.
- **Never use synchronous I/O inside async functions.** Keep the async boundary clean.

---

## Tech stack

### Backend (active)

| Layer              | Technology              | Notes                                   |
|--------------------|-------------------------|-----------------------------------------|
| Language           | Python 3.11+            | Type hints on every function            |
| Exchange connector | ccxt 4.x                | Unified API — Binance, Kraken, Coinbase |
| Indicators         | pandas-ta               | Built on pandas DataFrames              |
| ORM                | SQLAlchemy 2.x (async)  | Async session everywhere                |
| Migrations         | Alembic                 | Only way to touch the schema            |
| Scheduler          | APScheduler             | Drives fetch + screen cycles            |
| Alerts             | python-telegram-bot     | Async client, no blocking calls         |
| Config             | pydantic-settings       | Typed config loaded from .env           |
| Testing            | pytest + pytest-asyncio | Core logic requires tests               |

### Infrastructure

| Layer            | Technology                      |
|------------------|---------------------------------|
| Database         | PostgreSQL 15+                  |
| Local dev        | Docker + docker-compose         |
| Deploy (planned) | Railway — simplest first deploy |

### Frontend (Phase 3 — not started yet)

| Layer      | Technology                     |
|------------|--------------------------------|
| Framework  | Next.js 14 (App Router)        |
| Styling    | Tailwind CSS + shadcn/ui       |
| Charts     | TradingView Lightweight Charts |
| Data fetch | SWR                            |

---

## Project structure

```
candle/
├── CLAUDE.md                    # This file — always read before doing anything
├── README.md
├── .env                         # Never commit
├── .env.example                 # Committed — all keys with placeholder values
├── docker-compose.yml           # PostgreSQL + app for local dev
├── pyproject.toml               # Single source of truth for deps and tooling
├── alembic.ini
│
├── candle/                      # Main Python package
│   ├── __init__.py
│   ├── config.py                # Single Settings instance via pydantic-settings
│   │
│   ├── data/                    # Fetching layer — talks to exchanges
│   │   ├── __init__.py
│   │   ├── fetcher.py           # ccxt wrapper — fetch_ohlcv per exchange/pair
│   │   ├── normalizer.py        # Raw ccxt output → clean DataFrame
│   │   └── exchange_factory.py  # Builds ccxt exchange instances from config
│   │
│   ├── indicators/              # Pure functions. Input: DataFrame. Output: DataFrame
│   │   ├── __init__.py
│   │   ├── trend.py             # EMA, SMA, MACD
│   │   ├── momentum.py          # RSI, Stochastic
│   │   └── volume.py            # VWAP, OBV, CVD
│   │
│   ├── screener/                # Evaluation engine
│   │   ├── __init__.py
│   │   ├── conditions.py        # Condition primitives (crossover, threshold, etc.)
│   │   ├── rules.py             # Composable rule definitions
│   │   └── engine.py            # Runs rules against indicator output
│   │
│   ├── alerts/                  # Notification layer
│   │   ├── __init__.py
│   │   └── telegram.py          # Formats and sends alert messages
│   │
│   ├── db/                      # Database layer
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── session.py           # Async engine + session factory
│   │   └── repository.py        # All DB queries go here — no raw SQL elsewhere
│   │
│   └── scheduler/               # Task orchestration
│       ├── __init__.py
│       └── jobs.py              # APScheduler job definitions
│
├── migrations/                  # Alembic migration files
│   └── versions/
│
└── tests/
    ├── conftest.py              # Shared fixtures (test DB, mock exchange, etc.)
    ├── test_fetcher.py
    ├── test_indicators.py
    ├── test_screener.py
    └── test_alerts.py
```

---

## Database models (Phase 1)

```
Exchange      id, name, slug (binance | kraken | coinbase)
TradingPair   id, exchange_id, symbol (BTC/USDT), timeframe (4h | 1d), active
Candle        id, pair_id, timestamp, open, high, low, close, volume
ScreenerRule  id, name, description, conditions (JSON), active
Alert         id, rule_id, pair_id, triggered_at, message, sent
```

All timestamps are **UTC**. No exceptions.

---

## Supported exchanges (Phase 1)

| Exchange | ccxt slug  | Notes                       |
|----------|------------|-----------------------------|
| Binance  | `binance`  | Primary — deepest liquidity |
| Kraken   | `kraken`   | EU-friendly, reliable API   |
| Coinbase | `coinbase` | US pairs, good for BTC/ETH  |

Exchange instances are **read-only**. API keys are optional for public OHLCV data.
If keys are provided, they must only have read permissions.

---

## Supported timeframes

`1h` · `4h` · `1d`

Start with `4h` for swing screening. Anything below `1h` is out of scope for Phase 1.

---

## Screener conditions (Phase 1 primitives)

- `ema_crossover(fast, slow)` — fast EMA crosses above slow EMA
- `rsi_range(min, max)` — RSI within a given range
- `price_above_vwap()` — close above VWAP
- `volume_spike(multiplier)` — volume N× the rolling average

Conditions are composable with AND logic. OR logic comes in Phase 2.

---

## Environment variables

```bash
# .env.example

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/candle

# Exchanges (all optional for public OHLCV data)
BINANCE_API_KEY=
BINANCE_API_SECRET=
KRAKEN_API_KEY=
KRAKEN_API_SECRET=
COINBASE_API_KEY=
COINBASE_API_SECRET=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Scheduler
FETCH_INTERVAL_MINUTES=60
SCREEN_INTERVAL_MINUTES=60
DEFAULT_TIMEFRAME=4h
```

---

## Language conventions

- All code in English: variable names, function names, class names, comments
- All docstrings in English
- All log messages in English
- Commit messages in English following Conventional Commits:
  `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`
- README and internal technical docs in English
- CLAUDE.md can be updated in Spanish by the developer

## Coding conventions

- **Type hints on every function signature.** No bare `dict` — use TypedDict or Pydantic models.
- **Async by default** in data, db, and alerts layers. Sync only for pure indicator
  functions (CPU-bound, no I/O).
- **No business logic in models.** Models are data containers. Logic lives in
  repositories or services.
- **Repository pattern for all DB access.** No SQLAlchemy queries outside `db/repository.py`.
- **Indicators are pure functions.** Same input always produces same output. No side
  effects. No DB calls. No logging inside indicator functions.
- **One responsibility per module.** `fetcher.py` fetches. `normalizer.py` normalizes.
  They do not know about each other.
- **Fail loudly in development, fail gracefully in production.** Use environment-aware
  error handling via the config.

---

## What NOT to do — common mistakes to avoid

- Do not use `requests` or any sync HTTP library. Use ccxt's async client.
- Do not store raw ccxt responses in the database. Always normalize first.
- Do not compute indicators inside the fetcher. Keep layers strictly separate.
- Do not hardcode symbols or timeframes anywhere. They come from the DB or config.
- Do not send a Telegram message directly from the screener. Go through the alerts layer.
- Do not create a new DB session per query. Use the session factory from `db/session.py`.

---

## Development workflow

```bash
# Start local DB
docker-compose up -d postgres

# Apply migrations
alembic upgrade head

# Run tests
pytest

# Run scheduler manually (development)
python -m candle.scheduler.jobs --once
```

---

## Phase checklist

### Phase 1 — Backend core
- [x] Project scaffolding + pyproject.toml
- [x] Docker-compose with PostgreSQL
- [x] Config via pydantic-settings
- [x] ccxt exchange factory
- [x] OHLCV fetcher for Binance / Kraken / Coinbase
- [x] DataFrame normalizer
- [x] EMA, RSI, VWAP indicators
- [x] Alembic models + initial migration
- [x] Repository layer (save candles, read candles)
- [x] Screener engine with 2 working rules
- [x] pytest suite for indicators and screener

### Phase 2 — Alerts + scheduling
- [x] Telegram bot setup
- [x] Alert formatter and sender
- [x] APScheduler jobs wired to fetcher + screener
- [x] Alert persistence in DB
- [x] Deduplication (no re-alert for same condition within N hours)
- [x] Railway deploy (EU West, Dockerfile, alembic release command)

### Phase 3 — API + frontend
- [ ] FastAPI router for pairs, candles, alerts
- [ ] Authentication (API key, simple)
- [ ] Next.js project scaffolding
- [ ] Price chart with indicators overlay
- [ ] Alert history view

---

## MCP servers in use

| MCP        | Purpose                                           |
|------------|---------------------------------------------------|
| filesystem | Claude navigates and edits project files          |
| github     | PRs, commits, issue tracking from conversation    |
| postgresql | Claude queries the live dev DB during development |

---

## Testing rules

- Indicators must have at least 2 tests each: one happy path, one edge case
- Never call real exchange APIs in tests — use fixtures in `tests/fixtures/`
- Never use random data — fixtures must contain known signals with known outputs
- A fixture is a real OHLCV response downloaded once with ccxt and saved as CSV or JSON
- Integration tests use a separate test database (`DATABASE_URL_TEST` in `.env`)
- Repository tests run against a real PostgreSQL test instance, not SQLite
- Mock the Telegram client — verify it was called with the correct message, never send real messages in tests
- A test that only checks "no exception raised" is not a test

### Fixture strategy

```
tests/fixtures/
├── btc_4h_100.csv          # 100 real BTC/USDT 4h candles for indicator tests
├── btc_4h_crossover.csv    # Candles containing a known EMA crossover signal
├── btc_4h_overbought.csv   # Candles where RSI exceeds 70
└── raw_ccxt_binance.json   # Raw ccxt response saved once, used in normalizer tests
```

Generate fixtures once with a helper script (`scripts/generate_fixtures.py`).
Never regenerate them automatically — fixtures must be stable and committed to git.

---

## Open questions (resolve before Phase 3)

- Authentication strategy if moving toward multi-user SaaS
- Whether to use Supabase instead of raw PostgreSQL for easier auth
- Frontend charting library: TradingView Lightweight Charts vs Recharts
- Pricing model if monetizing

---

*Last updated: 2026-03-24 — Phase 1 not started*
