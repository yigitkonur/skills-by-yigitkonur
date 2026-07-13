# Advanced Instrumentation (Breadcrumbs, Tags, Scope, Context, Logs)

This is the heart of "deep, not basic." All of it works on macOS. **Every example assumes
the scrubber is in place** (`privacy-and-scrubbing.md`) — never pass user content into any
of these APIs.

## Breadcrumbs — the trail before an event

```swift
let crumb = Breadcrumb()
crumb.level = .info
crumb.category = "recording"          // fixed vocabulary
crumb.message = "Session started"     // no filenames, no user text
SentrySDK.addBreadcrumb(crumb: crumb)
```

- Confirmed fields on the Apple docs: `category`, `level`, `message`. (`type`, `data`,
  `timestamp` exist in the SDK; verify against source before relying on `.data`/`.type` —
  the scrubber drops `data` anyway.)
- Keep the trail small: `maxBreadcrumbs = 20`, `enableNetworkBreadcrumbs = false`.
- **Good breadcrumbs** are lifecycle/operation milestones with fixed strings + numbers:
  `recording: started/stopped (duration)`, `transcription: submitted/completed (http.status)`,
  `update: found / relaunching`, `lifecycle: onboarding completed`.

## Tags — the searchable, filterable dimensions

Tags make issues triageable. Use **fixed vocabularies**, never free-form user strings.

```swift
SentrySDK.configureScope { scope in
    scope.setTag(value: "production", key: "channel")
    scope.setTag(value: "soniox-batch", key: "subsystem")   // which component
    scope.setTag(value: "openrouter", key: "provider")      // which dependency
}
```

Per-event tags via the capture closure (see scope, below).

## Scope & context — attach structured detail

```swift
SentrySDK.configureScope { scope in
    scope.setContext(value: [
        "engine": "batch",
        "streaming": true,
        "retry_count": 2          // numbers are safe; user strings are not
    ], key: "job")                // free-form key except "type" (reserved)
    scope.setLevel(.info)
}
```

- `setContext` is the current structured API. **`setExtra` is deprecated** — don't use it.
- **Do not set an identifying `user`** for a privacy-sensitive app — keep `event.user = nil`
  in the scrubber (also removes the `{{auto}}` IP placeholder locally).
- Oversized context is rejected server-side (`413`) — keep it small; never dump blobs.

### Global vs. per-event scope

```swift
// Per-event scope (the Cocoa "withScope" pattern — a trailing closure on capture):
SentrySDK.capture(message: "Enhancement failed") { scope in
    scope.setLevel(.warning)
    scope.setTag(value: "openrouter", key: "provider")
}
```

Exceptions thrown *inside* a scope closure are silently ignored — keep it trivial.

### Fingerprinting — control grouping

When Sentry's default grouping splits or merges issues wrong, override with a fingerprint
(fixed tokens only):

```swift
SentrySDK.capture(error: error) { scope in
    scope.setFingerprint(["transcription-timeout", "batch"])
}
```

## Manual capture

```swift
SentrySDK.capture(message: "Storage fell back to in-memory")
SentrySDK.capture(error: someError)                 // any Error / NSError
SentrySDK.capture(error: someError) { scope in ... } // with per-event scope
```

## Structured logs — and the OSLog reality

Sentry structured logs are **GA (9.0.0)** and work on macOS:

```swift
options.enableLogs = true
```
```swift
let log = SentrySDK.logger
log.info("Updated profile")
log.warn("Rate limit reached", attributes: ["endpoint": "/transcribe"])   // String/Int/Double/Bool only
log.error("Payment failed", attributes: ["code": 402])
// levels: trace, debug, info, warn, error, fatal
options.beforeSendLog = { entry in entry.level == .info ? nil : entry }    // filter
```

**There is NO official `os.Logger` → Sentry bridge** (two feature requests closed
"not planned"). Maintainers advise **against** wrapping `os.Logger`. Instead, at the
specific sites you want visible remotely, call `SentrySDK.logger.*` (or `addBreadcrumb`)
alongside the existing `os.Logger` call — a thin dual-log wrapper keeps it one line. Don't
mirror your whole log volume into Sentry.

**Privacy landmine:** Swift string interpolation in logs auto-extracts attributes —
`log.info("User \(userId) …")` captures `userId` as structured data. **Never interpolate
user/transcript/path data into a Sentry log.**

## Attachments — use with restraint

`Attachment(path:)` / `Attachment(data:filename:)` + `scope.addAttachment` work on macOS
(`maxAttachmentSize` default 200 MiB). **Do not attach user media, transcripts, or logs
containing user content.** If you must attach a diagnostic, scrub it first and keep it tiny.
Attachments count toward quota as soon as stored, even if the event is later dropped.

## The one rule that ties it together

If you're about to type a variable that could hold what the user said, wrote, pasted, or a
path with their name in it — **stop.** Instrument the *shape* of the event (subsystem, code,
count, duration), never its contents.
