#!/usr/bin/env bash
# MEC scraper — runs on OCI because MEC currently blocks the Lightsail AWS egress.
set -euo pipefail

PROJ_DIR="${PROJ_DIR:-$HOME/arcteryx}"
LOG="${LOG:-$PROJ_DIR/mec.log}"
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
LEASE_SCOPE="mec"
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

log "===== MEC START ====="
git remote set-url origin "$GITHUB_REMOTE"
git fetch origin main 2>&1 | tee -a "$LOG"
git reset --hard origin/main 2>&1 | tee -a "$LOG"

lease_result=$($PYTHON tools/crawler_lease.py acquire --scope "$LEASE_SCOPE" --owner "$CRAWLER_NODE" --ttl-minutes 90)
if [ "$lease_result" != "true" ]; then
  log "Another node owns the MEC lease; skipping this window"
  trap - EXIT
  exit 0
fi
LEASE_ACQUIRED=true

mkdir -p dealers/_partial
rm -f dealers/_partial/*.json
log "scrape → dealers.mec"
timeout 1800 "$PYTHON" -u -m dealers.mec 2>&1 | tee -a "$LOG"

# A successful process with an empty/partial challenge response must not publish.
"$PYTHON" - <<'PY'
import json
from pathlib import Path

path = Path("dealers/_partial/mec.json")
if not path.exists():
    raise SystemExit("MEC partial missing")
payload = json.loads(path.read_text())
count = len(payload.get("items") or [])
if payload.get("crawl_complete") is not True:
    raise SystemExit(f"MEC crawl incomplete: {count}/{payload.get('expected_count') or '?'}")
if count < 50:
    raise SystemExit(f"MEC partial too small: {count} < 50")
expected = payload.get("expected_count")
if expected is not None and count < expected:
    raise SystemExit(f"MEC parsed count below expected: {count} < {expected}")
print(f"[mec] partial gate OK: {count}/{expected or '?'} items")
PY

log "merge → results.json"
"$PYTHON" -m dealers.merge_partial 2>&1 | tee -a "$LOG"
log "sync → Supabase"
"$PYTHON" -m dealers.supabase_sync 2>&1 | tee -a "$LOG"
log "data quality check"
"$PYTHON" tools/check_data_quality.py --online --dealer mec --max-age-hours 36 --min-rows 50 2>&1 | tee -a "$LOG"

log "git commit + push"
git config user.email "bot@arcteryx-deals.local"
git config user.name "ArcBot"
git add dealers/results.json
if ! git diff --cached --quiet; then
  TS=$(date '+%Y-%m-%d %H:%M')
  git commit -m "data(mec): auto refresh ${TS}" 2>&1 | tee -a "$LOG"
  git pull --rebase origin main 2>&1 | tee -a "$LOG"
  git push origin main 2>&1 | tee -a "$LOG"
else
  log "no changes"
fi

"$PYTHON" notify_feishu.py --mode dealers 2>&1 | tee -a "$LOG" || log "feishu notification failed (non-fatal)"
log "===== MEC END ====="
