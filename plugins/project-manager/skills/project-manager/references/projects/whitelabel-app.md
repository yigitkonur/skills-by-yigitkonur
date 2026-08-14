# Project: whitelabel-app — white-label LobeChat fork

Domain orientation for supervising work in `/root/dev/whitelabel-app`. Read before writing any
mission brief for this repo. Accurate as of 2026-08-12; when a doc and the code disagree,
trust the code.

GitHub: `teamproject/lobe-white-label`. "Wope" is the reference brand/infra name in source, not
a product identity — customer identity comes from build-time `BRAND_*` values.

---

## 1. The tenant model

A **tenant** is one customer brand, defined by a single committed JSON at
`scripts/whitelabel/tenants/<slug>.json`. Each produces **three Vercel projects**:

```
<slug>         authenticated app     APP_AUTH_MODE=required
<slug>-demo    authless/mock app     APP_AUTH_MODE=mock, auto-logs-in a mock user
<slug>-market  per-tenant Hono gateway + OIDC alias
```

Both app projects share one isolated Neon Postgres (`<slug>-prod`) and Upstash Redis
(`<slug>-redis`), but each has its **own** runtime env and JWKS key. Auth mode is
process-global, which is *why* two full projects exist rather than one.

**The demo alias is never an OAuth callback target.**

### Config surface

| Block | Required | Notes |
|---|---|---|
| `slug` | strongly recommended | Pins project/DB/Redis names; unset → derived from brand name (drift risk with non-ASCII) |
| `brand.name`, `brand.social.site` | **yes** | Build fails without them; the rest of `brand.*` has defaults |
| `vercel.scope` / `vercel.domain` | no | `domain` sets a custom domain for the **auth'd** app only |
| `auth.ssoProviders` / `redirectUris.google` / `allowedEmails` | no | **Omission = no external SSO**, enforced, not a gap. When present, the redirect URI must exactly equal the computed callback |
| `gateway` | present by default | `{}` means "enabled, defaults" — not "unconfigured" |
| `llm` | no | Opts into a tenant's own OpenAI-compatible endpoint. Key never in JSON |
| `sandbox.consoleUrl` | auto-set | Installer provisions the console and writes it back |
| `storage` | no | Per-tenant bucket `<slug>-files`; account-level Tigris credentials |
| `search` | no | Default-on, serper-first. **Omission is the default chain, not "no search"** |
| `behavior.reasoningMode` | no | |

**Omission of an optional block is meaningful and intentional** — scrubbed or defaulted, not
a gap to "fill in".

---

## 2. Deployment topology

- **Frontend:** Vercel, **prebuilt artifact upload only**. Never trigger cloud/preview/branch
  builds or `turbo`. Build happens on an Ubicloud runner, then the artifact is uploaded.
- **Backend:** whitelabel tenants run backend as Vercel functions in the same project (no
  Railway). The reference flagship deployment is split Vercel+Railway — that divergence is
  intentional; don't "migrate" one to the other unasked.
- **Agent gateway containers:** what makes "close the tab, the agent keeps working" work.
  Each *project* gets `gw-<project>` and `gw-device-<project>` on the Coolify host under
  `*.endpoints.lol`. Provisioned by `provision-gateway-coolify.mjs <slug> --apply`, which
  must run **after** the Vercel pass (it reads back the per-project JWKS key).
- **OnlyBoxes sandbox console:** per-tenant code execution at `<slug>.endpoints.lol`.
  `SANDBOX_PROVIDER` must be `onlyboxes`; the fallback value `market` is a **hard failure**
  for a whitelabel tenant — every sandbox call 401s and surfaces only as a broken tool row
  inside a chat.
- **Storage (Tigris):** one account, **account-shared credentials**, dedicated bucket per
  tenant with CORS for both origins.
- **Neon / Upstash:** isolated per tenant.
- **QStash:** **account-shared** — no per-tenant instance. Isolation is by schedule ID/route.

---

## 3. The installer

`scripts/whitelabel/new-client.mjs` — turnkey CLI: gathers brand facts, writes the tenant
JSON, creates the client repo, dispatches the deploy. **Fail-closed by design:** any
console/Coolify/SSH/capacity/storage-credential failure aborts *before* dispatch. There is
deliberately no silent fallback to a shared bucket or `market` sandbox.

`deploy-whitelabel-fullstack.yml` dispatch inputs:

```
tenant_config   e.g. nova-ai.json (must be committed)
immutable_ref   full commit SHA; the workflow verifies HEAD equals it
target          must equal "production"
confirm_live    must equal "DEPLOY_TENANT"
vercel_org      optional
```

`destroy-whitelabel-tenant.yml`:

```
tenant_config    bare <name>.json basename
immutable_ref    full 40-char SHA
confirm_destroy  must equal "DESTROY_TENANT"
```

Destroy runs snapshot → plan → destroy → **prove absence** (fails if anything remains).

**Secret channel.** All per-tenant secrets travel only through the encrypted repo secret
`TENANT_DISPATCH_SECRETS`, sourced from the 0600 local feed
`~/.config/whitelabel-installer/tenant-dispatch-secrets.json`, managed by
`lib/tenant-dispatch-store.mjs`. `workflow_dispatch` inputs are **structurally unmaskable** —
never reintroduce a secret-carrying input. Never hand-edit the repo secret; go through the
feed.

---

## 4. tenant-doctor — the verification tool

```bash
bun run tenant:doctor                       # all tenants
bun run tenant:doctor -- <slug>             # one
bun run tenant:doctor -- --quick            # config+infra+endpoints only
bun run tenant:doctor -- <slug> --full      # + a real chat/search turn
bun run tenant:doctor -- --json
```

Credentials come from `.env.installer.local` (repo root, gitignored) or env. Secret values
are never printed — only presence and an 8-char fingerprint.

What it checks, and what each proves:

- **Infra existence** — Vercel projects, Neon project, Upstash DB really exist
- **Endpoint health** — market/health, main get-session, demo root, plus a dedicated
  OAuth-callback redirect probe (catches a 3xx with no `Location`)
- **Env correctness** — auth mode, SSO drift (expected vs actual), Google client
  presence/absence matching intent, allowed emails, default agent model
- **Sandbox + storage identity** — **hard failures**, not warnings. `SANDBOX_PROVIDER=market`
  or a bucket that isn't this tenant's own are states no legitimate tenant can be in
- **Cross-tenant secret sharing** — flags a shared `AUTH_SECRET` (forgeable cookies)
- **LLM proxy** — `/models` plus a real completion against both Smart and Fast models
- **Search — function, per provider** — a real Serper POST with the tenant key and a real
  SearXNG query, so a dead primary can't hide behind a working fallback
- **Storage** — real `HeadBucket` plus a CORS-origin check
- **Queue** — signing-key match, both schedules present, empty DLQ, and an unsigned POST
  correctly rejected with 401
- **Gateway** — all four hosts, **plus** a browser-equivalent WS auth handshake per project
  signed with that project's own JWKS key. This closes the "`/health` green but every
  browser login fails" gap
- **Resend / Redis** — key validity, verified sender domains, a real ping

**`--full` mode** additionally: calls the deployed demo over real tRPC, creates a fresh
topic, runs a real agent turn, and requires **persisted exact tool-call evidence**
(`lobe-web-browsing` fired with the exact query) *plus* a browser-rendered proof. Prints a
`Full chat` row and folds `full-chat ✓/✗` into the summary. Exits nonzero on failure.

A `Full chat ✓` means a real user reached the deployed app, asked something needing search,
the agent called the exact tool, the evidence persisted, and a browser render shows it.

---

## 5. Invariants — never let a worker break these

- Prebuilt-only Vercel deploys; never trigger a cloud build or `turbo`
- Visible-branding and behaviour-lockdown patches stay intact; preserve `parseUxConfig(...)`,
  env-driven provider policy, market-driven MCP selection. No generic
  `params.provider === 'openai'` branch, no automatic plugin mutation
- Kernel operator access stays allowlisted/off by default; provider URLs stay
  encrypted/proxied; completion cleanup must not close parked async-tool sessions
- Upstream adoption is selective — exclude Cloud billing/commercial packages; migrations
  generate in this fork's chain
- New tenants are committed config + workflow, **not forks**
- A tenant defect's generic cause is fixed in the installer/templates/runbook **first**;
  the tenant-specific patch comes after
- Gateway execution is default-on wherever `AGENT_GATEWAY_URL` is served
- External SSO is strictly opt-in; omission must scrub shared provider config at both build
  and runtime; keep email/password on the authenticated app
- OAuth secrets never touch tenant JSON, argv, logs, task files, or git history
- Never restore the old manual sandbox pre-step or a silent `market`/shared-bucket fallback
- `--no-sandbox` / `--no-storage` / `--no-gateway` are explicit recorded opt-outs; doctor
  keeps them hard red
- **Never weaken a check** to make CI or doctor pass
- Never touch `entire/*` branches
- Deploys, force-pushes, branch deletion, and credential changes need explicit authorization
  every time; ordinary pushes and fast-forward merges to `main` do not

---

## 6. Known limits — real, but NOT bugs

Don't let a worker "fix" these, and don't report them as defects:

- **Tigris credentials are account-shared; buckets are per-tenant.** Deliberate. Bucket-scoped
  IAM keys are a documented follow-up, not a gap to close unasked
- **Email sends from the shared verified domain** with a branded display name. Per-tenant
  branded sender is owner-gated DNS work
- **QStash is account-shared** — no per-tenant instance exists
- **`infra ⚠` in the doctor summary** means the *local* Neon/Upstash management-listing
  credentials are absent. It is **not** a tenant outage — runtime health is proven by the
  Redis ping, endpoint health, and queue rows
- **A `/health` 200 is liveness, not function** — this is why the gateway check includes a WS
  handshake
- **Background tasks for brand-new users** on a tenant-custom LLM fall back to a hardcoded
  mini model until the user saves a setting. Documented follow-up, not a regression
- **CI has no build gate and no full matrix** — a known accepted gap, not something a routine
  task should silently "fix"

---

## 7. CI reality

Every workflow is `workflow_dispatch`-only: `pr-ci.yml`, `heavy-tests.yml`,
`deploy-vercel-fullstack.yml`, `deploy-whitelabel-fullstack.yml`,
`destroy-whitelabel-tenant.yml`. No push/PR triggers anywhere, and **no branch protection on
main**.

The operating rule this project chose: **run CI manually on the exact final SHA** rather
than adding automatic triggers, to avoid standing runner cost.

```bash
gh workflow run pr-ci.yml --ref main
gh run list --workflow pr-ci.yml --json databaseId,headSha,conclusion -L 5
gh run view <id> --json headSha,conclusion,jobs
```

`ci-required` is the aggregate lane worth reading. **Never add Playwright/e2e to CI** — heavy
suites stay opt-in and have no cron deliberately.

GitHub ops for `teamproject/*` may need a specific gh config dir — check before trusting an
empty `gh` result.

---

## 8. Task bookkeeping

Tasks live at `.agent-docs/tasks/<MM-DD-name>/`, archived under `.agent-docs/tasks/archive/`:

```
task.json        id, title, status, priority, completedAt, notes (closing evidence)
prd.md           requirements
design.md        architecture
implement.md     execution plan
implement.jsonl  curated context for implement subagents
check.jsonl      curated context for check subagents
```

**Failure mode to watch:** `task.json` claims `completed` while the jsonl files still hold
only their seeded `_example` placeholder. That means bookkeeping was skipped — verify actual
code landed rather than trusting the status field.

"Done" here means status completed **and** notes carrying real verification evidence — e.g. a
specific doctor run with a topic ID and tool-call ID, not "tests pass".

---

## 9. First five minutes

```bash
git status
git log --oneline -20
git fetch origin main --quiet
git log origin/main..HEAD --oneline    # local not pushed
git log HEAD..origin/main --oneline    # remote not pulled

ls .agent-docs/tasks/
cat .agent-docs/tasks/<active>/task.json | head -30

gh run list --limit 10

ls scripts/whitelabel/tenants/
bun run tenant:doctor -- --quick
```

If the doctor reports a Vercel-wide failure, check the token first — `.env.installer.local`
can hold a stale one while the CLI auth store has a working token.
