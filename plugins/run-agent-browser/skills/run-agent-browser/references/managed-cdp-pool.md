# Patchright browser pool on this host

Read this when the task needs Google AI Overview, Google AI Mode, or Gemini capture through the existing rotating-proxy browser pool; when checking pool capacity/health; or when diagnosing `503`/retry behavior.

Despite the historical filename, this service is **not a CDP pool for agent-browser**. It is an authenticated HTTP scrape API backed by four persistent headed Patchright/Chrome contexts.

## Deployed service

| Property | Current value |
|---|---|
| Coolify project | `zeogen` |
| Coolify application/resource UUID | `uh4q7gub10k6ffbgawcsvxef` |
| Container | `patchright-browserpool-uh4q7gub10k6ffbgawcsvxef-042104642940` |
| Internal port | `8091` |
| Public route | `https://browserpool.65.108.140.207.sslip.io` |
| Slots | 4 (`POOL_SIZE=4`) |
| Proxies | 20 configured; one proxy is leased per slot and burned/rotated on adverse verdicts |
| Restart policy | `unless-stopped` |
| Host port | None — routed through Coolify/Traefik only |

The public route responds `401` without Bearer auth. `GET /health` is deliberately unauthenticated and safe for operational counts.

## What it is for

Supported `provider` values are exact:

- `google_ai_overview`
- `google_ai_mode`
- `google_gemini`

The service handles:

- slot acquisition and queueing,
- headed Chromium contexts via Patchright,
- authenticated proxy selection,
- Google navigation and form interaction,
- DOM snapshots and HTML capture,
- provider-specific response text extraction,
- screenshot capture,
- Gemini citation extraction,
- AIO/adverse/captcha/blank/denied verdicts,
- burning a bad context/proxy and replacing it on the next request.

It is not a general-purpose interactive browsing API. It exposes no `/json/version`, CDP port, or browser WebSocket URL, and must not be passed to `agent-browser --cdp`.

## Security and credentials

`POST /warm` and `POST /scrape` require:

```http
Authorization: Bearer <POOL_AUTH>
```

`POOL_AUTH` and proxy records are secrets. Never print, log, commit, paste into command history, or return their values. Do not inspect `BROWSERPOOL_PROXY_URLS` except when a maintenance task explicitly requires it.

The secret lives in Coolify's encrypted application env for resource UUID `uh4q7gub10k6ffbgawcsvxef`. Use a process-local retrieval pattern that avoids stdout and keeps `POOL_AUTH` out of command-line arguments. The token is read by curl from a mode-600 config file, so it never appears in curl's process argument vector. Example for an authorized maintenance script:

```bash
source "$HOME/.config/coolify-cloud.env"
POOL_AUTH_FILE=$(mktemp)
CURL_CFG_FILE=$(mktemp)
cleanup() { rm -f "$POOL_AUTH_FILE" "$CURL_CFG_FILE"; }
trap cleanup EXIT
chmod 600 "$POOL_AUTH_FILE" "$CURL_CFG_FILE"

curl -fsS \
  "https://app.coolify.io/api/v1/applications/uh4q7gub10k6ffbgawcsvxef/envs" \
  -H "Authorization: Bearer $COOLIFY_CLOUD_API_TOKEN" \
| jq -r '[.[] | select(.key == "POOL_AUTH" and .is_preview == false) | .value] | first' \
> "$POOL_AUTH_FILE"
unset COOLIFY_CLOUD_API_TOKEN

printf 'header = "Authorization: Bearer %s"\n' "$(<"$POOL_AUTH_FILE")" > "$CURL_CFG_FILE"

# POOL_AUTH never appears in argv or shell history; curl reads it from the config file:
curl -fsS -K "$CURL_CFG_FILE" -X POST https://browserpool.65.108.140.207.sslip.io/warm
```

Do not keep the pool token in a generic global environment variable unless the user explicitly chooses that tradeoff. Unlike Steel, this pool is publicly routed; its Bearer token is the security boundary.

## Health and capacity

No auth required:

```bash
curl -fsS https://browserpool.65.108.140.207.sslip.io/health | jq
```

Current response shape:

```json
{
  "ok": true,
  "svc": "patchright-browserpool",
  "size": 4,
  "warm": 4,
  "busy": 0,
  "queued": 0,
  "proxies": 20
}
```

Interpretation:

- `size`: fixed slot count.
- `warm`: slots with a live browser context.
- `busy`: active scrape requests.
- `queued`: callers waiting for a slot.
- `proxies`: configured proxy pool size.

A healthy idle pool is `warm == size`, `busy == 0`, `queued == 0`.

## Warm endpoint

`POST /warm` launches any missing contexts and returns health:

```bash
curl -fsS -K "$CURL_CFG_FILE" -X POST \
  https://browserpool.65.108.140.207.sslip.io/warm | jq
```

Use it after a deploy/restart or when `warm < size`. It does not perform a scrape.

## Scrape request

`POST /scrape` accepts JSON:

```json
{
  "provider": "google_ai_overview",
  "query": "best ergonomic office chair for a tall person",
  "captureScreenshot": true
}
```

Validation:

- `provider` must be one of the exact three values.
- `query` must be a non-empty string.
- `captureScreenshot` defaults to true.
- `geo`, `language`, and `userAgent` are not part of the current deployed request contract. Unknown fields are ignored; using `prompt` instead of `query` returns `err:bad_request`.

Safe command pattern (token read from the mode-600 curl config created above, body from stdin):

```bash
curl -fsS -K "$CURL_CFG_FILE" -X POST \
  -H 'Content-Type: application/json' \
  --data-binary @- \
  https://browserpool.65.108.140.207.sslip.io/scrape <<'JSON'
{
  "provider": "google_ai_overview",
  "query": "example query",
  "captureScreenshot": true
}
JSON
```

## Response shape

The deployed endpoint returns a compact provider-normalized result:

```json
{
  "ok": true,
  "present": true,
  "answer": "...",
  "sources": ["https://..."],
  "verdict": "ok"
}
```

`captureScreenshot: true` may add a screenshot artifact; treat it as sensitive page data. Do not assume internal slot/proxy/debug fields are public response fields.

Common non-success verdicts observed or handled by the deployed service include `err:bad_request`, `err:aio_miss`, `err:not_typed`, captcha/rate-limit/blank/denied outcomes, and browser/page errors. `ok: false` can be a provider-result miss rather than infrastructure unavailability; check `/health` separately.

Gemini responses may include external citation links in `sources`; internal Google URLs are filtered and redirect wrappers may be unwrapped.

## Admission, retries, and burning

Verified numbers from the deployed source: 4 slots (`POOL_SIZE`), 150 s acquire timeout (`POOL_ACQUIRE_TIMEOUT_MS`, floor 1 s), 330 s scrape deadline (`POOL_SCRAPE_DEADLINE_MS`, default `DEFAULT_SCRAPE_DEADLINE_MS=330_000`, floor 10 s), 15 min proxy cooldown (`BROWSERPOOL_PROXY_COOLDOWN_MS`, floor 1 s), 20 proxies.

The service queues callers when all four slots are busy. If slot acquisition exceeds the 150 s acquire timeout, it returns:

```json
{
  "ok": false,
  "error": "browserPool acquisition wait exceeded",
  "retryable": true,
  "retryAfterMs": 150000,
  "busy": 4,
  "size": 4,
  "queued": 1
}
```

`retryAfterMs` mirrors `POOL_ACQUIRE_TIMEOUT_MS` (150000 by default). HTTP status is `503`. Respect `retryAfterMs`; inspect `/health`; retry once. Do not bypass into container internals or launch an unmanaged fifth browser.

Each scrape has a 330 s deadline. Retry attempts fit within the remaining deadline. The slot is burned after `captcha`, `rate_limited`, `blank`, `denied`, `browser_error`, or `page_error`; the proxy enters its 15 min cooldown and a fresh context uses the next eligible proxy.

## Operational verification

After a pool task:

1. Confirm HTTP response status and `ok`.
2. Record `present`, `verdict`, answer length, and source count — no credentials or private content.
3. Validate the requested answer/source fields and any screenshot artifact.
4. Recheck `/health`; ensure `busy` returns to zero and `warm` returns to four.
5. Do not expose screenshot base64 or full answer text if it contains sensitive content.

## Recovery

| Symptom | Action |
|---|---|
| `/health` fails | Inspect Coolify application/container status and logs; do not recreate manually before understanding the failure. |
| `warm < size` | Call authenticated `/warm`; inspect browser launch errors if it stays low. |
| HTTP 401 | Credential missing/invalid; fetch `POOL_AUTH` from Coolify securely. Do not guess or weaken auth. |
| `err:bad_request` | Fix the required `provider`/`query` request shape. |
| HTTP 503 | Respect `retryAfterMs`, check `busy`/`queued`, retry once. |
| Captcha/rate-limit verdict | Service burns context/proxy automatically; inspect the final verdict and `/health`. |
| Deadline error | Reduce concurrency or investigate target/provider latency; do not hide it with an unbounded client timeout. |
| Repeated blank/denied | Review provider selectors and target changes; the pool may need code maintenance. |

Never kill shared Chrome/Patchright processes, edit the rendered Coolify compose, expose 8091 as a host port, or read unrelated profile/session data.
