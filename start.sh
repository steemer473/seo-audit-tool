#!/bin/bash
set -e

echo "=== Installing Playwright browsers ==="
python -m playwright install chromium

echo "=== Installing Playwright system dependencies ==="
python -m playwright install-deps chromium || echo "Warning: Some system deps may have failed"

echo "=== Starting Uvicorn server ==="
uvicorn app:app --host 0.0.0.0 --port $PORT
