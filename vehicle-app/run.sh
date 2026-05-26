#!/usr/bin/env bash
# BC Family Vehicle Browser — startup script (macOS / Linux)
# Run from anywhere: bash vehicle-app/run.sh

set -e
cd "$(dirname "$0")"

# --- Python ----------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.9+ and try again."
  exit 1
fi

# --- Venv ------------------------------------------------------------------
# Use a project-local venv so we never touch system Python (and don't need
# pip's --break-system-packages escape hatch on macOS / newer Linux).
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# --- Dependencies ----------------------------------------------------------
if ! "$PY" -c "import flask, requests, bs4, PIL" &>/dev/null; then
  echo "Installing dependencies..."
  "$PIP" install -q -r requirements.txt
fi

# --- Images ----------------------------------------------------------------
IMAGE_COUNT=$(find images -name "*.jpg" 2>/dev/null | wc -l | tr -d ' ')
if [ "$IMAGE_COUNT" -lt 12 ]; then
  if [ -f "data/image_seeds.json" ]; then
    echo "Downloading vehicle images (one-time, ~1 min)..."
    "$PY" scrapers/fetch_images.py
  else
    echo "NOTE: data/image_seeds.json not present; app will run with placeholder galleries."
  fi
fi

# --- Port ------------------------------------------------------------------
# macOS uses port 5000 for AirPlay Receiver. Pick the first free port from
# the user's PORT env var, then 5000, then a fallback.
pick_port() {
  for p in "$@"; do
    if ! lsof -nP -iTCP:"$p" -sTCP:LISTEN &>/dev/null; then
      echo "$p"
      return
    fi
  done
  echo ""
}
PORT="${PORT:-$(pick_port 5000 5057 5500 8080)}"
if [ -z "$PORT" ]; then
  echo "ERROR: no free port found (tried 5000, 5057, 5500, 8080). Set PORT=<n> and re-run."
  exit 1
fi
export PORT

# --- Run -------------------------------------------------------------------
echo
echo "Starting BC Family Vehicle Browser on http://localhost:$PORT"
echo "Ctrl+C to stop."
echo
exec "$PY" app.py
