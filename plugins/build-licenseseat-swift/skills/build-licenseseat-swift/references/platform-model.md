# LicenseSeat Platform Model & Server API

What the LicenseSeat server does — domain model, endpoints, key types, offline tokens, lifecycle, propagation. All claims sourced from licenseseat.com docs and SDK source, accessed 2026-07-12.

## Contents
- [Domain model](#domain-model)
- [API keys: pk vs sk](#api-keys-pk-vs-sk)
- [Endpoints and shapes](#endpoints-and-shapes)
- [Seats and devices](#seats-and-devices)
- [Entitlements](#entitlements)
- [Offline licensing](#offline-licensing)
- [Air-gapped licensing](#air-gapped-licensing)
- [License lifecycle and revocation propagation](#license-lifecycle-and-revocation-propagation)
- [Heartbeats and telemetry](#heartbeats-and-telemetry)
- [Rate limits](#rate-limits)

## Domain model

Hierarchy: **Product → License → Seats/Activations → Devices**, with **Entitlements** attached to a license.

- **Product** — identified by `productSlug`, appears in every endpoint path.
- **License** — `key` (format like `LS-ABCD-1234-EFGH-5678`), `status`, `starts_at`, `expires_at`, `mode` (e.g. `"hardware_locked"`), `plan_key`, `seat_limit`, `active_seats`, `active_entitlements[]`, `metadata`, nested `product`.
- **Seat/activation** — consumed once per `activate` for a new device.
- **Device** — identified by a fingerprint (`fingerprint` / `device_fingerprint` / `device_id` all accepted on validate). macOS fingerprint source: `IOPlatformUUID`.

## API keys: pk vs sk

Stripe-like convention, per licenseseat.com/docs/llms.txt (verbatim): "Use `pk_*` (publishable) keys in client applications. Keep `sk_*` (secret) keys server-side only."

- Ship **only** `pk_live_…` in the app (Settings → API Keys in the dashboard). Client-safe by design; still lightly obfuscate it (e.g. Base64 + salt constant) so it doesn't sit in a bare `strings` dump.
- `sk_*` keys are for a vendor backend (issuing/managing licenses) — never in the binary.
- One marketing page shows `ls_live_…`; treat that as a stale example, `pk_`/`sk_` is canonical.
- **Unconfirmed:** no `pk_test_`/sandbox mode was found anywhere in the docs (searched 2026-07-12). For testing, use a dedicated test product + test license keys, or a stubbed `urlSession`.

## Endpoints and shapes

Base: `https://licenseseat.com/api/v1`. Auth header: `Authorization: Bearer pk_live_…`.

| Endpoint | Purpose |
|---|---|
| `POST /products/{slug}/licenses/{key}/activate` | consume a seat, bind device |
| `POST /products/{slug}/licenses/{key}/validate` | check validity |
| `POST /products/{slug}/licenses/{key}/deactivate` | release the seat |
| `POST /products/{slug}/licenses/{key}/heartbeat` | device liveness ping |
| `POST /products/{slug}/licenses/{key}/machine-file` | signed offline artifact (air-gapped) |
| `GET /signing_keys/{key_id}` | Ed25519 public key — **no auth required** |
| `/offline_token`, `/releases`, `/download_token`, `/health` | offline token fetch, update distribution, health |

**Validation always returns HTTP 200** — validity is the `valid` boolean; failures carry `error.code` / `error.message`. Exception: routing-level failures use real HTTP codes — a wrong API key is 401, a missing/unknown product slug is **404 with `product_not_found`** even when the key and license are fine. This is the cheap smoke test before debugging any client code:

```bash
curl -s -o /dev/null -w '%{http_code}' -X POST \
  "https://licenseseat.com/api/v1/products/<slug>/licenses/<key>/validate" \
  -H "Authorization: Bearer pk_live_…"
# 401 → key wrong · 404 → product slug doesn't exist in the dashboard · 200 → read the valid field
```

The base URL is `https://licenseseat.com/api/v1` — NOT `https://api.licenseseat.com` (a plausible-looking guess that shipped into a design doc once; there is no such host).

Response shape:

```json
{
  "object": "validation_result",
  "valid": true,
  "license": {
    "object": "license", "key": "LS-ABCD-1234-EFGH-5678", "status": "active",
    "starts_at": "2026-01-19T00:00:00Z", "expires_at": "2027-01-19T00:00:00Z",
    "mode": "hardware_locked", "plan_key": "pro-annual",
    "seat_limit": 5, "active_seats": 1, "active_entitlements": [], "metadata": {},
    "product": { "object": "product", "slug": "my-product", "name": "My Product" }
  }
}
```

## Seats and devices

- `activate` consumes one seat per new device; re-activating the same fingerprint does not double-consume, and a `machine-file` request for an already-activated device consumes nothing.
- `seat_limit_exceeded` on activation = no seats left. Recommended UX: "This license is active on too many devices. Deactivate another device first."
- Releasing a seat requires calling `deactivate` — clearing local state leaks the seat (dashboard removal is the only recovery).
- On macOS the SDK's hardware-derived device ID means reinstall ≠ new seat.

## Entitlements

- Attached to a license: `key` (lowercase alphanumeric + hyphen/underscore), optional `expires_at`, optional `metadata`.
- Three expiration modes: never / with the license / fixed duration from `starts_at`.
- Platform's stated best practice: **gate on entitlements, not `plan_key`** — plans change, entitlement keys are the stable contract.
- Client-side: `LicenseSeatStore.shared.entitlement("key")`, `entitlementPublisher(for:)`, `@EntitlementState("key")`. Inactive reasons: `no_license`, `not_found`, `expired`.

## Offline licensing

For devices that are *intermittently* offline (the normal desktop case):

- The SDK caches a signed **offline token** and verifies it locally with Ed25519 when the network is down (`offlineFallbackMode` decides when).
- Token refresh cadence: `offlineTokenRefreshInterval`, default 72 h (SDK source only — not in platform docs).
- Grace: `maxOfflineDays` (SDK default 0 = disabled; vendor guide recommends 7 days; a daily-driver desktop app should err generous, e.g. 14).
- Vendor TTL guidance: 30 days consumer, 90–365 enterprise.

Offline token payload (verified from SDK verification code; JSON casing inferred snake_case):

| Field | Type |
|---|---|
| `kid` | String — signing key id → `GET /signing_keys/{kid}` |
| `license_key`, `product_slug`, `mode`, `plan_key` | String |
| `seat_limit` | Int? |
| `exp`, `nbf` | Int (Unix) — token window; no `iat` field |
| `license_expires_at` | Int? (Unix) |
| `entitlements` | array |
| `metadata` | Any? |

Plus, alongside the payload: `canonical` (exact signed JSON string) and `signature.value` (Base64URL Ed25519 signature). Verification: decode public key (`Curve25519.Signing.PublicKey(rawRepresentation:)`), `isValidSignature(sig, for: canonicalData)`, then `exp`/`nbf`/license-expiry/grace/clock-skew checks.

Clock tamper: the SDK records last successful validation; a backwards clock jump beyond `maxClockSkewMs` (default 5 min) yields `clock_tamper`.

## Air-gapped licensing

For devices that *never* connect — operator-assisted, not automated. Not relevant to a normal consumer desktop flow, but the API:

```
POST /api/v1/products/{slug}/licenses/{KEY}/activate
  Authorization: Bearer pk_live_…
  {"fingerprint": "target-machine-fingerprint", "device_name": "Factory PLC 07"}

POST …/machine-file
  {"fingerprint": "target-machine-fingerprint", "ttl": 365, "include": ["license"]}
```

Produces a PEM-like Ed25519-signed file, manually transferred (USB) to the target. Machine-file encryption key binding: `SHA256(license_key + device_fingerprint)`. No challenge-response, QR, or dashboard wizard exists (docs state this explicitly).

## License lifecycle and revocation propagation

States surface as error codes on validate/activate: `expired`/`license_expired`, `revoked`, `suspended`/`license_suspended` (free-form strings; suspended-vs-revoked semantics are not documented — treat both as "not valid now").

**There are no webhooks.** Confirmed absent across llms.txt, the OpenAPI reference, and targeted searches (2026-07-12). There is also **no license-create API** — keys are issued from the dashboard (or by a purchase integration on LicenseSeat's side). For Gumroad specifically: marketing pages advertise an inbound Gumroad→LicenseSeat integration, but the docs said "coming soon" as of 2026-07-12 — verify it exists in the dashboard before depending on it; the fallback is manual key issuance. Propagation to a running client is polling-only:

| Channel | Default cadence |
|---|---|
| Auto-validation | 1 h (`autoValidateInterval`) → flips status, emits `license:revoked` on revocation |
| Heartbeat | 5 min (`heartbeatInterval`) |
| Offline reconnect | on reconnect; cached token dies at its TTL — vendor: "Revocation takes effect when the client reconnects; offline machine file will expire at its TTL." |

Consequence: after a dashboard revoke, a running app may keep working up to one auto-validation interval; an offline machine keeps working until its token TTL. Choose TTLs accordingly.

## Heartbeats and telemetry

- Heartbeat = device liveness; also fires after each auto-validation cycle. "Stale device" in the dashboard = no heartbeat for 7+ days.
- Telemetry (optional, `telemetryEnabled`, default **true**) attaches to activate/deactivate/validate/heartbeat bodies. Fields include: `sdk_name`, `sdk_version`, `os_name`, `os_version`, `platform`, `device_model`, `app_version`, `app_build`, `device_type`, `architecture`, `cpu_cores`, `memory_gb`, `locale`, `language`, `timezone`, `screen_resolution`, `display_scale`. Disabling it is the safe default for privacy-sensitive apps — flipping it on is a product decision, not a code tweak.

## Rate limits

From licenseseat.com/docs/api-reference/: Free 60 req/min · 1,000 req/day; Pro 300 req/min · 50,000 req/day; Enterprise unlimited. Headers: `X-RateLimit-Limit` / `-Remaining` / `-Reset`. Default SDK cadence (1 h validate + 5 min heartbeat ≈ ~312 req/day/device) fits the free tier for small device counts only — check tier before shipping defaults to many users.

## Sources (accessed 2026-07-12)

- https://licenseseat.com/docs/api-reference/ · https://licenseseat.com/docs/api/
- https://licenseseat.com/docs/guides-offline-licensing/ · https://licenseseat.com/docs/guides-air-gapped-licensing/
- https://licenseseat.com/docs/api-reference-signing-keys/ · https://licenseseat.com/docs/api-reference-telemetry/
- https://licenseseat.com/docs/entitlements/ · https://licenseseat.com/docs/sdks/ · https://licenseseat.com/docs/llms.txt
- https://github.com/licenseseat/licenseseat-swift (source, tags, releases)
