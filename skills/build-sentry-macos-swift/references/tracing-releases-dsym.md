# Tracing, Releases & dSYM (Symbolication Without CI)

## Performance tracing on macOS

On native macOS there is **no automatic root transaction** (app-start/UIViewController
instrumentation is iOS-only). Value comes from **manual transactions + network tracking**.

Enable deliberately — start at 0 and raise consciously (spans are events too; they cost
quota and must be scrubbed):

```swift
options.tracesSampleRate = 0.2          // or tracesSampler for per-transaction rates
```

Wrap meaningful operations (current, non-deprecated API — `startTransaction`/`startChild`/
`finish`, not the `startSpan`-first spec which isn't the Cocoa surface):

```swift
let tx = SentrySDK.startTransaction(name: "process-file", operation: "job")
let step = tx.startChild(operation: "download")
// ...
step.finish()
tx.setMeasurement(name: "input_seconds", value: 42, unit: MeasurementUnitDuration.second)
tx.finish()
```

Span names/descriptions/data are events — keep user content out of them.

### Network tracking + backend correlation

`enableSwizzling` + `enableAutoPerformanceTracing` (both default on) instrument `URLSession`.
`sentry-trace`/`baggage` headers attach to outgoing requests per `tracePropagationTargets`.
**Narrow the targets** to your backend host so you don't leak trace headers to third parties:

```swift
options.tracePropagationTargets = ["https://api.yourbackend.example"]   // default is all requests
```

If the backend is yours and runs a Sentry SDK, it can continue the trace for end-to-end
distributed tracing. Only pursue this after basic crash reporting is solid; verify one
request produces a single linked trace before relying on it.

## Releases & environments

- **Leave `releaseName` auto** — it derives to `bundleID@CFBundleShortVersionString+CFBundleVersion`,
  which already matches a Sparkle appcast's `sparkle:shortVersionString`/`sparkle:version`.
  Only override if you set a custom release, and derive it from the same `CFBundle*` values.
- **`environment`** — map from build config (`production` / `staging` / `development`).
- **`dist`** — optional (`CFBundleVersion`); tagging only, **not** needed for symbolication.
- **Release health** — `enableAutoSessionTracking` (default on, macOS-supported) gives
  crash-free sessions/users. Nothing to do beyond leaving it on.

Associate commits from a **local git tree** (no CI needed) — unlocks suspect commits:

```bash
V="com.example.App@1.4.2+318"
sentry-cli releases new "$V"
sentry-cli releases set-commits "$V" --auto     # uses local git tree; no repo integration needed
sentry-cli releases finalize "$V"
sentry-cli deploys new --release "$V" -e production   # optional deploy marker
```

## dSYM upload without CI (the macOS-indie reality)

Readable macOS crash traces require the build's **dSYMs** uploaded to Sentry. With no CI,
this is a **local** step.

### Two credentials — don't confuse them

| Credential | Secret? | Where |
|---|---|---|
| **DSN** | No | embedded in the app (client key) |
| **`SENTRY_AUTH_TOKEN`** (`sntrys_…`, org-scoped) | **YES** | gitignored `~/.sentryclirc` or env var — never committed |

```gitignore
.sentryclirc
```

### The build setting

```
DEBUG_INFORMATION_FORMAT = dwarf-with-dsym   # confirm for the config you ship
```
```bash
ls YourApp.xcarchive/dSYMs/   # → YourApp.app.dSYM
```

### Upload — Makefile step (recommended when there's no CI)

```bash
sentry-cli debug-files upload \
  --org "$SENTRY_ORG" --project "$SENTRY_PROJECT" \
  YourApp.xcarchive/dSYMs
# add --include-sources ONLY if you accept uploading source code (fine for private repos)
```

Wire it as a Makefile target that runs after the notarized archive. Uploading the whole
`dSYMs/` folder in one invocation satisfies the "same-invocation" integrity rule.

### Or an Xcode Run Script build phase

Sentry's documented script uses `$DWARF_DSYM_FOLDER_PATH`. It's valid, but **do not hardcode
the auth token** in a committed build phase — read it from the environment. For a no-CI
Makefile build, the discrete Makefile step above is cleaner.

### Facts that save time

- **Symbolication matches by Debug UUID, not release/dist** — a dSYM with no release still
  symbolicates any build carrying that UUID.
- **No SPM auto-upload plugin exists** (feature request closed "not planned").
- Notarization/Hardened Runtime don't affect dSYM generation (built before signing).
- Verify locally with `sentry-cli debug-files check <path>`; confirm server-side in
  **Project Settings → Debug Files**.

## Keep three things aligned per shipped build

The SDK release (auto), the uploaded dSYMs (from that exact archive), and the Sparkle
appcast version. They align automatically if you upload dSYMs from the archive you ship and
don't hand-edit `releaseName`.
