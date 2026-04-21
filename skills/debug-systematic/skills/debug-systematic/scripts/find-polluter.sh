#!/usr/bin/env bash
# find-polluter.sh — multi-runner test-pollution binary search
#
# Given a test that passes alone but fails when run after other tests, binary-search
# the pre-test list to find the smallest subset that triggers the failure.
#
# Usage:
#   bash find-polluter.sh --target <test-id> [--runner auto|jest|vitest|pytest|cargo|gotest|rspec|mvn|gradle] [--candidates <file>]
#
# Auto-detects the test runner from the project's manifest files. If multiple runners
# are present (e.g., a monorepo), pass --runner explicitly.
#
# Exits 0 on success (polluter identified), 1 on no polluter found, 2 on usage error,
# 3 on runner-not-detected.

set -euo pipefail

target=""
runner="auto"
candidates_file=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)     target="$2"; shift 2 ;;
    --runner)     runner="$2"; shift 2 ;;
    --candidates) candidates_file="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$target" ]]; then
  echo "error: --target is required" >&2
  exit 2
fi

# --------------------------------------------------------------------
# Auto-detect test runner from project manifests
# --------------------------------------------------------------------
detect_runner() {
  if [[ -f package.json ]]; then
    if grep -qE '"(jest|ts-jest)"\s*:' package.json 2>/dev/null; then echo jest; return
    elif grep -qE '"vitest"\s*:' package.json 2>/dev/null; then echo vitest; return
    fi
  fi
  [[ -f pyproject.toml || -f pytest.ini || -f setup.cfg ]] && { echo pytest; return; }
  [[ -f Cargo.toml ]] && { echo cargo; return; }
  [[ -f go.mod ]] && { echo gotest; return; }
  [[ -f Gemfile ]] && { echo rspec; return; }
  [[ -f pom.xml ]] && { echo mvn; return; }
  [[ -f build.gradle || -f build.gradle.kts ]] && { echo gradle; return; }
  echo none
}

if [[ "$runner" == "auto" ]]; then
  runner="$(detect_runner)"
fi

if [[ "$runner" == "none" ]]; then
  echo "error: no test-runner manifest found (package.json / pyproject.toml / Cargo.toml / go.mod / Gemfile / pom.xml / build.gradle)" >&2
  exit 3
fi

# --------------------------------------------------------------------
# Build the list of candidate pre-tests
# --------------------------------------------------------------------
list_all_tests() {
  case "$runner" in
    jest|vitest)
      # enumerate test files by convention
      find . -type f \( -name '*.test.ts' -o -name '*.test.tsx' -o -name '*.test.js' -o -name '*.spec.ts' -o -name '*.spec.js' \) -not -path './node_modules/*' | sort ;;
    pytest)
      # pytest --collect-only -q prints test ids
      pytest --collect-only -q 2>/dev/null | grep -v '^$' | head -n -2 ;;
    cargo)
      # cargo test -- --list lists tests in format "<name>: test"
      cargo test --no-run 2>/dev/null >/dev/null
      cargo test -- --list 2>/dev/null | grep ': test$' | sed 's/: test$//' ;;
    gotest)
      # go test enumerates via go test -list
      go test -list '.*' ./... 2>/dev/null | grep -v '^ok\|^PASS\|^FAIL' ;;
    rspec)
      bundle exec rspec --dry-run --format documentation 2>/dev/null | grep -E '^\s+it ' ;;
    mvn)
      find . -name '*Test.java' -not -path '*/target/*' | sort ;;
    gradle)
      find . -name '*Test.kt' -o -name '*Test.java' | grep -v build/ | sort ;;
    *) echo "error: unknown runner: $runner" >&2; exit 2 ;;
  esac
}

# --------------------------------------------------------------------
# Run a subset of tests plus the target; return 0 if target passes
# --------------------------------------------------------------------
run_subset_then_target() {
  local subset="$1"
  case "$runner" in
    jest)    pnpm exec jest --runInBand $subset "$target" >/dev/null 2>&1 ;;
    vitest)  pnpm exec vitest run $subset "$target" >/dev/null 2>&1 ;;
    pytest)  pytest $subset "$target" -q >/dev/null 2>&1 ;;
    cargo)
      # cargo test runs in arbitrary order; to impose order, use separate invocations
      # subset first (ignore failures), then target
      for t in $subset; do cargo test "$t" >/dev/null 2>&1 || true; done
      cargo test "$target" >/dev/null 2>&1 ;;
    gotest)  go test -run "$(echo $subset $target | tr ' ' '|')" ./... >/dev/null 2>&1 ;;
    rspec)   bundle exec rspec $subset "$target" >/dev/null 2>&1 ;;
    mvn)     mvn -q test -Dtest="$(echo $subset $target | tr ' ' ',')" >/dev/null 2>&1 ;;
    gradle)  ./gradlew test $(for t in $subset "$target"; do echo --tests "$t"; done) >/dev/null 2>&1 ;;
  esac
}

# --------------------------------------------------------------------
# Load candidates
# --------------------------------------------------------------------
if [[ -n "$candidates_file" ]]; then
  mapfile -t candidates < "$candidates_file"
else
  mapfile -t candidates < <(list_all_tests | grep -v -F "$target")
fi

if [[ ${#candidates[@]} -eq 0 ]]; then
  echo "no candidate pre-tests found" >&2
  exit 1
fi

echo "runner: $runner"
echo "target: $target"
echo "candidates: ${#candidates[@]}"

# Baseline: does the target pass alone?
if ! run_subset_then_target ""; then
  echo "target fails in isolation — not a pollution issue" >&2
  exit 1
fi

# Confirm the full set triggers the failure
full_set="$(IFS=' '; echo "${candidates[*]}")"
if run_subset_then_target "$full_set"; then
  echo "target passes after full candidate set — no polluter found" >&2
  exit 1
fi

# --------------------------------------------------------------------
# Binary search
# --------------------------------------------------------------------
echo "bisecting ${#candidates[@]} candidates..."

lo=0
hi=$((${#candidates[@]} - 1))

while (( lo < hi )); do
  mid=$(( (lo + hi) / 2 ))
  first_half=("${candidates[@]:lo:$((mid - lo + 1))}")
  subset="$(IFS=' '; echo "${first_half[*]}")"
  if run_subset_then_target "$subset"; then
    # first half passes → polluter in second half
    lo=$((mid + 1))
  else
    # first half fails → polluter in first half
    hi=$mid
  fi
  echo "range [$lo, $hi] (${#candidates[@]} candidates total)"
done

polluter="${candidates[$lo]}"

# --------------------------------------------------------------------
# Report
# --------------------------------------------------------------------
cat <<EOF

================================================================
polluting test identified: $polluter

minimal reproduction:
EOF

case "$runner" in
  jest)    echo "  pnpm exec jest --runInBand $polluter $target" ;;
  vitest)  echo "  pnpm exec vitest run $polluter $target" ;;
  pytest)  echo "  pytest $polluter $target -q" ;;
  cargo)   echo "  cargo test $polluter && cargo test $target" ;;
  gotest)  echo "  go test -run '$(basename $polluter)|$(basename $target)' ./..." ;;
  rspec)   echo "  bundle exec rspec $polluter $target" ;;
  mvn)     echo "  mvn -q test -Dtest=\"$polluter,$target\"" ;;
  gradle)  echo "  ./gradlew test --tests $polluter --tests $target" ;;
esac

cat <<EOF

next action: read $polluter and identify what shared state it mutates
  (in-memory cache, global singleton, module-level config, on-disk file).
  the polluter's teardown is incomplete. either add per-test cleanup,
  or isolate the shared resource (fresh instance per test).

see references/bisection-strategies.md § Test-pollution bisection for the
fix recipe once you've identified the shared-state mutation.
================================================================
EOF

exit 0
