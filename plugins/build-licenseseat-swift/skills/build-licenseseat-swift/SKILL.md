---
name: build-licenseseat-swift
description: "Use if integrating the LicenseSeat Swift SDK into a macOS/Swift app — activation, validation, seats."
---

# Build LicenseSeat Licensing Into a Swift App

Wire the LicenseSeat licensing platform (`licenseseat/licenseseat-swift`) into a macOS/Swift app correctly. The SDK's real API differs from its own README in ways that **fail to compile or silently misbehave**, and several traps compile clean and only surface at runtime. This skill carries the source-verified surface (v0.4.1) plus an integration blueprint hardened by a shipped macOS app that went through four adversarial review rounds (~25 findings).

## When to use

- "Add licensing / license keys to this Mac app", "integrate LicenseSeat"
- Writing or changing any call against the LicenseSeat Swift SDK
- Activation/deactivation UI, trials, entitlement gating, seat management
- Debugging licensing behavior (activation "fails", status stuck, offline weirdness)
- Reviewing a licensing diff

## When NOT to use

- App Store IAP / StoreKit — different distribution model entirely
- Other license vendors (Polar, Paddle, Keygen, Lemon Squeezy, Gumroad's native keys) — the anti-pattern evidence in `references/pitfalls.md` transfers, the API surface does not
- Pricing strategy / packaging decisions

## Critical facts (read before writing any code)

Source-verified against the **v0.4.1 tag** on 2026-07-12. The vendor README and https://licenseseat.com/docs/sdks-swift/ contradict several of these — trust this list. When resolving a compile error, ground truth is the checkout under your build's `SourcePackages/checkouts/licenseseat-swift`, never `master` (master has drifted from the pinned tag).

1. **There are TWO independent singletons. Configure the one you operate through — never mix.** `LicenseSeat.configure(...)` (static) builds `LicenseSeat.shared`; `LicenseSeatStore.shared.configure(...)` builds the store's own *internal* instance. They do not see each other. If any code observes `LicenseSeatStore.shared.$status` or calls store methods, you MUST configure the store — otherwise every store call throws `notConfigured` and cached licenses never surface. This shipped as a real bug: launch used the static configure, the manager used the store; caught only in adversarial review.

   ```swift
   // Store-based app (recommended architecture):
   LicenseSeatStore.shared.configure(apiKey: "pk_live_…") { cfg in
       cfg.productSlug = "your-product"
       cfg.maxOfflineDays = 14
       cfg.telemetryEnabled = false
   }
   // WRONG for a store-based app — configures a DIFFERENT singleton:
   // LicenseSeat.configure(apiKey: …, productSlug: "your-product")
   ```

2. **`LicenseSeatStore.shared.configure(apiKey:productSlug:)` DOES NOT COMPILE.** The instance method has no `productSlug` parameter (the README shows it 6+ times anyway). The slug goes in the trailing closure. The only overload with a `productSlug:` parameter is the static `LicenseSeat.configure` — which fact 1 says not to use in a store-based app.

3. **Status is `.pending` for up to 1 hour after a successful activation.** `activate()` caches the license *without* a validation record; `getStatus()` maps that to `.pending`, and the auto-validation loop sleeps a full `autoValidateInterval` (default 3600 s) *before* its first validate. UI that derives "licensed" purely from `$status` makes every successful activation look failed. Fix: the successful `activate()` return IS the proof — set licensed state directly from it; treat `.pending` in status sinks as keep-last-state, never as unlicensed.

4. **`.offlineValid` / `.offlineInvalid` are dead enum cases** (declared, never constructed — `getStatus()` only ever returns `.active`, `.inactive`, `.invalid`, `.pending`, even after successful offline verification). Handle them in a merged branch; never build logic that waits for them.

5. **Unfiltered `eventPublisher` silently misses all `offlineToken:*` events** (internal catalog bug lists them as `offlineLicense:*`). Subscribe explicitly: `.on("offlineToken:verified") { … }` or `.filter { $0.name.hasPrefix("offlineToken:") }`.

6. **There is no manual heartbeat path in a store-based app.** `LicenseSeatStore.shared.seat` is internal (README's `seat?.heartbeat()` fails to compile), and `LicenseSeat.shared.heartbeat()` operates the *other*, unconfigured singleton. Rely on the automatic heartbeat `activate()` starts (`heartbeatInterval`, default 300 s).

7. **Offline grace is OFF by default** (`maxOfflineDays = 0`). Shipping without setting it means a server outage locks out paying users (see the Setapp/QSpace incidents in `references/pitfalls.md`). Set 7–14 for daily-driver apps.

8. **`product_not_found` (HTTP 404) means the dashboard, not your code.** Auth failures are 401; a missing/wrong product slug 404s even with a valid key. Smoke-test with curl before debugging Swift (recipe in `references/integration-blueprint.md`) — a missing dashboard product looks exactly like broken client code.

9. Both `LicenseSeat` and `LicenseSeatStore` are `@MainActor`; mutating APIs are `async throws`. Persistence is UserDefaults (`licenseseat_` prefix) + JSON in Application Support — not Keychain (fine: the cached license is a signed artifact, not a secret).

## Install

```swift
// Xcode: File → Add Package Dependencies
// https://github.com/licenseseat/licenseseat-swift.git, Up to Next Major from 0.4.1
// Product: "LicenseSeat"  (module is LicenseSeat; source dir LicenseSeatSDK is internal naming)
import LicenseSeat
```

Requires macOS 12+, Swift tools 5.9, pulls `apple/swift-crypto`. Pin `from: "0.4.1"` — the README's own snippet pins a stale 0.3.1, and 0.4.1 fixed offline endpoint paths.

**pbxproj trap:** in projects with objectVersion-77 file-system-synced groups, new *Swift files* auto-include — SPM products do NOT. The package reference alone is not enough; the product must appear in the app target's `packageProductDependencies`, or `import LicenseSeat` fails to resolve. When editing `project.pbxproj` with string replacement, re-read the actual section first — guessed orderings mismatch.

## Decision tree

| Task | Do | Read first |
|---|---|---|
| First-time integration | Follow `references/integration-blueprint.md` end to end | `references/integration-blueprint.md` |
| Exact signature / config field / enum / error / event name | Never guess — look it up | `references/api-surface.md` |
| Server behavior: seats, revocation, offline tokens, endpoints, key types | Look it up | `references/platform-model.md` |
| Debugging weird SDK behavior; reviewing licensing code | Check the known-bug + runtime-trap tables | `references/pitfalls.md` |
| "Activation fails with 404 / product_not_found" | Dashboard problem, not code — curl smoke test | `references/integration-blueprint.md` |
| Activation UI / gating / trial UX decisions | Use shipped-app verdicts | `references/integration-blueprint.md` + `references/pitfalls.md` |

## Operating rules

- **Propagation is polling-only.** LicenseSeat has no webhooks and no license-create API. Dashboard changes (revoke, entitlement edits) reach a running app via auto-validation (default 1 h) and heartbeat (default 5 min); offline devices learn on reconnect.
- **Validation HTTP is always 200** — validity is the `valid` field, error info in `error.code`. Don't branch on status codes (the 401/404 routing failures above are the exception).
- **Server error codes are open-ended strings** (`APIError.code: String?`), not an enum. Switch with a `default:`; known codes in `references/api-surface.md`.
- **Entitlements over plan keys.** Gate on `entitlement("key").active` / `@EntitlementState("key")`, not `plan_key` comparisons.
- **One owning LicenseManager object.** All gating flows through it; no scattered `if licensed` checks. Blueprint with the race-hardened skeleton: `references/integration-blueprint.md`.
- **Verify claims against the pinned tag.** Anything you read about this SDK — including these references — check against the version your Package.resolved pins when the stakes are compile errors. Known drift: master's `LicenseSeatError` cases differ from 0.4.1; `LicenseStatusDetails.license` is the key `String` at 0.4.1, not a struct.
- **Testing:** inject `urlSession` and override `cfg.apiBaseUrl`; the SDK's own `LicenseSeatStoreTests.swift` shows the pattern. Never hit the live API from CI.
- **Rate limits:** free tier 60 req/min, 1000 req/day — don't validate eagerly in loops.

## Reference files

| File | When to read |
|---|---|
| `references/api-surface.md` | Any time you write or review a call against the SDK — exact signatures, the two-singleton rule, config fields + defaults, status/error/event catalogs, offline methods, persistence layout. |
| `references/platform-model.md` | Server-side questions: products/licenses/seats/devices/entitlements, endpoints and JSON shapes, pk/sk keys, offline token format + Ed25519 verification, air-gapped flow, revocation propagation, rate limits. |
| `references/integration-blueprint.md` | Wiring the SDK into an app: credentials, launch config, the race-hardened LicenseManager skeleton, pairing with a second backend, activation UI, gating, config values, runtime verification checklist. |
| `references/pitfalls.md` | Before claiming licensing work done, when debugging, or when reviewing a diff — confirmed SDK bugs, non-compiling README patterns, compile-clean runtime traps, and shipped-app anti-patterns with incident evidence. |

## Guardrails

- Do not copy code from the LicenseSeat README or https://licenseseat.com/docs/sdks-swift/ without checking it against `references/api-surface.md` — multiple documented snippets do not compile.
- Do not configure one singleton and operate through the other — a reviewer should be able to point at exactly one configure call and trace every SDK touchpoint back to it.
- Do not derive "licensed" from `$status` alone across an activation — the successful `activate()` return is the source of truth for that transition.
- Do not embed an `sk_*` key; lightly obfuscate the `pk_live_` key rather than committing it raw.
- Do not block app launch or in-progress user work on a license network call — cached state first, network in the background.
- Do not remove a license locally without calling `deactivate()` first (seat leak), and do not let deactivate race an in-flight background op — serialize lifecycle operations.
- Do not write logic that depends on `.offlineValid` / `.offlineInvalid` being delivered, or on unfiltered `eventPublisher` delivering `offlineToken:*` events.
- Do not leave `telemetryEnabled` at its default (true) without an explicit product decision — it ships device model, locale, timezone, and screen data.
