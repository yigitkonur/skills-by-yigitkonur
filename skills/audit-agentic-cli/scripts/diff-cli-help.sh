#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage: diff-cli-help.sh OLD_HELP_SNAPSHOT NEW_HELP_SNAPSHOT

Compare two captured help snapshots. The script does not invoke the live CLI.
It reports command and flag additions/removals plus likely breaking changes.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

OLD_FILE="${1:-}"
NEW_FILE="${2:-}"

if [[ -z "$OLD_FILE" || -z "$NEW_FILE" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -f "$OLD_FILE" ]]; then
  echo "Old snapshot not found: $OLD_FILE" >&2
  exit 2
fi

if [[ ! -f "$NEW_FILE" ]]; then
  echo "New snapshot not found: $NEW_FILE" >&2
  exit 2
fi

extract_flags() {
  grep -Eoh -- '--[A-Za-z0-9][A-Za-z0-9_-]*' "$1" | sort -u
}

extract_commands() {
  awk '
    BEGIN { in_commands = 0 }
    /^[[:space:]]*(Commands|Subcommands|Available Commands):[[:space:]]*$/ {
      in_commands = 1
      next
    }
    in_commands && /^[[:space:]]*$/ { next }
    in_commands && /^[[:space:]]*-/ { next }
    in_commands && /^[[:space:]]*[A-Za-z0-9][A-Za-z0-9:_-]+([[:space:],]|$)/ {
      cmd = $1
      sub(/,$/, "", cmd)
      print cmd
      next
    }
  ' "$1" | sort -u
}

extract_usage() {
  grep -Ei '^[[:space:]]*Usage:' "$1" | sed 's/[[:space:]]\+/ /g' | sort -u
}

print_list() {
  local title="$1"
  local file="$2"
  echo "## $title"
  echo
  if [[ ! -s "$file" ]]; then
    echo "- None detected."
  else
    while IFS= read -r item || [[ -n "$item" ]]; do
      echo "- \`$item\`"
    done < "$file"
  fi
  echo
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

extract_flags "$OLD_FILE" > "$TMP_DIR/old_flags"
extract_flags "$NEW_FILE" > "$TMP_DIR/new_flags"
extract_commands "$OLD_FILE" > "$TMP_DIR/old_commands"
extract_commands "$NEW_FILE" > "$TMP_DIR/new_commands"
extract_usage "$OLD_FILE" > "$TMP_DIR/old_usage"
extract_usage "$NEW_FILE" > "$TMP_DIR/new_usage"

comm -13 "$TMP_DIR/old_flags" "$TMP_DIR/new_flags" > "$TMP_DIR/added_flags"
comm -23 "$TMP_DIR/old_flags" "$TMP_DIR/new_flags" > "$TMP_DIR/removed_flags"
comm -13 "$TMP_DIR/old_commands" "$TMP_DIR/new_commands" > "$TMP_DIR/added_commands"
comm -23 "$TMP_DIR/old_commands" "$TMP_DIR/new_commands" > "$TMP_DIR/removed_commands"

echo "# CLI Help Diff"
echo
echo "| Field | Value |"
echo "|---|---|"
echo "| Old snapshot | \`$OLD_FILE\` |"
echo "| New snapshot | \`$NEW_FILE\` |"
echo

print_list "Command Additions" "$TMP_DIR/added_commands"
print_list "Command Removals" "$TMP_DIR/removed_commands"
print_list "Flag Additions" "$TMP_DIR/added_flags"
print_list "Flag Removals" "$TMP_DIR/removed_flags"

echo "## Likely Breaking Changes"
echo
breaking=0
while IFS= read -r item || [[ -n "$item" ]]; do
  [[ -z "$item" ]] && continue
  echo "- Removed command: \`$item\`"
  breaking=$((breaking + 1))
done < "$TMP_DIR/removed_commands"
while IFS= read -r item || [[ -n "$item" ]]; do
  [[ -z "$item" ]] && continue
  echo "- Removed flag: \`$item\`"
  breaking=$((breaking + 1))
done < "$TMP_DIR/removed_flags"
if ! diff -q "$TMP_DIR/old_usage" "$TMP_DIR/new_usage" >/dev/null 2>&1; then
  echo "- Usage line changed; inspect command grammar for positional or required-flag changes."
  breaking=$((breaking + 1))
fi
if [[ "$breaking" -eq 0 ]]; then
  echo "- None detected by this heuristic snapshot diff."
fi
