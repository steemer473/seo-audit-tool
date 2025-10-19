#!/bin/bash
set -e

echo "=== Upgrading pip ==="
pip install --upgrade pip

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Installing Playwright Chromium ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.browsers
python -m playwright install chromium

echo "=== Installing Playwright system dependencies ==="
python -m playwright install-deps chromium || echo "Warning: Some system deps may not have installed"

echo "=== Verifying Playwright installation ==="
python -m playwright --version
ls -la /opt/render/project/.browsers/ || echo "Browsers directory not found!"

echo "=== Build complete! ==="
