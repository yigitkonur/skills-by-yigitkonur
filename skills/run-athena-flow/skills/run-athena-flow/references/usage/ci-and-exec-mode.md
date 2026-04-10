# CI and Exec Mode

```bash
athena-flow exec "<prompt>"
```

Runs Athena non-interactively. No TUI, no input bar. Designed for CI pipelines and scripts.

## Exec-Only Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--json` | Emit JSONL events to stdout | off |
| `--output-last-message=<path>` | Write final assistant message to file | — |
| `--ephemeral` | Don't persist session data | off |
| `--on-permission=<policy>` | Permission request policy | `fail` |
| `--on-question=<policy>` | AskUserQuestion policy | `fail` |
| `--timeout-ms=<ms>` | Hard timeout for the run | — |
| `--continue[=<sessionId>]` | Resume most recent or specific session | — |

## Permission Policies (`--on-permission`)

| Value | Behavior |
|-------|----------|
| `allow` | Automatically allow all permission requests |
| `deny` | Automatically deny all permission requests |
| `fail` | Fail the run on any permission request (default) |

## Question Policies (`--on-question`)

| Value | Behavior |
|-------|----------|
| `empty` | Respond with empty string |
| `fail` | Fail the run on any question (default) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Permission request with `--on-permission=fail` |
| 3 | Question with `--on-question=fail` |
| 4 | Timeout exceeded |
| 5 | Agent error |
| 6 | Session not found (for `--continue`) |
| 7 | Hook registration failure |

## JSONL Output Format

With `--json`, structured events are emitted to stdout:

| Event Type | Description |
|------------|-------------|
| `exec.started` | Execution began |
| `runtime.event` | A RuntimeEvent from the harness |
| `runtime.decision` | A decision made by Athena |
| `process.started` | Agent process spawned |
| `process.exited` | Agent process exited |
| `exec.completed` | Execution finished successfully |
| `exec.error` | Execution failed |

## Examples

```bash
# CI-friendly: JSON output, auto-deny permissions, ignore questions
athena-flow exec "run tests" --json --on-permission=deny --on-question=empty

# With timeout
athena-flow exec "lint all files" --timeout-ms=60000

# Ephemeral (no session persistence)
athena-flow exec "check for security issues" --ephemeral

# Save the final message
athena-flow exec "summarize changes" --output-last-message=./summary.txt

# Continue a previous session
athena-flow exec "continue previous work" --continue
```

## GitHub Actions

```yaml
- name: Run Athena
  run: |
    npx @athenaflow/cli exec "run all tests and report results" \
      --json \
      --on-permission=deny \
      --on-question=empty \
      --timeout-ms=300000 \
      --ephemeral
```

## GitLab CI

```yaml
athena-test:
  script:
    - npx @athenaflow/cli exec "run all tests and report results"
        --json
        --on-permission=deny
        --on-question=empty
        --timeout-ms=300000
        --ephemeral
```

## Standard Flags in Exec Mode

All standard flags work in exec mode too:

- `--workflow=<name>` — Activate a workflow
- `--isolation=<preset>` — Set isolation level
- `--plugin=<path>` — Load a plugin
- `--project-dir=<path>` — Set project directory
- `--model=<model>` — Override model
