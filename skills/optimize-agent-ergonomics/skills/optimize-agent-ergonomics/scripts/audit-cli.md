# audit-cli.sh

Run this helper when Mode A needs a quick CLI preflight before a full audit.

## Inputs

```bash
bash scripts/audit-cli.sh [--json-flag FLAG|none] [--timeout SECONDS] -- <command> [args...]
```

- `<command> [args...]` must be a safe, read-only probe.
- `--json-flag` defaults to `--json`; pass `none` when the probe already emits JSON.
- `--timeout` defaults to 10 seconds when GNU `timeout` or `gtimeout` is available.

## Outputs

The script prints a markdown scorecard with:

- help availability
- probe completion
- stdout JSON parseability
- stderr separation signal
- ANSI-free stdout signal
- exit-code taxonomy signal

The script exits `0` when the safe probe passes core checks, `1` when the probe exposes likely agent-readiness issues, and `2` for usage errors.

## Limitations

This is not a complete CLI audit. It exercises one safe command and cannot prove destructive operations, auth flows, all exit classes, retries, pagination, streaming, or every subcommand. Use `../references/cli/audit-checklist.md` for the complete audit.
