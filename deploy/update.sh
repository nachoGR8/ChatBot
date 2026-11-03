#!/usr/bin/env bash
# Actualiza a la última versión de main y reinicia. Uso: bash update.sh
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
