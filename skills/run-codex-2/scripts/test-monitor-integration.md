# test-monitor-integration.mjs

Smoke harness for the dispatcher. Verifies the per-mode Monitor hints parse as JS, carry the right shape (`codex-monitor.sh` for fleet modes, `tail -F | awk fflush()` for single), have their `timeout_ms` clamped to Monitor's hard ceiling (1h), and that core argv-validation surface (strict parse, concurrency gate, rescue-subset selection) holds.

## Inputs

```bash
node test-monitor-integration.mjs
```

No flags. Reads the dispatcher (`run-codex-2.mjs`) at the same path; runs 10 scenarios; reports pass/fail.

## Outputs

```
test-monitor-integration.mjs — run-codex-2 Monitor + dispatcher harness

[1] exec mode tool_hint
  PASS  monitor.tool_hint exists and is a string
  PASS  tool_hint parses as JS expression
  ...

[10] selectRescueSubset
  PASS  failed-only matches failed entries
  ...

=========================================
PASS: 57   FAIL: 0
OK
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All scenarios pass |
| 1 | At least one scenario fails (the failure is printed inline) |
| 2 | Harness crash (uncaught exception) |

## Scenarios covered

1. **exec mode hint parses as JS.** `new Function("return (" + hint.replace("Monitor","") + ")")()` succeeds; the command invokes `codex-monitor.sh`.
2. **batch mode hint parses as JS.** Same fleet shape as exec.
3. **single mode hint parses as JS.** Tail through `awk '{ print; fflush(); }'` and `tail -n +1 -F`.
4. **review mode hint parses as JS.** Same fleet shape as exec.
5. **Monitor timeout clamp.** Oversized `timeout_ms` (99h input) is clamped to `MONITOR_HARD_MAX_MS = 3,600,000`.
6. **Monitor-hint quoting safety.** Description with backslashes, double-quotes, and newlines round-trips through `JSON.stringify` cleanly.
7. **Awk fflush correctness.** A 5-event producer with 100 ms sleeps reaches the consumer with > 200 ms total span — events streamed live, not bunched at producer EOF.
8. **parseArgsStrict — unknown options error out.** Known flags accepted; `--bogus-flag` produces `error.code="unknown_option"` with the offending flag in the message; stray `-x` short flags rejected.
9. **resolveConcurrency soft gate + override capture.** Default cap accepted; above-default rejected without `--i-have-measured`; with justification, the override is captured at `{value, justification, set_at}`. Above hard-cap (20) gated identically. Above absolute ceiling (100) rejected unconditionally. Flag wins over `JOBS` env.
10. **selectRescueSubset.** `failed-only` / `never-started-only` / `all-non-done` / `ids:s1,s2` resolve correctly; unknown ids surface; garbage subset reports invalid.

## Notes

Run after every dispatcher change to catch regressions in Monitor template hygiene AND argv-validation surface. Pre-flight gate: this passes before the dispatcher ships.

The harness does not need a real codex binary, manifest, or runner — it imports the dispatcher's exported pure functions and exercises them directly.
