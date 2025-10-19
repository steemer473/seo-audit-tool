#!/bin/bash
set -e

echo "=== Verifying Playwright browsers are installed ==="
python -m playwright install chromium --dry-run || python -m playwright install chromium

echo "=== Starting Uvicorn server ==="
uvicorn app:app --host 0.0.0.0 --port $PORT
