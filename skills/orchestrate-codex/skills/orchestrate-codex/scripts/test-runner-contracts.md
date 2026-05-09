# test-runner-contracts.mjs

Dispatcher/runner contract test harness. Runs all modes through temp dry-run paths without live Codex calls.

## Inputs

No flags.

The harness sets:

```bash
ORCHESTRATE_SKIP_PREFLIGHT=1
ORCHESTRATE_RUNNER_FOREGROUND=1
```

## Coverage

- Dispatcher help and bad-argument envelopes.
- `exec` dry-run runner invocation and manifest entry shape.
- `batch` render → run dry-run path, answer files, and audit report.
- `single` inline prompt, deterministic `single` entry id, answer path, and JSONL path.
- `review` branch-list parsing, classifier path, and terminal `converged` state.
- `rescue` classification plus `--redo failed` redispatch through the original runner.

## Outputs

Pass/fail lines on stdout and a final summary:

```text
PASS: 30  FAIL: 0
```

Exit code `0` means every contract passed. Exit code `1` means at least one contract failed.
