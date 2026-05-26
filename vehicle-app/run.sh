#!/usr/bin/env bash
# Family Vehicle Browser — startup script (macOS / Linux)
#
# Run from anywhere:
#   bash vehicle-app/run.sh                  # uses default ../user-kaan-and-tess
#   VEHICLE_DATA_DIR=../user-other bash vehicle-app/run.sh
#   PORT=5500 bash vehicle-app/run.sh        # pin a port

set -e
cd "$(dirname "$0")"
SKILL_DIR="$(pwd)"

# --- Data directory -------------------------------------------------------
# Default to the kaan-and-tess folder beside vehicle-app/. Anything outside
# this skill folder is treated as the per-family inputs + outputs.
if [ -z "$VEHICLE_DATA_DIR" ]; then
  export VEHICLE_DATA_DIR="$(cd .. && pwd)/user-kaan-and-tess"
fi
if [ ! -d "$VEHICLE_DATA_DIR" ]; then
  echo "ERROR: VEHICLE_DATA_DIR=$VEHICLE_DATA_DIR does not exist."
  exit 1
fi
if [ ! -f "$VEHICLE_DATA_DIR/vehicles.json" ]; then
  echo "ERROR: $VEHICLE_DATA_DIR/vehicles.json missing — can't load candidate list."
  exit 1
fi

# --- Python ---------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.9+ and try again."
  exit 1
fi

# --- Venv -----------------------------------------------------------------
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $SKILL_DIR/$VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# --- Dependencies ---------------------------------------------------------
if ! "$PY" -c "import flask, requests, bs4, PIL" &>/dev/null; then
  echo "Installing dependencies..."
  "$PIP" install -q -r requirements.txt
fi

# --- Images ---------------------------------------------------------------
IMAGE_COUNT=$(find "$VEHICLE_DATA_DIR/images" -name "*.jpg" 2>/dev/null | wc -l | tr -d ' ')
if [ "$IMAGE_COUNT" -lt 12 ]; then
  if [ -f "$VEHICLE_DATA_DIR/image_seeds.json" ]; then
    echo "Downloading vehicle images (one-time, ~1 min)..."
    "$PY" scrapers/fetch_images.py
  else
    echo "NOTE: $VEHICLE_DATA_DIR/image_seeds.json not present; app will run with placeholder galleries."
  fi
fi

# --- Port -----------------------------------------------------------------
# macOS uses port 5000 for AirPlay Receiver. Pick the first free port.
pick_port() {
  for p in "$@"; do
    if ! lsof -nP -iTCP:"$p" -sTCP:LISTEN &>/dev/null; then
      echo "$p"
      return
    fi
  done
}
PORT="${PORT:-$(pick_port 5000 5057 5500 8080)}"
if [ -z "$PORT" ]; then
  echo "ERROR: no free port found (tried 5000, 5057, 5500, 8080). Set PORT=<n> and re-run."
  exit 1
fi
export PORT

# --- Run ------------------------------------------------------------------
echo
echo "Starting Family Vehicle Browser on http://localhost:$PORT"
echo "Data: $VEHICLE_DATA_DIR"
echo "Ctrl+C to stop."
echo
exec "$PY" app.py
