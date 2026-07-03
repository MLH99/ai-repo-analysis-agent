#!/bin/sh
set -e

if [ -z "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY saknas. Sätt den i .env eller docker-compose.yml."
  exit 1
fi

REPO_PATH="${REPO_PATH:-repo}"
INDEX_PATH="${INDEX_PATH:-data/faiss_index}"

has_repo_files() {
  find "$REPO_PATH" -type f \
    ! -path '*/.git/*' \
    ! -name '.gitkeep' \
    ! -name 'README.md' \
    2>/dev/null | head -n 1 | grep -q .
}

if has_repo_files; then
  if [ ! -d "$INDEX_PATH" ] || [ -z "$(ls -A "$INDEX_PATH" 2>/dev/null)" ]; then
    echo "FAISS-index saknas. Bygger index från ${REPO_PATH}..."
    python scripts/build_index.py --repo "$REPO_PATH" --index "$INDEX_PATH"
  fi
else
  echo "Varning: ${REPO_PATH} är tom."
  echo "Lägg in din kodbas i ./repo (se repo/README.md) och kör POST /index."
fi

echo "Startar API på http://0.0.0.0:8000"
exec uvicorn src.api.app:app --host 0.0.0.0 --port 8000
