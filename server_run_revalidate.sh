#!/usr/bin/env bash
# Dealer URL Revalidator — 每天复检已知 URL 价格
# Cron: 30 6 * * *  (UTC 06:30, 错开 outlet 06:00 + dealer 03/09/15/21)
set -euo pipefail

PROJ_DIR="${PROJ_DIR:-$HOME/arcteryx}"
LOG="${LOG:-$PROJ_DIR/revalidate.log}"
DEFAULT_PYTHON="$HOME/arcteryx-venv/bin/python"
if [ -x "$DEFAULT_PYTHON" ]; then
  PYTHON="${PYTHON:-$DEFAULT_PYTHON}"
else
  PYTHON="${PYTHON:-python3.12}"
fi

if [ -f "$HOME/.arcteryx_secrets" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.arcteryx_secrets"
fi
export SUPABASE_URL="${SUPABASE_URL:-https://bupqagkrcvrezjkdbald.supabase.co}"
: "${SUPABASE_KEY:?SUPABASE_KEY env required}"
export SUPABASE_KEY

cd "$PROJ_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "===== REVALIDATE START ====="
git fetch origin main 2>&1 | tee -a "$LOG"
git reset --hard origin/main 2>&1 | tee -a "$LOG"

timeout 3600 $PYTHON -m dealers.revalidate 2>&1 | tee -a "$LOG" || log "revalidate timeout/error (non-fatal)"

log "===== REVALIDATE END ====="
