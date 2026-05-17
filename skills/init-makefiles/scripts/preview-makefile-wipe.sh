#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
mode="${2:-table}"

if [ "$mode" != "table" ] && [ "$mode" != "--paths-only" ]; then
  printf 'usage: %s [project-root] [--paths-only]\n' "$0" >&2
  exit 2
fi

cd "$root"

is_git=0
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  is_git=1
fi

declare -a candidates=()

while IFS= read -r -d '' path; do
  case "$path" in
    ./Makefile|*/Makefile|./*.mk|*/*.mk|*/*/*.mk|*/scripts/dev.sh|*/scripts/deploy.sh|./make-*.sh|*/make-*.sh|*/*/make-*.sh)
      candidates+=("$path")
      ;;
  esac
done < <(
  find . -maxdepth 3 \
    \( -path './.git' \
    -o -path './node_modules' \
    -o -path './.pnpm-store' \
    -o -path './.yarn/cache' \
    -o -path './.yarn/unplugged' \
    -o -path './vendor' \
    -o -path './dist' \
    -o -path './build' \
    -o -path './coverage' \
    -o -path './.next' \
    -o -path './.turbo' \
    -o -path './.cache' \
    -o -path './.parcel-cache' \
    -o -path './.nuxt' \
    -o -path './.svelte-kit' \
    -o -path './target' \) -prune \
    -o -type f -print0
)

if [ "${#candidates[@]}" -eq 0 ]; then
  if [ "$mode" = "table" ]; then
    printf 'init-makefiles wipe preview (read-only)\n'
    printf 'root: %s\n\n' "$(pwd)"
    printf 'No candidate scaffold paths found.\n'
  fi
  exit 0
fi

sorted=$(
  for path in "${candidates[@]}"; do
    printf '%s\n' "$path"
  done | LC_ALL=C sort -u
)

reason_for() {
  case "$1" in
    ./Makefile) printf 'root Makefile' ;;
    */Makefile) printf 'nested Makefile within depth 3' ;;
    ./*.mk|*/*.mk|*/*/*.mk) printf 'mk include file within depth 3' ;;
    */scripts/dev.sh) printf 'legacy dev helper script' ;;
    */scripts/deploy.sh) printf 'legacy deploy helper script' ;;
    ./make-*.sh|*/make-*.sh|*/*/make-*.sh) printf 'legacy make helper script' ;;
    *) printf 'matched scaffold pattern' ;;
  esac
}

tracked_for() {
  if [ "$is_git" -ne 1 ]; then
    printf 'no-git'
    return
  fi
  if git ls-files --error-unmatch "$1" >/dev/null 2>&1; then
    printf 'tracked'
  else
    printf 'untracked'
  fi
}

status_for() {
  if [ "$is_git" -ne 1 ]; then
    printf 'not-a-git-repo'
    return
  fi
  status=$(git status --porcelain -- "$1")
  if [ -z "$status" ]; then
    printf 'clean'
  else
    printf '%s' "$status" | tr '\n' ';' | sed 's/;$//'
  fi
}

if [ "$mode" = "--paths-only" ]; then
  printf '%s\n' "$sorted"
  exit 0
fi

printf 'init-makefiles wipe preview (read-only)\n'
printf 'root: %s\n' "$(pwd)"
printf 'excludes: .git node_modules vendored caches build output\n\n'
printf '%-42s  %-34s  %-10s  %s\n' 'path' 'reason' 'tracked' 'git status'
printf '%-42s  %-34s  %-10s  %s\n' '----' '------' '-------' '----------'

while IFS= read -r path; do
  [ -n "$path" ] || continue
  printf '%-42s  %-34s  %-10s  %s\n' \
    "$path" \
    "$(reason_for "$path")" \
    "$(tracked_for "$path")" \
    "$(status_for "$path")"
done <<< "$sorted"
