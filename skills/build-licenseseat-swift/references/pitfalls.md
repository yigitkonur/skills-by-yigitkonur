# Pitfalls: SDK Bugs, Doc Traps, and Shipped-App Anti-Patterns

Read before claiming licensing work done, when debugging unexpected SDK behavior, or when reviewing a licensing diff. Three sections: confirmed defects in licenseseat-swift v0.4.1 itself, runtime traps that compile clean, caught by adversarial review of a real shipped macOS integration, then anti-patterns from real shipped macOS apps with incident evidence.

## Confirmed SDK defects and doc traps (v0.4.1 tag, source-verified 2026-07-12)

| # | Trap | Symptom | Fix |
|---|---|---|---|
| 1 | **Two independent singletons:** static `LicenseSeat.configure` builds `LicenseSeat.shared`; the store's configure builds its own internal instance — they never see each other | store-based code throws `LicenseSeatStoreError.notConfigured` on every call; cached licenses never surface; static-side code silently operates an unconfigured twin | configure the singleton you operate through (store-based apps: `LicenseSeatStore.shared.configure`); audit that every SDK touchpoint reaches the configured one |
| 2 | README's `LicenseSeatStore.shared.configure(apiKey:productSlug:)` — shown 6+ times — **does not compile**; the instance method has no `productSlug` param | build error: extra argument | slug in closure: `configure(apiKey:) { $0.productSlug = "…" }` |
| 3 | `configure` is first-write-wins (`force: false` default) — a second call is a silent no-op | "I updated the config but nothing changed" | one configure call per process; `force: true` only for tests |
| 4 | **`.pending` for up to 1 h after successful activation:** `activate()` caches without a validation record; `getStatus()` maps that to `.pending`; first auto-validation sleeps a full `autoValidateInterval` before running | activation "fails" in any UI that derives licensed purely from `$status` | set licensed state directly from the successful `activate()` return; `.pending` in status sinks = keep last state |
| 5 | `.offlineValid` / `.offlineInvalid` declared but **never constructed** — `getStatus()` (sole producer) returns only `.active/.inactive/.invalid/.pending`; successful offline verify maps to `.active` | offline-specific UI branches never run; "works online-only" illusions in review | merged `default:` branch; drive offline UX off `validation:offline-success` events or `verifyCachedOffline()` result instead |
| 6 | Unfiltered `eventPublisher` misses all `offlineToken:*` events (internal `allEvents` catalog says `offlineLicense:*`, emits say `offlineToken:*`) | offline token lifecycle invisible despite "subscribing to everything" | explicit `.on("offlineToken:verified")` / `.on("offlineToken:verificationFailed")`, or `.filter { $0.name.hasPrefix("offlineToken:") }` |
| 7 | README's `LicenseSeatStore.shared.seat?.heartbeat()` — `seat` getter is internal; and `LicenseSeat.shared.heartbeat()` operates the *other* singleton (trap 1) | build error: inaccessible; or a heartbeat that throws `apiKeyRequired` at runtime | no manual heartbeat in a store-based app — rely on the automatic one `activate()` starts |
| 8 | `maxOfflineDays` defaults to **0 = no offline grace at all** (docs prose implies 7-day grace exists; that's only their example value) | users locked out the moment the server or their network hiccups | set explicitly (a daily-driver app: 7–14) |
| 9 | `telemetryEnabled` defaults **true** — silently ships 17 fields (device model, locale, timezone, screen resolution…) | unexpected data egress; privacy-policy drift | opt out explicitly unless product signs off |
| 10 | README install snippet pins 0.3.1; 0.4.1 changed offline endpoint paths (`/offline-token`→`/offline_token`, `/signing-keys/`→`/signing_keys/`) | pre-0.4.1 offline sync 404s against current server | pin `from: "0.4.1"` |
| 11 | `APIError.code` is a free-form `String?`; the SDK doc-comment and README list *different* non-exhaustive code sets (`expired` vs `license_expired`, etc.) | exhaustive switch misses codes; brittle equality checks | always include a `default:` using `error.message`; match both spellings where it matters |
| 12 | **master has drifted from the 0.4.1 tag** — different `LicenseSeatError` cases; `LicenseStatusDetails.license` is a `String` (the key) at 0.4.1, docs written from master call it a struct | code written against master-sourced docs doesn't compile against the pinned package | resolve compile errors against the checkout in `SourcePackages/checkouts/licenseseat-swift`, never against master or memory |
| 13 | CHANGELOG's `[1.0.0]` entry claims macOS 11+/Linux — stale, no such tag; real floor is macOS 12, Linux dropped in 0.2.0 | wrong platform assumptions | trust `Package.swift` |
| 14 | Device-ID cache key `licenseseat_device_identifier` is hardcoded to `UserDefaults.standard`, ignoring `storagePrefix` (non-macOS path) | surprise on iOS ports / defaults wipes | macOS unaffected (hardware UUID); just don't rely on prefix isolation for it |

## Runtime traps that compile clean (adversarial-review findings from a shipped macOS integration, 2026-07-12)

Every one of these passed the compiler and looked correct in review; each was a real finding against working code in a macOS dictation app (VoiceInk) that pairs LicenseSeat with a metering backend. When reviewing a licensing diff, check for the *shape*, not the specific line:

| Trap | How it bit | Rule |
|---|---|---|
| Configured one singleton, operated the other | launch called static `LicenseSeat.configure`; `LicenseManager` observed/activated through the store → every store call would throw `notConfigured` | one configure call, and trace every SDK touchpoint back to it |
| SPM product declared but not linked | `project.pbxproj` had the LicenseSeat package reference but the app target's `packageProductDependencies` omitted the product → `import LicenseSeat` unresolved | objectVersion-77 synced groups auto-include *files*, never SPM products; check the target's product list explicitly |
| First-use races launch-path registration | device registration started in an unawaited launch `Task`; first transcription synchronously read a nil token and failed "not registered" | any launch-started async setup needs an awaitable, coalescing accessor at every consumer boundary |
| `try? await` on a coalesced in-flight task | swallowed the registration failure and returned a stale, server-rejected token | propagate (`try await`) — an error you swallow becomes a worse error downstream |
| Lifecycle ops racing each other | deactivate could be overtaken by an in-flight license-link retry, resurrecting the released seat | FIFO-serialize activate/deactivate/link/reconcile; re-check identity *inside* the serialized closure |
| Secondary-system failure treated as success | proxy `linked:false` was silently swallowed; user saw "licensed" while still metered free | surface divergence as a distinct outcome (`.pendingSync`) with retries; celebrate only on full success |
| `DispatchQueue.main.sync` from arbitrary threads to read status | support-info export could deadlock against the MainActor | mirror the value behind a lock (`LicenseStatusMirror`) for off-main reads |
| Keychain delete-then-add | transient window with no credential under concurrent readers | `SecItemUpdate`-or-add, never delete-then-add |
| Plain `UserDefaults` read gating a SwiftUI sheet | consent flag changes never invalidated the view; the gate went stale | `@AppStorage(key)` in the presenter for anything reactive |
| Edit tool on pbxproj with a guessed `old_string` | ordering assumptions about pbxproj sections don't hold | re-read the actual file section before editing generated/machine-formatted files |

## Shipped-app anti-patterns (evidence-backed verdicts)

Patterns observed across production macOS license integrations — upstream VoiceInk (Polar), naviapps/license-kit, vendor guides, and r/macapps incident threads (all accessed 2026-07-12).

### AVOID — with real-world incident evidence

| Anti-pattern | Evidence | Consequence |
|---|---|---|
| Launch-blocking or hard-fail license check when the server is unreachable | **Setapp outage:** "No error message. All the apps… quit on their own… no app will launch" (r/macapps y1lbz9). **QSpace:** "the QSpace-server is down… no usage of QSpace" (r/macapps 1l7w0zb) | paying users locked out by an outage that isn't theirs; reputational damage in reviews |
| `NSApp.terminate(nil)` on failed validation | a published Gumroad-integration guide does exactly this on sheet dismiss | same as above, but self-inflicted by design |
| Clearing local license state without calling `deactivate()` | upstream VoiceInk's "Remove License" clears Keychain only — seat stays consumed server-side | users burn through seat limits, support tickets, manual dashboard cleanup |
| Irrevocable device binding with no self-service path | QSpace: "Once a license is locked to a Mac, it is irrevocable" (r/macapps 1moxmeo) | every hardware upgrade becomes a support ticket |
| Raw license key in `@AppStorage`/plist | Lemon Squeezy community gist | key harvestable from unencrypted prefs; syncs where it shouldn't |
| Scattered `if licensed` checks across views/services | — | gating drift, untestable, inconsistent degradation |

### RECOMMENDED — convergent pattern across good implementations

- **Trust cached state at launch; validate in the background.** Upstream VoiceInk skips server validation on startup entirely; license-kit refreshes async only when stale. The SDK's `configure` + `license:loaded` + auto-validation gives this for free — don't defeat it.
- **Grace period on failure, tiered by failure class** (license-kit: 7 days for transport errors, 24 h for confirmed server rejections). LicenseSeat's `maxOfflineDays` is flat — approximate the distinction by treating `.invalid` (server-confirmed) as degrade-now while network errors keep cached state.
- **One owning state object + enum state machine**, Combine-published; single gating surface (upstream VoiceInk gates in exactly one call site).
- **Soft degradation** — nag banner / disabled premium features, never a locked app. A dictation tool interrupting mid-recording over licensing is unacceptable UX.
- **Deactivate-on-this-device button** that actually frees the seat, so seat limits self-serve instead of generating support load.

### ACCEPTABLE trade-offs

- Validating only on user action with no periodic revalidation (upstream VoiceInk): zero lockout risk, but revocation never lands — fine for goodwill-license apps, wrong for paid seat enforcement. LicenseSeat's 1 h auto-validation is the better default; leave it on.
- UserDefaults+file persistence for the *cached license artifact* (what this SDK does): it's a signed token, not a secret; tampering fails Ed25519 verification. Keychain remains better for the raw user-entered key if you store it separately — the SDK stores the license record, so most apps need no extra key storage.

## Review checklist for licensing diffs

- [ ] Exactly one `configure` call; every SDK touchpoint (activate, status, entitlements) reaches the SAME singleton it configures (trap 1)
- [ ] No `configure(apiKey:productSlug:)` instance-call (trap 2); slug set via closure
- [ ] Licensed-state transition on activation comes from the `activate()` return, not from waiting on `$status` (trap 4); `.pending` branches keep last state
- [ ] Status switches don't depend on `.offlineValid`/`.offlineInvalid` (trap 5)
- [ ] Offline-token event subscriptions are explicit, not via unfiltered publisher (trap 6)
- [ ] `maxOfflineDays` explicitly set; `telemetryEnabled` explicitly decided (traps 8–9)
- [ ] No license network call on the launch/recording path; cached state trusted first
- [ ] Every local "remove license" path calls `deactivate()` before clearing, and lifecycle ops are serialized (no deactivate/link races)
- [ ] Failures of a secondary system (proxy link) surface as distinct outcomes, never silent success
- [ ] `APIError.code` handling has a `default:` branch (trap 11)
- [ ] Signatures verified against the pinned-tag checkout, not master or memory (trap 12)
- [ ] No `pk_live_` string committed raw; lightly obfuscated behind a credentials helper; no `sk_*` anywhere
- [ ] Failure UX degrades softly — nothing terminates, blocks launch, or interrupts recording

## Sources

- SDK defects: direct source read of github.com/licenseseat/licenseseat-swift at the **v0.4.1 tag** (Sources/LicenseSeatSDK/*, Tests, Examples, CHANGELOG, tags/releases), 2026-07-12; re-verified against the SPM checkout in a real build's SourcePackages.
- Runtime traps: VoiceInk licensing-metering integration, 4 rounds of adversarial review (Codex gpt-5.6-sol, 2026-07-12) — ~25 findings, all fixed and re-verified; commits `12de51bc`, `38c2c67c`, `48498b54` in yigitkonur/VoiceInk-clone.
- Incidents: r/macapps threads y1lbz9 (Setapp outage), 1l7w0zb + 1moxmeo (QSpace); accessed 2026-07-12.
- Patterns: github.com/Beingpax/VoiceInk (LicenseViewModel/LicenseManager/PolarService/KeychainService, TranscriptionDelivery gating); github.com/naviapps/license-kit; vendor guides (Gumroad, Lemon Squeezy examples), 2026-07-12.
