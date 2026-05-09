#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  extract-styles.sh --html PATH --asset-root DIR [--out DIR]

Detects the strongest CSS corpus for a saved page or captured route, then writes:
  css-corpus-manifest.json
  inline-styles.css            (when <style> blocks exist)
  custom-properties.txt
  font-summary.txt
  media-queries.txt
  keyframes.txt

Supported evidence:
  - adjacent {page}_files directories
  - local CSS files referenced by the HTML
  - inline <style> blocks / SingleFile exports
  - mirrored live-capture CSS under the supplied asset root
EOF
}

html=""
asset_root=""
out=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --html)
      html="${2:-}"
      shift 2
      ;;
    --asset-root)
      asset_root="${2:-}"
      shift 2
      ;;
    --out)
      out="${2:-}"
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

if [ -z "$html" ] || [ -z "$asset_root" ]; then
  echo "--html and --asset-root are required" >&2
  usage >&2
  exit 64
fi

if [ ! -f "$html" ]; then
  echo "HTML file not found: $html" >&2
  exit 66
fi

if [ ! -d "$asset_root" ]; then
  echo "Asset root not found: $asset_root" >&2
  exit 66
fi

html_dir=$(cd "$(dirname "$html")" && pwd)
html_abs="$html_dir/$(basename "$html")"
html_base=$(basename "$html")
html_stem="${html_base%.*}"

if [ -z "$out" ]; then
  out=".design-soul/wave0/$html_stem/style-corpus"
fi

mkdir -p "$out"

tmp_css_list=$(mktemp)
tmp_reasons=$(mktemp)
trap 'rm -f "$tmp_css_list" "$tmp_reasons"' EXIT

add_css() {
  css_path="$1"
  reason="$2"
  if [ -f "$css_path" ]; then
    css_abs=$(cd "$(dirname "$css_path")" && pwd)/$(basename "$css_path")
    printf '%s\n' "$css_abs" >> "$tmp_css_list"
    printf '%s\t%s\n' "$css_abs" "$reason" >> "$tmp_reasons"
  fi
}

snapshot_dir="$html_dir/${html_stem}_files"
if [ -d "$snapshot_dir" ]; then
  while IFS= read -r css; do
    add_css "$css" "_files snapshot"
  done < <(find "$snapshot_dir" -type f -name '*.css' | sort)
fi

perl -ne 'while (/href=["'\'']([^"'\'']+\.css[^"'\'']*)["'\'']/gi) { print "$1\n" }' "$html_abs" |
  sed 's/[?#].*$//' |
  while IFS= read -r href; do
    case "$href" in
      http://*|https://*|//*|data:*|'')
        continue
        ;;
      /*)
        candidate="$asset_root$href"
        ;;
      *)
        candidate="$html_dir/$href"
        ;;
    esac
    add_css "$candidate" "html stylesheet href"
  done

if [ -d "$asset_root/css" ]; then
  while IFS= read -r css; do
    add_css "$css" "mirrored live-capture css"
  done < <(find "$asset_root/css" -type f -name '*.css' | sort)
fi

while IFS= read -r css; do
  add_css "$css" "asset-root css"
done < <(find "$asset_root" -type f -name '*.css' | sort)

inline_css="$out/inline-styles.css"
perl -0777 -ne 'while (m{<style\b[^>]*>(.*?)</style>}gis) { print "$1\n\n" }' "$html_abs" > "$inline_css"
if [ -s "$inline_css" ]; then
  add_css "$inline_css" "inline style block"
else
  rm -f "$inline_css"
fi

sort -u "$tmp_css_list" > "$out/css-files.txt"

if [ ! -s "$out/css-files.txt" ]; then
  cat > "$out/css-corpus-manifest.json" <<EOF
{
  "html": "$html_abs",
  "assetRoot": "$asset_root",
  "cssFiles": [],
  "status": "no-css-corpus-found"
}
EOF
  echo "No CSS corpus found for $html_abs" >&2
  exit 65
fi

hash_file() {
  path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$path" | awk '{print $1}'
  else
    cksum "$path" | awk '{print $1}'
  fi
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

reason_for() {
  grep -F "$1	" "$tmp_reasons" | cut -f2- | sort -u | paste -sd ', ' -
}

manifest="$out/css-corpus-manifest.json"
{
  printf '{\n'
  printf '  "html": "%s",\n' "$(json_escape "$html_abs")"
  printf '  "assetRoot": "%s",\n' "$(json_escape "$asset_root")"
  printf '  "cssFiles": [\n'
  count=$(wc -l < "$out/css-files.txt" | tr -d ' ')
  index=0
  while IFS= read -r css; do
    index=$((index + 1))
    comma=","
    if [ "$index" -eq "$count" ]; then
      comma=""
    fi
    bytes=$(wc -c < "$css" | tr -d ' ')
    hash=$(hash_file "$css")
    reason=$(reason_for "$css")
    printf '    {"path": "%s", "bytes": %s, "sha256": "%s", "reason": "%s"}%s\n' \
      "$(json_escape "$css")" "$bytes" "$(json_escape "$hash")" "$(json_escape "$reason")" "$comma"
  done < "$out/css-files.txt"
  printf '  ],\n'
  printf '  "status": "css-corpus-ready"\n'
  printf '}\n'
} > "$manifest"

mapfile -t css_files < "$out/css-files.txt"

grep -hEo -- '--[a-zA-Z0-9_-]+\s*:\s*[^;}]+' "${css_files[@]}" | sort -u > "$out/custom-properties.txt" || true

{
  echo "# @font-face blocks"
  perl -0777 -ne 'while (m{@font-face\s*\{.*?\}}gis) { print "$&\n\n" }' "${css_files[@]}" || true
  echo "# font-family declarations"
  grep -hEo 'font-family\s*:\s*[^;}]+' "${css_files[@]}" | sort | uniq -c | sort -rn || true
  echo "# font urls"
  grep -hEo 'url\([^)]+\)' "${css_files[@]}" | grep -Ei '\.(woff2?|ttf|otf|eot)' | sort -u || true
  echo "# font-display declarations"
  grep -hEo 'font-display\s*:\s*[^;}]+' "${css_files[@]}" | sort -u || true
} > "$out/font-summary.txt"

grep -hEo '@media[^{]+' "${css_files[@]}" | sort -u > "$out/media-queries.txt" || true
grep -hEo '@keyframes[[:space:]]+[-_a-zA-Z0-9]+' "${css_files[@]}" | sort -u > "$out/keyframes.txt" || true

echo "CSS corpus manifest: $manifest"
echo "CSS files: $out/css-files.txt"
echo "Summaries: $out/custom-properties.txt, $out/font-summary.txt, $out/media-queries.txt, $out/keyframes.txt"
