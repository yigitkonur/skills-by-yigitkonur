#!/usr/bin/env bash
# find-polluter.sh — multi-runner test-pollution binary search
#
# Given a test that passes alone but fails when run after other tests, binary-search
# the pre-test list to find the smallest subset that triggers the failure.
#
# Usage:
#   bash find-polluter.sh --target <selector> [--runner auto|jest|vitest|pytest|cargo|gotest|rspec|mvn|gradle] [--candidates <file>]
#
# --target is a runner-native selector, NOT a test title:
#   jest/vitest: test-file path (e.g., "tests/auth.test.ts")
#   pytest:      nodeid (e.g., "tests/test_auth.py::test_missing_token")
#   cargo:       test function name (e.g., "auth::missing_token")
#   gotest:      regex for -run (e.g., "^TestAuth_MissingToken$")
#   rspec:       file:line selector (e.g., "spec/auth_spec.rb:42") or example id
#   mvn/gradle:  test class or class#method (e.g., "com.example.AuthTest")
#
# Auto-detects the test runner from the project's manifest files. If multiple runners
# are present (e.g., a monorepo), pass --runner explicitly.
#
# IMPORTANT CAVEAT — test ordering: most runners parallelize or randomize within a
# single invocation. This script enforces ordering by invoking the subset and the
# target in separate runner calls where possible (cargo, mvn, gradle) and by using
# --runInBand / -n 0 flags where the runner supports them (jest, vitest, pytest).
# If the runner randomizes even with those flags, consider disabling randomization
# (e.g., pytest-randomly's --randomly-seed=0, gotest -shuffle=off) via your project
# config before running this script.
#
# Exits 0 on success, 1 on no polluter found, 2 on usage error, 3 on runner-not-detected.

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
      sed -n '2,26p' "$0"
      exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$target" ]]; then
  echo "error: --target is required (runner-native selector, not a test title)" >&2
  exit 2
fi

# --------------------------------------------------------------------
# Detect the JS package manager (pnpm > yarn > npm > bun)
# --------------------------------------------------------------------
detect_js_pm() {
  if   command -v pnpm >/dev/null 2>&1 && [[ -f pnpm-lock.yaml ]]; then echo pnpm
  elif command -v yarn >/dev/null 2>&1 && [[ -f yarn.lock ]]; then     echo yarn
  elif command -v bun  >/dev/null 2>&1 && [[ -f bun.lockb  ]]; then    echo bun
  else echo npm
  fi
}

# Turn a package manager name into the prefix for running a local binary.
js_exec() {
  case "$(detect_js_pm)" in
    pnpm) echo "pnpm exec" ;;
    yarn) echo "yarn" ;;  # yarn can run a binary directly: `yarn jest args`
    bun)  echo "bunx" ;;
    npm)  echo "npx" ;;
  esac
}

# --------------------------------------------------------------------
# Auto-detect test runner
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

JS_EXEC="$(js_exec)"

# --------------------------------------------------------------------
# Build the list of candidate pre-tests — runner-native selectors ONLY
# --------------------------------------------------------------------
list_all_tests() {
  case "$runner" in
    jest|vitest)
      # file-path candidates (runners accept these directly)
      find . -type f \( -name '*.test.ts' -o -name '*.test.tsx' -o -name '*.test.js' -o -name '*.spec.ts' -o -name '*.spec.js' \) -not -path './node_modules/*' | sort ;;
    pytest)
      # --collect-only -q prints nodeids followed by a summary line.
      # Keep only lines matching a nodeid shape (path::something) to avoid the trailing summary.
      pytest --collect-only -q 2>/dev/null | grep -E '^[^[:space:]]+::[^[:space:]]+' | sort -u ;;
    cargo)
      # cargo test -- --list lists tests as "<name>: test"
      cargo test --no-run 2>/dev/null >/dev/null
      cargo test -- --list 2>/dev/null | grep ': test$' | sed 's/: test$//' ;;
    gotest)
      # Emit go test -run patterns (regex-anchored test function names)
      go test -list '.*' ./... 2>/dev/null \
        | grep -E '^Test|^Example|^Benchmark' \
        | sed 's/^/^/; s/$/$/' ;;
    rspec)
      # Use --dry-run with the examples formatter to get runnable file:line selectors
      bundle exec rspec --dry-run --format json 2>/dev/null \
        | python3 -c 'import json,sys; d=json.load(sys.stdin); print("\n".join(e["file_path"]+":"+str(e["line_number"]) for e in d.get("examples",[])))' ;;
    mvn)
      # Extract test class names from source files — mvn -Dtest expects class names
      find . -name '*Test.java' -not -path '*/target/*' \
        | sed 's|.*/\([^/]*\)\.java$|\1|' \
        | sort -u ;;
    gradle)
      # Same as mvn — gradle --tests expects class or class.method patterns
      find . \( -name '*Test.kt' -o -name '*Test.java' \) -not -path '*/build/*' \
        | sed 's|.*/\([^/]*\)\.\(kt\|java\)$|\1|' \
        | sort -u ;;
    *) echo "error: unknown runner: $runner" >&2; exit 2 ;;
  esac
}

# --------------------------------------------------------------------
# Run a subset of tests THEN the target, in order. Return 0 if target passes.
# --------------------------------------------------------------------
run_subset_then_target() {
  local subset="$1"
  case "$runner" in
    jest)
      # --runInBand forces serial within one invocation; we invoke twice to force ordering.
      if [[ -n "$subset" ]]; then
        $JS_EXEC jest --runInBand $subset >/dev/null 2>&1 || true
      fi
      $JS_EXEC jest --runInBand "$target" >/dev/null 2>&1
      ;;
    vitest)
      if [[ -n "$subset" ]]; then
        $JS_EXEC vitest run --no-file-parallelism $subset >/dev/null 2>&1 || true
      fi
      $JS_EXEC vitest run --no-file-parallelism "$target" >/dev/null 2>&1
      ;;
    pytest)
      # -p no:randomly disables pytest-randomly if present
      if [[ -n "$subset" ]]; then
        pytest -p no:randomly -q $subset >/dev/null 2>&1 || true
      fi
      pytest -p no:randomly -q "$target" >/dev/null 2>&1
      ;;
    cargo)
      for t in $subset; do cargo test "$t" -- --test-threads=1 >/dev/null 2>&1 || true; done
      cargo test "$target" -- --test-threads=1 >/dev/null 2>&1 ;;
    gotest)
      # -shuffle=off turns off internal test shuffling; -p 1 avoids package-level parallelism
      if [[ -n "$subset" ]]; then
        go test -shuffle=off -p 1 -run "$(echo $subset | tr ' ' '|')" ./... >/dev/null 2>&1 || true
      fi
      go test -shuffle=off -p 1 -run "$target" ./... >/dev/null 2>&1 ;;
    rspec)
      if [[ -n "$subset" ]]; then
        bundle exec rspec --order defined $subset >/dev/null 2>&1 || true
      fi
      bundle exec rspec --order defined "$target" >/dev/null 2>&1 ;;
    mvn)
      # mvn surefire has no ordering guarantee between -Dtest classes, so invoke twice
      if [[ -n "$subset" ]]; then
        mvn -q -Dsurefire.runOrder=alphabetical test -Dtest="$(echo $subset | tr ' ' ',')" >/dev/null 2>&1 || true
      fi
      mvn -q test -Dtest="$target" >/dev/null 2>&1 ;;
    gradle)
      if [[ -n "$subset" ]]; then
        ./gradlew test $(for t in $subset; do echo --tests "$t"; done) >/dev/null 2>&1 || true
      fi
      ./gradlew test --tests "$target" >/dev/null 2>&1 ;;
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
[[ "$runner" == "jest" || "$runner" == "vitest" ]] && echo "js package manager: $(detect_js_pm)"
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
  echo "target passes after full candidate set — no polluter found (or runner still randomizing)" >&2
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
    lo=$((mid + 1))
  else
    hi=$mid
  fi
  echo "range [$lo, $hi]"
done

polluter="${candidates[$lo]}"

cat <<EOF

================================================================
polluting test identified: $polluter

minimal reproduction:
EOF

case "$runner" in
  jest)    echo "  $JS_EXEC jest --runInBand $polluter && $JS_EXEC jest --runInBand $target" ;;
  vitest)  echo "  $JS_EXEC vitest run --no-file-parallelism $polluter && $JS_EXEC vitest run --no-file-parallelism $target" ;;
  pytest)  echo "  pytest -p no:randomly $polluter && pytest -p no:randomly $target" ;;
  cargo)   echo "  cargo test $polluter -- --test-threads=1 && cargo test $target -- --test-threads=1" ;;
  gotest)  echo "  go test -shuffle=off -p 1 -run '$polluter' ./... && go test -shuffle=off -p 1 -run '$target' ./..." ;;
  rspec)   echo "  bundle exec rspec --order defined $polluter $target" ;;
  mvn)     echo "  mvn test -Dtest=\"$polluter\" && mvn test -Dtest=\"$target\"" ;;
  gradle)  echo "  ./gradlew test --tests $polluter && ./gradlew test --tests $target" ;;
esac

cat <<EOF

next action: read $polluter and identify what shared state it mutates
  (in-memory cache, global singleton, module-level config, on-disk file).
  the polluter's teardown is incomplete. either add per-test cleanup
  or isolate the shared resource (fresh instance per test).

see references/bisection-strategies.md § Test-pollution bisection for the
fix recipe once you've identified the shared-state mutation.
================================================================
EOF

exit 0
