# Repository Discovery and Target Proof

Use this reference to turn an unfamiliar backend repository into a short, evidence-backed TestSprite test brief before creating or spending any cloud run.

## Deliverable

Produce this table before authoring tests:

| Question | Evidence | Decision |
|---|---|---|
| What public behavior matters? | Product docs, route code, native tests | Candidate TestSprite scenarios |
| What is the authoritative contract? | OpenAPI/schema plus implementation | Fields, errors, headers, streams to assert |
| How is the API authenticated? | Middleware, docs, secret wiring | public/static/auto-refresh auth |
| Which URL is safe to test? | Deploy config, environment docs | Public target and mutation policy |
| Which revision is live? | `/version`, image label, deploy API, CI | Expected and observed SHA |
| Which serving lane answered? | Host, tenant, route metadata, account/browser lane | Faithful reproduction boundary |
| Which external resources are required? | Account, proxy, provider, quota, human gates | Available, degraded, or blocked before run |
| Which TestSprite project owns it? | Repo config and project API | Project ID/type |
| What already exists? | Test list, saved code, result history | Reuse, edit, or create |
| What would this test catch beyond native CI? | Contract/risk statement | Keep, refine, or omit |

If any answer is unknown, gather evidence before filling it. Do not turn an assumption into a table entry.

## 1. Read the instruction hierarchy

Find and read agent/project guidance before interpreting code:

```bash
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README.md' -g 'CONTRIBUTING.md'
```

Read the root instructions and the nearest scoped file for every path you may edit. Record rules about branches, local-vs-CI testing, secrets, production probes, generated files, and deployment authorization.

Do not copy project-specific restrictions into this reusable skill. Apply them in that repository.

## 2. Map the backend surface

For TypeScript repositories, start with:

```bash
rg --files -g 'package.json' -g 'pnpm-workspace.yaml' -g 'turbo.json' \
  -g 'tsconfig*.json' -g '*openapi*' -g '*swagger*'
rg -n "route|router|app\.(get|post|put|patch|delete)|openapi|swagger" \
  --glob '*.ts' --glob '*.tsx' --glob '*.json' --glob '*.yaml' --glob '*.yml'
rg -n "authorization|bearer|api.?key|auth|middleware|rate.?limit|idempot" \
  --glob '*.ts' --glob '*.tsx'
rg --files -g '*.test.ts' -g '*.spec.ts' -g '*.integration.ts'
```

Then trace at least one request end to end:

```text
public route -> validation -> auth -> domain/service -> external dependency -> response mapper
```

For Python, Go, Java, Ruby, Rust, .NET, or another stack, inspect the equivalent manifests, route/controller registration, serializers/schema definitions, middleware, native integration tests, and deploy files. TestSprite still calls the finished service over HTTP; only repository discovery changes.

## 3. Establish contract authority

Read the implementation and the public schema side by side. Extract:

- method, path, content type, and authentication;
- required and optional request fields;
- success status and body shape;
- documented error statuses and typed error body;
- required response headers;
- streaming protocol and terminal marker;
- idempotency or state transition rules;
- source/citation/routing/correlation requirements; and
- external-provider conditions that may block the behavior.

Use native tests to find invariants that generated OpenAPI descriptions omit. Use product docs to find semantic requirements code types cannot express, such as “sources must be real URLs” or “targeted routing must not fall back.”

TestSprite Portal discovery can combine API documentation, natural-language intent, and live probes into an endpoint list. Treat that list as a candidate inventory: remove internal/deprecated/unsafe endpoints, correct inferred paths and auth, and reconcile it with repository truth before generation. Generated breadth is not evidence that every scenario is authorized or valuable.

### Conflict rule

When sources disagree, do not pick the most convenient assertion. Rank evidence:

1. observed intended deployment;
2. executable implementation and native tests;
3. published schema;
4. maintained product docs;
5. examples, comments, and generated prose.

Then classify the drift:

| Drift | Action |
|---|---|
| Implementation violates intended public contract | Write the TestSprite assertion and fix code |
| Schema is stale but behavior is intentional | Update schema before generating more tests |
| Deployment serves old code | Deploy intended SHA before release proof |
| Product rule is ambiguous | Find runtime or owner evidence; do not encode a guess |

## 4. Find the deployment path

Inspect repository-native deployment evidence:

```bash
rg --files .github .gitlab-ci.yml Dockerfile* docker-compose* wrangler.toml \
  wrangler.jsonc fly.toml railway.toml vercel.json 2>/dev/null
rg -n "deploy|environment|staging|production|version|revision|commit|sha|image" \
  .github docs scripts package.json 2>/dev/null
```

Adapt for the actual platform: Cloudflare, Kubernetes, Coolify, Fly, Railway, Render, AWS, GCP, Azure, or an internal deployer.

Find the narrowest faithful revision proof. Examples:

- `/version` returns a commit SHA;
- response header exposes release/revision;
- container image tag or digest maps to a commit;
- deployment API reports source revision;
- CI artifact provenance links the uploaded artifact to a SHA; or
- immutable release metadata is queryable in logs.

Do not infer deployment from “workflow succeeded.” Verify the target is serving that artifact.

### Target fingerprint

Record enough identity to reproduce the same boundary later:

| Field | Examples |
|---|---|
| Public target | scheme, host, base path, environment |
| Revision | full commit SHA, immutable image digest, or release ID |
| Route/lane | tenant, region, routing header, credential-backed vs login-less/browser lane |
| Saved test | test ID and `codeVersion` |
| Runtime resources | credential mode, account/slot/proxy/provider availability |

Probe the fingerprint immediately before and after a release-gating run. If it changes mid-run, the result may still diagnose one response but cannot prove a single revision.

## 5. Verify public reachability and safety

TestSprite cloud cannot call localhost, RFC1918/private addresses, or host-only tunnels. Confirm:

```bash
curl --fail-with-body --silent --show-error "$API_BASE_URL/health"
curl --fail-with-body --silent --show-error "$API_BASE_URL/version"
```

Use the repository's real health/version paths. A target without a version endpoint may require platform/API evidence instead.

Before live writes, determine:

- Is this staging, preview, canary, or production?
- Are create/update/delete operations authorized?
- Is there a dedicated tenant/account/namespace?
- Is cleanup idempotent and guaranteed?
- Can tests send notifications, charge money, consume scarce provider accounts, or trigger abuse controls?
- What concurrency can the environment safely absorb?

Also distinguish resource prerequisites from product behavior. A test that requires a scarce account, warm browser slot, healthy proxy, or third-party provider needs a preflight and a declared `runtime gate` outcome. CAPTCHA, SMS, payment, and other human challenges cannot be converted into a code pass.

If only production exists, prefer read-only behavior, invalid-input checks, idempotent operations, and fixtures designed by the application owners. A TestSprite suite is not authorization for load or destructive testing.

## 6. Resolve TestSprite state

Inspect current CLI and project state with JSON output:

```bash
testsprite --version
testsprite --output json auth status
testsprite --output json project list --max-items 100
```

Resolve project ID from explicit task context, `TESTSPRITE_PROJECT_ID`, repository `.testsprite/config.json`, or an unambiguous project match. Then inspect:

```bash
testsprite --output json project get "$PROJECT_ID"
testsprite --output json test list --project "$PROJECT_ID" --type backend --max-items 100
testsprite --output json test list --project "$PROJECT_ID" --type backend \
  --status failed,blocked --max-items 100
```

For each existing test, record:

- test ID and name;
- latest status and run ID;
- saved-code version;
- target observed in Data Flow/artifacts;
- whether it uses managed credentials;
- whether assertions still match the public contract; and
- whether it is independent, a producer, a consumer, or teardown.

Inspect the completed run's Data Flow as well as saved code. It reveals the actual host, request/response, producer/consumer wiring, cleanup calls, and “other observed” traffic; the test name and plan are only intent.

Do not create duplicates just because a test name is unfamiliar. Read its saved code first.

## 7. Convert discovery into a suite brief

Example:

| Priority | Capability | Scenario | Evidence source | Mutation | External gate |
|---|---|---|---|---|---|
| P0 | health | deployed revision responds | version route + deploy workflow | none | none |
| P0 | auth | missing credential is typed 401 | auth middleware + OpenAPI | none | none |
| P0 | search | response has non-empty valid source URLs | product docs + mapper test | read-only | provider availability |
| P1 | stream | metadata precedes terminal event | SSE parser + integration test | read-only | provider availability |
| P1 | create/read/delete | created ID round-trips, then cleanup | route code + schema | reversible | test tenant |

For each row, add the expected non-product outcomes (`deployment drift`, `resource gate`, `runner failure`) and how they will be recognized. This prevents a later environment failure from being mislabeled as a regression or silently accepted as a pass.

Every planned assertion must point to a source. Every planned mutation must name cleanup. Every external gate must remain visible in the final report.

## Troubleshooting discovery

| Symptom | Response |
|---|---|
| Multiple TestSprite projects match | Compare project type, test names, recent targets, and repo docs; do not guess |
| OpenAPI and code disagree | Run the intended deployment, classify drift, then fix the authoritative layer |
| Code fix exists but the target still fails identically | Compare revisions; an old deployment is expected to retain the old bug |
| No public URL | Use the repository's approved tunnel/preview path or stop at native tests; TestSprite cannot prove runtime |
| No revision endpoint | Use platform image/deployment provenance and record that proof explicitly |
| Production is the only target | Restrict to safe operations and obtain explicit scope before mutations |
| Existing tests have opaque names | Export saved code and history before replacing or duplicating them |
| Success requires an unavailable account/proxy/provider | Record a runtime gate; verify typed degradation separately and do not weaken the success contract |
