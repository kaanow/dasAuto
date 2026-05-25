#!/bin/bash
# BC Family Vehicle Browser — startup script
# Run from the vehicle-app directory: bash run.sh

set -e
cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌  python3 not found. Install Python 3.10+ and try again."
  exit 1
fi

# Install dependencies if needed
if ! python3 -c "import flask, requests, bs4, PIL" &>/dev/null 2>&1; then
  echo "📦  Installing dependencies..."
  pip install -r requirements.txt --break-system-packages -q
fi

# Warn if no images yet
IMAGE_COUNT=$(find images -name "*.jpg" 2>/dev/null | wc -l | tr -d ' ')
if [ "$IMAGE_COUNT" -lt 12 ]; then
  echo "⚠   Only $IMAGE_COUNT images found."
  echo "    Run this first for full image galleries:"
  echo "    python3 scrapers/fetch_images.py"
  echo ""
fi

echo "🚗  Starting BC Family Vehicle Browser..."
echo "    http://localhost:5000"
echo "    Ctrl+C to stop"
echo ""
python3 app.py
