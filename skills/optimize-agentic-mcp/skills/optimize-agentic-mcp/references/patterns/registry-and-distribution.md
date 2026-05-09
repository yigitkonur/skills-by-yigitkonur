# MCP Registry, Gateway, and Trust Ecosystem

How to choose where to publish an MCP server, which gateway to route consumers through, and what trust signals actually defend against the 2025 supply-chain attack wave. The generic meta-server gateway pattern lives in `composition.md`; the hosting substrate (Cloudflare, Vercel, Fly, Lambda) lives in `deployment-platforms.md`. This file is about the **distribution and trust layer** — catalogs, namespaces, federation, and the named incidents that reshaped the ecosystem.

## The Three-Tier Taxonomy

The MCP distribution ecosystem splits into three functionally distinct tiers. Confusing them is the single most common architectural error in 2025-26.

| Tier | What it does | What it is NOT | Examples |
|---|---|---|---|
| **Registries** | Index metadata about servers; answer "does this server exist?" and "who owns this name?" | A runtime — does not execute tool calls | Official Registry, Smithery (hybrid), MCP.so, PulseMCP, Docker MCP Catalog, GitHub MCP Registry, Glama |
| **Gateways / Aggregators** | Sit on the request path; aggregate N upstream servers into 1 endpoint; apply policy, auth, logging | A catalog — they consume registries, not replace them | MetaMCP, MCPJungle, Portkey MCP Gateway, Cloudflare AI Gateway, Glama Gateway |
| **Hosted Tool-as-a-Service** | Execute tools on their infra with managed OAuth; you build against their API, not MCP directly | A neutral registry — they are the runtime and the catalog | Composio, Klavis, Arcade.dev, Pica, Smithery (hybrid), Gumloop, Superinterface |

**The consolidation event**: Anthropic donated MCP to the **Linux Foundation Agentic AI Foundation on 2025-12-09** ([anthropic.com, 2025-12](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)). The **Official MCP Registry preview launched 2025-09-08** ([blog.modelcontextprotocol.io, 2025-09](https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/)) and froze **API v0.1 around 2025-10-24**. GitHub, Docker, PulseMCP, and Smithery all now either federate from it or implement its API. **v0 is unstable — do not implement it** ([docs.github.com, 2025-10](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-mcp-usage/configure-mcp-registry)).

---

## 1. Registries — the Catalog Tier

### Official MCP Registry — `registry.modelcontextprotocol.io`

Positioned as "DNS for MCP": open metadata API, no hosting, no code execution. Donated to LF AAIF 2025-12-09.

- **Trust model**: namespace authentication via **GitHub OAuth**, **GitHub Actions OIDC**, **DNS TXT record**, or **HTTP `/.well-known/mcp-registry-auth`** ([modelcontextprotocol.io, 2025-10](https://modelcontextprotocol.io/registry/authentication)). Scanning delegated to downstream aggregators.
- **Manifest**: `server.json`. Name format reverse-DNS — `io.github.alice/weather-server` for GitHub-authed publishers, `com.example/server` for DNS-verified.
- **Versioning**: each entry has an **opaque stable UUID** that never changes even when name or metadata change. Semver in `version` field. API endpoints: `GET /v0.1/servers`, `GET /v0.1/servers/{serverName}/versions/latest`, `GET /v0.1/servers/{serverName}/versions/{version}`. Flat URL encoding: `com.example%2Fmy-server`.
- **Pricing**: free.
- **Audience**: downstream aggregators, sub-registry operators, enterprise mirrors. **Not a user-facing portal.**
- **Publish**: `mcp-publisher login github && mcp-publisher init && mcp-publisher publish`. DNS auth: `mcp-publisher login dns --domain example.com --private-key "$KEY"`.

### Smithery.ai — Registry + Hosted Gateway + CLI

Self-styled largest open MCP marketplace. Hybrid: catalog + managed hosting + OAuth broker + CLI.

- **Trust model**: **"Verified" badge after publishing**; automated scan on publish via `/.well-known/mcp/server-card.json`; crawls from Cloudflare Workers IPs with `User-Agent: SmitheryBot/1.0`; servers **must return HTTP 401 (not 403)** for unauthenticated requests so OAuth discovery works per RFC 9728 ([smithery.ai/docs, 2025](https://smithery.ai/docs/build)). Tokens advertised as "ephemeral."
- **Manifest**: `smithery.yaml` at build time (`startCommand`, `type: stdio|sse`, `configSchema`, `commandFunction`) + runtime `/.well-known/mcp/server-card.json` ([github.com/smithery-ai/cli, 2026-04-12, v4.8.0](https://github.com/smithery-ai/cli)).
- **Versioning**: `serverInfo.version` per deploy.
- **Namespace**: `@org/server` (e.g. `-n @your-org/your-server`).
- **Pricing**: free publish; paid managed hosting tiers.
- **Audience**: MCP server builders who want analytics + hosted OAuth; agent devs who want one-click `smithery mcp add`.

### MCP.so

Community directory. Popular but **unauthoritative**: "no namespace verification, no QA" ([truefoundry.com, 2025](https://www.truefoundry.com/blog/best-mcp-registries)). GitHub-issue submission. Free. Treat listings here as marketing surface, not trust signal.

### PulseMCP

Directory with **12,630+ servers updated daily** plus a **Sub-Registry API** implementing the Generic MCP Registry API — anyone who runs a PulseMCP-compatible endpoint becomes a federated MCP registry discoverable by conforming clients.

- **Trust model**: hybrid curation. Manual submissions via `/submit`, automated scrape+crawl with manual curation, federation with the Official Registry, optional vendor security analyses surfaced as `securityAnalysisFromVendorX.status: "pass"`, `isOfficial: true` flag.
- **Manifest**: extended `server.json`. Custom namespace `_meta.com.pulsemcp/server` carries enrichment (`visitorsEstimateLastFourWeeks`).
- **API**: `/api/docs/v0.1` ([pulsemcp.com/api, 2025](https://www.pulsemcp.com/api); [pulsemcp.com/statistics](https://www.pulsemcp.com/statistics)).
- **Audience**: partners wanting to federate catalogs, analysts wanting ecosystem stats.

### Docker MCP Catalog + Registry

Curated catalog of **signed, containerized** MCP servers. **The only platform shipping cryptographic signatures, SBOMs, and provenance by default.**

- **Trust model**: Docker-built images include cosign signatures, SBOM, build provenance. Container isolation is the default runtime. Non-compliant servers can be reviewed or removed ([docs.docker.com, 2025](https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/)).
- **Manifest**: OCI reference; submission is a PR to `github.com/docker/mcp-registry` ([github.com/docker/mcp-registry, 2025](https://github.com/docker/mcp-registry)).
- **Namespace**: Docker Hub `mcp/` organization.
- **Versioning**: standard OCI tags.
- **Pricing**: free.
- **Publish**: open PR with server spec → Docker builds, signs, publishes → live within 24h. Self-provided pre-built images skip signing.
- **Audience**: mainstream developers, enterprises that already run Docker, anyone who needs cryptographic supply-chain assurances.

### GitHub MCP Registry — `github.com/mcp`

Curated discovery portal, launched **2025-09-16** ([github.blog, 2025-09](https://github.blog/changelog/2025-09-16-github-mcp-registry-the-fastest-way-to-discover-ai-tools/)). Copilot Business/Enterprise customers configure which registry feeds their org.

- **Trust model**: editorial curation. Forward statement: "working with the MCP steering committee on the OSS MCP Registry to eventually allow self-publication."
- **Enterprise path**: host the OSS registry in Docker or a fork, **or** use **Azure API Center** (managed, CORS + governance; free tier basic, Standard tier for higher limits) as the GitHub-recommended managed option.
- **Required spec**: v0.1 endpoints (`GET /v0.1/servers`, `/v0.1/servers/{name}/versions/latest`, `/v0.1/servers/{name}/versions/{version}`). **v0 unstable — do not implement.**
- **Audience**: Copilot-first organizations.

### Glama.ai — Registry + Inspector + Gateway

Three in one: catalog, live inspector, and request-mediating gateway.

- **Trust model**: **quantitative quality-scoring algorithm**. Indexes after automated checks, logs every call, gates tool access, supports OAuth 2.1 DCR.
- **Manifest**: `glama.json` (`$schema: https://glama.ai/mcp/schemas/server.json`).
- **Scoring formula** ([glama.ai, 2025](https://glama.ai/mcp/servers/acashmoney/bio-mcp/score)):
  - Overall = **70% Tool Definition Quality** + **30% Server Coherence**.
  - Per-tool TDQS scores 1-5 across six dimensions, weighted: Purpose Clarity 25%, Usage Guidelines 20%, Behavioral Transparency 20%, Parameter Semantics 15%, Conciseness 10%, Contextual Completeness 10%.
  - Server-level TDQS = **60% mean + 40% minimum** (punishes one-great-tool + three-sloppy-tools vs flat averaging).
  - Server Coherence scored equal-weight on Disambiguation, Naming, Tool Count, Completeness.
  - Tiers: A ≥3.5, B ≥3.0, C ≥2.0, D ≥1.0, F <1.0. **B+ is passing.**
- **Gates**: **no LICENSE = not installable**; `glama.json` required; server must be inspectable; no known vulnerabilities; author verified.
- **Audience**: authors who want a public quality ranking; consumers who want a reproducible quality signal.

### OpenTools

Gateway-as-API, not a passive registry. Single OpenAI-compatible completions endpoint that executes MCP tools inline: `POST https://api.opentools.com/v1/chat/completions` with `tools: [{ "type": "mcp", "ref": "google-maps" }]` ([opentools.com, 2025](https://opentools.com/)).

- Managed connectors — "no personal API keys needed."
- Pricing: token pass-through at cost plus execution charges; unified billing.
- Audience: LLM app builders who want MCP tools without integrating an MCP client.

### MCP-Hub Verified Publishers

Trust-badge-as-a-service. **$199/year per organization**: submit certificate of incorporation + tax ID + domain ownership → 5-business-day review → green verified badge, priority listing, enterprise-policy access ([mcp-hub.info, 2025](https://mcp-hub.info/verified-publishers)). Automated security audit of published MCPs. Full refund if rejected. Cross-registry — the badge is a signal, not a hosting change.

---

## 2. Gateways / Aggregators — the Request-Path Tier

Gateways consume registries and upstreams; they do not replace them. See `composition.md` for the generic meta-server pattern. The profiles below are the **concrete products** most MCP operators compare in 2025-26.

### MetaMCP (metatool-ai)

Open-source aggregator, orchestrator, and gateway. Proxies N upstream servers into one unified server with middleware.

- **Trust**: **Better Auth** for frontend/backend; internal proxy uses session cookies; external access uses API keys via `Authorization: Bearer`; MCP OAuth spec 2025-06-18 compliant; OIDC SSO with PKCE; multi-tenant public/private scopes. **Public API keys cannot access private MetaMCPs** ([docs.metamcp.com, 2025](https://docs.metamcp.com/en/concepts/namespaces)).
- **Namespace collision handling**: tools auto-prefixed `{ServerName}__{originalToolName}`.
- **Middleware**: pluggable for logging, filtering, scanning.
- **Pricing**: free OSS; self-host.

### MCPJungle

Self-hosted gateway for private agent fleets. Single `/mcp` endpoint proxies many registered servers; supports Tool Groups.

- **Trust**: self-hosted; static bearer token for Streamable HTTP upstreams; upstream OAuth "coming soon."
- **Naming**: `<mcp-server-name>__<tool-name>` (collides-by-convention with MetaMCP, deliberately).
- **Enterprise**: OpenTelemetry observability ([github.com/mcpjungle/MCPJungle, 2025](https://github.com/mcpjungle/MCPJungle)).

### Portkey MCP Gateway

Enterprise control plane. "Unified layer to access and govern MCP tools without modifying your agents or servers."

- **Trust**: OAuth 2.1 + API tokens + header auth; JWT validation with identity forwarding; **credentials never leave the gateway**; BYO IdP (Okta, Entra, Auth0) ([portkey.ai, 2025](https://portkey.ai/features/mcp); [docs.portkey.ai, 2025](https://docs.portkey.ai/docs/product/mcp-gateway)).
- **Namespace**: `https://mcp.portkey.ai/{server-slug}/mcp`.
- **Observability**: end-to-end traces, per-tool logs, filterable by server/user/time.
- **Adoption**: "3,000+ GenAI teams."

### Cloudflare AI Gateway + Remote MCP + Enterprise Reference

Three stacked products, each independently useful:

1. **Cloudflare's own MCP catalog** — 10+ product servers at `mcp.cloudflare.com`, `docs.mcp.cloudflare.com`, `bindings.mcp.cloudflare.com`, `observability.mcp.cloudflare.com`. The Cloudflare-API MCP compresses **2,500+ REST endpoints into 2 tools** (`search()` + `execute()`) via the **Codemode** pattern in an isolated Dynamic Worker sandbox — see `deployment-platforms.md` for the Workers substrate.
2. **Remote MCP on Workers** — `workers-oauth-provider` makes a Worker **both OAuth provider (to MCP client) and OAuth client (to upstream)**. Implements RFC 7591 DCR + RFC 8414 AS Metadata ([developers.cloudflare.com, 2025](https://developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/)). Upstream tokens encrypted in Workers KV, never exposed to client.
3. **Enterprise reference architecture** — Cloudflare Access as OAuth provider, MCP portals revealing authorized servers, default-deny write; Gateway inspects/logs/blocks/redirects MCP JSON-RPC; Code Mode activated by appending `?codemode=search_and_execute` ([blog.cloudflare.com, 2025](https://blog.cloudflare.com/enterprise-mcp/)).

### Glama Gateway

Same product as the Glama registry — the quality score runs on gateway traffic, the gateway logs every call. Supports OAuth 2.1 DCR.

### Gateway comparison — when each one fits

| Need | MetaMCP | MCPJungle | Portkey | Cloudflare | Glama Gateway |
|---|---|---|---|---|---|
| Self-host required | Yes | Yes | Optional (SaaS default) | Yes (Workers) | No (SaaS) |
| Multi-tenant public/private scopes | Yes | Limited | Yes | Via Access | No |
| OAuth 2.1 DCR | Partial | Coming | Yes | Yes (reference impl) | Yes |
| Built-in observability | OTel-ready | OTel (enterprise) | First-class traces | Gateway logs + analytics | Per-call audit |
| Network edge | Operator's infra | Operator's infra | Portkey edge | Cloudflare global | Glama cloud |
| Namespace strategy | `{Server}__{tool}` | `{server}__{tool}` | `{slug}` in URL | Product subdomains | Repo path |

If the MCP operator already runs a control plane (Okta/Entra + Gateway/API Gateway), MetaMCP or Portkey slot in cleanly. If the MCP operator runs on Cloudflare's edge, `workers-oauth-provider` saves building OAuth from scratch. If the MCP operator wants a quality signal surfaced to consumers, Glama is the only gateway that publishes one.

---

## 3. Hosted Tool-as-a-Service — the Runtime Tier

You build against their API, not MCP directly. They take on OAuth, token refresh, compliance, rate limiting.

### Composio

"Your agent decides what to do. We handle the rest." 1,000+ managed app integrations, JIT tool calls with scoped permissions, centralized auth with token refresh. SOC 2 + ISO 27001:2022, ephemeral sandboxes, optional VPC/BYOC enterprise tier.

**Pricing** ([composio.dev/pricing, 2025](https://composio.dev/pricing)): Free 20K calls/mo · Starter $29/mo for 200K + $0.299 / 1K overage · Business $229/mo for 2M + $0.249 / 1K overage · Enterprise custom + SOC 2 + VPC.

### Klavis

Hosted MCP + open-source SDK. Markets itself as an **RL/training environment** — live environments for training and running agents with progressive tool discovery.

- **Trust**: SOC 2 Type II + GDPR; zero-trust architecture; multi-tenant isolation; per-tenant throttling; RBAC + guardrails; advertised 99.99% uptime SLA.
- **Namespace**: `Klavis-AI/klavis` GitHub org; REST at `api.klavis.ai/v1/mcp-server/strata` and `/instance`.
- **Distinctive feature**: **white-label OAuth** — business-branded OAuth consent screens (logo, colors, text). Unique among hosted-MCP vendors.
- **Deployment modes**: cloud (`klavis.ai`), self-host via Docker `ghcr.io/klavis-ai/github-mcp-server:latest`, or pipx `strata-mcp`.
- **"Strata" progressive discovery**: servers → categories → actions → schemas ([klavis.ai/blog, 2025](https://www.klavis.ai/blog)).

### Arcade.dev

MCP runtime, SDK, hosted cloud, plus on-prem, VPC, and air-gapped deployment. `@app.tool` Python decorators; `arcade configure` to deploy.

- **Trust**: **user-scoped auth (not service accounts)**; IDP flows; dedicated-tenant isolation; RBAC; SSO/SAML on enterprise; OSS MIT-licensed SDK.
- **Namespace**: `Provider.Capability` (e.g. `Google.SendEmail`).
- **Pricing** ([arcade.dev/pricing, 2025](https://arcade.dev/pricing/)): Hobby FREE (1,000 standard executions, 100 user challenges, 50 pro executions, 1 Arcade-hosted worker, 5 self-hosted) · Growth $25/mo + usage (2,000 std @ $0.01 after, 600 challenges @ $0.05 after, $0.05/server-hour) · Enterprise custom.

### Pica

Hosted MCP connector. Single endpoint `https://mcp.picaos.com/mcp`. Custom header `x-pica-secret: YOUR_SECRET_KEY` — no OAuth documented ([mcp.picaos.com, 2025](https://mcp.picaos.com/)). Pitched for OpenAI Agent Builder. Secret-header auth is weaker than the rest of this tier; fine for prototypes, avoid for regulated data.

### Gumloop and Superinterface (honorable mentions)

**Gumloop** ([gumloop.com/mcp, 2025](https://gumloop.com/mcp)) — workflow-oriented hosted MCP where each "flow" is exposed as a tool; useful when the MCP audience is non-technical operators composing flows visually rather than code.

**Superinterface** ([superinterface.ai, 2025](https://superinterface.ai/)) — hosted MCP for embedding AI assistants into customer-facing apps; overlaps with Klavis's white-label approach but positioned toward end-user chat rather than agent workloads.

### Hosted-tier decision factors

| Factor | Composio | Klavis | Arcade | Pica |
|---|---|---|---|---|
| Compliance ceiling | SOC 2 + ISO 27001 + VPC | SOC 2 Type II + GDPR | SSO/SAML + dedicated tenant | Secret header only |
| User-scoped auth | Per-connection | Strata progressive | **Yes (first-class)** | No (shared secret) |
| White-label | Enterprise only | **Branded OAuth screens** | Via on-prem | No |
| Self-host | No | Yes (Docker, pipx) | Yes (OSS MIT SDK) | No |
| Published pricing | Yes — 4 tiers | OSS + cloud (paid tiers) | Yes — 3 tiers | Not published |
| Best fit | Agent SaaS with 1,000+ integrations target | Training envs + white-label consumer products | Teams that need user-scoped auth with full audit | Quick prototypes against OpenAI Agent Builder |

---

## 4. Comparison Table

| Platform | Tier | Trust | Manifest | Versioning | Namespace | Pricing | Audience |
|---|---|---|---|---|---|---|---|
| Official Registry | Registry | GitHub OAuth + DNS/HTTP + OIDC | `server.json` | Opaque UUID + semver; API v0.1 | Reverse-DNS `io.github.*/*`, `com.example/*` | Free | Sub-registries, aggregators |
| Smithery | Registry + Hosted | Verified badge + server-card scan | `smithery.yaml` + `/.well-known/mcp/server-card.json` | `serverInfo.version` | `@org/server` | Free publish; paid hosting | MCP builders + agent devs |
| MCP.so | Registry | **None** | — | — | GitHub-issue curated | Free | Community |
| PulseMCP | Registry | Curated + vendor audits | Extended `server.json` | Sub-Registry API v0.1 | Inherits official | Free + partner API paid | Partners, analysts |
| OpenTools | Registry + Gateway | Managed connectors | `ref` in completions | — | Flat `ref` | Token pass-through + execution | LLM app builders |
| Docker Catalog | Registry | **Signatures + SBOM + provenance + container isolation** | OCI reference | OCI tags | Docker Hub `mcp/*` | Free | Mainstream devs |
| GitHub Registry | Registry | Curated; Azure API Center for enterprise | v0.1 spec | v0.1 API | Inherits official | Free + Azure Standard tier | Copilot customers |
| Glama | Registry + Gateway | **Quantitative quality score** | `glama.json` | Server releases | GitHub `owner/repo` | Free + paid | Authors + consumers |
| MetaMCP | Gateway | Better Auth + OIDC + multi-tenant scopes | Namespace groups | — | `{Server}__{tool}` prefix | Free OSS | Self-host teams |
| MCPJungle | Gateway | Static bearer; OAuth upstream soon | JSON or CLI | — | `{server}__{tool}` | Free OSS | Private agents |
| Portkey | Gateway | OAuth 2.1 + IdP + RBAC | `mcpServers` + Bearer | — | `{slug}` in URL | Unpublished | 3,000+ GenAI teams |
| Cloudflare | Gateway + Hosted | Access OAuth + Gateway policy + DCR | `mcpServers` JSON | Protocol version | Product subdomains | AI Gateway on all plans | Enterprise |
| Composio | Hosted | SOC 2 + ISO 27001 + VPC | N/A | API-stable | Per-toolkit | Free 20K → $29 → $229 → custom | Agent SaaS builders |
| Klavis | Hosted | SOC 2 Type II + GDPR + zero-trust | N/A | Python SDK v2.20.0 | Progressive (Strata) | Free OSS + paid cloud | AI labs + production |
| Arcade.dev | Hosted | User-scoped + SSO/SAML | `@app.tool` | Not documented | `Provider.Capability` | Free → $25 → custom | Dev teams + enterprise |
| Pica | Hosted | Secret header | N/A | — | — | Unknown | OpenAI Agent Builder |
| MCP-Hub Verified | Trust overlay | Incorporation + tax ID + domain + security audit | N/A | — | Cross-registry | $199/yr | Publishers needing a visible badge |

---

## 5. Named Trust Incidents (2025)

The ecosystem's trust architecture is not theoretical. Three incidents in 2025 reshaped how registries and gateways approach supply-chain risk. Any brand-sensitive MCP must be designed with these in mind.

### Incident 1 — Smithery path traversal exposed 3,000+ hosted servers

- **Timeline**: discovered 2025-06-10 → disclosed and acknowledged 2025-06-13 → partial fix + key rotation 2025-06-14 → full fix 2025-06-15 → public write-up 2025-10-15 through 2025-10-22 ([blog.gitguardian.com, 2025-10](https://blog.gitguardian.com/breaking-mcp-server-hosting/); [scworld.com, 2025-10](https://www.scworld.com/news/smithery-ai-fixes-path-traversal-flaw-that-exposed-3000-mcp-servers)).
- **Attack**: attacker-controlled `smithery.yaml` with `dockerBuildPath: ".."` and a malicious `Dockerfile` exfiltrated builder files including `.docker/config.json`, recovering an overprivileged fly.io token reusable against fly.io Machines API — arbitrary code execution on any machine in the organization.
- **Impact**: thousands of API keys exposed across 3,000+ hosted apps. No evidence of exploitation; fully patched.
- **Lesson**: centralized hosting platforms are high-value targets. Multi-tenant build systems need sandboxed builders, scoped build-time credentials, and yaml-path validation that rejects `..`.

### Incident 2 — `postmark-mcp` rug pull (first in-the-wild malicious MCP)

- **Timeline**: 2025-09-15 npm upload by `phanpak` impersonating ActiveCampaign's official Postmark MCP → 2025-09-17 v1.0.16 silently added BCC of every email to `phan@giftshop[.]club` → 2025-09-29 reported by The Hacker News and Koi Security → package deleted ([thehackernews.com, 2025-09](https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html)).
- **Downloads before discovery**: 1,643.
- **Attack class**: **rug-pull** (trusted-version → auto-update → backdoor) plus **npm typosquat** against a legitimate brand.
- **Impact**: exfiltration of password resets, invoices, customer correspondence, internal memos.
- **Lesson**: **the Official Registry's namespace authentication is the structural fix**. Brands must claim `com.<domain>/*` via DNS verification before a squatter claims it via GitHub. See the picker rubric below — this is why "tool vendor" archetype must publish to Official Registry first.

### Incident 3 — CVE-2025-6514 `mcp-remote` RCE

- **Timeline**: discovered 2025-07 by JFrog.
- **Attack**: a malicious MCP server returns a crafted `authorization_endpoint`; `mcp-remote` (no URL validation) passes it to the system shell → **RCE on the MCP client** ([docker.com, 2025](https://www.docker.com/blog/mcp-horror-stories-the-supply-chain-attack/); [nvd.nist.gov, 2025](https://nvd.nist.gov/vuln/detail/CVE-2025-6514)).
- **Scale**: 437,000+ downloads before patch. Used in tutorials by Cloudflare, Hugging Face, Auth0.
- **Significance**: first documented full RCE against an MCP client from a supply-chain vector. Shifted community's view: the client-side adapter is a supply-chain target.
- **Lesson**: validate every URL and every string consumed from upstream MCP responses before passing it to anything shell-like.

### Bonus — Kaspersky `devtools-assistant` PoC rug pull (2025-09-15)

Published as benign PyPI package; later backdoored to exfiltrate files via disguised GitHub API traffic ([securelist.com, 2025-09](https://securelist.com/model-context-protocol-for-ai-integration-abused-in-supply-chain-attacks/117473/)). Not weaponized in-the-wild, but formalizes the MCP rug-pull technique: trust → auto-update → swap.

---

## 6. Publisher Picker Rubric

Match archetype to registries and gateways. Do not publish everywhere reflexively — every surface is another place your namespace can drift, another scan that can fail, another badge to re-earn.

| Archetype | Primary | Secondary | Why |
|---|---|---|---|
| **Personal / hobby OSS server** | Official Registry (`io.github.<you>/*` via GitHub OAuth) | PulseMCP + Glama auto-index | GitHub OAuth is the cheapest trust foundation — zero-cost verified identity. |
| **Indie SaaS selling the MCP** | Smithery (distribution + analytics + managed OAuth) | Official Registry with `com.<domain>/*` + Docker Catalog | Smithery handles OAuth and provides user analytics; DNS-verified namespace protects brand; Docker Catalog gets you into `mcp/*` with signatures. |
| **Enterprise internal MCP** | Self-hosted MetaMCP **or** Portkey + GitHub MCP Registry via Azure API Center | Cloudflare Access for OAuth; MCP-Hub Verified ($199/yr) if you need an external green badge | Internal registry with RBAC, audit logs, IdP integration. **Never publish internal servers to public registries** — leakage risk is higher than discoverability upside. |
| **Open-source community server wanting trust signals** | Docker MCP Catalog (signed images + SBOM) | Glama (public quality score) + Official Registry | Docker signing is the strongest technical trust signal; Glama provides a reproducible quality ranking for consumers. |
| **Tool vendor (Stripe/Postmark class)** | Official Registry with DNS-verified `com.yourbrand/*` + Smithery + Docker Catalog + GitHub Registry | Composio/Klavis/Arcade for managed tool hosting if you don't want to operate the runtime | Brand protection via DNS-verified namespace + distribution across every client-facing catalog. **The `postmark-mcp` incident proves brand squatting is active — claim your namespace now.** |
| **Agent platform builder (consuming only)** | Gateway (MetaMCP / Portkey / Cloudflare) | Hosted (Composio / Klavis / Arcade) per OAuth workload | Do not publish. Aggregate upstream behind one controlled endpoint with observability; shift OAuth complexity to a hosted provider only when you need it. |

**Never rely solely on** MCP.so (no verification), Pica (single-tenant secret header), or any registry with no namespace authentication, for brand-sensitive work.

---

## 7. Publish-and-Consume How-Tos

### Official Registry

```bash
# Publish
mcp-publisher login github
mcp-publisher init                       # writes server.json
mcp-publisher publish

# Alt: DNS-verified namespace
mcp-publisher login dns --domain example.com --private-key "$KEY"

# Consume
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.alice/weather"
curl "https://registry.modelcontextprotocol.io/v0.1/servers/com.example%2Fmy-server/versions/latest"

# Self-host mirror
docker run -p 8080:8080 ghcr.io/modelcontextprotocol/registry:v1.0.0
```

### Smithery

```bash
# Publish
smithery mcp publish "https://your-server.com/mcp" \
  -n @your-org/your-server \
  --config-schema '{"type":"object","properties":{"apiKey":{"type":"string"}}}'
# Requirements: server exposes /.well-known/mcp/server-card.json
#               returns HTTP 401 (not 403) for unauth — needed for RFC 9728 OAuth discovery

# Consume
npm install -g @smithery/cli@latest
smithery auth login
smithery mcp search github
smithery mcp add https://server.smithery.ai/@smithery-ai/github
smithery tool call @smithery-ai/github createIssue '{"title":"...","body":"..."}'
```

### Docker MCP Catalog

```bash
# Publish: open PR against github.com/docker/mcp-registry with server spec.
# Docker builds, signs (cosign), attaches SBOM + provenance, publishes to mcp/<name>.
# Live in the catalog within 24h.

# Consume
docker mcp catalog pull registry.example.com/mcp/team-catalog:latest
# Or browse: https://hub.docker.com/mcp
```

### Cloudflare Remote MCP + AI Gateway

```typescript
// Publish: build a Worker using workers-oauth-provider
// The Worker becomes:
//   - OAuth provider to the MCP client (serves /authorize, /token, /register)
//   - OAuth client to the upstream service
// Routes exposed: /sse, /authorize, /token, /register
// Upstream tokens stored encrypted in Workers KV, never handed to the MCP client.
```

```json
// Consume
{
  "mcpServers": {
    "cloudflare-api": { "url": "https://mcp.cloudflare.com/mcp" }
  }
}
// For CI / automation: pass a Cloudflare API token as bearer.
// Enable Code Mode (search + execute) by appending ?codemode=search_and_execute.
```

### Glama (quality-gated)

```bash
# Submit the GitHub repo URL via https://glama.ai/servers
# Add glama.json at repo root with {"$schema": "https://glama.ai/mcp/schemas/server.json", "maintainers": [...]}
# In the Glama admin: Claim server → add Dockerfile → Deploy → Make Release
# Gate: no LICENSE = not installable. B+ (Overall ≥3.0) is passing.

# Consume
curl https://glama.ai/api/mcp/v1/servers/acashmoney/bio-mcp
```

### PulseMCP Sub-Registry (federation)

```bash
# Consume: standard Generic MCP Registry API on a partner registry
curl "https://www.pulsemcp.com/api/v0.1/servers?search=weather"

# Publish: submit at https://www.pulsemcp.com/submit
# PulseMCP auto-enriches with _meta.com.pulsemcp/server fields
# (visitorsEstimateLastFourWeeks, securityAnalysisFromVendorX.status)

# Federate your own registry: implement /v0.1/servers, /v0.1/servers/{name}/versions/latest,
# /v0.1/servers/{name}/versions/{version} per the spec. Clients conforming to v0.1 auto-discover.
```

---

## 8. Federation, Mirroring, and Self-Hosted Catalogs

One of the most important 2025 design choices in the Official Registry was opening the API spec so anyone can **implement the registry, not just consume it**. This has direct operational consequences:

- **Internal mirrors** — enterprises can run `ghcr.io/modelcontextprotocol/registry:v1.0.0` inside the VPC, federating from upstream Official Registry during sync windows. Copilot Enterprise admins can point the organization's MCP registry at a self-hosted instance or Azure API Center; all `github.com/mcp` discovery flows through the mirror.
- **Curated subsets** — a security team can stand up a sub-registry that mirrors only servers passing an internal security review, using the Official Registry UUID as the cross-mirror stable key. When upstream metadata changes but UUID is stable, automation doesn't break.
- **Namespace inheritance** — sub-registries that federate inherit the upstream namespace authority. If upstream says `com.stripe/*` is DNS-verified to Stripe, the mirror trusts that assertion; it cannot mint its own `com.stripe/*` entries without overriding authentication.
- **Partner enrichment** — PulseMCP's custom `_meta.com.pulsemcp/server` namespace shows how a federated registry adds value on top without forking the schema. Any federating registry is free to attach its own `_meta.<reverse-dns>/*` fields for enrichment.

Do not confuse self-hosted **registries** with self-hosted **gateways** — the registry answers "what is this server?", the gateway answers "execute this call." A private MCP deployment will usually need both: a Docker-hosted Official Registry mirror plus MetaMCP or Portkey for request-path policy.

---

## 9. Ecosystem Mechanics Worth Knowing

- **DNS-like design**: the Official Registry stores metadata only, never code. It positions itself as the root authority for aggregators — the same split as DNS (names + pointers) vs hosting (content).
- **Opaque stable UUIDs**: each registry entry has a UUID separate from its name. This lets aggregators store cache-safe pointers that survive renames and metadata edits — critical for federation at scale.
- **Namespace authority tiers**: GitHub OAuth · GitHub OIDC · DNS TXT · HTTP `/.well-known/mcp-registry-auth`. The last is the escape hatch for publishers who control a URL but not the domain's DNS.
- **SEP-1400 semver proposal**: authored 2025-08-28 by Anurag Pant and Surbhi Bansal ([github.com/modelcontextprotocol/modelcontextprotocol/issues/1400](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1400)) to replace MCP's date-based versioning with **semver 2.0.0**. Motivation: batching was added 2025-03-26 and removed 2025-06-18 — date-based schemes cannot express non-additive change. Status: open, still debated.
- **Nov 25 2025 spec update**: introduced **server identity** as first-class, alongside async operations, statelessness, and official extensions.
- **Namespace-collision conventions in the gateway tier**: MetaMCP and MCPJungle both use `{server}__{tool}` (deliberately aligned); Cursor uses `mcp_{server}_{tool_name}`; the OpenAI Agents SDK currently **errors** on duplicates ([issue #464, 2025-04-09, still open](https://github.com/openai/openai-agents-python/issues/464)) rather than de-duping.
- **Glama's 60% mean + 40% minimum server-level weighting**: penalizes "one great tool + three sloppy tools" vs a simple average. Reproducible — use the published formula when self-assessing before publishing.
- **Cloudflare API MCP's two-tool compression**: 2,500+ REST endpoints reduced to `search()` + `execute()` in a Dynamic Worker sandbox. Pattern name: **Codemode**.
- **Klavis white-label OAuth** is unique in the hosted tier — business-branded consent screens for a remote MCP, not a Klavis-branded screen. Useful for vendors embedding MCPs into their own product UX.
- **`workers-oauth-provider`** is a reference implementation for MCP spec 2025-03-26 auth — it implements RFC 7591 DCR + RFC 8414 AS Metadata and is the simplest path to a spec-compliant remote MCP.
- **OWASP MCP Top 10 (2025)** exists and maps to the incidents above: MCP03 (Tool Poisoning / Rug Pull / Schema Poisoning), MCP04 (Supply Chain), MCP09 (Shadow MCP Servers). Cross-reference with `threat-catalog.md` for defense tactics.
- **PulseMCP's Sub-Registry API** implements the **Generic MCP Registry API specification** — anyone can stand up a conforming registry and have MCP clients auto-discover it. Federation is explicit, not accidental.
- **MCPHosting "80% revenue share" pitch** on `github.com/BrowserMCP/mcp/issues/168` (2026-04-03) is the first documented third-party monetization solicitation against a major MCP project. Treat unsolicited "we'll host your server for a revshare" offers as supply-chain risk until they ship a trust model on par with Docker Catalog or Klavis.

---

## When This File Applies

Surface this reference when diagnosing:

- **"Where should we publish our MCP server?"** → Section 6 rubric.
- **"How do we prevent brand squatting on our MCP?"** → Section 5 (postmark-mcp), Section 6 (tool vendor archetype), Section 7 (Official Registry with DNS).
- **"Our enterprise wants a private catalog"** → Section 1 (GitHub + Azure API Center, self-host Official Registry), Section 2 (MetaMCP, Portkey).
- **"We want one endpoint for many servers"** → `composition.md` for pattern; this file for concrete products (MetaMCP, MCPJungle, Portkey, Cloudflare, Glama Gateway).
- **"How do we know a third-party MCP is trustworthy before we install it?"** → Section 1 (Glama quality score, Docker signing, Verified Publishers), Section 5 (what the attacks actually look like).
- **"Can we just build against Composio / Klavis / Arcade instead of MCP directly?"** → Section 3 — yes, with the trade-off that you are no longer publishing to the MCP ecosystem; you are consuming a hosted runtime whose tools happen to include MCP.
