#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 path/to/script.py|script.sh [args...]" >&2
  exit 2
fi

script_path=$1
shift

if [[ ! -f "$script_path" ]]; then
  echo "FAIL $script_path: file does not exist" >&2
  exit 1
fi

mode=$(
  sed -n '1,80s/^[[:space:]]*#[[:space:]]*@raycast\.mode[[:space:]]*\(.*\)$/\1/p' "$script_path" |
    head -n 1
)

if [[ -z "$mode" ]]; then
  mode="unknown"
fi

stdout_file=$(mktemp)
stderr_file=$(mktemp)
trap 'rm -f "$stdout_file" "$stderr_file"' EXIT

set +e
if [[ -x "$script_path" ]]; then
  "$script_path" "$@" >"$stdout_file" 2>"$stderr_file"
else
  shebang=$(head -n 1 "$script_path")
  interpreter=${shebang#\#!}
  if [[ "$interpreter" == "$shebang" || -z "$interpreter" ]]; then
    echo "FAIL $script_path: no shebang found" >&2
    exit 1
  fi
  read -r -a interpreter_parts <<<"$interpreter"
  "${interpreter_parts[@]}" "$script_path" "$@" >"$stdout_file" 2>"$stderr_file"
fi
exit_code=$?
set -e

first_stdout_line=$(sed -n '1p' "$stdout_file")
last_stdout_line=$(sed -n '${p;}' "$stdout_file")

case "$mode" in
  fullOutput)
    display=$(cat "$stdout_file")
    display_label="full stdout"
    ;;
  compact)
    display=$last_stdout_line
    display_label="last stdout line"
    ;;
  silent)
    display=$last_stdout_line
    display_label="last stdout line if present"
    ;;
  inline)
    display=$first_stdout_line
    display_label="first stdout line"
    ;;
  *)
    display=$last_stdout_line
    display_label="unknown mode; showing last stdout line"
    ;;
esac

echo "Display-contract preview"
echo "- script: $script_path"
echo "- mode: $mode"
echo "- exit_code: $exit_code"
echo "- display_source: $display_label"
echo
echo "Raycast-relevant display:"
if [[ -n "$display" ]]; then
  printf '%s\n' "$display"
else
  echo "(empty)"
fi

if [[ $exit_code -ne 0 ]]; then
  echo
  echo "Non-zero exit behavior:"
  echo "- Raycast treats this as a failure."
  echo "- For compact and inline, Raycast uses the last output line as the error message."
fi

if [[ -s "$stderr_file" ]]; then
  echo
  echo "stderr:"
  cat "$stderr_file"
fi
