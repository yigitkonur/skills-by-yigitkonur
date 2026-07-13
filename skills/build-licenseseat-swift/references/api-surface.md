# LicenseSeat Swift SDK — API Surface (v0.4.1, source-verified)

Exact public API of `licenseseat/licenseseat-swift` as read from the **v0.4.1 tag** (the version Package.resolved pins) on 2026-07-12. Use this instead of the vendor README, which contains non-compiling examples, and instead of `master`, which has drifted from the pinned tag (different `LicenseSeatError` cases, `LicenseStatusDetails.license` type changed). When resolving a compile error, the ground truth is the checkout under your build's `SourcePackages/checkouts/licenseseat-swift`. Repo: https://github.com/licenseseat/licenseseat-swift.

**The two-singleton rule (most expensive trap in this SDK):** `LicenseSeat.shared` and the `LicenseSeat` instance inside `LicenseSeatStore.shared` are *independent*. The static `LicenseSeat.configure(...)` rebuilds only the former; `LicenseSeatStore.shared.configure(...)` builds only the latter. A store-based app that calls the static configure gets `LicenseSeatStoreError.notConfigured` from every store call and never sees the cached license. Pick one architecture and route *every* SDK touchpoint through it.

## Contents
- [Package](#package)
- [LicenseSeat (core class)](#licenseseat-core-class)
- [LicenseSeatStore (SwiftUI-facing singleton)](#licenseseatstore-swiftui-facing-singleton)
- [Property wrappers](#property-wrappers)
- [LicenseStatus enum](#licensestatus-enum)
- [LicenseSeatConfig (all fields + defaults)](#licenseseatconfig-all-fields--defaults)
- [Errors](#errors)
- [Events catalog](#events-catalog)
- [Offline validation methods](#offline-validation-methods)
- [Device identifier](#device-identifier)
- [Persistence + concurrency](#persistence--concurrency)
- [Version history](#version-history)

## Package

```swift
// Package.swift (repo root) — swift-tools-version: 5.9
platforms: [.macOS(.v12), .iOS(.v13), .tvOS(.v13), .watchOS(.v8)]
// dependency: apple/swift-crypto from "2.6.0" (product "Crypto")
```

Consumer side:

```swift
.package(url: "https://github.com/licenseseat/licenseseat-swift.git", from: "0.4.1")
.product(name: "LicenseSeat", package: "licenseseat-swift")
```

```swift
import LicenseSeat  // module is LicenseSeat; Sources/LicenseSeatSDK is just the folder name
```

The README's install snippet pins `from: "0.3.1"` — stale; use 0.4.1+ (offline endpoint paths changed in 0.4.1).

## LicenseSeat (core class)

Source: `Sources/LicenseSeatSDK/LicenseSeat.swift`.

```swift
@MainActor
public final class LicenseSeat {
    public static var shared: LicenseSeat
    public init(config: LicenseSeatConfig = .default, urlSession: URLSession? = nil)

    public func activate(licenseKey: String, options: ActivationOptions = .init()) async throws -> License
    public func validate(licenseKey: String, options: ValidationOptions = .init()) async throws -> ValidationResponse
    public func deactivate() async throws
    public func heartbeat() async throws
    public func checkEntitlement(_ key: String) -> EntitlementStatus
    public func getStatus() -> LicenseStatus
    public func currentLicense() -> License?
    public func healthCheck() async throws -> HealthResponse
    public func reset()
    public func purgeCachedLicense()
    @discardableResult
    public func on(_ event: String, handler: @escaping (Any) -> Void) -> AnyCancellable

    // public since v0.4.1
    public func syncOfflineAssets() async
    public func verifyCachedOffline() async -> ValidationResponse
}
```

Static convenience extension (the ONLY configure overload with a `productSlug` parameter — but it configures `LicenseSeat.shared`, NOT the store; see the two-singleton rule above):

```swift
public extension LicenseSeat {
    static func configure(
        apiKey: String,
        productSlug: String,
        apiBaseURL: URL? = nil,
        force: Bool = false,
        options customize: (inout LicenseSeatConfig) -> Void = { _ in }
    )
    // also: static activate(...), deactivate(), entitlement(_:), statusPublisher
    // — all of these operate LicenseSeat.shared, never the store's instance
}
```

Note `force: Bool = false`: a second configure call on an already-configured instance is a **silent no-op** unless `force: true` — you cannot "fix up" a config later; get it right in the one launch-path call.

REST endpoints hit by these methods (relative to `apiBaseUrl`, default `https://licenseseat.com/api/v1`):
`POST /products/{slug}/licenses/{key}/activate | /validate | /deactivate | /heartbeat`.

## LicenseSeatStore (SwiftUI-facing singleton)

Source: `Sources/LicenseSeatSDK/LicenseSeatStore.swift`. `@MainActor`, `ObservableObject` under `#if canImport(Combine)`.

```swift
public final class LicenseSeatStore {
    public static let shared: LicenseSeatStore

    // NO productSlug parameter — set it in the closure. README shows a
    // configure(apiKey:productSlug:) call 6+ times; it does not compile.
    public func configure(
        apiKey: String,
        apiBaseURL: URL? = nil,
        force: Bool = false,
        urlSession: URLSession? = nil,
        options customize: (inout LicenseSeatConfig) -> Void = { _ in }
    )

    // @Published var status: LicenseStatus  → subscribe via $status
    // activate(_:options:), deactivate(), validate(licenseKey:),
    // entitlement(_:), entitlementPublisher(for:)

    private(set) var seat: LicenseSeat?  // getter is internal → NOT visible to consumers
}

public enum LicenseSeatStoreError: LocalizedError { case notConfigured }

extension View {
    @MainActor public func licenseSeat(_ store: LicenseSeatStore? = nil) -> some View
}
```

Correct configuration:

```swift
LicenseSeatStore.shared.configure(apiKey: "pk_live_…") { cfg in
    cfg.productSlug = "your-product"
}
```

`seat?.heartbeat()` (a README pattern) fails outside the package — `seat` is internal. And `LicenseSeat.shared.heartbeat()` is NOT the fix in a store-based app: that's the other, unconfigured singleton (two-singleton rule) and throws `apiKeyRequired`/`productSlugRequired`. There is no manual heartbeat path through the store; rely on the automatic heartbeat that `activate()` starts (`heartbeatInterval`, default 300 s, 0 disables).

## Property wrappers

`#if canImport(SwiftUI)`, backed by `@StateObject private var store = LicenseSeatStore.shared`:

```swift
@LicenseState private var status                  // wrappedValue: LicenseStatus
@EntitlementState("pro-features") private var hasPro  // wrappedValue: EntitlementStatus
```

## LicenseStatus enum

Source: `Sources/LicenseSeatSDK/Models/LicenseStatus.swift`.

```swift
public enum LicenseStatus: Equatable, Sendable {
    case inactive(message: String)
    case pending(message: String)
    case invalid(message: String)
    case offlineInvalid(message: String)      // DEAD — never constructed (v0.4.1)
    case active(details: LicenseStatusDetails)
    case offlineValid(details: LicenseStatusDetails)  // DEAD — never constructed (v0.4.1)
}

public struct LicenseStatusDetails: Equatable, Sendable {
    public let license: String        // the license KEY string — NOT a struct (master drifted here)
    public let device: String         // device identifier
    public let activatedAt: Date
    public let lastValidated: Date
    public let entitlements: [Entitlement]
}
```

**Only `.active`, `.inactive`, `.invalid`, `.pending` are ever produced.** `getStatus()` is the sole producer feeding both `statusPublisher` and the store's `$status`; a successful offline verification maps to `.active`, not `.offlineValid`. Verified by full-repo grep: the offline cases appear only in the enum declaration and in example-app switches. Cover them with a merged/default branch for exhaustiveness only.

**`.pending` is what you get right after a successful `activate()`** — `getStatus()` returns `.pending("License pending validation")` whenever the cached license has no validation record, and activation caches without one. The first auto-validation runs a full `autoValidateInterval` (default 1 h) later, so status-driven UI shows "not licensed" for up to an hour unless you treat the successful `activate()` return itself as the licensed transition and make `.pending` keep-last-state.

Entitlement checking:

```swift
public struct EntitlementStatus: Equatable, Sendable {
    public let active: Bool
    public let reason: EntitlementInactiveReason?   // .noLicense / .notFound / .expired
    public let expiresAt: Date?
    public let entitlement: Entitlement?
}
```

## LicenseSeatConfig (all fields + defaults)

Source: `Sources/LicenseSeatSDK/LicenseSeatConfig.swift`. All 16 fields:

| Field | Type | Default | Notes |
|---|---|---|---|
| `apiBaseUrl` | String | `https://licenseseat.com/api/v1` | override in tests |
| `apiKey` | String? | nil | publishable `pk_live_…` |
| `productSlug` | String? | nil | required for all calls |
| `storagePrefix` | String | `licenseseat_` | cache key prefix |
| `deviceIdentifier` | String? | nil | nil = auto (see below) |
| `autoValidateInterval` | TimeInterval | 3600 | background re-validation |
| `heartbeatInterval` | TimeInterval | 300 | 0 disables auto-heartbeat |
| `networkRecheckInterval` | TimeInterval | 30 | offline connectivity probe |
| `maxRetries` | Int | 3 | API retries |
| `retryDelay` | TimeInterval | 1 | base, exponential backoff |
| `offlineFallbackMode` | OfflineFallbackMode | `.networkOnly` | or `.always` |
| `offlineTokenRefreshInterval` | TimeInterval | 259200 (72 h) | offline token refresh cadence |
| `maxOfflineDays` | Int | **0 (disabled!)** | offline grace period — set it |
| `maxClockSkewMs` | TimeInterval | 300000 (5 min) | clock-tamper tolerance |
| `telemetryEnabled` | Bool | **true** | 17-field device telemetry |
| `debug` | Bool | false | logging |

```swift
public enum OfflineFallbackMode: String, Codable, Sendable {
    case networkOnly = "network_only"   // offline verify only when network is down
    case always = "always"              // prefer offline verify
}
```

Constants: `LicenseSeatConfig.sdkVersion == "0.4.1"`, `LicenseSeatConfig.productionAPIBaseURL`.

## Errors

`Sources/LicenseSeatSDK/LicenseSeatError.swift` — SDK-side failures. **This is the v0.4.1 tag's enum** (master's differs — docs written from master list cases like `notConfigured`/`noLicenseKey` that do not exist at 0.4.1; `notConfigured` at 0.4.1 lives on `LicenseSeatStoreError`, not here):

```swift
public enum LicenseSeatError: LocalizedError, Sendable, Equatable {
    case noActiveLicense, apiKeyRequired, productSlugRequired,
         invalidOfflineToken, invalidKeyId, invalidPublicKey,
         cryptoUnavailable, networkError, deviceIdentifierError, cacheError,
         validationFailed(reason: String), activationFailed(reason: String)
}
```

`Sources/LicenseSeatSDK/Networking/APIError.swift` — server-reported failures:

```swift
public struct APIError: LocalizedError, Equatable, Sendable {
    public let code: String?                    // free-form server string, NOT an enum
    public let message: String
    public let status: Int                      // HTTP status code
    public let details: [String: Any]?
}
```

**Routing-level failures use real HTTP codes even though validation results are always-200:** a wrong or missing product slug returns HTTP 404 with `code: "product_not_found"`; a bad API key returns 401. If activation 404s with a key you believe is valid, check the dashboard for the product slug before touching Swift.

Known `code` values (union of source doc-comments and README — neither list is exhaustive, always include a default branch): `license_not_found`, `product_not_found`, `expired` / `license_expired`, `revoked`, `suspended` / `license_suspended`, `seat_limit_exceeded`, `device_not_activated`, `device_mismatch`, `product_mismatch`, `parameter_missing`.

```swift
do { try await LicenseSeatStore.shared.activate(key) }
catch let error as APIError {
    switch error.code {
    case "seat_limit_exceeded": // "Deactivate another device first."
    case "license_not_found":   // "Check the key for typos."
    default:                    // error.message
    }
}
```

## Events catalog

Subscribe via `licenseSeat.on("name") { data in … }` (returns `AnyCancellable`) or `eventPublisher` (Combine).

| Event | Fires when |
|---|---|
| `activation:start/success/error` | activation lifecycle |
| `validation:start/success/failed/error` | online validation |
| `validation:offline-success/offline-failed` | offline verification |
| `deactivation:start/success/error` | deactivation lifecycle |
| `license:loaded` | cached license loaded at startup |
| `license:revoked` | server revoked the license |
| `offlineToken:verified` / `offlineToken:verificationFailed` | offline token signature check |
| `heartbeat:success` / `heartbeat:error` | heartbeat result |
| `autovalidation:cycle` | auto-validation tick |
| `network:online/offline` | connectivity change |
| `sdk:reset` | state cleared |

**Bug (v0.4.1):** the internal `allEvents` catalog backing *unfiltered* `eventPublisher` subscriptions lists offline events under a stale `offlineLicense:*` prefix, but emission uses `offlineToken:*`. Unfiltered publisher subscriptions silently miss them; explicit `.on("offlineToken:verified")` or a `.filter { $0.name.hasPrefix("offlineToken:") }` works (exact string match at emit time).

## Offline validation methods

`Sources/LicenseSeatSDK/LicenseSeat+OfflineValidation.swift`, public since 0.4.1:

```swift
public func syncOfflineAssets() async
// fetches + caches the signed offline token and Ed25519 signing key, quick-verifies locally

public func verifyCachedOffline() async -> ValidationResponse
// full local Ed25519 verification pipeline against the cached token; never throws —
// failures come back as ValidationResponse with valid == false and a code
```

`verifyCachedOffline()` failure codes: `no_offline_token`, `no_public_key`, `signature_invalid`, `license_mismatch`, `token_expired`, `token_not_yet_valid`, `license_expired`, `grace_period_expired`, `clock_tamper`, `verification_error`.

Verification checks: Ed25519 signature over a `canonical` JSON string (CryptoKit, swift-crypto fallback), constant-time license-key comparison, `exp`/`nbf` windows, license expiry, grace period (`maxOfflineDays`), clock-tamper (`maxClockSkewMs`). Token format details: `references/platform-model.md`.

## Device identifier

`Sources/LicenseSeatSDK/Utilities/DeviceIdentifier.swift`:

- **macOS:** `"mac-<IOPlatformUUID>"` read from IOKit on demand — stable across app reinstalls, UserDefaults resets, and OS reinstalls on the same hardware. This is why macOS apps should leave `deviceIdentifier` nil.
- **iOS/tvOS/watchOS:** composite hash + random suffix cached in `UserDefaults.standard` under hardcoded key `licenseseat_device_identifier` (ignores `storagePrefix`) — regenerates after uninstall/reinstall (inferred from iOS container semantics).

## Persistence + concurrency

- Dual persistence: UserDefaults (`"\(storagePrefix)license"` etc.) **and** JSON at `Application Support/<bundleId>/<prefix>license.json`. Not Keychain — the cached license is a signed artifact, not a secret, but be aware backups/migration tools may carry it.
- `@MainActor` classes; background loops use `Task.detached` + `Task.sleep` (offline refresh still uses a legacy `Timer`).
- Combine usage is `#if canImport(Combine)`-gated with a hand-rolled `AnyCancellable` fallback.
- Testability: `init(config:urlSession:)` and `configure(..., urlSession:)` accept an injected `URLSession`; the SDK's `Tests/LicenseSeatSDKTests/LicenseSeatStoreTests.swift` shows the pattern (custom `apiBaseUrl` + stub session).

## Version history

| Version | Date | Notes |
|---|---|---|
| 0.4.1 | 2026-02-09 | offline URL paths `-`→`_` (`/offline_token`, `/signing_keys/`); `syncOfflineAssets()`/`verifyCachedOffline()` made public |
| 0.4.0 | 2026-02-09 | device telemetry (17 fields), `heartbeat()`, `heartbeatInterval`, `telemetryEnabled` |
| 0.3.1 | — | cache moved Documents → Application Support; `synchronize()` for CLI use |
| 0.2.0 | — | dropped Linux; fixed non-deterministic device IDs |

CHANGELOG.md contains a stale `[1.0.0]` entry claiming macOS 11+/Linux support — no such tag exists; ignore it. Sources: repo tags + GitHub Releases API, accessed 2026-07-12.
