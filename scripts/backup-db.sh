#!/bin/bash
# EsportsForge Database Backup Script
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/tmp/esportsforge-backups}"
mkdir -p "$BACKUP_DIR"

if [[ "$DATABASE_URL" == *"sqlite"* ]]; then
    DB_FILE=$(echo "$DATABASE_URL" | sed 's|.*:///||')
    cp "$DB_FILE" "$BACKUP_DIR/esportsforge_${TIMESTAMP}.db"
    echo "SQLite backup: $BACKUP_DIR/esportsforge_${TIMESTAMP}.db"
else
    BACKUP_FILE="$BACKUP_DIR/esportsforge_${TIMESTAMP}.sql"
    pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
    echo "PostgreSQL backup: $BACKUP_FILE"
fi

# Prune backups older than 30 days
find "$BACKUP_DIR" -name "esportsforge_*" -mtime +30 -delete 2>/dev/null || true
echo "Backup complete."
