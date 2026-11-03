#!/usr/bin/env bash
# Copia la base de datos (negocios, FAQs, conversaciones) a deploy/backups/. Uso: bash backup.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p backups
file="backups/chatbot-$(date +%Y%m%d-%H%M%S).db"
# Copia consistente aunque el servidor esté escribiendo (API de backup de SQLite).
docker compose exec -T chatbot python -c "
import sqlite3
src = sqlite3.connect('/data/chatbot.db'); dst = sqlite3.connect('/tmp/backup.db')
src.backup(dst); dst.close(); src.close()"
docker compose cp chatbot:/tmp/backup.db "$file"
docker compose exec -T chatbot rm -f /tmp/backup.db
echo "Copia guardada en $file"
# shellcheck disable=SC2012  # los nombres los genera este script
ls -1t backups/*.db | tail -n +15 | xargs -r rm --   # conserva las 14 últimas
