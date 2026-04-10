# Python Integration

Use subprocess wrappers around the released CLI instead of reimplementing MCP in Python for smoke tests.

## Minimal wrapper

```python
import json
import subprocess


def run_mcpc(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["mcpc", *args],
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_json(*args: str):
    code, stdout, stderr = run_mcpc("--json", *args)
    stream = stdout if stdout.strip() else stderr
    payload = json.loads(stream) if stream.strip() else None
    return code, payload, stderr
```

## Current connect shape

```python
code, payload, stderr = run_json("connect", "https://research.yigitkonur.com/mcp", "@research")
```

If you build higher-level wrappers, normalize Python-friendly names to the real hyphenated flags:

- `no_profile` -> `--no-profile`
- `client_id` -> `--client-id`
- `client_secret` -> `--client-secret`

## Task helpers worth exposing

- `tools-call(..., task=True)` -> append `--task`
- `tools-call(..., detach=True)` -> append `--detach`
- wrappers for `tasks-list`, `tasks-get`, and `tasks-cancel`

## Error-handling rule

Nonzero JSON failures often place the structured payload on `stderr`, not `stdout`.
Parse `stderr` first when `stdout` is empty.
