#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  cluster-files.sh < paths.txt
  cluster-files.sh --base BASE --head HEAD
EOF
}

base=""
head=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base)
      base="${2:-}"
      shift 2
      ;;
    --head)
      head="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -n "$base" ] || [ -n "$head" ]; then
  if [ -z "$base" ] || [ -z "$head" ]; then
    printf 'error: --base and --head must be provided together\n' >&2
    exit 2
  fi
  command -v git >/dev/null 2>&1 || {
    printf 'error: git is required for --base/--head mode\n' >&2
    exit 127
  }
  mapfile -t paths < <(git diff --name-only "$base...$head")
else
  mapfile -t paths
fi

declare -a data=()
declare -a security=()
declare -a api=()
declare -a core=()
declare -a frontend=()
declare -a infra=()
declare -a config=()
declare -a docs=()
declare -a tests=()
declare -a types=()
declare -a other=()

add_path() {
  local bucket="$1"
  local path="$2"
  case "$bucket" in
    data) data+=("$path") ;;
    security) security+=("$path") ;;
    api) api+=("$path") ;;
    core) core+=("$path") ;;
    frontend) frontend+=("$path") ;;
    infra) infra+=("$path") ;;
    config) config+=("$path") ;;
    docs) docs+=("$path") ;;
    tests) tests+=("$path") ;;
    types) types+=("$path") ;;
    other) other+=("$path") ;;
  esac
}

classify() {
  local path="$1"
  local lower
  lower="$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    *"/__tests__/"*|*"__tests__/"*|*"tests/"*|*"test/"*|*"spec/"*|*.test.*|*.spec.*|*_test.*|test_*|*tests.*)
      add_path tests "$path"
      return
      ;;
    *"/types/"*|*"/interfaces/"*|*.d.ts|*"schema.ts"|*"schemas/"*)
      add_path types "$path"
      return
      ;;
    *"/migrations/"*|*"/migrate/"*|*"/seeds/"*|*"/fixtures/"*|*"schema"*|*.sql|*"/prisma/"*|*"/drizzle/"*|*"/alembic/"*|*"/flyway/"*)
      add_path data "$path"
      return
      ;;
    *"/auth/"*|*"/security/"*|*"/permissions/"*|*"/rbac/"*|*"guard"*|*"policy"*|*"middleware"*)
      add_path security "$path"
      return
      ;;
    *"/api/"*|*"/routes/"*|*"/controllers/"*|*"/handlers/"*|*"/endpoints/"*|*"/graphql/"*|*"/resolvers/"*)
      add_path api "$path"
      return
      ;;
    *"/services/"*|*"/domain/"*|*"/core/"*|*"/lib/"*|*"/utils/"*|*"/models/"*|*"/helpers/"*)
      add_path core "$path"
      return
      ;;
    *"/components/"*|*"/pages/"*|*"/views/"*|*"/layouts/"*|*"/hooks/"*|*"/stores/"*|*.tsx|*.jsx|*.css|*.scss|*.sass|*.vue|*.svelte)
      add_path frontend "$path"
      return
      ;;
    dockerfile*|*"/dockerfile"*|docker-compose*|".github/"*|*"/.github/"*|*"/ci/"*|*"/deploy/"*|terraform/*|k8s/*|helm/*|*.tf|*.yaml|*.yml)
      add_path infra "$path"
      return
      ;;
    *.config.*|*.env*|package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|tsconfig*|*.toml|pyproject.toml|cargo.toml|go.mod|go.sum)
      add_path config "$path"
      return
      ;;
    *.md|*"/docs/"*|docs/*|changelog*|readme*|license*|*.txt)
      add_path docs "$path"
      return
      ;;
    *)
      add_path other "$path"
      ;;
  esac
}

for path in "${paths[@]}"; do
  [ -n "$path" ] || continue
  classify "$path"
done

print_bucket() {
  local title="$1"
  shift
  local items=("$@")
  [ "${#items[@]}" -gt 0 ] || return 0
  printf '\n### %s (%s)\n' "$title" "${#items[@]}"
  local item
  for item in "${items[@]}"; do
    printf -- '- `%s`\n' "$item"
  done
}

total=0
for path in "${paths[@]}"; do
  [ -n "$path" ] && total=$((total + 1))
done

printf '# File Cluster Map\n\n'
printf -- '- Files: %s\n' "$total"
if [ -n "$base" ]; then
  printf -- '- Comparison: `%s...%s`\n' "$base" "$head"
else
  printf -- '- Comparison: stdin path list\n'
fi

print_bucket "Data / Migration" "${data[@]}"
print_bucket "Security / Auth" "${security[@]}"
print_bucket "API / Routes" "${api[@]}"
print_bucket "Core / Business Logic" "${core[@]}"
print_bucket "Frontend" "${frontend[@]}"
print_bucket "Infrastructure" "${infra[@]}"
print_bucket "Configuration" "${config[@]}"
print_bucket "Documentation" "${docs[@]}"
print_bucket "Tests" "${tests[@]}"
print_bucket "Types / Schemas" "${types[@]}"
print_bucket "Other / Mixed" "${other[@]}"

cat <<'EOF'

## Pairing Rules

- Review test files with the source cluster they validate; a test-only bucket is a signal to confirm whether source changed elsewhere.
- Review type, schema, and interface files with consuming clusters; do not treat them as isolated review silos.
- For monorepos, split the map by package/service first, then apply the concern buckets inside each package.
- Review generated files lightly and focus on the source definitions that produced them.
EOF
