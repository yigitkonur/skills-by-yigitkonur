# Integration Blueprint: LicenseSeat in a macOS App

A generalized architecture distilled from a shipped, adversarially-reviewed macOS integration (a menu-bar dictation app pairing LicenseSeat with a usage-metering backend). Adapt names to your codebase; keep the invariants.

## Contents
- [Credentials](#credentials)
- [Configuration at launch](#configuration-at-launch)
- [One owning LicenseManager](#one-owning-licensemanager)
- [Pairing with a second backend](#pairing-with-a-second-backend)
- [Activation UI flow](#activation-ui-flow)
- [Feature gating](#feature-gating)
- [Recommended config values](#recommended-config-values)
- [Testing strategy](#testing-strategy)

## Credentials

Ship only the **publishable** key (`pk_live_…`) — client-safe by design. Lightly obfuscate it (Base64 + salt constant is enough) so it isn't a bare `strings`-dump hit; this is obfuscation, not security, and that's fine for a `pk_` key. Secret `sk_*` keys never enter the binary. The product slug is not a secret — a plain constant.

## Configuration at launch

Configure in app init, synchronously — it loads the cached license and starts background auto-validation without network I/O on the launch path:

```swift
// Store-based apps MUST configure LicenseSeatStore.shared — the static
// LicenseSeat.configure wires a DIFFERENT singleton the store never reads
// (see api-surface.md, two-singleton rule). Slug goes in the closure;
// the store's configure has no productSlug parameter.
LicenseSeatStore.shared.configure(apiKey: publishableKey) { cfg in
    cfg.productSlug = "your-product"
    cfg.maxOfflineDays = 14          // default 0 locks users out on any outage
    cfg.telemetryEnabled = false     // default true ships 17 device fields
    #if DEBUG
    cfg.debug = true
    #endif
}
```

Rules:
- **Never** `await validate(…)` on the launch path. Cached state first; auto-validation refreshes in the background.
- Leave `cfg.deviceIdentifier` nil on macOS — the SDK derives `"mac-<IOPlatformUUID>"` from hardware, stable across reinstalls and defaults resets. Substituting your own scheme means a later change orphans every activated seat.
- Keep the default `storagePrefix` unless a migration requires otherwise; changing it strands the cached license.
- Configure is first-write-wins (`force: false`): a second call is a silent no-op. Exactly one configure call per process.

## One owning LicenseManager

One `@MainActor ObservableObject` owns all license state; everything else observes it. The load-bearing pieces:

```swift
@MainActor
final class LicenseManager: ObservableObject {
    static let shared = LicenseManager()

    @Published private(set) var isLicensed = false
    @Published private(set) var statusDescription = "Not activated"

    private var cancellables = Set<AnyCancellable>()
    /// FIFO chain serializing every lifecycle op for its full duration.
    private var operationChain: Task<Void, Never> = Task {}

    private init() {
        LicenseSeatStore.shared.$status
            .receive(on: DispatchQueue.main)
            .sink { [weak self] in self?.apply($0) }
            .store(in: &cancellables)
    }

    private func apply(_ status: LicenseStatus) {
        switch status {
        case .active(let details):
            isLicensed = true            // details.license is the KEY STRING
            statusDescription = "Licensed"
        case .inactive:
            isLicensed = false
            statusDescription = "Not activated"
        case .invalid(let message):
            isLicensed = false           // server-confirmed — degrade softly
            statusDescription = "License invalid: \(message)"
        case .pending:
            break                        // keep last state — see below
        default:
            break                        // .offlineValid/.offlineInvalid: dead cases (0.4.1)
        }
    }

    func activate(_ key: String) async throws {
        try await serialized {
            _ = try await LicenseSeatStore.shared.activate(
                key.trimmingCharacters(in: .whitespacesAndNewlines))
            // The successful return IS the proof: the SDK reports .pending
            // until its first validation (up to autoValidateInterval = 1 h),
            // so status-driven UI would show "not licensed" after a
            // successful activation. Set state directly.
            self.isLicensed = true
            self.statusDescription = "Licensed"
        }
    }

    /// Frees the server-side seat FIRST; local state clears via $status.
    func deactivate() async throws {
        try await serialized {
            try await LicenseSeatStore.shared.deactivate()
        }
    }

    private func serialized<T>(_ op: @escaping @MainActor () async throws -> T) async throws -> T {
        let previous = operationChain
        let task = Task { () throws -> T in
            await previous.value
            return try await op()
        }
        operationChain = Task { _ = try? await task.value }
        return try await task.value
    }
}
```

Why each piece is there (all were real review findings, not style):

| Piece | Why it must stay |
|---|---|
| `.pending` keeps last state | right after `activate()` the SDK reports `.pending` until first validation (up to 1 h); auto-validation cycles also pass through `.pending` — treating it as unlicensed flaps or breaks the UI |
| `activate()` sets state from its own return | same trap: waiting on `$status` makes successful activation look failed for up to an hour |
| FIFO `serialized` chain | without it a deactivate can be overtaken by an in-flight background op (validation retry, secondary-backend link) and resurrect a released seat |
| `deactivate()` before clearing anything local | clearing local state without the server call leaks the seat forever (shipped bug in a real Polar integration) |

For per-entitlement flags, add `LicenseSeatStore.shared.entitlementPublisher(for: "key").map(\.active)` pipelines *inside* the manager — still one owning object. Revocation lands through the same `$status` sink (`.invalid` within one auto-validation cycle); the store has no event API, and `LicenseSeat.shared.on(...)` is the wrong singleton in a store-based app.

## Pairing with a second backend

If licensing also unlocks something server-side (a metering proxy, sync service, API quota), keep two invariants:

1. **SDK-first ordering.** Activate binds the seat before telling your backend; deactivate frees the seat before your backend unlink. Seat state is the scarce resource users pay for; your backend can self-heal.
2. **Secondary failure is a surfaced divergence, never silent success.** If the backend link fails after a successful SDK activation, return a distinct outcome (e.g. `.pendingSync`), keep a visible notice, retry on a timer with identity guards (so a later deactivate cancels retries), and reconcile on restart. Celebrate only on full success.

Launch-race rule for any async setup (device registration, token fetch): expose an awaitable, coalescing accessor and **propagate** its failure — `try? await` on a coalesced task returns stale, server-rejected state. A synchronous cached read on a first-use path races launch setup and fails spuriously.

## Activation UI flow

1. Key `TextField` + Activate button → `try await LicenseManager.shared.activate(key)`.
2. Map `APIError.code` to copy: `seat_limit_exceeded` → "This license is active on too many devices. Deactivate another device first."; `license_not_found` → "Check the key for typos."; `product_not_found` → your config/dashboard problem, not the user's key; **always a `default:`** using `error.message` (codes are free-form strings).
3. When licensed: masked key + "Deactivate This Mac" with a confirmation dialog (it frees the seat for another machine).
4. Activation requires network — surface transport failures as "Connect to the internet to activate", not a generic error.
5. Any blocking/paywall sheet should be dismissable (dark-pattern avoidance) and hosted at the window root, not inside a view that may be hidden.

## Feature gating

- Gate through the LicenseManager (or `@EntitlementState` in leaf SwiftUI views) — never scatter raw `LicenseSeatStore` reads.
- Gate on entitlement keys (e.g. `"pro"`), not `plan_key` comparisons — plans change, entitlement keys are the stable contract.
- Soft degradation only: banner or disabled premium paths. Never block launch, never interrupt in-progress user work, never `NSApp.terminate` (see pitfalls.md for the Setapp/QSpace lockout incidents).
- If support/diagnostics code reads license status from arbitrary threads, mirror the value behind a lock — a `DispatchQueue.main.sync` hop from a background thread into a `@MainActor` object is a deadlock risk.

## Recommended config values

| Setting | Value | Why |
|---|---|---|
| `maxOfflineDays` | 7–14 | default 0 = lockout on outage; vendor recommends ≥7; daily-driver tools err generous |
| `telemetryEnabled` | false unless product signs off | ships device model/locale/resolution/timezone |
| `heartbeatInterval` | default (300) or 0 | keep if dashboard device-liveness matters; 0 minimizes traffic — revocation still lands via auto-validation |
| `autoValidateInterval` | default (3600) | revocation propagates within ~1 h; faster polling burns rate limit |
| `offlineFallbackMode` | default (`.networkOnly`) | offline verify only when the network is actually down |
| `deviceIdentifier` | nil | hardware-UUID stability (see above) |

## Testing strategy

- **Unit:** inject a stub `URLSession` + `cfg.apiBaseUrl` override via `configure(apiKey:apiBaseURL:urlSession:options:)` — mirror the SDK's own `LicenseSeatStoreTests.swift`. Never hit the live API from CI.
- **Before any runtime test, smoke-test the product exists:** `curl -s -o /dev/null -w '%{http_code}' -X POST https://licenseseat.com/api/v1/products/<slug>/licenses/<key>/validate -H "Authorization: Bearer pk_live_…"` — 404 `product_not_found` means the dashboard has no such slug (a real launch blocker that looks exactly like broken client code); 401 means the key is wrong; only 200 makes Swift-side results meaningful.
- **Runtime verification checklist** (real test key, scratch product):
  1. Activate → licensed state flips **immediately** (from the activate return; if it takes ~1 h the `.pending` trap is back), dashboard shows the seat.
  2. Quit, disable Wi-Fi, relaunch → still licensed from cache.
  3. Revoke in dashboard, reconnect → `.invalid` within one auto-validation cycle; UI degrades softly.
  4. Deactivate → dashboard seat count drops; re-activation on the same key works.
  5. `seat_limit_exceeded`: activate a 1-seat license from a second machine → correct error copy.

## Cross-references

- Exact signatures, the two-singleton rule, dead cases: `api-surface.md`
- Seat semantics, propagation timing, endpoints, rate limits: `platform-model.md`
- SDK bugs, compile-clean runtime traps, incident-backed anti-patterns: `pitfalls.md`
