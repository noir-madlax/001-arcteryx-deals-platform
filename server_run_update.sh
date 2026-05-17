#!/usr/bin/env bash
# ============================================================
#  Arc'teryx full update — runs on EC2 server
#  Cron: 0 6,12,18,0 * * *
# ============================================================
set -euo pipefail

PROJ_DIR="$HOME/arcteryx"
LOG_FILE="$PROJ_DIR/update.log"
PYTHON="python3"

export SUPABASE_URL="https://bupqagkrcvrezjkdbald.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjQ0NTU1MywiZXhwIjoyMDkyMDIxNTUzfQ.QPg4iHNEix_uB1Dlo6ONz2fBq59XhV9NZdEIsXc95_k"

GITHUB_REPO="noir-madlax/001-arcteryx-deals-platform"
# GITHUB_TOKEN is sourced from ~/.arcteryx_secrets below

# ── Telegram notification credentials ──
# Kept in ~/.arcteryx_secrets (NOT committed to git) so we don't leak tokens.
# That file should contain:
#   export TELEGRAM_BOT_TOKEN="..."
#   export TELEGRAM_CHAT_ID="..."
if [ -f "$HOME/.arcteryx_secrets" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.arcteryx_secrets"
fi
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

cd "$PROJ_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# Record run start time (used by notify_telegram.py for duration)
date -u '+%Y-%m-%d %H:%M:%S' > "$PROJ_DIR/.last_run_start"

log "===== UPDATE START ====="

# 1. Refresh product list
log "Step 1: Global scraper (product list)"
$PYTHON global_scraper.py 2>&1 | tee -a "$LOG_FILE"

# 2. Playwright scrape (full re-scrape)
log "Step 2: Playwright scrape"
$PYTHON sku_scraper.py --reset 2>&1 | tee -a "$LOG_FILE"

# 3. Sync to Supabase (authoritative data store)
log "Step 3: Supabase sync"
$PYTHON supabase_sync.py 2>&1 | tee -a "$LOG_FILE"

# 4. Push data files to GitHub (backup + Vercel static fallback)
log "Step 4: GitHub sync + push"
git config user.email "bot@arcteryx-deals.local"
git config user.name  "ArcBot"
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"

TMPDIR=$(mktemp -d)
for f in data.js arcteryx_skus.json global_data.json; do
  [ -f "$f" ] && cp "$f" "$TMPDIR/$f"
done

git fetch origin main 2>&1 | tee -a "$LOG_FILE"
# Discard any local tracked changes + switch to clean main (data files are in TMPDIR)
git reset --hard HEAD 2>&1 | tee -a "$LOG_FILE" || true
git checkout -B main origin/main 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE"
# Remove untracked files that would conflict (but preserve state files)
git clean -fd -e .last_run_start -e .last_sync -e .sku_progress.json -e update.log -e update_global.log -e dealers.log -e dealers/_partial -e .arcteryx_secrets 2>&1 | tee -a "$LOG_FILE" || true

for f in data.js arcteryx_skus.json global_data.json; do
  [ -f "$TMPDIR/$f" ] && cp "$TMPDIR/$f" "$f"
done
rm -rf "$TMPDIR"

git add data.js arcteryx_skus.json global_data.json
if ! git diff --cached --quiet; then
  git commit -m "data: auto update $(date '+%Y-%m-%d %H:%M')"
  git push origin main 2>&1 | tee -a "$LOG_FILE" || log "git push failed (non-fatal)"
else
  log "No data changes to commit"
fi

# 5. 检查降价提醒订阅 (price_alerts) 并发邮件
log "Step 5: Price alerts check"
$PYTHON check_price_alerts.py 2>&1 | tee -a "$LOG_FILE" || log "price alerts check failed (non-fatal)"

# 6. Telegram notification with stats report
log "Step 6: Telegram notification"
$PYTHON notify_telegram.py 2>&1 | tee -a "$LOG_FILE" || log "telegram notification failed (non-fatal)"

log "===== UPDATE DONE ====="
