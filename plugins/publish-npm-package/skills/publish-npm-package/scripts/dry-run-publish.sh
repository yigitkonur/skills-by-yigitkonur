#!/usr/bin/env bash
set -euo pipefail

package_dir="."
run_publish="0"
access_flag=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --publish)
      run_publish="1"
      shift
      ;;
    --access)
      if [[ $# -lt 2 ]]; then
        echo "ERROR --access requires a value" >&2
        exit 2
      fi
      access_flag=(--access "$2")
      shift 2
      ;;
    -h|--help)
      sed -n '1,120p' "$(dirname "$0")/dry-run-publish.md"
      exit 0
      ;;
    *)
      package_dir="$1"
      shift
      ;;
  esac
done

cd "$package_dir"

if [[ ! -f package.json ]]; then
  echo "ERROR package.json not found in $(pwd)" >&2
  exit 1
fi

echo "== npm pack --dry-run =="
npm pack --dry-run

if [[ "$run_publish" == "1" ]]; then
  echo "== npm publish --dry-run =="
  npm publish --dry-run "${access_flag[@]}"
else
  echo "Skipped npm publish --dry-run. Pass --publish to run it."
fi

echo "No package was published."
