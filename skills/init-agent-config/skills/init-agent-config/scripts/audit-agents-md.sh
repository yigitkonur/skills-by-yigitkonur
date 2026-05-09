#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage: audit-agents-md.sh [repo-root]

Read-only audit of AGENTS-first instruction surfaces in a repository.
Defaults to the current directory.
EOF
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
esac

root=${1:-.}
if [ ! -d "$root" ]; then
  echo "error: repo root is not a directory: $root" >&2
  exit 2
fi

cd "$root"

find_pruned() {
  find . \( -path './.git' -o -path './node_modules' -o -path './.venv' -o -path './vendor' \) -prune -o "$@" -print | sort
}

print_section() {
  printf '\n## %s\n' "$1"
}

print_line_count() {
  file=$1
  if [ -f "$file" ] || [ -L "$file" ]; then
    count=$(wc -l < "$file" 2>/dev/null || printf '?')
    printf '%7s  %s\n' "$count" "$file"
  fi
}

classify_claude() {
  file=$1
  if [ -L "$file" ]; then
    target=$(ls -ld "$file" | sed 's/.* -> //')
    printf 'symlink -> %s' "$target"
    return
  fi

  first=$(sed -n '/[^[:space:]]/{s/^[[:space:]]*//;s/[[:space:]]*$//;p;q;}' "$file" 2>/dev/null || true)
  case "$first" in
    '@AGENTS.md'|'See AGENTS.md'*|'See `AGENTS.md`'*)
      printf 'wrapper'
      ;;
    *)
      printf 'independent'
      ;;
  esac
}

agents=$(find_pruned -name 'AGENTS.md')
claudes=$(find_pruned -name 'CLAUDE.md')
reviews=$(find_pruned -name 'REVIEW.md')

echo "# AGENTS.md Instruction Surface Audit"
printf 'Repo: %s\n' "$(pwd)"

print_section "AGENTS.md files"
if [ -n "$agents" ]; then
  printf '%s\n' "$agents"
else
  echo "none"
fi

print_section "CLAUDE.md files"
if [ -n "$claudes" ]; then
  printf '%s\n' "$claudes" | while IFS= read -r file; do
    printf '%s  [%s]\n' "$file" "$(classify_claude "$file")"
  done
else
  echo "none"
fi

print_section "REVIEW.md files"
if [ -n "$reviews" ]; then
  printf '%s\n' "$reviews"
else
  echo "none"
fi

print_section "Native surfaces"
for path in \
  './.claude' \
  './GEMINI.md' \
  './.cursor' \
  './.cursorrules' \
  './.github/copilot-instructions.md' \
  './.github/instructions' \
  './.greptile' \
  './greptile.json'
do
  if [ -e "$path" ] || [ -L "$path" ]; then
    echo "$path"
  fi
done

print_section "Line counts"
{
  printf '%s\n' "$agents"
  printf '%s\n' "$claudes"
  printf '%s\n' "$reviews"
  find_pruned -name 'GEMINI.md'
  find_pruned -name '.cursorrules'
  find_pruned -path './.github/copilot-instructions.md'
  find_pruned -path './greptile.json'
} | sed '/^$/d' | sort -u | while IFS= read -r file; do
  print_line_count "$file"
done

print_section "Likely stale duplicate source-of-truth risks"
risk=0

if [ -n "$claudes" ]; then
  old_ifs=$IFS
  IFS='
'
  for file in $claudes; do
    kind=$(classify_claude "$file")
    dir=$(dirname "$file")
    if [ "$kind" = "independent" ] && [ -e "$dir/AGENTS.md" ]; then
      printf 'risk: %s is independent beside %s/AGENTS.md\n' "$file" "$dir"
      risk=1
    fi
  done
  IFS=$old_ifs
fi

for native in './.github/copilot-instructions.md' './.github/instructions' './.greptile' './greptile.json'; do
  if [ -e "$native" ] && [ -z "$reviews" ]; then
    printf 'risk: %s exists without a shared REVIEW.md layer\n' "$native"
    risk=1
  fi
done

if [ -z "$agents" ] && { [ -n "$claudes" ] || [ -e './.cursorrules' ] || [ -e './GEMINI.md' ]; }; then
  echo "risk: native instruction files exist without AGENTS.md as shared source of truth"
  risk=1
fi

independent_count=0
if [ -n "$claudes" ]; then
  independent_count=$(printf '%s\n' "$claudes" | while IFS= read -r file; do classify_claude "$file"; echo; done | grep -c '^independent$' || true)
fi

if [ "$independent_count" -gt 1 ]; then
  printf 'risk: %s independent CLAUDE.md files may drift from AGENTS.md\n' "$independent_count"
  risk=1
fi

if [ "$risk" -eq 0 ]; then
  echo "none detected by heuristic checks"
fi
