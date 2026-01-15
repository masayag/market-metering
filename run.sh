#!/bin/bash

# Simple DCA Alerts Runner
# Quick wrapper for the most common use case

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if .env exists
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Load environment and run
echo "🚀 Loading .env configuration and running DCA Market Drop Alert Service..."
echo

# Source environment variables
set -a
source "$SCRIPT_DIR/.env"
set +a

# Activate virtual environment and run the service
source "$SCRIPT_DIR/.venv/bin/activate"
exec python -m dca_alerts.main "$@"