#!/usr/bin/env bash
# ============================================================
#  Arc'teryx full update — runs on EC2 server
#  Cron: 0 6,12,18,0 * * *
# ============================================================
set -euo pipefail

PROJ_DIR="$HOME/arcteryx"
LOG_FILE="$PROJ_DIR/update.log"
PYTHON="python3"

# ── Supabase credentials (set these before first run) ────────
export SUPABASE_URL="YOUR_SUPABASE_URL"
export SUPABASE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"

# ── GitHub credentials (for pushing data.js backup) ─────────
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
GITHUB_REPO="noir-madlax/001-arcteryx-deals-platform"

cd "$PROJ_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "===== UPDATE START ====="

# 1. Run Playwright scraper (full re-scrape)
log "Step 1: Playwright scrape"
$PYTHON sku_scraper.py --reset 2>&1 | tee -a "$LOG_FILE"

# 2. Sync to Supabase
log "Step 2: Supabase sync"
$PYTHON supabase_sync.py 2>&1 | tee -a "$LOG_FILE"

# 3. Push data.js to GitHub as backup
log "Step 3: GitHub push"
git -C "$PROJ_DIR" config user.email "bot@arcteryx-deals.local"
git -C "$PROJ_DIR" config user.name  "ArcBot"
git -C "$PROJ_DIR" add data.js arcteryx_skus.json global_data.json
git -C "$PROJ_DIR" commit -m "data: auto update $(date '+%Y-%m-%d %H:%M')" || true
git -C "$PROJ_DIR" remote set-url origin \
    "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
git -C "$PROJ_DIR" push origin main 2>&1 | tee -a "$LOG_FILE" || log "git push failed (non-fatal)"

log "===== UPDATE DONE ====="
