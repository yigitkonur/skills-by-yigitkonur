---
name: optimize-cli-for-agents
description: "Use skill if you are auditing a CLI for agent-readiness, fixing output contracts, or designing new CLIs with agents as primary consumers."
---

# optimize-cli-for-agents

> Make CLIs reliably usable by AI agents — audit existing tools or design new ones with agent-first thinking.

## When to Use This Skill

| Situation | Mode |
|-----------|------|
| "I have a CLI that agents keep failing to use" | Audit Mode → score it, fix gaps |
| "I'm wrapping an API in a CLI that agents will call" | Design Mode → agent-first from day 1 |
| "My agent workflow is fragile, output parsing keeps breaking" | Audit Mode → fix output contracts |
| "I want to know if I should build MCP or CLI" | Decision Framework |
| "My CLI hangs when run in CI/agents" | Audit Mode → fix interactivity |

---

## 1. AUDIT MODE — Agent-Readiness Checklist

Run this checklist against any existing CLI to produce a score and prioritized fix list.

### CRITICAL (each missing item breaks agent workflows)

| # | Check | Verify | Fix |
|---|-------|--------|-----|
| C1 | Machine-parseable output exists (`--json` or `--output json`) | `mycli cmd --json 2>/dev/null \| jq .` succeeds | Add `--json` flag; stdout = pure JSON |
| C2 | stdout and stderr are separated | Run `mycli cmd --json > out.txt 2> err.txt` — `out.txt` must be valid JSON | Move all progress/human text to stderr |
| C3 | Exit codes are semantic (not all-zeros or all-ones) | Trigger a "not found" error; `echo $?` must not be 0 | Map error types to exit codes 2–7 |
| C4 | No mandatory interactive prompts in headless mode | Run `mycli dangerous-cmd </dev/null`; must not hang | Add `--yes`/`--force`; detect non-TTY and exit 2 |
| C5 | Errors have machine-parseable codes | Force an error with `--json`; check `error.code` in output | Add structured error object with `class`, `code`, `retryable` |

Each critical item is worth **20 points**. Missing all five = 0. All five present = 100.

### IMPORTANT (missing items cause fragility)

- Consistent field types across commands (no string/int flip-flopping between versions)
- Idempotent operations, or a `conflict` exit code (5) when operation can't be retried safely
- `--dry-run` flag for destructive commands
- `--help` includes realistic examples, not just flag lists
- Noun-verb grammar consistency across all commands

Each important item is worth **5 points** (max 25).

### NICE-TO-HAVE

- JSONL streaming for long-running operations (one JSON object per line)
- `--quiet` mode that emits bare, pipe-friendly output (IDs only, no envelope)
- `schema_version` field in every JSON output envelope
- Async job pattern (`job start` / `job status` / `job wait`) for slow operations

Each nice-to-have item is worth **2 points** (max 10).

### Scoring

| Score | Grade |
|-------|-------|
| ≥ 90 | ✅ Agent-Ready |
| 70–89 | 🟡 Mostly Ready — fix Important gaps |
| 50–69 | 🟠 Needs Work — agents will be brittle |
| < 50 | 🔴 Agent-Hostile — agents cannot use this reliably |

**Formula:** `(critical_passed × 20) + (important_passed × 5) + (nice_to_have_passed × 2)`

---

## 2. DESIGN MODE — Agent-First Principles

Use these when the agent is the *primary* consumer and you have greenfield control.

### Principle 1 — Determinism over Discoverability

- **Human-first:** Interactive menus, wizard flows, guided prompts help users explore
- **Agent-first:** Every command has a documented, stable output schema. Agents don't explore — they execute against contracts.
- **Example:** Instead of a setup wizard, provide `mycli init --config-file init.json` with a documented schema.

### Principle 2 — Data over Decoration

- **Human-first:** Colors, spinners, progress bars, emojis, aligned tables make output readable
- **Agent-first:** stdout is a data channel. All decoration goes to stderr. Agents pipe stdout directly to `jq` or language parsers.
- **Example:** Progress bar on stderr + JSON result on stdout. Never ANSI codes in stdout.

### Principle 3 — Fail Loudly, Fail Specifically

- **Human-first:** Generic "Something went wrong. Try again." is acceptable — humans ask for help
- **Agent-first:** Every error is a structured object. `{"error":{"class":"auth","code":"TOKEN_EXPIRED","retryable":true}}` lets agents self-heal without human escalation.
- **Example:** Auth failure exits 4 with `{"ok":false,"error":{"class":"auth","code":"TOKEN_EXPIRED","retryable":true,"suggestion":"Run 'mycli auth login' to refresh token"}}`.

### Principle 4 — Idempotent by Default

- **Human-first:** "Already exists" errors are fine — the human reads them and moves on
- **Agent-first:** Agents retry on transient failures. If creating a resource that already exists returns exit 5 (conflict) rather than exit 1 (unknown), the agent can route correctly without accidentally duplicating state.
- **Example:** `mycli user create alice` returns exit 5 + structured conflict error if alice exists, letting the agent branch to `user get` instead.

### Principle 5 — Self-Describing Contracts

- **Human-first:** `--help` is a quick reminder for experienced users
- **Agent-first:** `--help` is the API spec. It must include exit codes, output field names, and runnable examples. Agents read `--help` before calling a command for the first time.
- **Example:** Help text includes `Exit codes: 0=success 3=not_found 4=auth_error` and `Output fields: id (string), status (created|updated|deleted), created_at (ISO8601)`.

### Principle 6 — Predictable Grammar

- **Human-first:** Creative subcommand naming is memorable (`mycli nuke`, `mycli zap`)
- **Agent-first:** Strict noun-verb hierarchy. Agents discover capabilities through the `--help` tree. Inconsistent grammar forces agents to memorize special cases.
- **Example:** `mycli user create`, `mycli user get`, `mycli user delete` — not `mycli new-user`, `mycli fetch-user`, `mycli rm-user`.

### Principle 7 — Headless First

- **Human-first:** Default to interactive — prompt for missing values, confirm destructive ops
- **Agent-first:** Assume no TTY, no stdin, no user present. If a required value is missing, exit 2 with a specific error. Never hang waiting for input.
- **Example:** `if not sys.stdin.isatty() and not args.yes: sys.exit(2)` — fail fast, tell the agent what flag to add.

### Principle 8 — Recovery Paths

- **Human-first:** Error messages explain what went wrong
- **Agent-first:** Every error response must tell the agent what to do *next*. The `suggestion` field is not optional — it is the agent's next action.
- **Example:** `"suggestion": "Use 'mycli user get alice' to fetch the existing user, or add --force to overwrite"` — the agent can immediately retry with the correct command.

---

## 3. Output Contracts (Quick Reference)

### JSON Envelope (success and error)

Every `--json` response must conform to this envelope. Field presence is guaranteed.

```json
// Success
{
  "ok": true,
  "command": "user create",
  "schema_version": "1.0",
  "result": { "id": "usr_123", "status": "created" }
}

// Error
{
  "ok": false,
  "command": "user create",
  "schema_version": "1.0",
  "error": {
    "class": "conflict",
    "code": "USER_EXISTS",
    "message": "User 'alice' already exists",
    "retryable": false,
    "suggestion": "Use 'mycli user get alice' to fetch existing user, or 'mycli user update alice' to modify"
  }
}
```

### Exit Code Table (with agent routing)

| Code | Class | When | Agent Does |
|------|-------|------|-----------|
| 0 | success | Operation completed | Continue workflow |
| 1 | unknown | Unexpected crash / unhandled exception | Surface to user, do not retry |
| 2 | usage | Bad flags, missing args, invalid syntax | Fix invocation, do not retry |
| 3 | not_found | Resource does not exist | Create it or skip this step |
| 4 | auth | Token expired, forbidden, insufficient scope | Re-authenticate or escalate |
| 5 | conflict | Already exists / state clash | Resolve conflict or add `--force` |
| 6 | validation | Business rule violated, invalid input value | Fix input data |
| 7 | transient | Network error, rate-limit, timeout | Retry with exponential backoff |

### Stream Rules (non-negotiable)

- **stdout** = JSON data only. Nothing else ever reaches stdout.
- **stderr** = logs, progress bars, spinners, warnings, human-readable status
- **Verify with:** `mycli cmd --json 2>/dev/null | jq .` — must always succeed and produce valid JSON
- **JSONL streaming:** For long-running ops, emit one complete JSON object per line to stdout. Agents read line-by-line.

---

## 4. Common Fixes for Existing CLIs

### Problem 1: No structured output

**Symptom agents see:** Must regex-parse human-formatted tables or prose. Breaks on any formatting change.

**Fix:** Add a `--json` flag. When active, redirect all existing output to stderr and emit a JSON envelope to stdout.

```
# Before (stdout)
NAME     STATUS   AGE
web-1    Running  3d
```

```json
// After: mycli pods list --json (stdout only)
{"ok":true,"command":"pods list","schema_version":"1.0","result":{"pods":[{"name":"web-1","status":"running","age_seconds":259200}]}}
```

---

### Problem 2: All errors exit 1

**Symptom agents see:** Cannot distinguish "not found" from "auth failed" from "server crash" — must parse stderr text with regex.

**Fix:** Map error types to exit codes. Add a dispatch table in the error handler.

```python
EXIT_CODES = {
    "not_found": 3,
    "auth": 4,
    "conflict": 5,
    "validation": 6,
    "transient": 7,
}

def exit_with_error(error_class, code, message, retryable=False, suggestion=None):
    payload = {"ok": False, "error": {"class": error_class, "code": code,
                                       "message": message, "retryable": retryable}}
    if suggestion:
        payload["error"]["suggestion"] = suggestion
    print(json.dumps(payload))
    sys.exit(EXIT_CODES.get(error_class, 1))
```

---

### Problem 3: Interactive prompts hang agents

**Symptom agents see:** Workflow deadlocks indefinitely waiting for "y/N" confirmation. CI timeout eventually kills the process.

**Fix:** Detect non-TTY at startup. If running headless and `--yes` is not set, exit 2 immediately.

```python
# Python
if not sys.stdin.isatty() and not args.yes:
    print(json.dumps({"ok": False, "error": {"class": "usage", "code": "NON_INTERACTIVE",
                       "message": "Use --yes for non-interactive mode", "retryable": False}}))
    sys.exit(2)
```

```bash
# Shell
if [ ! -t 0 ] && [ "$YES" != "true" ]; then
  echo '{"ok":false,"error":{"class":"usage","code":"NON_INTERACTIVE","message":"Use --yes for non-interactive mode","retryable":false}}' >&1
  exit 2
fi
```

---

### Problem 4: stdout/stderr mixed

**Symptom agents see:** `mycli cmd --json | jq .` fails with parse errors because progress text (`Fetching... done`) is interleaved with JSON on stdout.

**Fix:** Audit every `print` / `console.log` / `echo` call in the codebase. Anything that isn't the final JSON result goes to stderr.

```python
# Before
print("Fetching resources...")      # goes to stdout — breaks jq
print(json.dumps(result))

# After
print("Fetching resources...", file=sys.stderr)  # progress → stderr
print(json.dumps(result))                         # data → stdout
```

---

### Problem 5: Inconsistent field names

**Symptom agents see:** Agent code breaks when `user_id` becomes `userId` in v2, or `created` becomes `created_at` in one command but not another.

**Fix:** Establish a naming convention (snake_case for CLIs is conventional), document it in CONTRIBUTING, and enforce it with a schema linter or JSON Schema validation in CI.

```json
// Consistent snake_case contract
{"user_id": "usr_123", "created_at": "2024-01-15T10:00:00Z", "is_active": true}

// Never mix
{"userId": "usr_123", "created": "2024-01-15T10:00:00Z", "isActive": true}
```

---

### Problem 6: No recovery hints in errors

**Symptom agents see:** Receives an error with a message like "Resource conflict". Has no next action. Escalates to human or fails the workflow.

**Fix:** Every error response must include `suggestion` with a concrete runnable command the agent can execute immediately.

```json
// Before — agent is stuck
{"ok": false, "error": {"message": "User already exists"}}

// After — agent knows exactly what to do next
{
  "ok": false,
  "error": {
    "class": "conflict",
    "code": "USER_EXISTS",
    "message": "User 'alice' already exists",
    "retryable": false,
    "suggestion": "Use 'mycli user get alice' to fetch existing user, or 'mycli user update alice --email new@example.com' to modify"
  }
}
```

---

## 5. Anti-Patterns (What Breaks Agents)

### Anti-Pattern 1: ANSI codes on stdout

```bash
# Breaks agents — color codes corrupt JSON parsing
echo -e "\033[32mSuccess!\033[0m user created with id usr_123"

# Agent-safe — decoration on stderr, data on stdout
echo "Success: user created" >&2
echo '{"ok":true,"result":{"id":"usr_123"}}'
```

**Why it breaks:** Agent tries to parse `\033[32m{"ok":true}` as JSON. Fails. Workflow dies.

---

### Anti-Pattern 2: Different output shape per subcommand

```bash
mycli user list    # returns {"users": [...]}
mycli role list    # returns [...]           ← different root shape
mycli group list   # returns {"data": {"groups": [...]}}  ← nested differently
```

**Why it breaks:** Agent must have special-case parsing logic per command. Any new command requires code changes. Fix: every list command returns `{"ok":true,"result":{"items":[...],"total":N}}`.

---

### Anti-Pattern 3: Success messages that look like errors

```bash
# Ambiguous — is this success or failure?
echo "Warning: user already exists, no changes made"
exit 0
```

**Why it breaks:** Agent has no way to know if the operation succeeded or was skipped without text parsing. Fix: exit 5 (conflict) with structured body, or exit 0 with `"result":{"action":"skipped","reason":"already_exists"}`.

---

### Anti-Pattern 4: Hiding the real error behind a wrapper

```bash
# Original error swallowed — agent sees useless message
try:
    do_thing()
except Exception:
    print("Operation failed")   # original exception lost
    sys.exit(1)
```

**Why it breaks:** Agent cannot distinguish root causes. Fix: include `error.code` mapped from the underlying exception class, and log the stack trace to stderr only.

---

### Anti-Pattern 5: Version-breaking field renames

```bash
# v1
{"user_id": "usr_123", "status": "active"}

# v2 — same command, renamed fields, no version signal
{"id": "usr_123", "state": "active"}
```

**Why it breaks:** Agent code written against v1 silently breaks against v2. Fix: include `schema_version` in every response; increment it on breaking changes; support old field names as aliases for one major version.

---

## 6. References

The following reference files provide deeper detail on specific topics:

| File | Contents |
|------|----------|
| `references/output-contracts.md` | Full JSON schema definitions, field-by-field spec, JSONL format for streaming |
| `references/mcp-vs-cli-decision.md` | Decision framework: when to build an MCP server vs a CLI wrapper |
| `references/execution-patterns.md` | Patterns for retry logic, backoff, job polling, and parallel execution from agents |
| `references/discovery-and-auth.md` | How agents discover CLI capabilities via `--help` parsing and handle auth flows |
| `references/examples.md` | End-to-end worked examples: auditing a real CLI, designing a greenfield agent CLI |
