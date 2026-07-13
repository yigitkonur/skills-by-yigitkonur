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
  find . \( -path './.git' -o -path '*/.claude/worktrees' -o -name 'node_modules' -o -name '.venv' -o -name 'venv' -o -name 'vendor' -o -name '__pycache__' -o -name 'dist' -o -name 'target' -o -name 'DerivedData' -o -name 'Pods' \) -prune -o "$@" -print | sort
}

# Source files under a directory, with build/dependency noise pruned.
# Extend the extension list rather than removing prunes.
src_find() {
  find "$1" \( -path '*/.*' -o -name 'node_modules' -o -name '.venv' -o -name 'venv' -o -name 'vendor' -o -name '__pycache__' -o -name 'dist' -o -name 'build' -o -name 'out' -o -name 'target' -o -name 'coverage' -o -name 'DerivedData' -o -name 'Pods' \) -prune -o -type f \( \
    -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.mjs' -o -name '*.cjs' \
    -o -name '*.py' -o -name '*.rs' -o -name '*.go' -o -name '*.swift' -o -name '*.kt' -o -name '*.java' \
    -o -name '*.rb' -o -name '*.php' -o -name '*.c' -o -name '*.h' -o -name '*.cpp' -o -name '*.hpp' \
    -o -name '*.cs' -o -name '*.m' -o -name '*.mm' -o -name '*.vue' -o -name '*.svelte' -o -name '*.sql' \
  \) -print
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
    '@AGENTS.md'|'@./AGENTS.md'|'@../AGENTS.md'|'See AGENTS.md'*|'See `AGENTS.md`'*)
      printf 'wrapper'
      ;;
    *)
      nonblank=$(grep -c '[^[:space:]]' "$file" 2>/dev/null || printf '0')
      if [ "$nonblank" -le 5 ] && grep -Eq 'AGENTS\.md' "$file" 2>/dev/null; then
        printf 'wrapper'
      else
        printf 'independent'
      fi
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

print_section "Folder coverage map"
echo "Code-bearing directories (depth <= 2) vs. their nearest own AGENTS.md."
echo "src-files/LOC counted recursively with build+dependency noise pruned."
printf '%-40s %9s %9s  %s\n' "DIRECTORY" "SRC-FILES" "SRC-LOC" "AGENTS.md"
coverage_dirs=$( { echo .; find . -mindepth 1 -maxdepth 2 -type d \
  ! -name '.*' ! -path './.*' ! -path '*/.*' \
  ! -name 'node_modules' ! -name 'vendor' ! -name 'venv' ! -name '__pycache__' \
  ! -name 'dist' ! -name 'build' ! -name 'out' ! -name 'target' ! -name 'coverage' \
  ! -name 'DerivedData' ! -name 'Pods' ! -name 'docs' ! -name 'doc' \
  ! -name 'assets' ! -name 'images' ! -name 'public' ! -name 'static' ! -name 'fixtures'; } | sort)
printf '%s\n' "$coverage_dirs" | while IFS= read -r dir; do
  [ -d "$dir" ] || continue
  files=$(src_find "$dir" | wc -l | tr -d ' ')
  [ "$files" -eq 0 ] && continue
  loc=$(src_find "$dir" | tr '\n' '\0' | xargs -0 cat 2>/dev/null | wc -l | tr -d ' ')
  if [ -f "$dir/AGENTS.md" ]; then
    marker="yes ($(wc -l < "$dir/AGENTS.md" | tr -d ' ') lines)"
  else
    marker="—"
  fi
  printf '%-40s %9s %9s  %s\n' "$dir" "$files" "$loc" "$marker"
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
    printf 'check: %s exists without REVIEW.md; add shared review context only if review standards are in scope, otherwise document the skip reason\n' "$native"
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
