#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  capture-url.sh --url URL [--route ROUTE] [--root ROOT] [--browser-command CMD]

Creates .design-soul/capture/{route}/ with the expected Capture Wave folders and
manifests. If --browser-command or BROWSER_CAPTURE_CMD is set, the command runs
with capture paths exported in the environment and the script verifies that the
required artifacts exist before returning success.

Environment exported to the browser command:
  CAPTURE_URL
  CAPTURE_ROUTE
  CAPTURE_DIR
  DOM_PATH
  HEADINGS_PATH
  RUNTIME_METADATA_PATH
  ASSETS_PATH
  MIRROR_DIR
  SCREENSHOTS_DIR

The script never writes done.signal. The executor writes signals only after the
Capture Wave gate passes.
EOF
}

url=""
route=""
root="."
browser_command="${BROWSER_CAPTURE_CMD:-}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --url)
      url="${2:-}"
      shift 2
      ;;
    --route)
      route="${2:-}"
      shift 2
      ;;
    --root)
      root="${2:-}"
      shift 2
      ;;
    --browser-command)
      browser_command="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [ -z "$url" ]; then
  echo "--url is required" >&2
  usage >&2
  exit 64
fi

if [ -z "$route" ]; then
  route=$(printf '%s' "$url" |
    sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##; s#[?#].*$##; s#/$##; s#[^a-zA-Z0-9]+#-#g; s#^-+##; s#-+$##' |
    tr '[:upper:]' '[:lower:]')
fi

if [ -z "$route" ]; then
  route="homepage"
fi

case "$route" in
  *[!a-z0-9-]*)
    echo "--route must be kebab-case: $route" >&2
    exit 64
    ;;
esac

capture_dir="$root/.design-soul/capture/$route"
mirror_dir="$capture_dir/mirror"
screenshots_dir="$capture_dir/screenshots"

mkdir -p \
  "$mirror_dir/css" \
  "$mirror_dir/js" \
  "$mirror_dir/fonts" \
  "$mirror_dir/images" \
  "$screenshots_dir"

cat > "$capture_dir/expected-artifacts.json" <<EOF
{
  "url": "$url",
  "route": "$route",
  "captureDir": "$capture_dir",
  "required": {
    "dom": "$capture_dir/dom.html",
    "headings": "$capture_dir/headings.json",
    "runtimeMetadata": "$capture_dir/runtime-metadata.json",
    "assets": "$capture_dir/assets.json",
    "mirror": "$mirror_dir",
    "screenshots": "$screenshots_dir"
  },
  "screenshots": {
    "desktop": "$screenshots_dir/desktop-full.png",
    "tablet": "$screenshots_dir/tablet-full.png",
    "mobile": "$screenshots_dir/mobile-full.png"
  },
  "status": "pending-browser-capture"
}
EOF

cat > "$capture_dir/capture-handoff.md" <<EOF
# Capture Handoff: $route

- URL: $url
- Route: $route
- Capture directory: $capture_dir
- Preferred helper: run-agent-browser
- Fallback helper: run-playwright only when explicitly requested, run-agent-browser is unavailable, or an existing Playwright CLI session is already active.

Required outputs:
- $capture_dir/dom.html
- $capture_dir/headings.json
- $capture_dir/runtime-metadata.json
- $capture_dir/assets.json
- $mirror_dir/
- $screenshots_dir/desktop-full.png
- $screenshots_dir/tablet-full.png
- $screenshots_dir/mobile-full.png

Do not create done.signal until the Capture Wave gate passes.
EOF

if [ -z "$browser_command" ]; then
  echo "Prepared capture skeleton at $capture_dir"
  echo "No browser command supplied; run browser capture with run-agent-browser or an approved fallback and leave done.signal unwritten."
  exit 0
fi

export CAPTURE_URL="$url"
export CAPTURE_ROUTE="$route"
export CAPTURE_DIR="$capture_dir"
export DOM_PATH="$capture_dir/dom.html"
export HEADINGS_PATH="$capture_dir/headings.json"
export RUNTIME_METADATA_PATH="$capture_dir/runtime-metadata.json"
export ASSETS_PATH="$capture_dir/assets.json"
export MIRROR_DIR="$mirror_dir"
export SCREENSHOTS_DIR="$screenshots_dir"

status_path="$capture_dir/capture-status.json"

set +e
sh -c "$browser_command"
code=$?
set -e

if [ "$code" -ne 0 ]; then
  cat > "$status_path" <<EOF
{
  "url": "$url",
  "route": "$route",
  "status": "browser-command-failed",
  "exitCode": $code
}
EOF
  echo "Browser capture command failed; see $status_path" >&2
  exit "$code"
fi

missing=0
for path in "$DOM_PATH" "$HEADINGS_PATH" "$RUNTIME_METADATA_PATH" "$ASSETS_PATH"; do
  if [ ! -s "$path" ]; then
    echo "Missing required capture artifact: $path" >&2
    missing=1
  fi
done

if ! find "$screenshots_dir" -type f -name '*.png' | grep -q .; then
  echo "Missing screenshots: expected at least one PNG under $screenshots_dir" >&2
  missing=1
fi

if [ "$missing" -ne 0 ]; then
  cat > "$status_path" <<EOF
{
  "url": "$url",
  "route": "$route",
  "status": "browser-command-incomplete",
  "note": "The command exited successfully but required capture artifacts were missing."
}
EOF
  exit 65
fi

cat > "$status_path" <<EOF
{
  "url": "$url",
  "route": "$route",
  "status": "capture-artifacts-present",
  "note": "Gate review still required before writing done.signal."
}
EOF

echo "Capture artifacts present at $capture_dir"
