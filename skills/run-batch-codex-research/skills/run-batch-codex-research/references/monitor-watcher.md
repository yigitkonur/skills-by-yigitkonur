# Monitor watcher — how the awk filter works

The watcher is the bridge between the runner's structured event log and Claude's conversation. It must be cheap, line-buffered, and never silent on a failure.

## The full pipeline

```
runner ──> logs/_runner.log ──> tail -F ──> awk filter ──> Monitor stdout
            (line-by-line             |          |
             append-only              |          └─ enriches DONE/SKIP with byte size
             from echo statements)    └─ follows truncation/recreation
```

Each `echo` in `run_one` becomes one line. `tail -F` re-reads the file as it grows; awk processes each line, optionally calls `wc -c` on the corresponding answer file, and prints the enriched event. Monitor delivers each printed line as a notification.

## Why every awk action ends with `fflush()`

Without `fflush()`, awk's stdout is block-buffered (typically 4–8 KB). On a sparse event stream — say, one DONE every 10 minutes — a single event could sit in the buffer for hours before any downstream sees it. Monitor would appear silent.

`fflush()` forces awk to emit the line immediately. Three or four extra fflush calls per second cost nothing.

## Why grep would be wrong here

A simpler `tail -F log | grep -E 'DONE|FAIL|SKIP|---'` would work for plain forwarding, but it can't enrich events with byte sizes. Once you need conditional logic (e.g. "only flag DONEs below MIN bytes"), awk is the right tool. And grep needs `--line-buffered` for the same reason awk needs `fflush()` — without it, events are delayed by buffering.

## The `sizeof()` function

```awk
function sizeof(name,   cmd, n) {
  cmd = "wc -c < " ANS "/" name ".md 2>/dev/null"
  cmd | getline n
  close(cmd)
  return n+0
}
```

Notes:

- The 4th-onward parameters in awk function signatures are **local variables**, not arguments. Awk has no built-in `local`; the convention is extra args after the real ones, separated by extra whitespace for visual cue.
- `cmd | getline n` reads one line from the command, which `wc -c` always produces (one number per file).
- `close(cmd)` is required — awk caches piped commands. Without close, after enough invocations awk hits the open-file limit and `getline` starts returning empty strings. Quietly. The size column would gradually fall to zero. (The bug only shows up around event 200+, which is exactly when you'd stop reading the events carefully.)
- `+0` coerces the string to a number (so the flag comparison works as numeric, not lexicographic — `"9999" < "10000"` is true lexicographically but false numerically).

## Why MIN flagging only on DONE/SKIP

START events fire before the answer file exists. Sizing them is meaningless (it'd report zero or stale data from a previous run). Same for FAIL — there's no answer to size.

DONE = answer just written, size is fresh.
SKIP = answer pre-existed, size is whatever was on disk when the runner started.

## Permission and process notes

- Monitor inherits Bash's permission rules. If your settings.local.json allows Bash, Monitor inherits that. If you've blocked specific commands, the same blocks apply.
- The watcher exits when its `tail -F` exits. `tail -F` does NOT exit when the tailed file stops growing — it keeps polling. You must `TaskStop` the monitor task to release the watcher.
- The watcher's awk and tail processes show in `pgrep -f watch-runner` after launch. Killing them manually also stops the Monitor.

## Tuning MIN

Default MIN is 10000 bytes. Calibrate to your prompt:

| Prompt shape | Reasonable MIN |
|---|---|
| Short summary (3–5 sentences expected) | 500–1000 bytes |
| Structured feature reference (this skill's example) | 8000–12000 bytes |
| Long research dump (10+ KB expected) | 15000+ bytes |

If MIN is too high, every answer flags `[SMALL]` and the signal is useless. If too low, weak outputs slip through. Tune after seeing one full run's distribution — the audit script reports stats to help.

## Variants worth knowing

**Suppress SKIPs in conversation noise:**

```awk
/^SKIP / { next }   # don't print SKIPs at all
```

Useful on reruns where 95% of events are SKIP and you only care about the new work. The audit script still surfaces SKIP totals from the log.

**Print only flagged events:**

```awk
/^DONE / {
  n = sizeof($2)
  if (n < MIN) { print $0 " (" n " bytes) [SMALL]"; fflush() }
  next
}
```

Even quieter — only suspicious DONEs surface. Combine with a separate summary line at end.

**Surface FAILs aggressively:**

```awk
/^FAIL / { print "ALERT: " $0; fflush(); next }
```

Useful when running a 200+ batch overnight and you want failures to jump out.

## Coverage check before arming

Before launching, ask the question every Monitor doc emphasises: **if the runner crashes mid-batch, would the watcher emit anything?**

Yes — because:

- A crashing run_one inside one job doesn't kill the runner; the FAIL line still emits.
- A crashing runner stops appending to the log, so tail goes idle. Past events are still visible, but no new ones arrive. Silence then is "all done or runner died" — not "all good silently."
- The "--- all jobs finished ---" sentinel is the positive signal that the runner exited cleanly. Its absence is meaningful.

If you genuinely want a heartbeat-style positive-liveness signal, append a `while sleep 60; do echo "PING $(date -u)"; done &` line in the runner. Most users don't need it.
