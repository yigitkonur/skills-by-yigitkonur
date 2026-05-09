# cli/audit-checklist.md

Mode A-CLI entry. Five checks catch most agent-integration failures in an existing CLI. Run them in order — earlier checks gate later ones (no point auditing structured errors if stdout and stderr are mixed). Each check has an executable test, a bad-vs-good code sample, and the failure mode it catches. Pair with `../common/audit-rhythm.md` (Explore → Diagnose → Present → Optimize) before recommending fixes.

## Check 1 — Stdout/stderr separation

Data on stdout. Prose on stderr. Nothing else.

If `--json` is passed and the agent pipes stdout into `jq`, every byte must parse. Logs, spinners, deprecation banners, "Connected to API…" lines are all stderr.

**How to test:**

```bash
# Stdout must parse cleanly even when stderr is suppressed.
mycli list --json 2>/dev/null | jq -e . > /dev/null && echo PASS || echo FAIL

# Stderr must NOT contaminate the JSON channel.
mycli list --json 2>&1 | jq -e . > /dev/null && echo PASS || echo FAIL
```

**Bad:**

```python
print("Connecting to server...")  # goes to stdout — pollutes JSON channel
print(json.dumps(result))
```

**Good:**

```python
import sys
print("Connecting to server...", file=sys.stderr, flush=True)
print(json.dumps(result))  # stdout, clean JSON
```

**Failure mode caught:** the agent's `--json | jq` pipeline crashes on the first non-JSON byte. Symptom: "agent works in unit tests but fails in production where logs ride on stdout."

## Check 2 — Exit codes

Codes are semantic and distinguishable. The agent reads `$?` before parsing anything. Use the taxonomy from `exit-codes.md` (0–7); never collapse all errors to `1`.

**How to test:**

```bash
# Force each failure mode and observe the code.
mycli get nonexistent-resource; echo "not-found: $?"   # expect 3
mycli --invalid-flag; echo "usage: $?"                  # expect 2
MYCLI_TOKEN=bogus mycli whoami; echo "auth: $?"         # expect 4
```

**Bad:**

```python
try:
    do_work()
except Exception as e:
    print(str(e), file=sys.stderr)
    sys.exit(1)  # one code for everything — agent can't classify
```

**Good:**

```python
try:
    do_work()
except NotFound as e:
    emit_error("not_found", str(e)); sys.exit(3)
except AuthError as e:
    emit_error("auth", str(e)); sys.exit(4)
except RateLimit as e:
    emit_error("transient", str(e)); sys.exit(7)
```

**Failure mode caught:** the agent retries a permanent failure (validation, auth) until it gives up, or fails to retry a transient one. Symptom: "agent loops on a bug or abandons a tool that would have worked next time."

## Check 3 — Non-interactive flags

Headless invocation never blocks on a prompt. Required: `--yes` (auto-confirm), `--no-input` (fail loudly instead of prompting), implicit non-interactive when stdout is not a TTY.

**How to test:**

```bash
# Pipe nothing in, time-bounded — anything that hangs fails.
echo "" | timeout 5 mycli delete dangerous-thing --yes --json
[ $? -eq 124 ] && echo FAIL || echo PASS  # 124 = timeout fired
```

**Bad:**

```python
answer = input("Delete? [y/N]: ")  # blocks forever in CI/agent contexts
if answer.lower() != "y":
    sys.exit(0)
```

**Good:**

```python
if not (args.yes or sys.stdout.isatty()):
    emit_error("usage", "deletion requires --yes in non-interactive mode")
    sys.exit(2)
delete_thing()
```

**Failure mode caught:** the subprocess hangs until the harness timeout; the agent reports "operation timed out" without a real cause. Symptom: "everything works locally, deploys hang in CI."

## Check 4 — Structured errors

Failures emit a JSON envelope on stdout when `--json` is passed: at minimum `ok=false`, an `error` object with code and message, and a `next_action` hint when known. Never plaintext-only error output in `--json` mode.

**How to test:**

```bash
# Force a known failure and check the envelope.
mycli get does-not-exist --json | jq -e '.ok==false and .error.code != null' \
  && echo PASS || echo FAIL
```

**Bad:**

```python
print(f"Error: resource '{name}' not found", file=sys.stderr)
sys.exit(3)  # JSON channel is empty — agent can't parse
```

**Good:**

```python
emit({
    "ok": False,
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": f"resource '{name}' not found",
        "next_action": "mycli list to see available names"
    },
    "schema_version": "1"
})
sys.exit(3)
```

**Failure mode caught:** the agent has no structured way to recover. It either escalates every failure to a human or retries blindly. Symptom: "agent gives up on the first failure even when the fix is one parameter change."

## Check 5 — Parsing reliability

Output is byte-stable across runs for a fixed input. No timestamps, no random IDs, no map-iteration order in agent-relevant fields. If a value must be present but is non-deterministic (e.g., a request ID), put it under `meta` so agents can scope-filter it out.

**How to test:**

```bash
# Run the same command twice and diff.
mycli list --json > a.json
mycli list --json > b.json
diff <(jq -S 'del(.meta)' a.json) <(jq -S 'del(.meta)' b.json) && echo PASS || echo FAIL
```

**Bad:**

```json
{"ok": true, "result": {"id": "res_abc123", "created_at": "2026-05-08T10:31:42Z"}}
{"ok": true, "result": {"id": "res_def456", "created_at": "2026-05-08T10:31:43Z"}}
```

**Good:**

```json
{"ok": true, "result": {"name": "web", "status": "active"}, "meta": {"request_id": "req_abc"}}
{"ok": true, "result": {"name": "web", "status": "active"}, "meta": {"request_id": "req_def"}}
```

`result` is byte-stable; `meta.request_id` is the only volatile field and lives outside the data the agent compares against.

**Failure mode caught:** the agent diffs two runs to detect drift; non-determinism in `result` triggers false positives. Symptom: "agent reports a resource changed when nothing changed."

## The audit script

A generic Bash runner. Save as `audit-cli.sh`, make it executable, point at any binary.

```bash
#!/usr/bin/env bash
set -uo pipefail

CLI="${1:?usage: audit-cli.sh <command> [args...]}"
shift
PASS=0; FAIL=0

ok()    { printf "PASS %s\n" "$1"; PASS=$((PASS+1)); }
fail()  { printf "FAIL %s — %s\n" "$1" "$2"; FAIL=$((FAIL+1)); }

# 1. stdout/stderr separation
if "$CLI" "$@" --json 2>/dev/null | jq -e . >/dev/null 2>&1; then
  ok "1.stdout-stderr"
else
  fail "1.stdout-stderr" "stdout did not parse as JSON when --json passed"
fi

# 2. exit codes — usage error must not return 1
if "$CLI" --definitely-not-a-real-flag >/dev/null 2>&1; then
  fail "2.exit-codes" "bad flag returned 0"
else
  code=$?
  if [ "$code" -eq 2 ]; then ok "2.exit-codes"; else fail "2.exit-codes" "bad flag returned $code, expected 2"; fi
fi

# 3. non-interactive
if echo "" | timeout 5 "$CLI" "$@" --no-input --json >/dev/null 2>&1; then
  ok "3.non-interactive"
else
  code=$?
  if [ "$code" -eq 124 ]; then fail "3.non-interactive" "command hung waiting for input"; else ok "3.non-interactive"; fi
fi

# 4. structured errors — force a failure, expect envelope
if "$CLI" "$@" --json 2>/dev/null | jq -e '.ok != null' >/dev/null 2>&1; then
  ok "4.structured-errors"
else
  fail "4.structured-errors" "no .ok field in --json output"
fi

# 5. parsing reliability — run twice, compare
A=$("$CLI" "$@" --json 2>/dev/null) || A="{}"
B=$("$CLI" "$@" --json 2>/dev/null) || B="{}"
if diff <(echo "$A" | jq -S 'del(.meta)') <(echo "$B" | jq -S 'del(.meta)') >/dev/null; then
  ok "5.parsing-reliability"
else
  fail "5.parsing-reliability" "result differed between identical runs"
fi

printf "\n%d passed, %d failed\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
```

Limitations: the script assumes a read-only command (e.g., `list`, `version`). For destructive commands, run the audit against the safe equivalents.

## Common findings catalog

The 10 findings the audit produces most often. Use them to populate the Diagnose phase from `../common/audit-rhythm.md`.

1. **Stderr noise on stdout when JSON requested.** A logger writes the connection banner before `--json` is parsed; banner lands in stdout. Fix: route logger to stderr unconditionally.
2. **Exit code 1 used for both crashes and validation errors.** Agent retries a validation error forever. Fix: split exit codes per `exit-codes.md`.
3. **Interactive prompts behind destructive commands without `--yes`.** `mycli delete` waits for `[y/N]` even with `--json`. Fix: gate prompts on `sys.stdout.isatty()`; require `--yes` in non-TTY.
4. **Plaintext error messages when `--json` was passed.** The error path bypasses the JSON formatter. Fix: error envelope through the same writer as success envelope.
5. **Non-deterministic timestamps in `result`.** Agent diff-checks fail. Fix: move timestamps to `meta` or omit when not load-bearing.
6. **Random ordering in list outputs.** Map iteration leaks. Fix: sort by stable key (id, name) before emitting.
7. **No `schema_version` field.** Agent has no way to detect a breaking change. Fix: add `schema_version: "1"` (see `output-envelope.md`).
8. **`--quiet` suppresses the JSON envelope instead of just prose.** Agent gets nothing. Fix: `--quiet` only suppresses stderr prose; envelope still emits.
9. **`--help` renders only when stdout is a TTY.** Agent calls `mycli --help`, gets nothing. Fix: help renders unconditionally; only ANSI colors are TTY-gated.
10. **Auth failures return exit code 1 with no envelope.** Agent can't tell auth from crash. Fix: exit code 4, envelope with `error.code = "UNAUTHENTICATED"`, `next_action = "mytool login"`.

## What to do with findings

Do not paste all 10 at the user. Pick the highest-impact two or three, present each with the test command they can run themselves, the bad-vs-good sample, and a one-line fix recommendation. The user accepts or pushes back; iterate. This is the rhythm — see `../common/audit-rhythm.md`.
