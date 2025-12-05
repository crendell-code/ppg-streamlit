#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "Removing .streamlit..."
rm -rf .streamlit

echo "Removing 'streamlit' from requirements.txt (if present)..."
if [ -f requirements.txt ]; then
  sed -i '' '/streamlit/d' requirements.txt 2>/dev/null || sed -i '/streamlit/d' requirements.txt
fi

read -p "Remove .venv (delete local virtualenv)? [y/N]: " yn
if [[ "$yn" =~ ^[Yy]$ ]]; then
  echo "Removing .venv..."
  rm -rf .venv
fi

echo "Done."
