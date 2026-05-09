# cli/output-envelope.md

The canonical CLI JSON envelope. Every command that supports `--json` emits this shape. The agent's parse-and-route function is written against this contract; if every command in your CLI returns it, the agent learns the contract once and reuses it everywhere.

## Schema

Success:

```json
{
  "ok": true,
  "result": { "...": "..." },
  "schema_version": "1"
}
```

Failure:

```json
{
  "ok": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource 'foo' does not exist.",
    "next_action": "Run mytool list to see available names."
  },
  "schema_version": "1"
}
```

`ok` and `schema_version` are required on every emit. `result` is required when `ok=true`. `error` is required when `ok=false`. No other top-level fields are reserved — add `meta` for diagnostics if needed (see Optional fields below).

## Field-by-field semantics

### `ok` (boolean, required)

The agent's primary branch. `true` means the command did what it advertised; `false` means it didn't.

- The agent reads `ok` first, before parsing `result` or `error`. Branching on `ok` is faster and more reliable than branching on the exit code (the exit code might be lost across some harnesses; the envelope is always intact when stdout is captured).
- `ok` and the exit code MUST agree: `ok=true` → exit 0; `ok=false` → exit ≠ 0. A mismatch is a CLI bug — see `exit-codes.md`.
- Don't introduce intermediate states ("partial", "warning", "maybe"). If the operation produced data but had a recoverable issue, return `ok=true` with a warning under `meta.warnings[]`. If it produced no usable data, return `ok=false`.

### `result` (object, required when `ok=true`)

The data the agent acts on. Project to agent-relevant fields — do not dump the upstream API's raw JSON.

- Shape is command-specific; document each command's `result` shape in `--help`.
- Use snake_case keys to match the rest of the envelope.
- Prefer flat over nested. If a field is `result.metadata.config.ui.theme`, the agent's prompt is going to retrieve all four levels. Flatten to `result.theme` unless the nesting carries semantic weight.
- Use stable types — numbers stay numbers, dates as ISO 8601 UTC, lists as lists (not space-separated strings).

### `error` (object, required when `ok=false`)

Structured error for the agent's recovery loop.

```json
{
  "code": "RATE_LIMITED",
  "message": "Rate limit hit; 50 requests/min.",
  "next_action": "Wait 30s, then retry.",
  "retryable": true,
  "retry_after_seconds": 30
}
```

- `code` (string, required) — SCREAMING_SNAKE_CASE machine-readable identifier. Stable across releases. The agent branches on `code`, never on `message`.
- `message` (string, required) — human-readable. The agent surfaces this to the operator if the loop fails. Keep one sentence.
- `next_action` (string, optional but strongly preferred) — what the agent should do next. Free-form. "Run `mytool login`." "Wait 30s and retry." "Edit the field and resubmit."
- `retryable` (boolean, optional) — the agent's retry policy hint. `true` = transient (network, rate limit, dependency). `false` = permanent (validation, auth, not-found). Match the exit-code taxonomy from `exit-codes.md`.
- `retry_after_seconds` (number, optional) — only when `retryable=true` and the server told you to wait that long. Otherwise omit; let the agent pick its own backoff.
- Additional fields are allowed for command-specific context (e.g., `field_path` for validation errors, `existing_id` for conflicts). Keep them under `error.details.*` so the standard fields stay flat.

### `schema_version` (string, required)

A stable string the agent can branch on if the envelope shape ever changes. Today, `"1"`. Bump to `"2"` if you make a breaking change.

- The agent reads `schema_version` once at startup; if it doesn't recognize the version, it falls back to "raw text" mode and surfaces a warning. This is what makes future evolution safe.
- Use simple integers (`"1"`, `"2"`), not semver. The schema is either compatible or it isn't; minor versions are noise.

## Schema versioning rules

A change is **non-breaking** (no version bump) if:
- New optional fields are added.
- Existing fields gain wider value ranges (e.g., `error.code` adds new possible values).
- New error codes are introduced.

A change is **breaking** (bump to `"2"`):
- A required field is renamed or removed.
- A field's type changes (`status` was a string, now an object).
- An existing error code's semantics change.

When you bump the version:
1. Keep the `"1"` shape working for at least one release. Emit `"2"` only when the user passes `--schema-version=2` or `MYTOOL_SCHEMA=2`.
2. Document the migration in `--help` and the changelog: "schema_version `2` adds `result.regions[]` (array). Pass `--schema-version=2` to opt in. Default flips to `2` in v3.0."
3. The agent that requested `"1"` keeps getting `"1"`. The agent that requested `"2"` (or omitted the request and accepts the default) gets `"2"`.

## Forward compatibility

Agents must ignore unknown fields, not crash. The CLI must not assume agents will never see an unfamiliar `error.code`. Both sides degrade gracefully.

Agent side:

```python
data = json.loads(stdout)
if not data["ok"]:
    code = data["error"]["code"]
    if code in {"RATE_LIMITED", "TIMEOUT", "NETWORK"}:
        retry_with_backoff()
    elif code in {"UNAUTHENTICATED", "FORBIDDEN"}:
        escalate_to_human()
    else:
        # Unknown code — fall back to retryable flag, then bail.
        if data["error"].get("retryable"):
            retry_once()
        else:
            escalate_to_human()
```

CLI side: every `error.code` value is documented in `--help` so the agent author can wire branches. Adding a new code is non-breaking but should be paired with a release note.

## Streaming vs single-shot

For commands that produce a single result, emit the envelope once on stdout, then exit.

For commands that stream progress (`watch`, `tail`, long-running `apply`), use NDJSON — one JSON object per line. Each line is a self-contained envelope or a progress event:

```ndjson
{"type": "progress", "phase": "downloading", "percent": 25}
{"type": "progress", "phase": "downloading", "percent": 75}
{"type": "progress", "phase": "applying", "percent": 100}
{"ok": true, "result": {"id": "deploy_123"}, "schema_version": "1"}
```

Rules for streaming:

- Each line is a complete JSON object — no pretty-printing.
- Flush after every line (`flush=True` in Python, `Stdout.Sync()` in Go).
- The final line is the canonical envelope (`{"ok": true, ...}` or `{"ok": false, ...}`). Progress events MUST NOT have `ok` — only the terminal envelope does. The agent reads lines until it sees `ok`.
- Heartbeats every 30s for long operations; emit `{"type": "heartbeat", "uptime_ms": ...}` to keep harness timeouts from firing.

Trigger streaming explicitly: `--stream`, `--follow`, or `--watch`. Don't stream by default; the single-shot envelope is the simpler contract and most commands should use it.

## Mixed text + JSON

Some commands have a TTY-friendly default (table output) and an agent-friendly mode (`--json`). Don't mix them in one command run.

- `mytool list` (no flag, TTY) → human-readable table on stdout.
- `mytool list --json` → envelope on stdout, no table.
- Auto-flip when stdout is not a TTY: if `not isatty(stdout)`, behave as if `--json` was passed. The agent never has to remember the flag — the CLI does the right thing in pipelines.

```python
def emit(data):
    if args.json or not sys.stdout.isatty():
        print(json.dumps(data))
    else:
        print(format_as_table(data))
```

## Optional `meta` field

`meta` is reserved for diagnostics that are not part of the load-bearing result.

```json
{
  "ok": true,
  "result": { "id": "res_001", "name": "web" },
  "meta": {
    "duration_ms": 142,
    "request_id": "req_xyz",
    "warnings": ["deprecated flag --legacy will be removed in v3.0"],
    "rate_limit": {"remaining": 47, "reset_at": "2026-05-08T11:00:00Z"}
  },
  "schema_version": "1"
}
```

- Agent SHOULD ignore `meta` when comparing two runs.
- `meta.warnings[]` is the canonical place to surface non-fatal advice.
- `meta.duration_ms`, `meta.request_id` are conventional but optional.

## Code samples

Python writer (stdlib only):

```python
import json, sys

def emit_success(result, meta=None):
    payload = {"ok": True, "result": result, "schema_version": "1"}
    if meta:
        payload["meta"] = meta
    print(json.dumps(payload))

def emit_error(code, message, next_action=None, retryable=False, **details):
    err = {"code": code, "message": message, "retryable": retryable}
    if next_action:
        err["next_action"] = next_action
    if details:
        err["details"] = details
    payload = {"ok": False, "error": err, "schema_version": "1"}
    print(json.dumps(payload))
```

Go writer (stdlib only):

```go
package envelope

import (
    "encoding/json"
    "os"
)

type Envelope struct {
    OK            bool        `json:"ok"`
    Result        interface{} `json:"result,omitempty"`
    Error         *ErrorBody  `json:"error,omitempty"`
    Meta          interface{} `json:"meta,omitempty"`
    SchemaVersion string      `json:"schema_version"`
}

type ErrorBody struct {
    Code        string                 `json:"code"`
    Message     string                 `json:"message"`
    NextAction  string                 `json:"next_action,omitempty"`
    Retryable   bool                   `json:"retryable"`
    Details     map[string]interface{} `json:"details,omitempty"`
}

func EmitSuccess(result interface{}) {
    json.NewEncoder(os.Stdout).Encode(Envelope{
        OK: true, Result: result, SchemaVersion: "1",
    })
}

func EmitError(code, message, nextAction string, retryable bool) {
    json.NewEncoder(os.Stdout).Encode(Envelope{
        OK: false,
        Error: &ErrorBody{
            Code: code, Message: message,
            NextAction: nextAction, Retryable: retryable,
        },
        SchemaVersion: "1",
    })
}
```

Agent's parse-and-route function (Python):

```python
def parse_envelope(stdout: str) -> dict:
    """Parse CLI stdout. Returns a normalized dict for the agent's loop."""
    try:
        env = json.loads(stdout)
    except json.JSONDecodeError as e:
        return {"ok": False, "parse_failure": str(e), "raw": stdout}

    sv = env.get("schema_version")
    if sv != "1":
        # Future-version envelope; degrade safely.
        return {"ok": env.get("ok", False), "unknown_schema_version": sv, "raw": env}

    return env
```

## Anti-patterns

- **No envelope.** The CLI prints raw API JSON. Agent has no `ok` flag to branch on. Fix: wrap in envelope.
- **Envelope on success, plain text on failure.** Asymmetric. Agent crashes on the failure path. Fix: error envelope through the same writer.
- **Boolean `ok` plus a string `status` field that contradicts it.** Agent has to reconcile. Fix: pick one — `ok` is canonical.
- **Numeric `error.code` (`"code": 42`).** Lossy; the agent has to maintain a code table that drifts from yours. Use SCREAMING_SNAKE_CASE strings.
- **`error.message` localized.** The agent's branches break when the locale flips. Keep `message` and `code` in English; offer `error.localized_message` if you must.
- **Stream events tagged with `ok`.** Agents read until they see `ok`; if every progress line has `ok=true`, the loop terminates after the first one. Reserve `ok` for the terminal envelope.
- **Pretty-printed JSON in single-shot mode.** Wastes bytes; some harnesses chunk on newlines. Pretty-print only when stdout is a TTY.

## Cross-references

- `exit-codes.md` — the exit code taxonomy `ok` and the envelope must agree with.
- `flags-and-discovery.md` — the `--json` and `--stream` flags that gate envelope emission.
- `iterative-pattern.md` — extended envelope fields for multi-turn workflows (`phase`, `state_token`, `validation_errors`).
- `subprocess-harness.md` — how a Python/Node harness parses this envelope.
- `../common/output-contracts.md` — cross-surface principles (CLI + MCP) that this file specializes for CLIs.
