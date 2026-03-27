FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY candle/ candle/
COPY scripts/ scripts/
COPY alembic.ini .
COPY migrations/ migrations/

# Non-root user
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

CMD ["python", "scripts/run.py"]
