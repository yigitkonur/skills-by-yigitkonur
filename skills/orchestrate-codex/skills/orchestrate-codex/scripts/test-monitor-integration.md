# test-monitor-integration.mjs

Monitor tool smoke harness. Verifies the dispatcher's per-mode Monitor hints parse as JS, carry `--line-buffered` in grep pipes, carry `fflush()` in awk pipes, and stream events live (events arrive within 250 ms of emission, not blocked until producer EOF).

## Inputs

```bash
node test-monitor-integration.mjs
```

No flags. Reads the dispatcher (`orchestrate-codex.mjs`) at the same path; runs 8 scenarios; reports pass/fail.

## Outputs

```
==> Scenario: exec mode hint parseability
PASS: tool_hint parses as JS
  description: orchestrate-codex exec fleet (run_id=...)
  persistent: true

==> Scenario: batch mode hint parseability
PASS: tool_hint parses as JS

...

==> Scenario: live-streaming
PASS: 3 events received within 250ms each (line-buffered confirmed)

==> Scenario: failure-coverage grep
PASS: filter surfaces all 5 terminal-state lines

PASS: 43   FAIL: 0
OK
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All scenarios pass |
| 1 | At least one scenario fails (the failure is printed inline) |

## Scenarios covered

1. **exec mode hint parses as JS.** `new Function("return (" + hint.replace("Monitor","") + ")")()` succeeds.
2. **batch mode hint parses as JS.**
3. **single mode hint parses as JS.**
4. **review mode hint parses as JS.**
5. **Failure-coverage grep.** Synthetic stream emits success + failure + crash; the filter must surface ALL three (silent failure = bug).
6. **Line-buffered streaming.** Synthetic stream emits 3 events with 1 s sleeps between; filter must emit each event within 250 ms of its source.
7. **Awk fflush correctness.** Same pattern but through an awk pipe.
8. **Monitor-hint quoting safety.** Verifies the dispatcher's hint strings survive shell-injection-resistant quoting.

## Notes

Run after every dispatcher change to catch regressions in Monitor template hygiene. Pre-flight gate: this passes before the dispatcher ships.

The harness uses `/tmp` stubs for the bash runners and Python helpers (so it doesn't depend on the parallel subagent's output to run). Stubs are documented inline; production users never see them.
