#!/bin/bash
set -e

echo "=== Setting Playwright browsers path ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

echo "=== Installing Playwright Chromium browser ==="
python -m playwright install chromium

echo "=== Starting Uvicorn server ==="
uvicorn app:app --host 0.0.0.0 --port $PORT
