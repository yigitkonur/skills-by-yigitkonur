# Verify With Evidence & Troubleshoot

A clean compile is not proof. Sentry integration is only "done" when a real event lands,
symbolicated, carrying no PII. Do this before declaring done.

## The verification workflow

1. **Detach the debugger.** In the scheme's Run action, **uncheck "Debug executable."**
   Crash and hang handlers do not install under a debugger — skip this and your test
   silently captures nothing.

2. **Smoke-test a message.** Add temporarily, run, confirm it appears in the dashboard
   within seconds:
   ```swift
   SentrySDK.capture(message: "sentry smoke test")   // TEMP — remove after
   ```
   (If the integration is opt-in, enable the toggle first.)

3. **Test a real crash and an uncaught NSException.** Trigger each, relaunch (crashes send on
   next launch), confirm both appear:
   ```swift
   // TEMP — remove after verifying
   // fatalError("sentry crash test")
   // NSException(name: .genericException, reason: "nsexception test", userInfo: nil).raise()
   ```

4. **Confirm symbolication.** The crash frames must show function names + line numbers — not
   raw addresses. Unreadable frames = dSYMs not uploaded for that build's UUID
   (`tracing-releases-dsym.md`).

5. **Audit one payload for PII.** Open a captured event and confirm: **no user content, no
   `/Users/<name>` paths, no IP address, no secrets.** If anything leaks, fix the scrubber
   before shipping (`privacy-and-scrubbing.md`).

6. **Test on a real signed build.** For a notarized + Hardened-Runtime app, do steps 3–4
   once on an actual signed build to close the "does crash capture survive Hardened Runtime"
   question empirically.

7. **Clean up.** Remove all test triggers. Report the **rung reached**: compiled / event
   received / crash symbolicated / privacy-audited / verified on signed build.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| No events at all | Debugger attached (uncheck "Debug executable"); or DSN wrong; or init not on main thread. Set `options.debug = true` to see SDK internals in the Xcode console. |
| Events appear but crashes don't | Same debugger caveat; crashes send on **next launch**, not immediately. |
| Uncaught NSException missing | `enableUncaughtNSExceptionReporting` not set (macOS). |
| Duplicate crash reports | Both `enableUncaughtNSExceptionReporting` AND the `SentryCrashExceptionApplication` principal-class swap enabled — pick one. |
| Stack traces unreadable (addresses) | dSYMs not uploaded, or uploaded for a different build UUID; `DEBUG_INFORMATION_FORMAT` not `dwarf-with-dsym`. |
| PII in events | Scrubber missing/incomplete; `beforeSend` not set; IP not suppressed server-side. |
| Hang events on permission prompts | Wrap prompt sites with `pause`/`resumeAppHangTracking()`. |
| Tracing data missing | `tracesSampleRate` still 0/nil; or `enableAutoPerformanceTracing` off. |
| Profiling data missing | `configureProfiling { $0.sessionSampleRate }` is 0; for `.trace` lifecycle, tracing must be on. |
| `profilesSampleRate` / `integrations` / `enableTracing` won't compile | Removed in 9.0.0 — use `configureProfiling`, `enable*` flags, `tracesSampleRate`. |
| `sessionReplay` / `attachScreenshot` seem to do nothing | Unavailable on native macOS (matrix) — remove them. |
| Events dropped past quota | Free-tier quota exceeded (drops, doesn't bill) — lower `tracesSampleRate`/`sampleRate`. |

## What "done" reports

State plainly: the chosen signals + sample rates; the privacy posture (scrub list + opt-in
state); files changed; the dSYM upload mechanism; and the verification rung reached (with the
issue URL if you got one). Name any macOS feature deliberately skipped and why.
