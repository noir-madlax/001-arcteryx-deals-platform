#!/usr/bin/env bash
set -euo pipefail

ROOT=${GEARDROP_ROOT:-/srv/geardrop}
SOURCE=${GEARDROP_SOURCE:-$ROOT/source}
REMOTE=${GEARDROP_REMOTE:-git@github.com:wantai-dev/001-arcteryx-deals-platform.git}
BRANCH=${GEARDROP_BRANCH:-main}
PRODUCT_SERVICE=${GEARDROP_PRODUCT_SERVICE:-geardrop-product.service}
PRODUCT_PORT=${GEARDROP_PRODUCT_PORT:-4181}
SMOKE_PORT=${GEARDROP_SMOKE_PORT:-4281}
LOCK_FILE=${GEARDROP_DEPLOY_LOCK:-$ROOT/deploy.lock}

if [ ! -d "$SOURCE/.git" ]; then
  echo "Dedicated source clone is missing: $SOURCE" >&2
  exit 1
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another GearDrop deployment is already running"
  exit 0
fi

git -C "$SOURCE" remote set-url origin "$REMOTE"
git -C "$SOURCE" fetch --quiet origin "$BRANCH"
REVISION=$(git -C "$SOURCE" rev-parse FETCH_HEAD^{commit})
CURRENT_REVISION=""
if [ -s "$ROOT/current/REVISION" ]; then
  CURRENT_REVISION=$(tr -d '[:space:]' < "$ROOT/current/REVISION")
fi

if [ "$REVISION" = "$CURRENT_REVISION" ]; then
  echo "already_current=$REVISION"
  exit 0
fi

# This checkout is deployment-owned and never used by the crawler.
git -C "$SOURCE" checkout --quiet --detach --force "$REVISION"
git -C "$SOURCE" reset --quiet --hard "$REVISION"

RELEASE="$ROOT/releases/$REVISION"
if [ ! -d "$RELEASE" ]; then
  "$SOURCE/ops/web/build-release.sh" "$RELEASE" "$REVISION"
fi

TMP_BODY=$(mktemp)
TMP_LOG=$(mktemp)
SMOKE_PID=""
cleanup() {
  if [ -n "$SMOKE_PID" ] && kill -0 "$SMOKE_PID" 2>/dev/null; then
    kill "$SMOKE_PID" 2>/dev/null || true
    wait "$SMOKE_PID" 2>/dev/null || true
  fi
  rm -f "$TMP_BODY" "$TMP_LOG"
}
trap cleanup EXIT INT TERM

GEARDROP_PRODUCT_PORT="$SMOKE_PORT" \
  /usr/bin/node "$RELEASE/ops/web/product-server.mjs" >"$TMP_LOG" 2>&1 &
SMOKE_PID=$!

READY=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS "http://127.0.0.1:$SMOKE_PORT/healthz" >/dev/null; then
    READY=1
    break
  fi
  sleep 0.5
done
if [ "$READY" -ne 1 ]; then
  echo "Candidate product service did not become ready" >&2
  sed -n '1,120p' "$TMP_LOG" >&2
  exit 1
fi

INVALID_STATUS=$(curl -sS -o /dev/null -w '%{http_code}' \
  "http://127.0.0.1:$SMOKE_PORT/p?sku=invalid%20sku")
if [ "$INVALID_STATUS" != "404" ]; then
  echo "Candidate invalid-SKU smoke returned $INVALID_STATUS" >&2
  exit 1
fi

SAMPLE_LOC=$(grep -m 1 '<loc>https://001\.100app\.dev/' \
  "$RELEASE/static/sitemap-products.xml" || true)
SAMPLE_PATH=$(printf '%s\n' "$SAMPLE_LOC" \
  | sed -n 's#.*<loc>https://001\.100app\.dev\([^<]*\)</loc>.*#\1#p')
if [ -z "$SAMPLE_PATH" ]; then
  echo "Product sitemap did not contain a canonical sample" >&2
  exit 1
fi
SAMPLE_STATUS=$(curl -sS -o "$TMP_BODY" -w '%{http_code}' \
  "http://127.0.0.1:$SMOKE_PORT$SAMPLE_PATH")
if [ "$SAMPLE_STATUS" != "200" ] || ! grep -q '<link rel="canonical"' "$TMP_BODY"; then
  echo "Candidate product smoke failed: status=$SAMPLE_STATUS path=$SAMPLE_PATH" >&2
  exit 1
fi

kill "$SMOKE_PID" 2>/dev/null || true
wait "$SMOKE_PID" 2>/dev/null || true
SMOKE_PID=""

PREVIOUS_LINK=""
if [ -L "$ROOT/current" ]; then
  PREVIOUS_LINK=$(readlink "$ROOT/current")
fi
NEXT_LINK="$ROOT/current.next.$$"
ln -s "releases/$REVISION" "$NEXT_LINK"
mv -Tf "$NEXT_LINK" "$ROOT/current"

rollback() {
  echo "Rolling back failed release $REVISION" >&2
  if [ -n "$PREVIOUS_LINK" ]; then
    ln -s "$PREVIOUS_LINK" "$NEXT_LINK"
    mv -Tf "$NEXT_LINK" "$ROOT/current"
    sudo -n systemctl restart "$PRODUCT_SERVICE" || true
  else
    rm -f "$ROOT/current"
    sudo -n systemctl stop "$PRODUCT_SERVICE" || true
  fi
}

if ! sudo -n systemctl restart "$PRODUCT_SERVICE"; then
  rollback
  exit 1
fi

LIVE=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS "http://127.0.0.1:$PRODUCT_PORT/healthz" >/dev/null; then
    LIVE=1
    break
  fi
  sleep 0.5
done
if [ "$LIVE" -ne 1 ]; then
  rollback
  exit 1
fi

LIVE_STATUS=$(curl -sS -o "$TMP_BODY" -w '%{http_code}' \
  "http://127.0.0.1:$PRODUCT_PORT$SAMPLE_PATH")
if [ "$LIVE_STATUS" != "200" ] || ! grep -q '<link rel="canonical"' "$TMP_BODY"; then
  rollback
  exit 1
fi

# Pick up deploy-script improvements only after the new release passes.
sudo -n install -m 0755 "$SOURCE/ops/web/deploy-server.sh" \
  /usr/local/libexec/geardrop-deploy-server

echo "deployed=$REVISION previous=${CURRENT_REVISION:-none}"
