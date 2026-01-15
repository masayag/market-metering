# DCA Market Drop Alert Service

A Python service that monitors S&P 500, NASDAQ 100, and Russell 2000 indices daily, detects drops from ATH (All-Time High) in 5% increments, and sends buy/hold recommendations via email and console output.

## Features

- **Daily market monitoring**: Fetches live data from Yahoo Finance
- **ATH tracking**: Persists all-time high values with atomic writes
- **Drop detection**: Triggers buy signals at 5%, 10%, 15%... drops from ATH
- **Notifications**: Console output and SMTP email support
- **Containerized**: Ready for Docker deployment with cron scheduling

## Project Structure

```
market-metering/
├── src/dca_alerts/
│   ├── main.py                 # Entry point and orchestrator
│   ├── config.py               # Configuration loading
│   ├── models.py               # Data classes
│   ├── market/
│   │   ├── fetcher.py          # yfinance wrapper
│   │   └── analyzer.py         # Drop detection logic
│   ├── persistence/
│   │   └── ath_store.py        # JSON ATH storage
│   └── notification/
│       ├── base.py             # Notifier protocol
│       ├── console_notifier.py
│       └── email_notifier.py
├── tests/                      # Unit tests
├── config/config.example.yaml  # Example configuration
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Installation

### Local Development

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Docker

```bash
docker build -t dca-alerts .
```

## Usage

### Command Line

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the service
python -m dca_alerts.main

# Run with verbose logging
python -m dca_alerts.main -v

# Run with custom config file
python -m dca_alerts.main -c config/config.yaml

# Show help
python -m dca_alerts.main --help
```

### Docker

```bash
# Run with environment file
docker run --rm \
    --env-file .env \
    -v ./data:/data \
    dca-alerts

# Run with explicit environment variables
docker run --rm \
    -e DCA_ATH_STORAGE_PATH=/data/ath_records.json \
    -e DCA_SMTP_HOST=smtp.gmail.com \
    -e DCA_SMTP_PORT=587 \
    -e DCA_SMTP_USER=your-email@gmail.com \
    -e DCA_SMTP_PASSWORD=your-app-password \
    -e DCA_SENDER_EMAIL=your-email@gmail.com \
    -e DCA_RECIPIENT_EMAIL=recipient@example.com \
    -v ./data:/data \
    dca-alerts
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DCA_ATH_STORAGE_PATH` | Path to ATH JSON file | `./data/ath_records.json` |
| `DCA_SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `DCA_SMTP_PORT` | SMTP server port | `587` |
| `DCA_SMTP_USER` | SMTP username | (required for email) |
| `DCA_SMTP_PASSWORD` | SMTP password | (required for email) |
| `DCA_SENDER_EMAIL` | Email sender address | (required for email) |
| `DCA_RECIPIENT_EMAIL` | Email recipient address | (required for email) |
| `DCA_SMTP_USE_TLS` | Enable TLS | `true` |
| `DCA_DROP_INCREMENT` | Drop percentage increment | `5` |
| `DCA_LOG_LEVEL` | Logging level | `INFO` |

### YAML Configuration

Create `config/config.yaml` based on `config/config.example.yaml`:

```yaml
indices:
  - symbol: "^GSPC"
    name: "S&P 500"
  - symbol: "^NDX"
    name: "NASDAQ 100"
  - symbol: "^RUT"
    name: "Russell 2000"

analysis:
  drop_increment: 5

storage:
  ath_path: "./data/ath_records.json"

email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true

logging:
  level: "INFO"
```

## Cron Scheduling

### System Cron with Docker

```bash
# Daily at 6 PM ET (23:00 UTC) - weekdays only
0 23 * * 1-5 docker run --rm \
    --name dca-alerts \
    --env-file /etc/dca-alerts/.env \
    -v /var/lib/dca-alerts/data:/data:rw \
    dca-alerts:latest >> /var/log/dca-alerts/cron.log 2>&1
```

### System Cron with Local Python

```bash
# Daily at 6 PM ET - weekdays only
0 18 * * 1-5 cd /path/to/market-metering && \
    .venv/bin/python -m dca_alerts.main >> /var/log/dca-alerts.log 2>&1
```

## Sample Output

```
=== DCA Market Alert - 2025-01-15 ===

S&P 500 (^GSPC)
  ATH:     6,000.00 (2025-01-10)
  Current: 5,700.00
  Gap:     -5.00%
  >>> BUY SIGNAL <<<

NASDAQ 100 (^NDX)
  ATH:     18,500.00 (2025-01-08)
  Current: 18,200.00
  Gap:     -1.62%
  HOLD - below 5% threshold

Russell 2000 (^RUT)
  ATH:     2,100.00 (2024-12-15)
  Current: 1,850.00
  Gap:     -11.90%
  >>> BUY SIGNAL (10% tier) <<<

ACTION REQUIRED: One or more indices have buy signals.
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success - all indices fetched, all notifications sent |
| `1` | Partial - some indices failed OR email failed |
| `2` | Failure - no market data retrieved OR critical error |

## Algorithm

The service implements a Dollar Cost Averaging (DCA) strategy based on market drops:

1. **Fetch current prices** for S&P 500, NASDAQ 100, and Russell 2000
2. **Load stored ATH** values from JSON file
3. **Analyze each index**:
   - If current price > stored ATH: Update ATH, recommend HOLD
   - If no stored ATH: Initialize with current price
   - Otherwise: Calculate gap from ATH
4. **Determine buy signal**:
   - Gap < 5%: HOLD
   - Gap >= 5%: BUY (tier = floor(gap / 5) * 5)
5. **Send notifications**: Console always, email if configured
6. **Persist updated ATH** values

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dca_alerts

# Run specific test file
pytest tests/test_analyzer.py -v
```

### Type Checking

```bash
mypy src/dca_alerts
```

### Linting

```bash
ruff check src/dca_alerts tests
ruff format src/dca_alerts tests
```

## License

MIT
