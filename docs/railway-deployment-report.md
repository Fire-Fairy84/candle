# Railway Deployment Report — Candle

## 1. Overview

Candle is a crypto market screener (Python, async SQLAlchemy, PostgreSQL) that fetches OHLCV data from exchanges, evaluates screening rules, and sends Telegram alerts. The goal was to deploy the scheduler bot (`scripts/run.py`) to Railway with a managed PostgreSQL instance.

---

## 2. Issues Encountered

### 2.1 `pandas-ta` build failure
- **What happened:** `pip install` failed during Docker build — `pandas-ta>=0.3.14b` not found.
- **Why:** PyPI only has pre-release versions (`0.4.67b0`, `0.4.71b0`). The `0.4.71b0` version requires `numba`, which fails to compile on `python:3.11-slim`.
- **Initial assumption:** The version specifier `>=0.3.14b` would match any available version on PyPI.
- **What I tried:** Checked available versions on PyPI, evaluated installing from GitHub vs removing the version constraint.
- **What I thought was happening:** The package name or specifier syntax was wrong.
- **What actually happened:** pip skips pre-release versions by default unless the specifier explicitly pins one. All `pandas-ta` releases on PyPI are pre-releases (`b0` suffix), so none matched.
- **General insight:** Pre-release-only packages on PyPI require explicit version pins. A `>=` constraint won't match beta versions unless the pin itself includes a pre-release tag.

### 2.2 Python version incompatibility
- **What happened:** `pandas-ta==0.4.67b0` requires Python >=3.12, but the Dockerfile used `python:3.11-slim`.
- **Why:** The original `pyproject.toml` specified `requires-python = ">=3.11"` and the Dockerfile matched that.
- **Initial assumption:** Python 3.11 was sufficient for all dependencies.
- **What I tried:** Evaluated three options — upgrade Python, switch to `ta-lib` (C library), or rewrite indicators with raw pandas.
- **What I thought was happening:** The dependency would install and work on 3.11.
- **What actually happened:** `pandas-ta 0.4.x` dropped 3.11 support. Upgrading to 3.12 was the lowest-risk fix.
- **General insight:** When pinning a dependency, always verify its runtime requirements against your target environment. A package that installs fine locally may fail in a container with a different Python version.

### 2.3 `No module named 'candle'`
- **What happened:** Container started but crashed immediately — the `candle` package was not installed.
- **Why:** The Dockerfile ran `pip install .` before copying `candle/` into the image. Hatchling had only `pyproject.toml` but no package source to install.
- **Initial assumption:** Copying `pyproject.toml` first and running `pip install .` would leverage Docker layer caching for dependencies, then copying the source code afterwards would make it available at runtime.
- **What I tried:** Reviewed the Dockerfile layer order.
- **What I thought was happening:** `pip install .` would install dependencies, and the later `COPY candle/` would provide the code.
- **What actually happened:** `pip install .` with hatchling builds and installs the package in one step. Without the source, it silently installed dependencies but not the `candle` package itself. Python then imported from `site-packages`, where the package was absent.
- **General insight:** With PEP 517 build backends (hatchling, setuptools, etc.), `pip install .` is not just a dependency installer — it builds and installs the package. The source must be present at build time, not just at runtime.

### 2.4 `Could not parse SQLAlchemy URL`
- **What happened:** SQLAlchemy rejected the database URL at startup.
- **Why:** Railway's PostgreSQL plugin provides `DATABASE_URL` with scheme `postgresql://`, but asyncpg requires `postgresql+asyncpg://`.
- **Initial assumption:** Railway would provide a URL that SQLAlchemy could use directly.
- **What I tried:** Added a `.replace()` call to normalize the scheme before passing it to `create_async_engine`.
- **What I thought was happening:** The URL was malformed or missing entirely.
- **What actually happened:** The URL was valid PostgreSQL, just missing the async driver prefix that SQLAlchemy needs to route to asyncpg.
- **General insight:** Async database drivers often require explicit dialect prefixes in connection URLs. When accepting URLs from external platforms, normalize the scheme at the application boundary rather than expecting the platform to match your driver's requirements.

### 2.5 `ValidationError: candle_db_url — Field required`
- **What happened:** pydantic-settings crashed at import time because no database URL was available.
- **Why:** `Settings()` was instantiated at module level in `config.py`. This runs during Python's import phase, before the application has a chance to read environment variables lazily. Railway also overwrites `DATABASE_URL` with an empty string on app services, making the standard variable name unusable.
- **Initial assumption:** Environment variables would be available at import time, as they are in local development with a `.env` file.
- **What I tried:** First renamed the variable to `CANDLE_DB_URL` to avoid Railway's override. Then added a `model_validator` to build the URL from `PG*` variables. Then moved the entire resolution out of pydantic-settings into lazy initialization.
- **What I thought was happening:** The variable existed in Railway but was somehow not being read by pydantic-settings.
- **What actually happened:** Multiple issues compounded — Railway overwrites `DATABASE_URL`, reference variables (`${{Postgres.DATABASE_URL}}`) didn't resolve, and module-level instantiation left no room for deferred reads. The fix required decoupling configuration validation from module import.
- **General insight:** Module-level initialization in Python is essentially "run at import time." In containerized environments, this can race against the platform's variable injection. Critical resources (database engines, API clients) should be initialized lazily — at first use, not at first import.

### 2.6 Railway variable sharing not working
- **What happened:** `CANDLE_DB_URL=${{Postgres.DATABASE_URL}}` resolved to empty string. The PG* variables (`PGHOST`, `PGPORT`, etc.) were also unavailable on the app service.
- **Why:** In this setup, PostgreSQL plugin variables were not accessible from the app service as expected. The auto-injected variables on the app service were only Railway system metadata (`RAILWAY_PROJECT_NAME`, `RAILWAY_SERVICE_ID`, etc.), not database credentials.
- **Initial assumption:** Railway would automatically share database credentials with linked services, similar to Heroku's add-on behavior.
- **What I tried:** Used `${{Postgres.DATABASE_URL}}` reference syntax, tried "Shared Variables" in project settings (showed "No suggestions"), added fallbacks for PG* variables in code.
- **What I thought was happening:** The reference syntax was correct but had a typo or wrong service name.
- **What actually happened:** The Postgres service variables were isolated to that service. No automatic sharing occurred, and the reference syntax did not resolve. Hardcoding the URL directly in the app service variables was the only approach that worked.
- **General insight:** Managed platforms vary widely in how they share configuration between services. Don't assume inter-service variable injection works — verify it explicitly, and have a fallback that doesn't depend on platform-specific reference syntax.

### 2.7 `Name or service not known` — private DNS failure
- **What happened:** `postgres.railway.internal` could not be resolved from the app service.
- **Why:** After changing both services to EU West region, Railway's private DNS did not propagate. This appeared to be a platform-level issue.
- **Initial assumption:** Private networking would work automatically between services in the same project and region.
- **What I tried:** Moved both services to EU West, redeployed both, used the private hostname.
- **What I thought was happening:** The region change would take effect immediately and DNS would resolve.
- **What actually happened:** Private DNS did not resolve even after redeployment. Switching to the public TCP proxy URL (`<proxy-host>:<proxy-port>`) resolved the issue.
- **General insight:** Internal service discovery on managed platforms can be fragile, especially after infrastructure changes like region migrations. Always have a public connectivity fallback, and don't assume private DNS is instantly consistent.

### 2.8 Binance 451 — geographic restriction
- **What happened:** Binance API returned HTTP 451: "Service unavailable from a restricted location."
- **Why:** Railway's default region is US-based. Binance blocks API access from US IP addresses.
- **Initial assumption:** Public API endpoints would be accessible from any region.
- **What I tried:** Evaluated switching to Kraken/Coinbase, using `binanceus` slug, or changing the deploy region.
- **What I thought was happening:** A temporary Binance outage or rate limit.
- **What actually happened:** HTTP 451 is a legal/geographic block, not a rate limit. The server's IP geolocation determines access, not the API key's origin.
- **General insight:** When deploying services that call third-party APIs, the server's geographic location matters. Some APIs enforce region-based access restrictions at the IP level. Always verify API access from your deployment region before going to production.

### 2.9 `database "railway       " does not exist`
- **What happened:** PostgreSQL rejected the connection — database name had trailing whitespace.
- **Why:** Trailing spaces were accidentally included when pasting the URL in Railway's Raw Editor.
- **Initial assumption:** The connection was fully working since the DNS resolved and authentication passed.
- **What I tried:** Re-checked the URL in the Raw Editor.
- **What I thought was happening:** A database configuration issue on Railway's side.
- **What actually happened:** Copy-paste artifact. The whitespace was invisible in the masked variable view but present in the raw value.
- **General insight:** When debugging connection failures that pass authentication but fail on resource lookup, check for invisible characters. Platform UIs that mask values make whitespace issues hard to spot — always verify in a raw/plaintext editor.

### 2.10 Scheduler jobs idle on first interval
- **What happened:** Railway killed the container for inactivity. APScheduler waited 60 minutes before firing the first job.
- **Why:** `IntervalTrigger` defaults to waiting one full interval before the first execution.
- **Initial assumption:** APScheduler would run jobs immediately on `scheduler.start()`.
- **What I tried:** Reviewed APScheduler docs for the `next_run_time` parameter.
- **What I thought was happening:** The scheduler was broken or not starting properly.
- **What actually happened:** The scheduler was running correctly — it was simply waiting for the configured interval (60 min) before the first trigger. Container platforms expect visible activity shortly after boot.
- **General insight:** Long-running services in containerized environments need to show activity quickly after startup. Scheduled tasks should execute once immediately, then repeat on interval. Silence at boot can look like a crash to the platform's health checker.

---

## 3. Solutions Applied

### 3.1 pandas-ta pinned to working version
- Pinned to `pandas-ta==0.4.67b0` in `pyproject.toml` (no numba dependency).

### 3.2 Python upgraded to 3.12
- Dockerfile: `python:3.11-slim` → `python:3.12-slim`
- `pyproject.toml`: `requires-python = ">=3.12"`

### 3.3 Dockerfile COPY order fixed
- Moved `COPY candle/ candle/` before `RUN pip install .` so hatchling can find the package source.

### 3.4 Automatic URL scheme normalization
- `session.py` applies `.replace("postgresql://", "postgresql+asyncpg://", 1)` before passing the URL to `create_async_engine`.

### 3.5 Lazy engine initialization + custom variable name
- **Removed** `model_validator` from `config.py` — `candle_db_url` is now `str = ""` with no import-time validation.
- **Added** `_resolve_db_url()` in `session.py` — reads from `os.environ` directly at first use, trying multiple variable names in order:
  1. `CANDLE_DB_URL`
  2. `DATABASE_PRIVATE_URL`
  3. `DATABASE_URL`
  4. Build from `PGHOST` + `PGUSER` + `PGPASSWORD` + `PGDATABASE`
  5. Fall back to `settings.candle_db_url` (for local dev `.env`)
- Engine and session factory are created on first use, not at import time.

### 3.6 Direct URL instead of Railway references
- Set `CANDLE_DB_URL` in Railway's Raw Editor with the hardcoded public proxy URL instead of `${{Postgres.DATABASE_URL}}`.

### 3.7 Public proxy URL instead of private DNS
- Used `<proxy-host>:<proxy-port>` (Railway's TCP proxy) instead of `postgres.railway.internal:5432`.

### 3.8 Region changed to EU West
- Both services (candle + Postgres) moved to EU West (Amsterdam, Netherlands) to avoid Binance geographic restrictions.

### 3.9 Immediate job execution on startup
- Added `next_run_time=datetime.now(tz=timezone.utc)` to both `add_job()` calls so jobs fire immediately when the scheduler starts.

### 3.10 Automatic migrations on deploy
- Added `releaseCommand = "alembic upgrade head"` to `railway.toml`.

---

## 4. Final Working Configuration

### Dockerfile
- Base: `python:3.12-slim`
- Installs `candle` package via `pip install .`
- Copies `scripts/`, `alembic.ini`, `migrations/`
- Runs as non-root user (`appuser`)
- Entrypoint: `CMD ["python", "scripts/run.py"]`

### railway.toml
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "python scripts/run.py"
releaseCommand = "alembic upgrade head"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 5
```

### Railway service variables (candle)
```
CANDLE_DB_URL=postgresql://postgres:<password>@<proxy-host>:<proxy-port>/railway
ENV=production
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>
FETCH_INTERVAL_MINUTES=60
SCREEN_INTERVAL_MINUTES=60
DEFAULT_TIMEFRAME=4h
ALERT_DEDUP_HOURS=4
```

### Service topology
- **candle** (app): EU West, Dockerfile build
- **Postgres** (database): EU West, Railway managed plugin
- Connection: via public TCP proxy (private DNS did not resolve after region migration)

---

## 5. Lessons Learned

1. **Managed platforms may override or inject environment variables that conflict with application-level configuration.** In this case, `DATABASE_URL` was silently set to an empty string. Using a namespaced variable (`CANDLE_DB_URL`) avoided the collision. When possible, prefix application variables to reduce the chance of conflicts with platform internals.

2. **Module-level initialization in Python is effectively "run at import time," which can race against the runtime environment.** Database engines, API clients, and configuration objects that depend on environment variables should be initialized lazily — at first use, not at first import. This is especially important in containerized deployments where the import phase and the runtime phase may have different contexts.

3. **Inter-service configuration sharing on managed platforms is not guaranteed to work as documented.** Reference syntax, shared variables, and automatic injection all failed in different ways during this deployment. The most reliable approach was hardcoding the connection URL directly. Trust what you can verify, not what the platform promises.

4. **Third-party APIs may enforce geographic restrictions at the IP level, not the account level.** The deploy region determines which APIs your service can reach. This should be validated early — ideally during a local `docker run` test or a staging deploy — not discovered after the first production crash.

5. **Async database drivers require explicit dialect prefixes in connection URLs.** Platforms typically provide `postgresql://` URLs, but asyncpg needs `postgresql+asyncpg://`. Normalizing connection URLs at the application boundary is a simple pattern that prevents this class of errors entirely.

6. **Long-running services in containerized environments must show signs of life quickly.** Schedulers, workers, and pollers that stay idle after boot can be killed by the platform's health checker. Running an initial cycle immediately on startup is both operationally correct and avoids false-positive container restarts.

7. **Invisible characters in configuration values cause failures that look like infrastructure problems.** Trailing whitespace from copy-paste, BOM characters in config files, or non-breaking spaces in environment variables can survive through authentication and DNS resolution, only to fail at the final step. When a connection fails at an unexpected stage, inspect the raw bytes.

---

## 6. What I Would Do Differently

- **Define a single, required environment variable for database connection** instead of building a fallback chain across five variable names. The cascade (`CANDLE_DB_URL` → `DATABASE_PRIVATE_URL` → `DATABASE_URL` → PG* components → settings) was a reaction to repeated failures, not a design decision. A single required variable with a clear error message would have been easier to debug.

- **Avoid relying on implicit platform behavior** for critical configuration. Shared variables, reference syntax, and automatic injection all looked correct in the UI but failed at runtime. Hardcoding the URL (or passing it explicitly) was the only approach that worked reliably. I would start there next time instead of trying to make the "elegant" reference approach work.

- **Add startup validation that fails fast** if critical configuration is missing, rather than deferring errors to the first database query. A simple check at the top of `run.py` — "is the database URL set and reachable?" — would have surfaced configuration issues in seconds instead of requiring multiple deploy cycles.

- **Test the container locally before deploying** by running `docker build` and `docker run` with production-equivalent variables. Several issues (missing module, URL scheme, import-time crashes) would have been caught immediately without waiting for Railway's build-deploy cycle.

- **Check API accessibility from the target region** before deploying. A quick `curl` from a VPS in the deploy region (or a test container on the platform) would have caught the Binance 451 before it became a production issue.

- **Use the platform's Raw Editor from the start** when setting environment variables, instead of the masked UI. The masked view hides whitespace, empty values, and unresolved references. Raw text removes ambiguity.
