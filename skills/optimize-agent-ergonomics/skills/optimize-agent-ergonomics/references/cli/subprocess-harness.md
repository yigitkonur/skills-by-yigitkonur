# cli/subprocess-harness.md

How an agent harness invokes an agent-ready CLI safely and parses the response. The harness IS the integration test — if your CLI doesn't survive being called this way, it isn't agent-ready. This file specifies the harness contract, ships Python / Node / Bash sample wrappers, catalogs the common failure modes, and explains how to use the harness as your final verification step before declaring a CLI agent-ready. Source: distilled from `optimize-agentic-cli/references/agent-integration.md`. Cross-link `../common/agent-integration.md` for the cross-surface principles.

## The harness contract

Every agent harness — Python `subprocess`, Node `child_process`, Bash with `timeout`, OpenAI tool-calling, Claude Code's `Bash` tool — does roughly the same six things:

1. **Append `--json`** (or the CLI's equivalent) to the command. Some harnesses also set `NO_COLOR=1` and `TERM=dumb` in the environment to suppress ANSI.
2. **Capture stdout and stderr separately.** stdout is the data channel; stderr is progress / diagnostics.
3. **Apply a timeout** (default 30s; longer for known-long commands like `apply` or `migrate`).
4. **Wait for the process to exit** OR the timeout to fire.
5. **Parse stdout as JSON.** On parse failure, fall back to raw text and surface the parse error.
6. **Classify by exit code.** Map the integer to the `class` per `exit-codes.md`. Then decide retry / surface / proceed based on `class` + the envelope's `error.retryable` field.

A tool that survives every step is "harness-correct." A tool that fails any step is broken from the harness's perspective regardless of how well it works under a human's hand.

## Python harness

A complete Python harness using stdlib `subprocess`. Captures both channels, applies timeout, parses JSON with fallback, classifies by exit code, retries on transient.

```python
"""Production-quality agent harness for an agent-ready CLI."""

import os
import subprocess
import json
import time
import random
from dataclasses import dataclass

EXIT_CLASS = {0: "success", 1: "crash", 2: "usage", 3: "not_found",
              4: "auth", 5: "conflict", 6: "validation", 7: "transient"}


@dataclass
class HarnessResult:
    ok: bool
    envelope: dict | None       # parsed JSON envelope, or None if parse failed
    error_class: str
    raw_stdout: str
    raw_stderr: str
    exit_code: int
    duration_ms: int


def invoke(cmd: list[str], *, timeout: int = 30, env_extra: dict | None = None) -> HarnessResult:
    """Invoke a CLI with --json; return a normalized result."""
    full_cmd = list(cmd)
    if "--json" not in full_cmd:
        full_cmd.append("--json")
    env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb", **(env_extra or {})}

    start = time.monotonic()
    try:
        proc = subprocess.run(full_cmd, capture_output=True, text=True,
                              timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired:
        return HarnessResult(False, None, "timeout", "", "", -1,
                             int((time.monotonic() - start) * 1000))

    duration = int((time.monotonic() - start) * 1000)
    cls = EXIT_CLASS.get(proc.returncode, f"unknown_{proc.returncode}")

    # Try to parse stdout as JSON; on NDJSON, take the last non-empty line.
    envelope: dict | None = None
    if proc.stdout.strip():
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            lines = [l for l in proc.stdout.splitlines() if l.strip()]
            if lines:
                try:
                    envelope = json.loads(lines[-1])
                except json.JSONDecodeError:
                    pass

    ok = bool(envelope and envelope.get("ok")) if envelope else (proc.returncode == 0)
    return HarnessResult(ok, envelope, cls, proc.stdout, proc.stderr, proc.returncode, duration)


def invoke_with_retry(cmd: list[str], *, max_attempts: int = 3,
                      base_delay: float = 1.0, timeout: int = 30) -> HarnessResult:
    """Retry on transient (exit 7); fail fast otherwise. Honors retry_after."""
    last: HarnessResult | None = None
    for attempt in range(max_attempts):
        last = invoke(cmd, timeout=timeout)
        if last.ok:
            return last

        err = (last.envelope or {}).get("error", {})
        retryable = bool(err.get("retryable")) or last.error_class == "transient"
        if not retryable:
            return last
        if attempt == max_attempts - 1:
            return last

        retry_after = float(err.get("retry_after") or err.get("retry_after_ms", 0) / 1000)
        delay = retry_after if retry_after > 0 else (base_delay * (2 ** attempt) + random.uniform(0, 1))
        time.sleep(delay)
    return last
```

For NDJSON streaming, replace `subprocess.run` with `subprocess.Popen`, iterate `proc.stdout` line-by-line, JSON-parse each line, and stop when the terminal envelope (the line with `"ok"`) arrives. The principle is the same; only the iteration changes.

Usage:

```python
result = invoke(["mytool", "greet", "--name=alice"])
if result.ok:
    greeting = result.envelope["result"]["greeting"]
elif result.envelope and result.envelope.get("error"):
    err = result.envelope["error"]
    print(f"Failed [{err['class']}/{err['code']}]: {err['message']}")

# Long-running with retry.
result = invoke_with_retry(["mytool", "deploy", "myservice"], max_attempts=3, timeout=120)
```

## Node harness

A complete Node harness using `child_process` with promise wrappers. Same contract as the Python harness.

```javascript
// harness.js — Node agent harness for an agent-ready CLI.
const { execFile } = require("child_process");
const { promisify } = require("util");

const EXIT_CLASS = {
  0: "success",
  1: "crash",
  2: "usage",
  3: "not_found",
  4: "auth",
  5: "conflict",
  6: "validation",
  7: "transient",
};

const execFilePromise = promisify(execFile);

async function invoke(cmd, { timeout = 30000, envExtra = {} } = {}) {
  const [bin, ...args] = cmd;
  if (!args.includes("--json")) args.push("--json");

  const env = { ...process.env, NO_COLOR: "1", TERM: "dumb", ...envExtra };
  const start = Date.now();

  let stdout = "";
  let stderr = "";
  let exitCode = 0;
  let timedOut = false;

  try {
    const result = await execFilePromise(bin, args, { timeout, env, encoding: "utf8" });
    stdout = result.stdout;
    stderr = result.stderr;
  } catch (err) {
    exitCode = err.code ?? 1;
    stdout = err.stdout || "";
    stderr = err.stderr || err.message || "";
    timedOut = err.killed === true || err.signal === "SIGTERM";
  }

  const duration_ms = Date.now() - start;
  const classification = timedOut ? "timeout" : EXIT_CLASS[exitCode] || `unknown_${exitCode}`;

  let envelope = null;
  if (stdout.trim()) {
    try {
      envelope = JSON.parse(stdout);
    } catch {
      // Try NDJSON: parse last non-empty line.
      const lines = stdout.split("\n").map((l) => l.trim()).filter(Boolean);
      if (lines.length) {
        try {
          envelope = JSON.parse(lines[lines.length - 1]);
        } catch {}
      }
    }
  }

  const ok = envelope ? Boolean(envelope.ok) : exitCode === 0;
  return {
    ok,
    envelope,
    errorClass: classification,
    rawStdout: stdout,
    rawStderr: stderr,
    exitCode,
    duration_ms,
  };
}

async function invokeWithRetry(cmd, { maxAttempts = 3, baseDelay = 1000, timeout = 30000 } = {}) {
  let last;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    last = await invoke(cmd, { timeout });
    if (last.ok) return last;

    const err = last.envelope?.error;
    const retryable = err?.retryable ?? last.errorClass === "transient";
    if (!retryable) return last;
    if (attempt === maxAttempts - 1) return last;

    const retryAfterMs =
      (err?.retry_after_ms ?? (err?.retry_after ?? 0) * 1000) ||
      baseDelay * 2 ** attempt + Math.random() * 1000;
    await new Promise((r) => setTimeout(r, retryAfterMs));
  }
  return last;
}

module.exports = { invoke, invokeWithRetry, EXIT_CLASS };
```

Usage:

```javascript
const { invoke, invokeWithRetry } = require("./harness");

(async () => {
  const result = await invoke(["mytool", "greet", "--name=alice"]);
  if (result.ok) {
    console.log(`Got: ${result.envelope.result.greeting}`);
  } else {
    const err = result.envelope?.error;
    console.error(`Failed [${err?.class}/${err?.code}]: ${err?.message}`);
    if (err?.suggestion) console.error(`  Suggestion: ${err.suggestion}`);
  }

  const deploy = await invokeWithRetry(["mytool", "deploy", "myservice"], {
    maxAttempts: 3,
    timeout: 120000,
  });
  console.log("deploy:", deploy.ok);
})();
```

## Bash harness

A pure-shell harness using `timeout` + `jq` + a `case` statement on exit code. Use this when the harness itself runs from a shell script (CI, makefile, glue).

```bash
#!/usr/bin/env bash
# harness.sh — pure-shell agent harness.
set -uo pipefail
# Note: NOT set -e — exit codes are signals, not failures.

invoke() {
  # Args: cmd... [--harness-timeout=SECS]
  local timeout=30
  local args=()
  for a in "$@"; do
    case "$a" in
      --harness-timeout=*) timeout="${a#*=}" ;;
      *) args+=("$a") ;;
    esac
  done
  # Append --json if not present.
  case " ${args[*]} " in
    *" --json "*) ;;
    *) args+=("--json") ;;
  esac

  local stdout stderr exit_code
  local stderr_file
  stderr_file="$(mktemp)"

  # `timeout` returns 124 on timeout. Exit codes from the underlying CLI flow through.
  stdout="$(NO_COLOR=1 TERM=dumb timeout "$timeout" "${args[@]}" 2>"$stderr_file")"
  exit_code=$?
  stderr="$(cat "$stderr_file")"
  rm -f "$stderr_file"

  # Classify.
  local class
  case "$exit_code" in
    0) class="success" ;;
    1) class="crash" ;;
    2) class="usage" ;;
    3) class="not_found" ;;
    4) class="auth" ;;
    5) class="conflict" ;;
    6) class="validation" ;;
    7) class="transient" ;;
    124) class="timeout" ;;
    *) class="unknown_$exit_code" ;;
  esac

  # Try to parse stdout as JSON; on NDJSON, take the last non-empty line.
  local envelope ok="false"
  if [ -n "$stdout" ]; then
    if echo "$stdout" | jq -e . >/dev/null 2>&1; then
      envelope="$stdout"
    else
      envelope="$(echo "$stdout" | tail -n +1 | tac | grep -m1 '.' || true)"
      if ! echo "$envelope" | jq -e . >/dev/null 2>&1; then
        envelope=""
      fi
    fi
  fi

  if [ -n "$envelope" ]; then
    ok="$(echo "$envelope" | jq -r '.ok // false')"
  elif [ "$exit_code" = "0" ]; then
    ok="true"
  fi

  # Emit a unified harness envelope on stdout.
  jq -n \
    --arg class "$class" \
    --argjson exit_code "$exit_code" \
    --arg envelope "$envelope" \
    --arg stderr "$stderr" \
    --argjson ok "$ok" \
    '{ok: $ok, error_class: $class, exit_code: $exit_code, envelope: ($envelope | fromjson? // null), stderr_summary: $stderr}'

  return $exit_code
}

# Usage:
#   result=$(invoke mytool greet --name=alice)
#   echo "$result" | jq '.envelope.result.greeting'
```

For retry, wrap `invoke` in a loop that branches on `error_class == "transient" || "timeout"` and sleeps with exponential backoff. Same shape as the Python `invoke_with_retry`. Less ergonomic than Python or Node but useful for shell-driven CI and Makefile integrations. Pair with `jq` on the parsing side.

## Common harness failure modes — and tool-side fixes

These are the failure modes every agent-ready CLI must survive. Test each before declaring done.

| Failure mode | Symptom | Tool-side fix |
|---|---|---|
| Timeout (CLI hangs) | Harness waits, sends SIGTERM, eventually SIGKILL | Detect non-TTY and skip prompts; require `--yes` or `--no-input`; honor SIGTERM and exit cleanly |
| Stdout buffer overflow | Harness gets partial output; JSON parse fails | Cap response sizes; paginate or truncate-with-signal; stream NDJSON for genuinely large output |
| Stderr noise on stdout | Harness sees `Loading...\n{...}` and JSON-parse fails | Strict separation: stderr for progress, stdout for envelope only |
| Mixed text and JSON | Harness sees `Done!\n{"ok":true}` and parses the wrong line | When `--json` is set, emit ONLY the envelope on stdout; suppress success prose |
| Malformed JSON | Pretty-printed JSON breaks NDJSON parsers; ANSI codes break JSON parsers | Compact JSON in single-shot mode; pretty-print only on TTY; suppress ANSI on non-TTY OR `NO_COLOR=1` |
| Exit code 1 for everything | Harness can't classify; treats all failures identically | Implement the 0–7 taxonomy from `exit-codes.md`; every error path picks the correct code |
| Stdout closed mid-write | CLI gets SIGPIPE on `head -1` and crashes with a stack trace | Ignore SIGPIPE OR catch the broken-pipe error; in Python, `signal.signal(signal.SIGPIPE, signal.SIG_DFL)` |
| Concurrent calls — race conditions | Multiple parallel CLIs corrupt shared state files | Atomic file operations (`os.rename` after temp-file write); honor `XDG_RUNTIME_DIR`; avoid global mutable state |
| Auth token expired mid-call | Tool returns auth error; harness has no refresh | Tool emits exit 4 + `error.next_action` with the refresh path; harness escalates |

## The harness as a unit test

The most reliable way to verify a CLI is agent-ready is to put it under a real harness and check the contract. Run this test set on every CLI before declaring it done:

```python
def test_agent_readiness(invoke):
    """Run before declaring a CLI agent-ready."""
    # 1. Happy path returns parseable success.
    r = invoke(["mytool", "version"])
    assert r.ok and r.envelope and r.envelope["ok"] is True
    assert r.envelope["schema_version"]

    # 2. Not-found returns retryable=False and a non-success class.
    r = invoke(["mytool", "get", "nonexistent"])
    assert not r.ok
    assert r.error_class == "not_found"
    assert r.envelope["error"]["retryable"] is False

    # 3. Transient errors return retryable=True with retry_after.
    r = invoke(["mytool", "trigger-rate-limit"])  # synthetic test endpoint
    assert r.error_class == "transient"
    assert r.envelope["error"]["retryable"] is True
    assert "retry_after" in r.envelope["error"] or "retry_after_ms" in r.envelope["error"]

    # 4. Validation errors carry field paths and suggested fixes.
    r = invoke(["mytool", "apply", "-f", "broken.yaml"])
    assert r.error_class == "validation"
    err = r.envelope["error"]
    assert "field" in err or "suggestion" in err

    # 5. Tool times out cleanly (doesn't hang past timeout).
    r = invoke(["mytool", "long-job"], timeout=1)
    assert r.error_class == "timeout"

    # 6. No stderr noise leaks into stdout when --json is set.
    raw = subprocess.run(["mytool", "list", "--json"], capture_output=True, text=True)
    assert raw.stdout.strip().startswith("{")  # JSON envelope only.

    # 7. Stdout/stderr separation under --json.
    r = invoke(["mytool", "version"])
    # raw_stderr can have progress/warnings but stdout should parse as JSON.
    assert r.envelope is not None
```

When all seven pass, the CLI meets the agent-readiness bar.

## Cross-references

- For the cross-surface harness contract, read `../common/agent-integration.md`.
- For the canonical envelope the harness parses, read `output-envelope.md`.
- For exit-code taxonomy the harness classifies on, read `exit-codes.md`.
- For NDJSON streaming the harness consumes, read `iterative-pattern.md`.
- For headless auth that the harness inherits, read `auth-headless.md`.
- For new-CLI design that survives the harness on day one, read `architect-new.md`.
- For language templates the harness calls, read `code-templates.md`.
