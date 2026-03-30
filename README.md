# Candle

**Crypto market screener and alert system.**

Fetches OHLCV data from multiple exchanges on a schedule, computes technical indicators, evaluates configurable screening rules, and delivers alerts via Telegram. Includes a REST API and a Next.js dashboard.

![Python](https://img.shields.io/badge/python-3.12+-blue)
![Deploy](https://img.shields.io/badge/deploy-Railway-blueviolet)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What it does

- **Fetches candle data** from Binance, Kraken, and Coinbase every N minutes via ccxt
- **Computes indicators** on each fetch cycle: EMA (9/21/50/200), RSI, VWAP
- **Screens for conditions**: EMA crossovers, RSI ranges, price vs VWAP, volume spikes
- **Deduplicates alerts**: the same rule won't fire twice for the same pair within a configurable window
- **Delivers alerts to Telegram** with rich messages that include real indicator values
- **Exposes a REST API** for pairs, candles (with indicators), and alert history
- **Dashboard** showing live price, change %, RSI per pair, and a candlestick chart with indicator overlays

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Scheduler (APScheduler)              │
│                                                             │
│   fetch_job (60 min)          screen_job (60 min)           │
│        │                             │                      │
│        ▼                             ▼                      │
│   Exchange APIs              Screener Engine                │
│  (ccxt — read only)          conditions.py / rules.py       │
│        │                             │                      │
│        ▼                             ▼                      │
│   Normalizer             ┌── RuleMatch ──┐                  │
│  (DataFrame)             │               │                  │
│        │              Alerts DB     Telegram Bot            │
│        ▼              (dedup)       (async send)            │
│   Candles DB                                                │
└─────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    FastAPI (REST)    │
                    │  /pairs             │
                    │  /pairs/{id}/candles│
                    │  /alerts            │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Next.js Dashboard  │
                    │  (SWR + TradingView │
                    │   Lightweight Charts│
                    └─────────────────────┘
```

Data flows in one direction: exchange → DB → screener → alert. The API and frontend are read-only consumers. No layer knows about the layer above it.

---

## Tech stack

| Layer              | Technology                  | Notes                                          |
|--------------------|-----------------------------|------------------------------------------------|
| Language           | Python 3.12+                | Type hints on every function signature         |
| Exchange connector | ccxt 4.x                    | Unified API across Binance, Kraken, Coinbase   |
| Indicators         | pandas-ta                   | Pure functions on pandas DataFrames            |
| ORM                | SQLAlchemy 2.x (async)      | Async sessions throughout; no sync I/O         |
| Migrations         | Alembic                     | Schema changes via migrations only             |
| Scheduler          | APScheduler                 | Interval jobs for fetch and screen cycles      |
| Alerts             | python-telegram-bot         | Async client                                   |
| Config             | pydantic-settings           | Typed, validated config from `.env`            |
| API framework      | FastAPI + uvicorn           | Rate-limited, API key auth                     |
| Rate limiting      | slowapi                     | Per-IP limits; 30–60 req/min by endpoint       |
| Database           | PostgreSQL 15+              | All timestamps UTC                             |
| Frontend framework | Next.js 14 (App Router)     | Server components + API proxy route            |
| Styling            | Tailwind CSS + shadcn/ui    |                                                |
| Charts             | TradingView Lightweight Charts v5 | Candlestick + EMA/RSI overlays           |
| Data fetching      | SWR                         | Auto-refresh every 30 s                        |
| Deploy             | Railway                     | Separate services for scheduler and API        |
| Local dev          | Docker + docker-compose     | PostgreSQL only; app runs outside container    |
| Testing            | pytest + pytest-asyncio     | 74 tests; real DB fixtures, no mocks for DB    |

---

## Getting started

**Requirements:** Docker, Python 3.12+, Node 18+

```bash
# 1. Clone and install
git clone https://github.com/Fire-Fairy84/candle.git && cd candle
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, API_KEY

# 4. Apply migrations and seed data
alembic upgrade head
python -m scripts.seed

# 5. Run scheduler (fetches + screens every 60 min)
python serve.py
```

Frontend (separate terminal):

```bash
cd frontend
npm install
cp .env.example .env.local   # set CANDLE_API_URL and CANDLE_API_KEY
npm run dev
```

Open `http://localhost:3000`.

---

## Configuration

All configuration is loaded from `.env` via pydantic-settings. Copy `.env.example` to get started.

| Variable                  | Required | Default | Description                                         |
|---------------------------|----------|---------|-----------------------------------------------------|
| `DATABASE_URL`            | Yes      | —       | PostgreSQL asyncpg URL                              |
| `API_KEY`                 | Yes (prod) | —     | Shared secret for `X-API-Key` header. Empty = auth disabled (local dev only) |
| `TELEGRAM_BOT_TOKEN`      | Yes      | —       | Bot token from @BotFather                           |
| `TELEGRAM_CHAT_ID`        | Yes      | —       | Target chat or user ID                              |
| `FETCH_INTERVAL_MINUTES`  | No       | `60`    | How often to pull new candles from exchanges        |
| `SCREEN_INTERVAL_MINUTES` | No       | `60`    | How often to run the screener                       |
| `ALERT_DEDUP_HOURS`       | No       | `4`     | Suppress re-alerts for the same rule+pair within N hours |
| `DEFAULT_TIMEFRAME`       | No       | `4h`    | Fallback timeframe when not specified               |
| `BINANCE_API_KEY`         | No       | —       | Optional — public OHLCV data works without keys     |
| `BINANCE_API_SECRET`      | No       | —       |                                                     |
| `KRAKEN_API_KEY`          | No       | —       |                                                     |
| `KRAKEN_API_SECRET`       | No       | —       |                                                     |

Exchange API keys are read-only. The application never places orders.

---

## API reference

All endpoints require `X-API-Key: <your-key>` header in production. Omit the header in local dev when `API_KEY` is unset.

Interactive docs available at `/docs` (Swagger UI) when the API is running.

### `GET /api/v1/pairs`

Returns all active trading pairs with their exchange.

Rate limit: 60 req/min per IP.

```bash
curl http://localhost:8000/api/v1/pairs \
  -H "X-API-Key: your-key"
```

```json
{
  "pairs": [
    {
      "id": 1,
      "symbol": "BTC/USDT",
      "timeframe": "4h",
      "active": true,
      "exchange": { "id": 1, "name": "Binance", "slug": "binance" }
    }
  ],
  "count": 1
}
```

---

### `GET /api/v1/pairs/{pair_id}/candles`

Returns candles for a pair with indicators computed on the fly. Indicators are `null` for leading rows where there is insufficient history (e.g. EMA 200 needs 200 candles).

Rate limit: 30 req/min per IP (CPU-bound indicator computation).

**Query params:**

| Param   | Type | Default | Range   |
|---------|------|---------|---------|
| `limit` | int  | `100`   | 1–500   |

```bash
curl "http://localhost:8000/api/v1/pairs/1/candles?limit=3" \
  -H "X-API-Key: your-key"
```

```json
{
  "pair_id": 1,
  "symbol": "BTC/USDT",
  "timeframe": "4h",
  "count": 3,
  "candles": [
    {
      "timestamp": "2026-03-29T20:00:00Z",
      "open": 82341.5,
      "high": 83100.0,
      "low": 82100.0,
      "close": 82900.0,
      "volume": 1245.8,
      "indicators": {
        "ema_9": 82750.3,
        "ema_21": 82100.1,
        "ema_50": 80500.0,
        "ema_200": null,
        "rsi": 58.4,
        "vwap": 82600.0
      }
    }
  ]
}
```

---

### `GET /api/v1/alerts`

Returns the most recent alerts, newest first.

Rate limit: 60 req/min per IP.

**Query params:**

| Param   | Type | Default | Range   |
|---------|------|---------|---------|
| `limit` | int  | `50`    | 1–200   |

```bash
curl "http://localhost:8000/api/v1/alerts?limit=2" \
  -H "X-API-Key: your-key"
```

```json
{
  "alerts": [
    {
      "id": 42,
      "triggered_at": "2026-03-30T14:00:00Z",
      "message": "RSI at 28.3 — entering oversold territory. Watch for a potential bounce.",
      "sent": true,
      "rule_name": "RSI Oversold",
      "symbol": "ETH/USDT",
      "timeframe": "4h",
      "exchange_slug": "binance"
    }
  ],
  "count": 1
}
```

---

## Project structure

```
candle/
├── candle/                      # Main Python package
│   ├── config.py                # Single Settings instance — all config lives here
│   ├── data/
│   │   ├── fetcher.py           # ccxt wrapper — fetch_ohlcv per exchange/pair
│   │   ├── normalizer.py        # Raw ccxt response → clean DataFrame
│   │   └── exchange_factory.py  # Builds read-only ccxt instances from config
│   ├── indicators/              # Pure functions: DataFrame in, Series out, no side effects
│   │   ├── trend.py             # EMA, SMA, MACD
│   │   ├── momentum.py          # RSI, Stochastic
│   │   └── volume.py            # VWAP, OBV
│   ├── screener/
│   │   ├── conditions.py        # Primitive condition functions (crossover, threshold, etc.)
│   │   ├── rules.py             # Rule dataclass — composes conditions with AND logic
│   │   └── engine.py            # Evaluates rules against DataFrames, builds alert messages
│   ├── alerts/
│   │   └── telegram.py          # Formats and sends alert messages via python-telegram-bot
│   ├── db/
│   │   ├── models.py            # SQLAlchemy ORM models — data containers only
│   │   ├── session.py           # Async engine and session factory
│   │   └── repository.py        # All DB queries — no raw SQL outside this module
│   ├── api/
│   │   ├── app.py               # FastAPI factory — registers routers and middleware
│   │   ├── auth.py              # X-API-Key dependency with constant-time comparison
│   │   ├── limiter.py           # Shared slowapi Limiter instance
│   │   ├── schemas.py           # Pydantic response models
│   │   └── routes/
│   │       ├── pairs.py         # GET /pairs, GET /pairs/{id}/candles
│   │       └── alerts.py        # GET /alerts
│   └── scheduler/
│       └── jobs.py              # APScheduler job definitions (fetch + screen cycles)
│
├── frontend/                    # Next.js 14 dashboard
│   └── src/
│       ├── app/                 # App Router pages
│       │   ├── page.tsx         # Dashboard — pair cards with live price/RSI
│       │   ├── alerts/          # Alert history table
│       │   └── pairs/[id]/      # Pair detail with candlestick chart
│       ├── components/
│       │   ├── chart/           # TradingView Lightweight Charts wrapper
│       │   ├── pairs/           # PairCard, PairsList
│       │   └── alerts/          # AlertsTable with category badges
│       └── lib/
│           └── hooks/           # SWR hooks: usePairs, useCandles, useAlerts
│
├── migrations/                  # Alembic versions
├── tests/                       # 74 tests — indicators, screener, API, alerts
│   └── fixtures/                # Real OHLCV CSVs with known signals — never regenerated
├── scripts/
│   ├── seed.py                  # Seeds exchanges and trading pairs
│   └── seed_pairs.py            # Adds additional pairs idempotently
├── docs/
│   ├── refactor-report.md       # Backend code review — quick wins and refactors
│   └── security-audit.md        # Pre-production security audit
├── serve.py                     # Entrypoint — starts scheduler or API based on args
├── docker-compose.yml           # PostgreSQL for local dev
└── pyproject.toml               # Single source of truth for deps and tooling
```

---

## Database schema

```
Exchange      id, name, slug
TradingPair   id, exchange_id, symbol, timeframe, active
Candle        id, pair_id, timestamp, open, high, low, close, volume
ScreenerRule  id, name, description, conditions (JSON), active
Alert         id, rule_id, pair_id, triggered_at, message, sent
```

All timestamps are UTC. Schema changes go through Alembic migrations exclusively — no `ALTER TABLE` directly.

---

## Roadmap

### v1.0 — complete

- [x] OHLCV fetcher for Binance, Kraken, Coinbase (read-only)
- [x] EMA, RSI, VWAP indicators with real-data fixtures
- [x] Composable screener rules with AND logic
- [x] Telegram alerts with deduplication
- [x] APScheduler fetch + screen cycles
- [x] Railway deploy (EU West)
- [x] REST API with rate limiting and API key auth
- [x] Next.js dashboard with candlestick chart and alert history
- [x] Security hardened: timing-safe auth, proxy input validation, sanitized logs

### v1.1 — planned

- [ ] Deploy frontend to Railway
- [ ] CORS and security headers middleware
- [ ] Health check endpoint
- [ ] OR logic for screener conditions
- [ ] Webhook support as an alternative to Telegram
- [ ] Per-rule alert thresholds configurable via API

---

## License

MIT
