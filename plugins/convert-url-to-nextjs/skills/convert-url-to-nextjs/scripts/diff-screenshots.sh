#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  diff-screenshots.sh --route ROUTE --source SRC --build BUILD --viewport NAME [--out DIR] [--threshold FLOAT] [--known-drift TEXT]
  diff-screenshots.sh --route ROUTE --source-dir DIR --build-dir DIR [--out DIR] [--threshold FLOAT] [--known-drift TEXT]

Compares source/build screenshots and writes:
  .design-soul/visual/{route}/summary.json

ImageMagick is used when available. If no comparator is installed, the script
writes a structured summary with comparatorAvailable=false and no fake metric.
Missing required image pairs always exit nonzero.
EOF
}

route=""
source_file=""
build_file=""
viewport=""
source_dir=""
build_dir=""
out=""
threshold=""
known_drift=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --route)
      route="${2:-}"
      shift 2
      ;;
    --source)
      source_file="${2:-}"
      shift 2
      ;;
    --build)
      build_file="${2:-}"
      shift 2
      ;;
    --viewport)
      viewport="${2:-}"
      shift 2
      ;;
    --source-dir)
      source_dir="${2:-}"
      shift 2
      ;;
    --build-dir)
      build_dir="${2:-}"
      shift 2
      ;;
    --out)
      out="${2:-}"
      shift 2
      ;;
    --threshold)
      threshold="${2:-}"
      shift 2
      ;;
    --known-drift)
      known_drift="${2:-}"
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

if [ -z "$route" ]; then
  echo "--route is required" >&2
  usage >&2
  exit 64
fi

case "$route" in
  *[!a-z0-9-]*)
    echo "--route must be kebab-case: $route" >&2
    exit 64
    ;;
esac

if [ -z "$out" ]; then
  out=".design-soul/visual/$route"
fi
mkdir -p "$out"

pairs_file=$(mktemp)
results_file=$(mktemp)
missing_file=$(mktemp)
trap 'rm -f "$pairs_file" "$results_file" "$missing_file"' EXIT

if [ -n "$source_file" ] || [ -n "$build_file" ]; then
  if [ -z "$source_file" ] || [ -z "$build_file" ] || [ -z "$viewport" ]; then
    echo "--source, --build, and --viewport must be supplied together" >&2
    exit 64
  fi
  printf '%s\t%s\t%s\n' "$viewport" "$source_file" "$build_file" > "$pairs_file"
else
  if [ -z "$source_dir" ] || [ -z "$build_dir" ]; then
    echo "Use either explicit --source/--build/--viewport or --source-dir/--build-dir" >&2
    exit 64
  fi
  if [ ! -d "$source_dir" ]; then
    echo "Source directory not found: $source_dir" >&2
    exit 66
  fi
  if [ ! -d "$build_dir" ]; then
    echo "Build directory not found: $build_dir" >&2
    exit 66
  fi
  while IFS= read -r src; do
    base=$(basename "$src")
    suffix="${base%.png}"
    if printf '%s' "$suffix" | grep -q '^source-'; then
      suffix="${suffix#source-}"
      build_candidate="$build_dir/build-$suffix.png"
    else
      build_candidate="$build_dir/$base"
    fi
    printf '%s\t%s\t%s\n' "$suffix" "$src" "$build_candidate" >> "$pairs_file"
  done < <(find "$source_dir" -type f -name '*.png' | sort)
fi

if [ ! -s "$pairs_file" ]; then
  echo "No source screenshots found" >&2
  exit 65
fi

comparator=""
if command -v magick >/dev/null 2>&1; then
  comparator="magick"
elif command -v compare >/dev/null 2>&1; then
  comparator="compare"
fi

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

compare_pair() {
  src="$1"
  build="$2"
  diff_path="$3"
  if [ -z "$comparator" ]; then
    printf 'null\tmissing-comparator\tfalse\n'
    return 0
  fi

  metric_file=$(mktemp)
  set +e
  if [ "$comparator" = "magick" ]; then
    magick compare -metric RMSE "$src" "$build" "$diff_path" 2>"$metric_file"
    code=$?
  else
    compare -metric RMSE "$src" "$build" "$diff_path" 2>"$metric_file"
    code=$?
  fi
  set -e

  metric=$(cat "$metric_file" | tr -d '\n')
  rm -f "$metric_file"

  if [ "$code" -gt 1 ]; then
    rm -f "$diff_path"
    printf '%s\tcompare-error\ttrue\n' "$(json_escape "$metric")"
    return 0
  fi

  if [ -n "$threshold" ]; then
    normalized=$(printf '%s' "$metric" | sed -n 's/.*(\([0-9.][0-9.]*\)).*/\1/p')
    if [ -z "$normalized" ]; then
      status="measured-no-normalized-metric"
    elif awk "BEGIN { exit !($normalized <= $threshold) }"; then
      status="pass"
    else
      status="fail"
    fi
  else
    status="measured-no-threshold"
  fi

  printf '%s\t%s\ttrue\n' "$(json_escape "$metric")" "$status"
}

while IFS=$'\t' read -r pair_viewport src build; do
  if [ ! -s "$src" ]; then
    printf '%s\t%s\n' "$pair_viewport" "$src" >> "$missing_file"
    continue
  fi
  if [ ! -s "$build" ]; then
    printf '%s\t%s\n' "$pair_viewport" "$build" >> "$missing_file"
    continue
  fi

  diff_path="$out/diff-$pair_viewport.png"
  IFS=$'\t' read -r metric status comparator_available < <(compare_pair "$src" "$build" "$diff_path")
  if [ "$comparator_available" != "true" ] || [ ! -s "$diff_path" ]; then
    diff_json="null"
  else
    diff_json="\"$(json_escape "$diff_path")\""
  fi

  pass_json="null"
  if [ "$status" = "pass" ]; then
    pass_json="true"
  elif [ "$status" = "fail" ]; then
    pass_json="false"
  fi

  printf '{"route":"%s","viewport":"%s","sourceScreenshot":"%s","buildScreenshot":"%s","diffArtifact":%s,"comparatorAvailable":%s,"measuredMetric":%s,"knownDrift":"%s","status":"%s","pass":%s}\n' \
    "$(json_escape "$route")" \
    "$(json_escape "$pair_viewport")" \
    "$(json_escape "$src")" \
    "$(json_escape "$build")" \
    "$diff_json" \
    "$comparator_available" \
    "$(if [ "$metric" = "null" ]; then printf 'null'; else printf '"%s"' "$metric"; fi)" \
    "$(json_escape "$known_drift")" \
    "$(json_escape "$status")" \
    "$pass_json" >> "$results_file"
done < "$pairs_file"

summary="$out/summary.json"

if [ -s "$missing_file" ]; then
  {
    printf '{\n'
    printf '  "route": "%s",\n' "$(json_escape "$route")"
    printf '  "status": "missing-required-pairs",\n'
    printf '  "pairs": [],\n'
    printf '  "missing": [\n'
    count=$(wc -l < "$missing_file" | tr -d ' ')
    index=0
    while IFS=$'\t' read -r missing_viewport missing_path; do
      index=$((index + 1))
      comma=","
      if [ "$index" -eq "$count" ]; then
        comma=""
      fi
      printf '    {"viewport": "%s", "path": "%s"}%s\n' "$(json_escape "$missing_viewport")" "$(json_escape "$missing_path")" "$comma"
    done < "$missing_file"
    printf '  ]\n'
    printf '}\n'
  } > "$summary"
  echo "Missing required screenshot pairs; see $summary" >&2
  exit 65
fi

overall_status="measured"
if grep -q '"status":"fail"' "$results_file"; then
  overall_status="fail"
elif grep -q '"status":"missing-comparator"' "$results_file"; then
  overall_status="missing-comparator"
elif grep -q '"status":"measured-no-threshold"' "$results_file"; then
  overall_status="measured-no-threshold"
elif grep -q '"status":"compare-error"' "$results_file"; then
  overall_status="compare-error"
elif grep -q '"status":"pass"' "$results_file"; then
  overall_status="pass"
fi

{
  printf '{\n'
  printf '  "route": "%s",\n' "$(json_escape "$route")"
  printf '  "status": "%s",\n' "$overall_status"
  printf '  "threshold": %s,\n' "$(if [ -n "$threshold" ]; then printf '"%s"' "$(json_escape "$threshold")"; else printf 'null'; fi)"
  printf '  "pairs": [\n'
  count=$(wc -l < "$results_file" | tr -d ' ')
  index=0
  while IFS= read -r row; do
    index=$((index + 1))
    comma=","
    if [ "$index" -eq "$count" ]; then
      comma=""
    fi
    printf '    %s%s\n' "$row" "$comma"
  done < "$results_file"
  printf '  ],\n'
  printf '  "missing": []\n'
  printf '}\n'
} > "$summary"

echo "Visual summary: $summary"
