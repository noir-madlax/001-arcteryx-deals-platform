#!/usr/bin/env bash
# Dealer URL Revalidator — 每天复检已知 URL 价格
# Cron: 30 6 * * *  (UTC 06:30, 错开 outlet 06:00 + dealer 03/09/15/21)
set -euo pipefail

PROJ_DIR="$HOME/arcteryx"
LOG="$PROJ_DIR/revalidate.log"
PYTHON=python3.12

export SUPABASE_URL="https://bupqagkrcvrezjkdbald.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjQ0NTU1MywiZXhwIjoyMDkyMDIxNTUzfQ.QPg4iHNEix_uB1Dlo6ONz2fBq59XhV9NZdEIsXc95_k"

cd "$PROJ_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "===== REVALIDATE START ====="
git fetch origin main 2>&1 | tee -a "$LOG"
git reset --hard origin/main 2>&1 | tee -a "$LOG"

timeout 3600 $PYTHON -m dealers.revalidate 2>&1 | tee -a "$LOG" || log "revalidate timeout/error (non-fatal)"

log "===== REVALIDATE END ====="
