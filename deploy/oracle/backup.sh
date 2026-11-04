#!/usr/bin/env bash
# Backup diário do Postgres (inclui o banco da Evolution API). Mantém 14 dias.
# Agende:  0 3 * * *  /caminho/do/projeto/deploy/oracle/backup.sh
# Copie também a pasta backups/ para FORA da VM (ex.: rclone para um Drive).
set -euo pipefail
cd "$(dirname "$0")/../.."
set -a; . ./.env; set +a

DEST="backups"
mkdir -p "$DEST"; chmod 700 "$DEST"
umask 077
ARQ="$DEST/pg_$(date +%Y%m%d_%H%M%S).sql.gz"

docker exec postgres_db pg_dumpall -U "$POSTGRES_USER" | gzip > "$ARQ"
[ -s "$ARQ" ] || { echo "backup vazio, abortando" >&2; rm -f "$ARQ"; exit 1; }
find "$DEST" -name 'pg_*.sql.gz' -mtime +14 -delete
echo "backup ok: $ARQ"
