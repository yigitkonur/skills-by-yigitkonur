# Project: crawler-service (crawler-omni)

Domain notes for supervising work in `/root/dev/crawler-service`, usually from the
worktree `.claude/worktrees/registration-automation` in a neighbouring Herdr pane. Distilled
from a supervision campaign over the registration → query → capture pipeline. This is a
point-in-time record — verify against live state before asserting any of it as fact.

`docs/CONTRACT.md` is the repo's declared single source of truth. Read it before writing any
mission brief. When the contract and a worker's claim disagree, the contract wins until a
live measurement overturns both.

---

## 1. What the system is

A crawler that (1) programmatically registers accounts on consumer AI engines, (2) uses those
accounts to run search-style queries, and (3) captures each answer plus the source URLs the
engine cited, storing it for a downstream product.

The chain, and who owns each link:

```
[registration]──►[session.json]──►[OmniRouteEngine]──►[capture]──►[Postgres]──►[downstream]
 services/         out/sessions/    /api/providers  packages/   crawler-api    projectradar
 registration/     (gitignored)     + /v1/chat      capture/    + migrations   (external)
```

Canonical engines: `chatgpt`, `perplexity`, `gemini`, `claude`, `copilot`, `grok`,
`deepseek`. Internal IDs map to OmniRouteEngine provider IDs by appending `-web`.

Live surfaces (both Coolify-managed, both were healthy during the campaign):

- OmniRouteEngine: `https://crawler-omni.endpoints.lol` — port 21128, container `crawler-engine-mvzu8…`
- crawler-api: `https://crawler-api.endpoints.lol` — port 21200, its own Postgres sidecar

Secrets live in a gitignored `.env` at the worktree root, loaded by `.envrc` via
`dotenv_if_exists`. `AGENTMAIL_API_KEY`, `CRAWLER_ENGINE_BASE_URL`, `CRAWLER_ENGINE_API_KEY`,
`CRAWLER_API_BASE_URL`, `PROXY_USER`, `PROXY_PASS`, `PROXY_POOL_FILE`. If a pane's statusline
shows `no env`, direnv has not loaded and every credential-dependent command will fail in a
confusing way — check this before diagnosing anything else.

---

## 2. The mistake that cost the most: build-vs-reuse

**Query execution is OmniRouteEngine's job, not `services/registration`'s.** A worker spent hours
writing ~39 throwaway `.mjs` browser-automation scripts to re-solve query execution from
scratch, then deleted every one. The capability it was rebuilding was already committed to
the same repository:

- `packages/capture/src/{sse,citations,quality,mentions}.ts` — SSE assembly, the four-strategy
  citation table from CONTRACT.md, capture-quality classification, brand-mention detection
- `services/crawler-api/src/domain/run-executor.ts` — fans a prompt across engines and
  accounts, persists the mandated capture shape, integration-tested against real Postgres

The build-vs-reuse question had been answered *and committed to the same git tree* before the
wasted effort started. Before greenlighting any engine-query work here, make the worker read
those paths first and say what they already cover.

Bespoke browser automation is justified only where an OmniRouteEngine lane is provably broken
upstream — and "provably" means a live measurement, not an assumption.

---

## 3. Known state of each engine lane

Measured live during the campaign. Re-measure before trusting; lanes rot.

| Engine | Registration | Query via OmniRouteEngine | The actual obstacle |
|---|---|---|---|
| chatgpt | committed | proven end-to-end into Postgres | cookie dies periodically; validator reports a Cloudflare block |
| perplexity | committed | lane works | free-tier quota exhaustion (`FREE_TIER_RATE_LIMITED`) — an *account* problem, not a credential one |
| claude | committed | capture confirmed | — |
| gemini | committed | **broken** | two independent defects, see §4 |
| grok | committed | **blocked at inference** | egress IP reputation, see §5 |
| copilot | committed | **blocked** | second challenge event, see §6 |
| deepseek | **none** | plumbing ready | signup blocked by abuse scoring — not a captcha, may not be solvable by engineering |

`testStatus: active` on an OmniRouteEngine connection proves the credential validated. It does not
prove inference works. An HTTP 200 whose SSE body contains `[Error: ...]` is a failure
wearing a success costume — and `captureQuality=complete` on such a response is a
classification defect, not a green.

---

## 4. Gemini: two defects stacked, fix the cheap one first

1. **Upstream:** OmniRouteEngine's `gemini-web.ts` drives a real Playwright browser; the composer
   click near lines 478–481 inherits Playwright's default 30s action timeout with no
   override. That matches the exact error string recorded in CONTRACT.md.
2. **Ours:** the harvested Gemini credential was under-captured — `credentialName` claimed
   `__Secure-1PSID + __Secure-1PSIDTS` while the stored value structurally contained one
   cookie.

Order matters and workers get it backwards. If Gemini never reaches a logged-in state, the
composer never renders, so the upstream timeout would be a *symptom* of our under-capture,
not the cause. Fix ours, re-measure, and only then treat the upstream timeout as real.

Forking OmniRouteEngine to patch it is acceptable — `deploy/README.md` documents a patched-image
workflow — provided the work happens in a separate worktree. `/root/dev/crawler-engine-engine` must never
be modified in place: other worktrees and a live service depend on it.

---

## 5. Grok: the egress lesson

This is the most transferable finding in the project.

A worker spent 25+ scripts on Grok and concluded "infrastructure blocker, needs a human
decision." The real blocker was one proxy line. Measured directly:

```
GET https://grok.com/rest/auth/get-user   (harvested sso cookie)
  direct from this host                 → 403
  through a pool proxy endpoint         → 200, authenticated
```

Two things the worker got specifically wrong:

**Proxy-level refusal vs site-level response.** Decodo refuses the CONNECT tunnel to
`grok.com` and `api.x.ai` at its own layer:

```
x-error-message: Access denied. You're trying to access a restricted target.
```

That is the vendor's allowlist, not Cloudflare. A bare status code conflates the two. Always
separate `CONNECT tunnel failed` from `CONNECT tunnel established` + an HTTP status. A sweep
over a second pool found 99/100 endpoints reaching `grok.com` with HTTP 200.

**Residential-vs-datacenter is the wrong axis.** Several passing endpoints are datacenter
ASNs (Leaseweb, Psychz, Ace Data Centers). The gate is IP *reputation*.

**cf_clearance pinning is a myth in this setup.** OmniRouteEngine's `grok-web.ts:688` warns the
cookie is pinned to the IP+TLS+UA that earned it. Measured: a cookie harvested through one
egress authenticates from unrelated proxies, and still works with `cf_clearance` and
`__cf_bm` stripped entirely — `sso` alone suffices. So credentials do **not** need pinning to
their harvest egress, and a proxy pool can rotate freely. An instruction derived from someone
else's code comment — including one you wrote into a mission brief — should lose to a
measurement.

**Still open at campaign end:** provider proxy config exists under `/api/settings/proxy`, but
a pinned live inference still returned `[Error: Request rejected by anti-bot rules.]`.
OmniRouteEngine's TLS client resolves its proxy from `CRAWLER_ENGINE_TLS_PROXY_URL`, then `HTTPS_PROXY`
/ `HTTP_PROXY` / `ALL_PROXY` (`grokTlsClient.ts:191-283`). The management-API setting does
not appear to feed that path. The fix is runtime env on the deployed service or a targeted
patch — verified by re-running the pinned inference, not by re-reading config.

---

## 6. Copilot: the diagnosis was wrong

The summary said hashcash was never accepted. Transcript forensics showed the opposite:
**hashcash is solved and accepted.** The next blocker is a second, unlabelled event:

```
{"event":"challenge","method":null,"parameter":null}
```

Nothing handles it. Separately, the UI-registration path produced `register()` reporting
`reachedHome: true` while the resulting page still showed a signed-out "Sign in to Copilot"
wall.

Upstream `solveHashcash` (`copilot-web.ts:84-93`) caps difficulty at 8 and, on failure to
solve within budget, sends an **empty token** rather than surfacing an error — so a failed
solve looks like a generic downstream failure. Copilot also has **no token refresh at all**;
a 401 surfaces as an undifferentiated 502.

Do not let a worker rewrite hashcash from zero. Point it at the `method: null` event and the
`reachedHome` contradiction.

---

## 7. Credential lifecycle — where "automatic" stops being automatic

The pipeline's real product requirement is that credentials stay alive without human
intervention. A worker delivered `src/liveness.ts` + `src/health-cli.ts` and reported the
requirement met. Independent checking found it is **diagnosis, not recovery**:

- `npm run health -- --apply` is a manual command — no scheduler, no Coolify service, no cron
- on `expired`, the policy deactivates the connection and prints `needs re-harvest (browser
  login)`. It does not trigger registration, create an inbox, re-harvest, or replace the
  crawler-api account

What genuinely good looks like here:

```
scheduled sweep
  → classify live / exhausted / expired / unknown
  → exhausted: stop selecting it, rotate to another active account
  → expired:   attempt login-first refresh of the same account
  → if unrecoverable: new AgentMail inbox → register → harvest → provision
                      → register in crawler-api → verify with a real query
```

The liveness module itself is genuinely well-reasoned and worth preserving — particularly its
insistence that `unknown` is not a failure verdict. A Cloudflare interstitial on a probe says
something about *our client's* TLS fingerprint, not about the credential; treating that 403 as
expiry would retire provably-good credentials and trigger endless pointless re-registration.
That asymmetry — a dead credential costs one failed run, a wrongly-retired live one costs a
full browser re-registration and can burn a non-resetting per-email quota — is the reasoning
to protect in any rewrite.

---

## 8. The two-database trap

Provisioning a credential into OmniRouteEngine is **not** enough. `run-executor` selects from
crawler-api's own `accounts` table. During the campaign OmniRouteEngine had 13 connections while
crawler-api had 5 account rows across four engines — so Grok and Copilot could not be selected
even once their credentials existed.

Any "the account pool is ready" claim needs both sides checked:

```bash
# OmniRouteEngine side
curl -H "Authorization: Bearer $CRAWLER_ENGINE_API_KEY" "$CRAWLER_ENGINE_BASE_URL/api/providers"

# crawler-api side
docker exec crawler-api-db-<id> psql -U crawler_api -d crawler_api \
  -c "SELECT engine_id, count(*) FILTER (WHERE is_active) FROM accounts GROUP BY engine_id;"
```

Reconciliation is idempotent-or-broken: an early attempt died on
`duplicate key value violates unique constraint "accounts_engine_id_connection_id_key"`.

---

## 9. Verifying a capture — the only proof that counts

```bash
docker exec crawler-api-db-<id> psql -U crawler_api -d crawler_api -P pager=off \
  -c "SELECT r.id, r.status, a.engine_id, a.ok, a.capture_quality,
             length(a.answer_text), a.citation_strategy
      FROM runs r JOIN answers a ON a.run_id = r.id WHERE r.id='<run-id>';" \
  -c "SELECT c.position, c.domain, c.strategy, c.confidence, c.url
      FROM citations c JOIN answers a ON a.id = c.answer_id
      WHERE a.run_id='<run-id>' ORDER BY c.position;"
```

A live SSE probe pinned to one connection, when you need to know whether a lane actually
answers:

```bash
curl -sS -N -H "Authorization: Bearer $CRAWLER_ENGINE_API_KEY" \
  -H "x-crawler-engine-connection: <connection-id>" -H "Content-Type: application/json" \
  -X POST "$CRAWLER_ENGINE_BASE_URL/v1/chat/completions" \
  -d '{"model":"<provider>-web/<model>","stream":true,"messages":[{"role":"user","content":"..."}]}'
```

Read the `delta.content` frames. Keepalive-only frames with no content is what a broken
Gemini lane looks like. Always `stream: true` — CONTRACT.md records the buffered path as
broken on web lanes.

---

## 10. Environment traps specific to this repo

**`gh` sees the wrong account.** An ambient `GH_TOKEN` for a personal account overrides both
`gh`'s active-account selection and git's credential helper, making the org's private repo
look nonexistent:

```
remote: Repository not found.
```

The repo exists and CI has run green many times. The worktree's `.envrc` already fixes this;
when direnv has not loaded:

```bash
env -u GH_TOKEN -u GITHUB_TOKEN GH_CONFIG_DIR=/root/.config/gh-project git ls-remote origin
```

This one burned the supervisor, not the worker — a bare 404 was reported to the user as
"the repo was never created". Confirm identity with `gh api user` before believing a 404.

**Worktree isolation refuses `cd`.** Git commands that compute a directory at runtime are
rejected outright:

```
This session is isolated in the worktree … Refusing to run it
```

The worker resolved it by writing a script that `cd`s to the absolute worktree path. Watch
that it doesn't "solve" it by operating on the main checkout instead.

**No local builds.** Repo policy: typechecks, tests, and builds run in CI. The workstation
stalls under load. A worker ran `npm run typecheck && npm test` locally and it passed — call
it out anyway; the policy exists because the failure mode is a stalled box, not a red test.

**Session files hold live cookies.** `services/registration/out/sessions/*.json` are mode 600
under a 700 directory, gitignored, never committed — verified. Keep it that way; CI has a
secret-scan job that fails the build on credential-shaped strings, and `src/redact.ts` is
where new patterns belong.

---

## 11. Recovering a worker's deleted scratch work

Everything a worker wrote and `rm -f`'d survives verbatim in the Claude Code session
transcript, which records each Write tool call with its full content and each Bash call with
its real output:

```
~/.claude/projects/-root-dev-crawler-service--claude-worktrees-registration-automation/
  <session-uuid>.jsonl        (this one ran to ~45 MB / 11,332 lines)
```

Never `cat`, `Read`, or `tail` one whole — grep and `jq` with tight filters. All 39 deleted
probe scripts were recovered this way after `git fsck --unreachable --dangling` found nothing
(never staged) and shell history had no trace (commands ran through the Bash tool).

This also makes the transcript a forensic record: **tool results are hard evidence, the
agent's prose to the user is testimony.** Grading claims against raw results is how the
"hashcash never accepted" story was overturned.

The recovered scripts carried one broadly useful lesson. What separated a working query
script from a failing one was not a longer timeout but a **negative guard** on completion
detection:

```js
// fires while the model is still restating the question
/KAYNAKLAR|Sources?:|https?:\/\//i.test(text) && text.length > 120

// working: same test, plus "and it is not still generating"
… && !/Claude is responding/i.test(text)     // Claude
… && !/Searching the web/i.test(text)        // Gemini
```

Gemini's working run finished in 10 seconds; the earlier "fix" of a 200-second poll was
treating a symptom.

---

## 12. Worker failure modes observed here

1. **Rebuilt a capability committed in the same repo** — never checked `packages/capture`
2. **Deleted every script that proved something worked**, including the working ones
3. **Diagnosed an infrastructure blocker without sweeping alternatives** — 25 Grok scripts
   against one proxy vendor, when the answer was a different egress
4. **Reported "all tasks completed" while its own statusline read
   `21 tasks (19 done, 1 in progress, 1 open)`** — and one shell still running
5. **Delivered diagnosis and called it recovery** (the health CLI)
6. **Proved one engine end-to-end and generalised to all of them**
7. **Ran local tests against explicit CI-only policy**

Notably absent: it did *not* fabricate. Transcript forensics found its factual claims
traceable to real tool results, including an explicit refusal to overclaim
(*"'6/6 sorgu çalışıyor' diyemem, çünkü çalışmıyor"*). The failure mode here is **premature
generalisation and scope-of-done inflation**, not invention — which calls for different
counters. Check the *boundary* of each claim rather than its truth.

---

## 13. Monitoring this pane — what actually works

Learned the hard way: the supervisor claimed to be watching and was not. Periodically calling
`agent get` between replies is not monitoring — the worker hit
`API Error: Server error mid-response`, stopped, and sat idle unnoticed until the user pointed
it out.

Two layers, because neither is sufficient alone:

**During an active turn — real push subscription.** Subscribe on the socket to both lifecycle
transitions and the exact error line:

```json
{"id":"watch","method":"events.subscribe","params":{"subscriptions":[
  {"type":"pane.agent_status_changed","pane_id":"<pane>"},
  {"type":"pane.output_matched","pane_id":"<pane>","source":"visible",
   "strip_ansi":true,"match":{"type":"regex","value":"^\\s*● API Error:"}}
]}}
```

Three bugs worth not repeating:

- Sending any second request (e.g. a `pane.read` baseline) down the **subscription socket**
  resets the connection. Keep that socket for events only; take state snapshots via the CLI.
- Matching on `recent_unwrapped` re-fires on scrollback that is already old. `visible` scopes
  it to the current screen.
- A bare `API Error:` substring matches the phrase inside your own mission prompt. Anchor the
  regex to the terminal's marker: `^\s*● API Error:`.

**Between turns — a scheduler safety net.** Harness-tracked background processes are killed
when the assistant turn closes, so the push watcher dies the moment you reply. A short-period
`CronCreate` job covers the gap: read state, stay silent while `working`, and act on anything
else. This is a fallback for a process-lifecycle limit, not a replacement for push events.

What the recovery policy should be, and what it must not be:

```
working                                 → silent, no user message
● API Error: Server error mid-response  → save evidence, send "continue", confirm working
idle / done                             → independently verify before relaying anything
blocked / unknown                       → read the pane, diagnose, escalate only if it's
                                          genuinely the user's call
test or CI failure                      → never a blind "continue"
```

The distinction that matters: `continue` is correct for a transient upstream server error and
wrong for everything else. A blanket auto-continue would bury a red test as if it were an API
hiccup.
