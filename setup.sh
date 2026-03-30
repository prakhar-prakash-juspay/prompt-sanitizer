#!/usr/bin/env bash
set -e

echo "=== Prompt Sanitizer — Local Setup ==="
echo ""

# Find Python 3.11+
PYTHON=""
for cmd in python3.12 python3.11 python3; do
  if command -v "$cmd" &>/dev/null; then
    version=$("$cmd" -c "import sys; print(sys.version_info[:2])")
    major=$("$cmd" -c "import sys; print(sys.version_info[0])")
    minor=$("$cmd" -c "import sys; print(sys.version_info[1])")
    if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "Error: Python 3.11+ is required."
  echo "Install with: brew install python@3.12 (macOS) or apt install python3.12 (Linux)"
  exit 1
fi

echo "Using $PYTHON ($($PYTHON --version))"

# Create venv
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv .venv
fi

source .venv/bin/activate

# Install
echo "Installing dependencies..."
pip install -q -e ".[dev]"

# spaCy model
if ! python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
  echo "Downloading spaCy model..."
  python -m spacy download en_core_web_sm -q
fi

# Setup config
echo "Running prompt-sanitizer setup..."
prompt-sanitizer setup --skip-shell

echo ""
echo "=== Setup complete ==="
echo ""
echo "To start the proxy:"
echo "  source .venv/bin/activate"
echo "  prompt-sanitizer start"
echo ""
echo "Then set your agent's base URL:"
echo "  export ANTHROPIC_BASE_URL=http://localhost:8443/anthropic"
echo "  export OPENAI_BASE_URL=http://localhost:8443/openai"
echo ""
echo "Log viewer: http://localhost:8443/viewer"
