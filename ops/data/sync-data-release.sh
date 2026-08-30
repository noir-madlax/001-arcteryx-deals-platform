#!/usr/bin/env bash
set -euo pipefail

ROOT=${GEARDROP_ROOT:-/srv/geardrop}
SOURCE=${GEARDROP_SOURCE:-$ROOT/source}
DATA_ROOT=${GEARDROP_DATA_ROOT:-$ROOT/data}
LOCK_FILE=${GEARDROP_DATA_LOCK:-$ROOT/data-sync.lock}
DEPLOY_LOCK=${GEARDROP_DEPLOY_LOCK:-$ROOT/deploy.lock}
KEEP_RELEASES=${GEARDROP_DATA_KEEP_RELEASES:-12}

if [ ! -d "$SOURCE/.git" ]; then
  echo "Dedicated source clone is missing: $SOURCE" >&2
  exit 1
fi

mkdir -p "$DATA_ROOT/releases"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another GearDrop data sync is already running"
  exit 0
fi
exec 8>"$DEPLOY_LOCK"
flock 8

CODE_REVISION=$(tr -d '[:space:]' < "$ROOT/current/REVISION")
STAGING=$(mktemp -d "$DATA_ROOT/.stage.XXXXXX")
cleanup() {
  if [ -n "${STAGING:-}" ] && [ -d "$STAGING" ]; then
    rm -rf -- "$STAGING"
  fi
}
trap cleanup EXIT INT TERM

GEARDROP_CODE_REVISION="$CODE_REVISION" \
  /usr/bin/node "$SOURCE/ops/data/build-data-release.mjs" --output "$STAGING"
DATA_REVISION=$(tr -d '[:space:]' < "$STAGING/DATA_REVISION")
if [[ ! "$DATA_REVISION" =~ ^[a-f0-9]{20}$ ]]; then
  echo "Invalid data revision: $DATA_REVISION" >&2
  exit 1
fi

RELEASE="$DATA_ROOT/releases/$DATA_REVISION"
if [ -d "$RELEASE" ]; then
  if ! cmp -s "$STAGING/MANIFEST.json" "$RELEASE/MANIFEST.json"; then
    echo "Data revision collision: $DATA_REVISION" >&2
    exit 1
  fi
else
  mv "$STAGING" "$RELEASE"
  STAGING=""
fi

for required in \
  public/data.js \
  public/data.js.gz \
  public/dealers/results.json \
  public/dealers/results.json.gz \
  public/sitemap-products.xml \
  public/publication.json \
  public/data-manifest.json \
  MANIFEST.json; do
  if [ ! -s "$RELEASE/$required" ]; then
    echo "Data release is missing: $required" >&2
    exit 1
  fi
done
if ! gzip -cd "$RELEASE/public/data.js.gz" | cmp -s - "$RELEASE/public/data.js"; then
  echo "Compressed data.js does not match its source" >&2
  exit 1
fi

NEXT_LINK="$DATA_ROOT/current.next.$$"
ln -s "releases/$DATA_REVISION" "$NEXT_LINK"
mv -Tf "$NEXT_LINK" "$DATA_ROOT/current"

/usr/bin/node "$SOURCE/ops/data/prune-data-releases.mjs" "$DATA_ROOT" "$KEEP_RELEASES"

READBACK_REVISION=$(tr -d '[:space:]' < "$DATA_ROOT/current/DATA_REVISION")
if [ "$READBACK_REVISION" != "$DATA_REVISION" ]; then
  echo "Data release readback mismatch: $READBACK_REVISION != $DATA_REVISION" >&2
  exit 1
fi

echo "data_current=$DATA_REVISION code_revision=$CODE_REVISION"
