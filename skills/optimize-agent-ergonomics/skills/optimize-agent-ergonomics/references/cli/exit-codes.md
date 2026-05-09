# cli/exit-codes.md

Exit codes give agents fast classification without parsing. The agent reads `$?` before it parses stdout — that's three orders of magnitude cheaper than running JSON through a parser. A semantic exit-code taxonomy lets the agent decide "retry, escalate, abort, repair" before it even looks at the envelope. This file defines the canonical taxonomy used by every CLI in this skill, the agent policy per code, and language-specific implementations.

## The taxonomy

| Code | Name | When to emit | Agent policy |
|---|---|---|---|
| `0` | success | Operation completed and produced the advertised effect | Continue; parse `result` |
| `1` | crash | Unhandled exception, panic, segfault, internal bug | Escalate; do not retry blindly |
| `2` | usage | Bad flags, missing required args, malformed CLI invocation | Do NOT retry — the input is wrong; surface to caller |
| `3` | not-found | Named resource doesn't exist | Disambiguate (run `list`), then retry with corrected name |
| `4` | auth | Unauthenticated, token expired, forbidden | Escalate to a privileged caller; do not retry |
| `5` | conflict | State mismatch, version skew, resource-already-exists | Re-read state, then re-apply with the new version |
| `6` | validation | Input failed business-logic validation | Repair the input using `error.next_action`, then retry |
| `7` | transient | Rate limit, network blip, dependency unavailable | Retry with exponential backoff; honor `retry_after_seconds` |
| `8+` | reserved | Command-specific extensions only | Fall back to `error.code` parsing |

`0–7` is the canonical range. `8+` is permitted only when a CLI has a domain-specific failure that doesn't map to any of the standard codes (rare). Any new value MUST be documented in `--help`.

## Per-code agent policy

### 0 — success

Operation succeeded. Parse `result` from the envelope and proceed. No retry, no escalation. If the operation was supposed to be idempotent and the agent is in a retry loop, exit code 0 means "stop retrying; we're done."

### 1 — crash

Unhandled error in the CLI itself. The agent should:
1. Capture stderr (the stack trace is there, not in the envelope).
2. Surface to the caller as "the tool crashed; this is a bug in the tool."
3. Do not retry — the same input will produce the same crash.

`1` is reserved for crashes; never use it for business-logic failures. A "resource not found" returning `1` is a CLI bug.

### 2 — usage

The CLI rejected the invocation before doing any work. Bad flag, missing arg, type mismatch. The agent should:
1. Read the envelope's `error.message` for the specific complaint.
2. NOT retry — the same flags will fail the same way.
3. Either repair the invocation (if the agent has the option) or surface to caller.

The exit code 2 contract: the CLI guarantees that no side effect occurred. The agent can trust this.

### 3 — not-found

The named resource doesn't exist. The agent should:
1. Read `error.next_action` — usually "run `mytool list`".
2. Run the disambiguation command.
3. Retry the original command with a corrected name.

If `list` returns zero resources, the resource genuinely doesn't exist; the agent escalates ("the resource you asked for hasn't been created").

### 4 — auth

The caller is unauthenticated or unauthorized. The agent should:
1. Check whether a refresh would help (read `error.code` — `TOKEN_EXPIRED` is recoverable; `FORBIDDEN` is not).
2. If recoverable: trigger the auth refresh (`mytool auth refresh`) and retry once.
3. If not: escalate to a privileged caller. Do not loop on auth failures.

Exit code 4 is special: it's the only failure code where the agent should escalate before retrying. Auth loops produce account lockouts.

### 5 — conflict

State has shifted underneath the agent. Examples: optimistic concurrency violation (etag mismatch), resource-already-exists, dependency-version-skew. The agent should:
1. Re-read the current state (`mytool get`).
2. Decide: is this a real conflict (someone else changed the resource) or a duplicate request (the agent already created it on a previous attempt)?
3. If duplicate: treat as success (the desired end-state holds).
4. If real: merge the agent's intended change with the new state, then re-apply.

### 6 — validation

Input is well-formed (it parsed) but failed business rules. Field too long, bad format, value out of range. The agent should:
1. Read `error.details` for the specific field and rule.
2. Repair the input using the rule.
3. Retry.

Validation errors are the agent's most productive cycle — repair-budget is well-spent here. See `iterative-pattern.md` for the full multi-turn validate-repair loop.

### 7 — transient

External system was unavailable. Rate limit, 503, DNS blip, dependency timing out. The agent should:
1. Honor `error.retry_after_seconds` if present.
2. Otherwise, exponential backoff: 1s, 2s, 4s, 8s, 16s; cap at 60s.
3. Retry up to N times (default: 3); after N, surface to caller.

Exit code 7 is the only code where unconditional retry is the right move. Every other code requires inspection.

## Why exit codes are more reliable than parsing

Three reasons agents prefer exit codes over JSON parsing for first-pass classification:

1. **Survives truncation.** A CLI that hits a buffer limit may emit half a JSON object; the exit code still arrives intact.
2. **Survives encoding issues.** Stdout might have a stray non-UTF-8 byte from a logger; the exit code is just a number.
3. **Survives malformed JSON.** A bug in the CLI's JSON serializer produces a crash before the envelope is written; the exit code is set by the runtime, not by the bug.

The contract: **the exit code MUST agree with `envelope.ok`.** `ok=true` ↔ exit 0; `ok=false` ↔ exit ≠ 0. A CLI that emits `{"ok": true}` with exit 5 is broken — the agent will believe one and ignore the other. Test this in CI.

## Mapping table

HTTP status → exit code, for CLIs that wrap REST APIs:

| HTTP status | Exit code | Reason |
|---|---|---|
| 200, 201, 204 | 0 | Success |
| 400 | 6 | Validation |
| 401 | 4 | Auth |
| 403 | 4 | Auth (forbidden) |
| 404 | 3 | Not-found |
| 409 | 5 | Conflict |
| 422 | 6 | Validation (semantic) |
| 429 | 7 | Transient (rate limit) |
| 500–599 | 7 | Transient (server) — but log internally; persistent 5xx is a real bug |
| 502, 503, 504 | 7 | Transient (gateway/dependency) |

Common patterns → exit code:

| Pattern | Exit code |
|---|---|
| `--help` invoked | 0 |
| `--version` invoked | 0 |
| Flag parser rejected input | 2 |
| Required arg missing | 2 |
| Token file unreadable | 2 (config error, agent's input) |
| Token expired | 4 |
| Network unreachable | 7 |
| File-not-found in input arg | 3 |
| Output dir not writable | 6 (validation of operating env) |
| Ctrl-C / SIGINT during work | 130 (POSIX convention; agents treat as 1) |

## Anti-patterns

- **All errors return 1.** The agent can't classify. Fix: split per the taxonomy.
- **Exit code disagrees with envelope.** `ok=false` with exit 0, or `ok=true` with exit 5. Fix: assert exit↔ok consistency at emit time.
- **Custom codes without documenting them.** Code 42 means "domain-specific thing"; agents have to read the source to learn that. Fix: reserve 8+ for domain-specific only and document in `--help`.
- **Using POSIX codes outside their conventional meanings.** 126 is "command found but not executable"; 127 is "command not found"; 128+N is "killed by signal N". Don't reuse these for business logic.
- **Returning 0 on partial failure.** Batch command processed 8 of 10 items, returns 0. Agent thinks all succeeded. Fix: emit `ok=false` with `error.code = "PARTIAL_FAILURE"`, exit code 6.
- **Returning 7 (transient) when the failure is actually permanent.** Agent retries forever, hits rate limits, gets banned. Fix: only emit 7 when the operation could plausibly succeed on the next call.

## Code samples

### Python

```python
class Exit:
    SUCCESS = 0
    CRASH = 1
    USAGE = 2
    NOT_FOUND = 3
    AUTH = 4
    CONFLICT = 5
    VALIDATION = 6
    TRANSIENT = 7

def exit_with_error(code: int, error_code: str, message: str, next_action: str = None) -> None:
    payload = {
        "ok": False,
        "error": {"code": error_code, "message": message},
        "schema_version": "1",
    }
    if next_action:
        payload["error"]["next_action"] = next_action
    if code == Exit.TRANSIENT:
        payload["error"]["retryable"] = True
    print(json.dumps(payload))
    sys.exit(code)
```

### Bash

```bash
readonly EXIT_SUCCESS=0
readonly EXIT_CRASH=1
readonly EXIT_USAGE=2
readonly EXIT_NOT_FOUND=3
readonly EXIT_AUTH=4
readonly EXIT_CONFLICT=5
readonly EXIT_VALIDATION=6
readonly EXIT_TRANSIENT=7

emit_error() {
    local code="$1" err_code="$2" msg="$3" next="${4:-}"
    if [ -n "$next" ]; then
        printf '{"ok":false,"error":{"code":"%s","message":"%s","next_action":"%s"},"schema_version":"1"}\n' \
            "$err_code" "$msg" "$next"
    else
        printf '{"ok":false,"error":{"code":"%s","message":"%s"},"schema_version":"1"}\n' \
            "$err_code" "$msg"
    fi
    exit "$code"
}

# usage:
emit_error "$EXIT_NOT_FOUND" "RESOURCE_NOT_FOUND" "no resource named '$1'" "run mytool list"
```

### Go

```go
package exit

import (
    "encoding/json"
    "os"
)

const (
    Success    = 0
    Crash      = 1
    Usage      = 2
    NotFound   = 3
    Auth       = 4
    Conflict   = 5
    Validation = 6
    Transient  = 7
)

type errEnvelope struct {
    OK            bool   `json:"ok"`
    Error         errBody `json:"error"`
    SchemaVersion string `json:"schema_version"`
}

type errBody struct {
    Code       string `json:"code"`
    Message    string `json:"message"`
    NextAction string `json:"next_action,omitempty"`
    Retryable  bool   `json:"retryable,omitempty"`
}

func WithError(code int, errCode, message, nextAction string) {
    body := errBody{Code: errCode, Message: message, NextAction: nextAction, Retryable: code == Transient}
    json.NewEncoder(os.Stdout).Encode(errEnvelope{OK: false, Error: body, SchemaVersion: "1"})
    os.Exit(code)
}
```

### Node

```typescript
export const Exit = {
    SUCCESS: 0,
    CRASH: 1,
    USAGE: 2,
    NOT_FOUND: 3,
    AUTH: 4,
    CONFLICT: 5,
    VALIDATION: 6,
    TRANSIENT: 7,
} as const;

export function exitWithError(
    code: number, errCode: string, message: string, nextAction?: string
): never {
    const body: Record<string, unknown> = { code: errCode, message };
    if (nextAction) body.next_action = nextAction;
    if (code === Exit.TRANSIENT) body.retryable = true;
    process.stdout.write(JSON.stringify({ ok: false, error: body, schema_version: "1" }) + "\n");
    process.exit(code);
}
```

### Rust (with std)

```rust
use std::process;

#[repr(i32)]
pub enum Exit {
    Success = 0,
    Crash = 1,
    Usage = 2,
    NotFound = 3,
    Auth = 4,
    Conflict = 5,
    Validation = 6,
    Transient = 7,
}

pub fn exit_with_error(code: Exit, err_code: &str, msg: &str, next_action: Option<&str>) -> ! {
    let envelope = serde_json::json!({
        "ok": false,
        "error": {
            "code": err_code,
            "message": msg,
            "next_action": next_action,
            "retryable": matches!(code, Exit::Transient),
        },
        "schema_version": "1",
    });
    println!("{}", envelope);
    process::exit(code as i32);
}
```

## Documenting exit codes in `--help`

Every CLI MUST list its exit codes in `--help`. The agent reads `--help` at integration time to wire branches; if the codes aren't there, the agent falls back to "0 vs non-0" and loses all the semantic value.

Example help text fragment:

```
EXIT CODES
  0  Success
  2  Usage error (bad flags or arguments)
  3  Resource not found
  4  Authentication failed
  5  State conflict (re-read and retry)
  6  Validation error (repair input)
  7  Transient failure (retry with backoff)
```

See `flags-and-discovery.md` for the full help-text-as-API contract.

## Cross-references

- `output-envelope.md` — `envelope.ok` MUST agree with the exit code; this file is the source of truth for the codes.
- `iterative-pattern.md` — validation (6) and conflict (5) drive the multi-turn repair loop.
- `subprocess-harness.md` — how the harness reads `$?` and dispatches to the right policy.
- `../common/error-strategy.md` — cross-surface error principles (CLI + MCP).
