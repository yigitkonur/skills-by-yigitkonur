# Verification matrix

Run all of it. Each row fails differently, and passing one says nothing about the others. Use this
for a fresh setup and for auditing one somebody else built.

```bash
HOST=app.example.com
ORIGIN=<origin-ip>
TEAM=<team-name>
```

| # | Check | Command / action | Pass |
|---|---|---|---|
| 1 | Edge enforces | `curl -sI https://$HOST/` | `302`/`303` to `$TEAM.cloudflareaccess.com` |
| 2 | Origin refuses direct HTTPS | `curl -skI --resolve $HOST:443:$ORIGIN https://$HOST/` | `403` |
| 3 | Origin refuses direct HTTP | `curl -skIL --resolve $HOST:80:$ORIGIN --resolve $HOST:443:$ORIGIN http://$HOST/ \| grep ^HTTP` | `403`, or a redirect (`301`/`308`) that ends in `403` |
| 4 | DNS is proxied | `dig +short $HOST` | Cloudflare anycast addresses, not `$ORIGIN` |
| 5 | Login page offers the intended methods | open `https://$HOST/` | Google + Email OTP (+ others you configured) |
| 6 | In-domain identity gets in | log in as `someone@example.com` | app loads |
| 7 | **Out-of-domain identity is refused** | log in as a personal account | "That account does not have access." |
| 8 | Neighbours unaffected | `curl -sI https://other-app.example.com/` for each hostname on the same proxy | unchanged from before |
| 9 | App still healthy | container/service logs, restart count | no new errors, no restart loop |
| 10 | Deep links are covered | `curl -sI https://$HOST/some/inner/path` | same redirect as row 1 |

## What each failure actually means

**Row 1 returns 200 with app content** — Access is not in the path. Either the DNS record is
grey-cloud (check row 4) or the app hostname does not match the Access application's `domain`. A
trailing-path mismatch (`app.example.com/admin` vs `app.example.com`) leaves the rest of the site
open.

**Row 1 loops** — zone SSL mode is Flexible while the origin serves TLS. Set Full.

**Row 2 or 3 returns 200** — the lockdown is not applied or not attached. On Traefik, confirm both
routers carry the middleware and that the middleware name resolves (`@docker` vs `@file` suffix).
On a PaaS, assume the attachment was regenerated away; see the split-brain section in
`origin-lockdown.md`.

**Row 2 returns 403 but row 3 returns 200** — middleware attached to `websecure` only.

**Row 2 returns 200 only from certain networks** — the proxy is reading a forwarded header for the
client IP and trusting something it should not.

**Row 5 shows fewer methods than expected** — the app's `allowed_idps` is restricting the list, or
an IdP failed its own test. Check the IdP list.

**Row 6 fails with a Google error page** — Google consent screen, not Access. See
`google-oauth-idp.md`.

**Row 7 lets the account in** — the policy is wrong, or a `bypass` policy at lower precedence is
matching first. List the app's policies by precedence and check for `everyone`.

**Row 8 changed** — the origin rule was applied globally instead of scoped to this app's routers.
Scope it and re-verify every hostname.

## Make row 2 permanent

The bypass check is the one that silently regresses. Put it in CI or a post-deploy hook:

```bash
code=$(curl -sk -o /dev/null -w '%{http_code}' \
  --resolve "$HOST:443:$ORIGIN" "https://$HOST/")
[ "$code" = "403" ] || { echo "ORIGIN BYPASS OPEN: $code"; exit 1; }
```

## Evidence to record

Write the results table into the repo docs with the date, and note what was tested with which kind
of account — **describe the identity, never paste the address**: "an in-domain account" and "an
out-of-domain account", not real emails. Same for the origin IP and team name in anything public.
