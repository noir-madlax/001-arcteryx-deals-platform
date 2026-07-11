#!/usr/bin/env bash
# ============================================================
#  Dealer scraper — SSENSE / MEC / EVO / REI 每 6h 一次
#  Cron: 0 3,9,15,21 * * *   (UTC, 错开 outlet 的 0/6/12/18 三小时)
#  这样两个 scraper 不会同时跑，避免 EC2 OOM
# ============================================================
set -euo pipefail

PROJ_DIR="${PROJ_DIR:-$HOME/arcteryx}"
LOG="${LOG:-$PROJ_DIR/dealers.log}"
DEFAULT_PYTHON="$HOME/arcteryx-venv/bin/python"
if [ -x "$DEFAULT_PYTHON" ]; then
  PYTHON="${PYTHON:-$DEFAULT_PYTHON}"
else
  PYTHON="${PYTHON:-python3.12}"
fi

GITHUB_REMOTE="git@github.com:noir-madlax/001-arcteryx-deals-platform.git"

if [ -f "$HOME/.arcteryx_secrets" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.arcteryx_secrets"
fi
export SUPABASE_URL="${SUPABASE_URL:-https://bupqagkrcvrezjkdbald.supabase.co}"
: "${SUPABASE_KEY:?SUPABASE_KEY env required}"
export SUPABASE_KEY
export FEISHU_APP_ID="${FEISHU_APP_ID:-}"
export FEISHU_APP_SECRET="${FEISHU_APP_SECRET:-}"
export FEISHU_CHAT_ID="${FEISHU_CHAT_ID:-}"

cd "$PROJ_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

CRAWLER_NODE="${CRAWLER_NODE:-$(hostname)}"
LEASE_SCOPE="dealers"
LEASE_ACQUIRED=false
finish_lease() {
  exit_code=$?
  trap - EXIT
  if [ "$LEASE_ACQUIRED" = true ]; then
    if [ "$exit_code" -eq 0 ]; then
      "$PYTHON" tools/crawler_lease.py finish --scope "$LEASE_SCOPE" --owner "$CRAWLER_NODE" --status success >/dev/null 2>&1 || true
    else
      "$PYTHON" tools/crawler_lease.py finish --scope "$LEASE_SCOPE" --owner "$CRAWLER_NODE" --status failed --message "exit $exit_code" >/dev/null 2>&1 || true
    fi
  fi
  exit "$exit_code"
}
trap finish_lease EXIT

log "===== DEALERS START ====="

# pull latest code
git remote set-url origin "$GITHUB_REMOTE"
git fetch origin main 2>&1 | tee -a "$LOG"
git reset --hard origin/main 2>&1 | tee -a "$LOG"

lease_result=$($PYTHON tools/crawler_lease.py acquire --scope "$LEASE_SCOPE" --owner "$CRAWLER_NODE" --ttl-minutes 180)
if [ "$lease_result" != "true" ]; then
    log "Another node owns the Dealers lease; skipping this window"
    trap - EXIT
    exit 0
fi
LEASE_ACQUIRED=true

# 4 个 dealer 串行跑（EC2 1.6GB RAM 不够并行 + Camoufox/Chromium 开销大）
mkdir -p dealers/_partial
rm -f dealers/_partial/*.json
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

# 硬性质量闸门：避免 stale partial / 币种错误 / 折扣不一致继续被当作健康数据
log "data quality check"
$PYTHON tools/check_data_quality.py --online --dealer mec --dealer evo --dealer rei --dealer ssense --max-age-hours 36 --min-rows 50 2>&1 | tee -a "$LOG"

# 检查降价提醒
log "price alerts check"
$PYTHON check_price_alerts.py 2>&1 | tee -a "$LOG" || log "price alerts check 失败 (non-fatal)"

# 推到 GitHub（只 commit results.json，dealers/_partial/ 在 .gitignore）
log "git commit + push"
git config user.email "bot@arcteryx-deals.local"
git config user.name  "ArcBot"
git remote set-url origin "$GITHUB_REMOTE"
git add dealers/results.json
if ! git diff --cached --quiet; then
    TS=$(date '+%Y-%m-%d %H:%M')
    git commit -m "data(dealers): auto refresh ${TS}" 2>&1 | tee -a "$LOG"
    git push origin main 2>&1 | tee -a "$LOG" || log "push failed (non-fatal)"
else
    log "no changes"
fi

log "feishu notification"
$PYTHON notify_feishu.py --mode dealers 2>&1 | tee -a "$LOG" || log "feishu notification failed (non-fatal)"

log "===== DEALERS END ====="
