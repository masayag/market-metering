FROM python:3.12-slim AS base

# Prevent Python from writing bytecode and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
FROM base AS dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Production image
FROM base AS production
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/ ./src/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /data && \
    chown appuser:appuser /data

USER appuser

# Data volume for ATH persistence
VOLUME ["/data"]

# Default ATH storage path
ENV DCA_ATH_STORAGE_PATH=/data/ath_records.json

ENTRYPOINT ["python", "-m", "dca_alerts.main"]
