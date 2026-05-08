#!/usr/bin/env bash
# ============================================================
#  Dealer scraper — SSENSE / MEC / EVO / REI 每 6h 一次
#  Cron: 0 3,9,15,21 * * *   (UTC, 错开 outlet 的 0/6/12/18 三小时)
#  这样两个 scraper 不会同时跑，避免 EC2 OOM
# ============================================================
set -euo pipefail

PROJ_DIR="$HOME/arcteryx"
LOG="$PROJ_DIR/dealers.log"
PYTHON=python3.12

GITHUB_REPO="noir-madlax/001-arcteryx-deals-platform"

# Supabase service_role key — 与 server_run_update.sh 保持一致
export SUPABASE_URL="https://bupqagkrcvrezjkdbald.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjQ0NTU1MywiZXhwIjoyMDkyMDIxNTUzfQ.QPg4iHNEix_uB1Dlo6ONz2fBq59XhV9NZdEIsXc95_k"

if [ -f "$HOME/.arcteryx_secrets" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.arcteryx_secrets"
fi

cd "$PROJ_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "===== DEALERS START ====="

# pull latest code
git fetch origin main 2>&1 | tee -a "$LOG"
git reset --hard origin/main 2>&1 | tee -a "$LOG"

# 4 个 dealer 串行跑（EC2 1.6GB RAM 不够并行 + Camoufox/Chromium 开销大）
mkdir -p dealers/_partial
for d in mec evo rei ssense; do
    log "→ dealers.$d"
    if timeout 1800 $PYTHON -m dealers.$d >> "$LOG" 2>&1; then
        log "  ✓ $d done"
    else
        log "  ✗ $d failed (timeout 30 min or error)"
    fi
done

# 合并到 results.json
log "merge → results.json"
$PYTHON -m dealers.merge_partial 2>&1 | tee -a "$LOG"

# 同步到 Supabase（products 表 dealer 列）
log "sync → Supabase"
$PYTHON -m dealers.supabase_sync 2>&1 | tee -a "$LOG" || log "supabase sync 失败 (non-fatal)"

# 推到 GitHub（只 commit results.json，dealers/_partial/ 在 .gitignore）
log "git commit + push"
git config user.email "bot@arcteryx-deals.local"
git config user.name  "ArcBot"
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
git add dealers/results.json
if ! git diff --cached --quiet; then
    TS=$(date '+%Y-%m-%d %H:%M')
    git commit -m "data(dealers): auto refresh ${TS}" 2>&1 | tee -a "$LOG"
    git push origin main 2>&1 | tee -a "$LOG" || log "push failed (non-fatal)"
else
    log "no changes"
fi

log "===== DEALERS END ====="
