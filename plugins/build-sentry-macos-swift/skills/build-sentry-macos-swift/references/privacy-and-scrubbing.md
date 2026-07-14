# Privacy & Scrubbing (The Crux)

Get this wrong and you exfiltrate user data to a third party. For any macOS/Swift app that
touches user content — documents, text, clipboard, audio, files, PII — this section is
non-negotiable. Defense in depth: **client scrubbing (primary) + server-side rules (backstop)
+ opt-in consent.**

## What must NEVER reach Sentry

| Data | Where it hides in an event |
|---|---|
| User text / documents / transcripts / clipboard | message, exception `value`, breadcrumb message, log attributes, context, attachments |
| **File paths** (non-sandboxed → `/Users/<name>/…`) | stack frames, error strings — the username deanonymizes the user |
| Filenames | breadcrumbs, messages |
| Secrets / API keys / license & device IDs | context, tags, request data |
| **IP address** | added automatically by Sentry as `{{auto}}` — see below |

## Layer 1 (primary): client-side scrubbers

Options that shrink the leak surface (also in the init block):

```swift
options.sendDefaultPii = false
options.maxBreadcrumbs = 20
options.enableNetworkBreadcrumbs = false      // URLs can carry sensitive params
options.enableCaptureFailedRequests = false   // avoid auto-capturing request metadata as events
options.attachScreenshot = false              // no-op on macOS, defensive
options.attachViewHierarchy = false
options.beforeSend = SentryScrub.event
options.beforeBreadcrumb = SentryScrub.breadcrumb
```

The scrubber — the primary control. Inspect and redact every event/breadcrumb on-device:

```swift
// COMPILE-CHECK THIS BLOCK against your pinned SDK. The bridged property names
// (event.message?.formatted, SentryMessage(formatted:), event.exceptions, event.extra,
// event.breadcrumbs) are the ones most likely to have drifted. Preserve the INTENT:
// null the user, redact message/exception, drop extra/data, strip home paths, cap length.
import Sentry

enum SentryScrub {
    static func event(_ event: Event) -> Event? {
        event.user = nil                                   // drops {{auto}} IP locally too
        if let m = event.message?.formatted {
            event.message = SentryMessage(formatted: redact(m))
        }
        event.exceptions?.forEach { $0.value = $0.value.map(redact) }
        event.extra = nil
        event.breadcrumbs = event.breadcrumbs?.compactMap { breadcrumb($0) }
        return event
    }

    static func breadcrumb(_ crumb: Breadcrumb) -> Breadcrumb? {
        if let c = crumb.category, ["http", "console", "navigation"].contains(c) { return nil }
        if let m = crumb.message { crumb.message = redact(m) }
        crumb.data = nil
        return crumb
    }

    private static func redact(_ s: String) -> String {
        var out = s.replacingOccurrences(
            of: #"/Users/[^/\s]+"#, with: "/Users/<redacted>", options: .regularExpression)
        if out.count > 200 { out = String(out.prefix(200)) + "…[truncated]" }
        return out
    }
}
```

**Capture discipline is the real first line.** The scrubber is a net; don't put user content
into events in the first place. Capture metadata (subsystem, HTTP status, error domain/code,
counts, durations) — never interpolate user text.

## Layer 2 (backstop): the IP gotcha + server-side

`sendDefaultPii = false` does **not** stop the IP on Apple — the SDK sets `ip_address` to
`{{auto}}` and the connection IP is inferred at ingest. Mitigate:

1. Client: `event.user = nil` (above).
2. **Project → Security & Privacy → enable "Prevent Storing of IP Addresses."**
3. Strongest: add an **Advanced Data Scrubbing** rule for `$user.ip_address` ("ultimately
   overrules any other logic").

Sentry also runs default server-side scrubbing (field-name keyword list → `[Filtered]`).
Keep it on and add project-specific sensitive fields. But server-side is a **backstop** —
by the time it runs, the data already crossed the network. Client scrubbing is what prevents
transmission.

**Data residency:** region (US/US2/EU) is chosen at **org creation** and is immutable; the
DSN does not encode it. If EU residency matters, create the org in the EU region up front.

## Layer 3: opt-in consent

Crash reporting is telemetry. For any app touching user data, make it **opt-in, default off**
— consistent with a privacy-first posture. Gate `SentrySDK.start` behind a flag:

```swift
guard UserDefaults.standard.bool(forKey: "diagnosticsEnabled") else { return }   // default false
SentrySDK.start { options in /* ... */ }
```

- Ask once (onboarding privacy step and/or a Settings toggle), plainly: "Share crash reports
  & diagnostics — never includes your content."
- Honor it everywhere: flag off → no `start`, no `capture`, no logs.
- Apply on next launch (matches how handlers install at start); say so under the toggle.
  Use `SentrySDK.close()` to stop mid-session if needed.
- Keep it separate from any feature-consent (e.g. cloud processing) — different questions.

## Checklist

- [ ] `beforeSend` nulls `event.user` and redacts message/exception/paths.
- [ ] `beforeBreadcrumb` drops risky categories; network breadcrumbs off.
- [ ] Project "Prevent Storing of IP Addresses" enabled (+ optional `$user.ip_address` rule).
- [ ] Reporting opt-in, default off, honored everywhere.
- [ ] Verified a real event payload carries no user content, path, or IP (`verify-and-troubleshoot.md`).
