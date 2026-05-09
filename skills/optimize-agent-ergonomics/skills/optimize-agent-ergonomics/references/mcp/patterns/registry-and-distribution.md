# Registry and distribution — publishing your MCP server

Three questions every MCP author has to answer before shipping: how do users **install** the server, where do they **discover** it, and how do they know which **version** to pin? This file covers the distribution mechanisms (npm, pip, Docker, hosted), the registry options (Official Registry, Smithery, Docker Catalog, Glama, GitHub MCP Registry), and the versioning hygiene that keeps production stable. Cross-link `transport-and-ops.md` for hosting platform constraints, `auth-identity.md` for OAuth registration during install, `security.md` for the supply-chain defenses these distribution channels enable.

The headline rule: **pin versions in production, never use `@latest`.** The 2025 supply-chain incidents (Smithery path traversal, `postmark-mcp` rug pull, CVE-2025-6514 in `mcp-remote`) all rewarded users who pinned and audited. Convenience-floats default to whatever the registry returns — that's the threat surface.

---

## Distribution mechanisms

Pick the distribution channel by where the server runs and who installs it. Most servers ship more than one — a typical production MCP publishes an npm package for `npx`-based local install, a Docker image for containerized deploys, and a hosted URL for zero-install remote access.

### 1. npm package — Node.js / TypeScript servers

The default for TypeScript MCP servers. Users install via `npx -y @org/mcp-server` or globally with `npm install -g @org/mcp-server`. The `npx -y` flow is the most common: clients (Claude Desktop, Claude Code, Cursor) configure the server with a `command: "npx"` + `args: ["-y", "@org/mcp-server@1.2.3"]` block, npm fetches and runs in one shot.

```json
{
  "name": "@acme/acme-mcp",
  "version": "1.2.3",
  "bin": { "acme-mcp": "./dist/server.js" },
  "engines": { "node": ">=20" },
  "files": ["dist/", "README.md", "LICENSE"]
}
```

Publish via `npm publish --access public`. Use scoped packages (`@org/name`) — easier to claim namespaces and prevent typosquats. Pin a minimum Node version; the SDK requires modern Node.

**Pros.** Universal Node tooling; `npx -y` is one command; semver native; npm registry handles deduplication and caching.
**Cons.** Users need Node installed; arbitrary code runs at install time; no signing by default.

### 2. Python pip / pipx — Python servers

The default for Python MCP servers. `pipx install acme-mcp` installs to an isolated virtualenv; `pipx run acme-mcp` runs without persistent install. Clients configure with `command: "pipx"` + `args: ["run", "acme-mcp==1.2.3"]`.

```toml
# pyproject.toml
[project]
name = "acme-mcp"
version = "1.2.3"
requires-python = ">=3.11"
dependencies = ["mcp>=1.0", "fastmcp>=3.0"]

[project.scripts]
acme-mcp = "acme_mcp.server:main"
```

Publish via `python -m build && twine upload dist/*` to PyPI. **Use a scoped or distinctive name** — PyPI typosquats are an active threat (Kaspersky's `devtools-assistant` PoC, 2025-09).

**Pros.** Native Python tooling; pipx isolation prevents dep conflicts; widely understood.
**Cons.** Cold install can be slow; arbitrary code runs at install time; no signing by default.

### 3. Docker image — containerized deploys

The right default when supply-chain assurances matter. Docker MCP Catalog is the only platform shipping cosign signatures, SBOMs, and provenance attestations by default. Users pull `docker pull mcp/acme-mcp:1.2.3` and run with predictable resource limits.

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY dist/ ./dist/

FROM node:20-alpine
LABEL org.opencontainers.image.source="https://github.com/acme/acme-mcp"
LABEL org.opencontainers.image.version="1.2.3"
COPY --from=build /app /app
WORKDIR /app
USER node
ENTRYPOINT ["node", "dist/server.js"]
```

Publish via `docker build` + `docker push registry/mcp/acme-mcp:1.2.3`. For Docker Catalog, open a PR against [github.com/docker/mcp-registry](https://github.com/docker/mcp-registry); Docker builds, signs, attaches SBOM and provenance, publishes to `mcp/<name>` within 24 hours.

**Pros.** Cryptographic signing (Docker Catalog); SBOM and provenance; sandboxed runtime; predictable env.
**Cons.** Users need Docker installed; image size is larger than a script; cold pull can be slow on first run.

### 4. Hosted URL — remote MCP, zero install

Publish a Streamable HTTP endpoint at a stable URL. Users add `{ "url": "https://mcp.acme.com/mcp" }` to their client config. No install. OAuth handled at the edge. The right default for SaaS-style MCP servers where the vendor wants to control the runtime.

```json
{
  "mcpServers": {
    "acme": {
      "url": "https://mcp.acme.com/mcp",
      "headers": { "Authorization": "Bearer ${env:ACME_TOKEN}" }
    }
  }
}
```

Cross-link `transport-and-ops.md` for the hosting-platform constraints (Cloudflare Workers, Vercel Fluid, Cloud Run, Lambda) — every choice has hard limits.

**Pros.** Zero install; vendor controls the runtime; OAuth at the edge; instant updates.
**Cons.** Users must trust the operator; no offline use; latency is network-bound.

### 5. Direct download / vendored binary

Rare but valid for some workflows: ship a single self-contained binary the user downloads. `flyctl mcp launch` provisions a Fly Machine and patches the local config — same idea, vendored runtime. Use when neither npm/pip/Docker nor a hosted URL fits.

---

## Registry options — where users find your server

Registries do not run code; they index metadata. Three tiers; pick by audience and trust model.

### Official MCP Registry — `registry.modelcontextprotocol.io`

Donated to the Linux Foundation Agentic AI Foundation on 2025-12-09 ([anthropic.com](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)). Open metadata API at v0.1; opaque stable UUIDs that survive renames. Trust model: namespace authentication via GitHub OAuth, GitHub Actions OIDC, DNS TXT record, or HTTP `/.well-known/mcp-registry-auth`. Free.

```bash
mcp-publisher login github
mcp-publisher init                           # writes server.json
mcp-publisher publish

# Alt: DNS-verified namespace for brand protection
mcp-publisher login dns --domain example.com --private-key "$KEY"
```

Name format is reverse-DNS: `io.github.<your-handle>/<server-name>` for GitHub-authed publishers, `com.<your-domain>/<server-name>` for DNS-verified. **Tool vendors must claim `com.<domain>/*` via DNS verification before a squatter claims it via GitHub** — the `postmark-mcp` rug-pull (2025-09) is the cautionary tale. Treat DNS verification as table-stakes brand protection.

**v0 of the API is unstable; do not implement against it.** Use v0.1 endpoints (`GET /v0.1/servers`, `GET /v0.1/servers/{name}/versions/latest`).

### npm and PyPI

The general-purpose package registries function as MCP registries by convention. No MCP-specific signal — anyone can publish — but they are the discovery mechanism that actually matters for `npx -y @org/mcp-server` and `pipx run mcp-server`. **Always use scoped names** on npm; **always claim distinctive names** on PyPI before someone else does.

Pair with one of the curated registries below for trust signals; don't rely on npm/PyPI alone for brand-sensitive servers.

### Docker MCP Catalog

The only platform shipping signatures + SBOM + provenance + container isolation by default. Submit via PR to `github.com/docker/mcp-registry`; live in Docker Hub `mcp/*` within 24h. Free. The strongest technical trust signal in the ecosystem.

```bash
# Publish: open PR with server spec; Docker builds, signs, publishes.
# Consume:
docker mcp catalog pull registry.example.com/mcp/team-catalog:latest
docker pull mcp/acme-mcp:1.2.3
```

### Smithery.ai — registry + hosted gateway + CLI

Hybrid: catalog + managed hosting + OAuth broker. **"Verified" badge after publishing**; automated scan via `/.well-known/mcp/server-card.json`. Servers must return HTTP 401 (not 403) for unauthenticated requests so OAuth discovery works per RFC 9728.

```bash
smithery mcp publish "https://your-server.com/mcp" \
  -n @your-org/your-server \
  --config-schema '{"type":"object","properties":{"apiKey":{"type":"string"}}}'

# Consume:
npm install -g @smithery/cli@latest
smithery auth login
smithery mcp search github
smithery mcp add https://server.smithery.ai/@smithery-ai/github
```

Trade-off: Smithery's 2025-06 path-traversal incident exposed 3,000+ hosted servers' API keys before being patched ([blog.gitguardian.com, 2025-10](https://blog.gitguardian.com/breaking-mcp-server-hosting/)). Centralized hosting is a high-value target — read [the post-mortem](https://www.scworld.com/news/smithery-ai-fixes-path-traversal-flaw-that-exposed-3000-mcp-servers) before committing critical workflows.

### GitHub MCP Registry — `github.com/mcp`

Curated discovery portal launched 2025-09-16 ([github.blog/changelog/2025-09-16](https://github.blog/changelog/2025-09-16-github-mcp-registry-the-fastest-way-to-discover-ai-tools/)). Editorial curation. For Copilot Business/Enterprise customers, admins configure which registry feeds the org. Enterprise path: host the OSS Official Registry in Docker, or use Azure API Center as the GitHub-recommended managed option.

### Glama.ai — registry + inspector + gateway

Quantitative quality scoring. Indexes after automated checks, runs every published server's tools through scoring rubric (Tool Definition Quality + Server Coherence). **Tier B+ (Overall ≥3.0) is the published "passing" threshold.** Useful when you want a public, reproducible quality signal — and when you can defend a B+ score.

### MCP.so

Community directory with no namespace verification or QA. Treat listings as marketing, not trust signal.

### PulseMCP

12,630+ servers, daily updates, federation API. Auto-enriches with usage stats. Useful for analysts and federation partners; less of a primary user destination.

---

## Versioning — semver, breaking changes, and handshake negotiation

### Semver discipline

Every release MUST follow [Semantic Versioning 2.0.0](https://semver.org):

- **MAJOR** when a breaking change ships — tool removed, parameter renamed, response shape changed in a way that breaks existing clients.
- **MINOR** when a backward-compatible feature ships — new tool, new optional parameter, new response field.
- **PATCH** when a backward-compatible bug fix ships.

The MCP spec itself uses date-based revision strings (e.g., `2025-11-25`), but server versioning is plain semver. **SEP-1400** ([github.com/modelcontextprotocol/modelcontextprotocol/issues/1400](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1400)) proposes moving the spec to semver too — open as of 2026-04, watch the issue.

### What counts as a breaking change

For an MCP server, breaking changes that bump MAJOR include:

- Removing a tool entirely (or making it return errors for previously valid inputs).
- Renaming a parameter, or making an optional parameter required.
- Changing the response shape — removing a field, changing its type, changing its semantics.
- Tightening input schema — narrowing an enum, lowering a max-length cap.

Non-breaking (MINOR):

- Adding a tool.
- Adding an optional parameter with a default.
- Adding a field to the response.
- Loosening input schema — widening an enum, raising a max-length cap.

### Version negotiation at handshake

The MCP `initialize` exchange surfaces the server's `version` (in `serverInfo.version`) and the spec revision (`protocolVersion`). Clients can read both. Most clients don't refuse to connect on version mismatch — they just trust the server. The version is a signal, not a gate.

Servers can use the client capabilities object (cross-link `client-compatibility.md`) to branch behavior, but they should not refuse to start because the client is on an older spec revision. Backward compatibility is a server concern; design for it.

### The "pin a version" rule for production

```json
{
  "mcpServers": {
    "acme": {
      "command": "npx",
      "args": ["-y", "@acme/acme-mcp@1.2.3"]
    }
  }
}
```

`@latest` (or no version specifier) silently picks up whatever the registry currently serves. The 2025 incidents prove this is a supply-chain hole:

- **`postmark-mcp` rug pull (2025-09).** Silent backdoor in v1.0.16; 1,643 downloads before discovery; `@latest` users were compromised, pinned-version users were not. ([thehackernews.com](https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html))
- **CVE-2025-6514 in `mcp-remote`.** RCE via crafted `authorization_endpoint`; 437,000+ downloads before patch. Users on a pinned old version were unaffected by the patched version's late update; users on `@latest` were exposed. ([nvd.nist.gov](https://nvd.nist.gov/vuln/detail/CVE-2025-6514))

Pin in production. Subscribe to release notifications. Audit before bumping. The 30 seconds it takes to read a changelog is cheaper than a rug-pull.

For Docker, pin by image digest (`mcp/acme-mcp@sha256:abc...`), not just by tag — tags can be repointed.

### Deprecation discipline

When you remove a tool or change a response shape, announce it in three places:

1. **The `instructions` field** of the `initialize` response (cross-link `tools.md` § "Use the `instructions` field"). Persistent, machine-readable, surfaced by every major client.
2. **The CHANGELOG** in the package. Conventional Commits + a generated changelog is fine.
3. **The deprecated tool itself** — return `isError: true` with text pointing at the replacement, for one full MAJOR release before fully removing.

GitHub's `create_pull_request_with_copilot` (issue #1220, 2025-10) is the cautionary tale — silent removal led to user confusion. Don't repeat it.

---

## Discovery — how clients actually find your server

Client discovery breaks into two phases.

### Phase 1 — install

The user runs the install command. Three patterns:

- **Direct config edit.** User pastes a `mcpServers` block into the client config (Claude Desktop, Cursor, Claude Code). Simple; no automation; the install command lives in the README.
- **Deeplink install.** Smithery and a few clients support `cursor://anysphere.cursor-deeplink/mcp/install?...` URLs that prefill the config. Reduces user error; works only on supporting clients.
- **CLI-driven add.** `claude mcp add` (Claude Code), `gh copilot mcp add` (Copilot CLI), `code --add-mcp` (VS Code). Best UX where supported.

Whichever the user picks, the install command **must** include the version pin. README boilerplate:

```bash
# Recommended — pinned version
npx -y @acme/acme-mcp@1.2.3

# Or with config block
{
  "mcpServers": {
    "acme": { "command": "npx", "args": ["-y", "@acme/acme-mcp@1.2.3"] }
  }
}
```

### Phase 2 — handshake

Once the server is running, the client opens the connection and sends `initialize`. The server responds with its capabilities, name, version, and `instructions`. From the user's side, the server "appears" — tools list, prompts list, resources list all populate.

Make the handshake fast (<500ms) and the `tools/list` lean (cross-link `client-compatibility.md` Pattern 9 — Claude Code captures the tool list once per session and ignores `tools/list_changed`). First impressions matter; a server that takes 5 seconds to surface tools loses users.

---

## Publisher picker — match archetype to channels

| Archetype | Primary channel | Secondary | Why |
|---|---|---|---|
| Personal / hobby OSS | Official Registry (`io.github.<you>/*`) + npm or PyPI | Smithery (analytics) | GitHub OAuth verification is the cheapest trust foundation. |
| Indie SaaS selling the MCP | Hosted URL + Smithery + Docker Catalog | Official Registry with `com.<domain>/*` (DNS-verified) | Smithery handles OAuth + analytics; Docker Catalog gets you signing; DNS namespace protects brand. |
| Enterprise internal MCP | Self-hosted Official Registry + private npm/PyPI | Cloudflare Access for OAuth | Internal registry with audit + IdP integration. **Never publish internal servers to public registries.** |
| Open-source community server | Docker MCP Catalog (signed images + SBOM) + Glama (quality score) + Official Registry | npm or PyPI | Docker signing is the strongest technical trust signal; Glama provides reproducible quality ranking. |
| Tool vendor (Stripe / Postmark class) | Official Registry with `com.brand/*` DNS-verified + Smithery + Docker Catalog + GitHub Registry | Hosted URL on owned infrastructure | Brand protection via DNS; broad distribution; signed images. **Claim your namespace before a squatter does.** |
| Agent platform consumer (not publishing) | Gateway (MetaMCP / Portkey / Cloudflare AI Gateway) | — | Don't publish. Aggregate upstream behind one controlled endpoint with observability. |

**Never rely solely on** unverified registries (MCP.so) or single-tenant secret-header services (Pica) for brand-sensitive work.

---

## Cross-references

- `transport-and-ops.md` — hosting platform constraints; what your server's deploy target can support.
- `auth-identity.md` — OAuth 2.1 + DCR + RFC 9728 PRM; the auth wiring expected by Smithery, Cloudflare, and the Official Registry.
- `security.md` — sanitization and untrusted-data wrapping that registries scan for.
- `threat-catalog.md` — named CVEs (CVE-2025-6514, postmark-mcp, Smithery path traversal) the version-pinning rule defends against.
- `exemplar-servers.md` — production examples of which channels each major vendor uses.
- `../../common/exemplars.md` — cross-surface vendor distribution comparison (CLIs alongside MCPs).
- `../decision-trees/production-readiness.md` — pre-deploy checklist that includes registry choice and version pin.
