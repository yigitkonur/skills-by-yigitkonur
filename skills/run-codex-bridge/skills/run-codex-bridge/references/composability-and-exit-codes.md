# Composability and exit codes

Use this file when you need shell-safe orchestration or machine-readable output.

## Output modes

- `--output text` — human-readable
- `--output json` — machine-readable

Prefer JSON in shell scripts:

```bash
codex-worker --output json run task.md --async
codex-worker --output json read <thread-id>
codex-worker --output json thread list --cwd "$PWD"
codex-worker --output json request list --status pending
```

## Pipe-friendly examples

Extract the thread id from an async run:

```bash
THREAD_ID="$(codex-worker --output json run task.md --async | jq -r '.threadId')"
```

Find failed threads in one cwd:

```bash
codex-worker --output json thread list --cwd "$PWD" \
  | jq -r '.data[] | select(.status == "failed") | .id'
```

## Inspection vs lifecycle commands

Inspection-style commands:
- `read`
- `logs`
- `thread read`
- `thread list`
- `request list`
- `request read`
- `doctor`
- `model list`
- `account read`
- `account rate-limits`
- `skills list`
- `app list`
- `daemon status`

Lifecycle-style commands:
- `run`
- `send`
- `thread start`
- `thread resume`
- `turn start`
- `turn steer`
- `turn interrupt`
- `request respond`
- `wait`
- `daemon start`
- `daemon stop`

Do not rely on a special blocked-request exit code unless you verified it in the current runtime. Prefer JSON status and `request list`.

## Anti-patterns

| Avoid | Use instead |
|---|---|
| parsing human text output | `--output json` + `jq` |
| assuming `task` or `session` helper commands exist | use `run`, `send`, `thread`, `turn`, `wait`, `request respond` |
| assuming blocked runs auto-answer | inspect `request list --status pending` |
