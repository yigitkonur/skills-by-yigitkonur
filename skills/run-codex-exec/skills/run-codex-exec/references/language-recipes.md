# Language Recipes

`codex-wrapper.sh` auto-detects the project's language and picks appropriate post-verify commands. When the auto-detect is wrong or unavailable, override with `POST_VERIFY_CMD` and `POST_VERIFY_TESTS` env vars.

The wrapper looks for these markers in the worktree (not the parent repo):

| Marker file(s) | Auto-picked POST_VERIFY_CMD | Auto-picked POST_VERIFY_TESTS |
|---|---|---|
| `tsconfig.json` | `npx tsc --noEmit` | `npx vitest run` (if vitest config present) or `npx jest --silent` (if jest config) |
| `pyproject.toml` or `mypy.ini` | `python3 -m mypy --strict . --no-error-summary` | `python3 -m pytest -q` (if pytest configured) |
| `Cargo.toml` | `cargo check --quiet` | `cargo test --quiet` |
| `go.mod` | `go vet ./...` | `go test ./...` |
| none of the above | `echo 'post-verify: no known type-check config detected'` | `echo 'post-verify: no known test runner detected'` |

Override whenever the defaults don't fit your project. Examples below.

## TypeScript / Node (default — no override needed in most cases)

```bash
# Strict TS + vitest (auto-detected)
/tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# Strict TS + jest (auto-detected from jest.config.*)
/tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# Skip tests entirely, only type-check:
POST_VERIFY_TESTS="echo skipped" /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# Use pnpm:
POST_VERIFY_CMD="pnpm tsc --noEmit" POST_VERIFY_TESTS="pnpm test --run" \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &
```

## Python

```bash
# mypy strict + pytest (auto-detected from pyproject.toml + [tool.pytest])
/tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# pyright instead of mypy:
POST_VERIFY_CMD="pyright --outputjson ." /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# pytest with coverage threshold:
POST_VERIFY_TESTS="python3 -m pytest -q --cov=mypkg --cov-fail-under=90" \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# ruff lint as the "type-check" step (catches errors the type system doesn't):
POST_VERIFY_CMD="ruff check ." /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &
```

## Rust

```bash
# cargo check + cargo test (auto-detected)
/tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# Include clippy as part of type-check:
POST_VERIFY_CMD="cargo clippy --quiet -- -D warnings" \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# Release-mode test:
POST_VERIFY_TESTS="cargo test --release --quiet" \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &
```

## Go

```bash
# go vet + go test (auto-detected)
/tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# staticcheck instead of go vet:
POST_VERIFY_CMD="staticcheck ./..." \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &

# Race-mode test:
POST_VERIFY_TESTS="go test -race ./..." \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &
```

## Static HTML / CSS / JS site (no type-checker)

```bash
# Use html-validate + playwright if wired; otherwise skip with explicit "ok":
POST_VERIFY_CMD="npx html-validate **/*.html" \
  POST_VERIFY_TESTS="echo ok" \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &
```

## Mixed / polyglot projects

For monorepos or projects that mix languages, override with a wrapper script:

```bash
cat > /tmp/verify.sh <<'SH'
#!/usr/bin/env bash
set -e
npx tsc --noEmit --project packages/ts
cargo check --manifest-path rust-core/Cargo.toml
python3 -m mypy --strict ml-pipeline/
SH
chmod +x /tmp/verify.sh

POST_VERIFY_CMD=/tmp/verify.sh \
  POST_VERIFY_TESTS="npm run test:all" \
  /tmp/codex-monitor/codex-wrapper.sh feat plan "task" &
```

## Reading the post-verify line

`codex-wrapper.sh` emits one post-verify line per run:

```
[wrapper <plan>] post-verify verify_errors=0 (cmd='npx tsc --noEmit') tests='Tests  184 passed (184)' (cmd='npx vitest run')
```

Signals:

- `verify_errors=0` → clean type-check
- `verify_errors=N` (integer) → N errors found; inspect the log for details
- `verify_errors=?` → type-check command exited non-zero but the error-line grep matched zero lines (unusual output format; look at the log)
- `tests='skipped'` → type-check failed, so tests weren't attempted
- `tests='skipped (no changes)'` → agent exited without editing; type-check ran but tests didn't
- `tests='no-summary-line'` → tests ran but produced no summary-line grep match (check the log — may need tuning)

## What the grep pattern matches

The wrapper counts error lines matching:

```
error TS       — TypeScript
: error:       — mypy, gcc, many linters
^error[        — cargo/rust errors
^ERROR         — generic all-caps ERROR prefix
```

If your type-checker uses a different format (e.g., `issue:` or `[error]`), add it to the override command's output or pipe through `sed` to reshape:

```bash
POST_VERIFY_CMD="my-checker . | sed 's/^issue:/error:/'" \
  /tmp/codex-monitor/codex-wrapper.sh ...
```
