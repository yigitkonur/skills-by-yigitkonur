# Internet Researcher Agent Suite

Five evidence-grounded research agents for developers and Claude agents who are stuck on a technical problem with a public solution.

## Why five, not twelve

A first cut of this suite shipped 12 agents — too many. The user pushed back; I dogfooded the generic agent against r/ClaudeAI, r/cursor, r/ChatGPTCoding, Hacker News, and dev blogs (2024-2026) to find where coding-agent users **actually** get stuck and ask for internet research. The recurring pain clusters were:

1. **Outdated docs / hallucinated APIs / version-pinned syntax drift** — by far the largest cluster. Tailwind 3→4, Svelte 4→5, React 18→19, SDK renames; ≈19.7% hallucinated-package rate cited in academic literature; an entire MCP-server market (Context7, Ref, Grounded Docs, llms.txt readers) exists because of this one problem.
2. **Stuck on a specific error or post-update regression.** Either an error code with a canonical public fix, or "claude-code 1.0.89 got worse" / vendor-confirmed degradation.
3. **Tech adoption decisions with cost attached.** Tech-choice and cost are inseparable in practice.
4. **"How do shipping apps actually do this"** — reverse-engineering source maps, userscript catalogs, extension stores. The Instagram blob-URL extraction pattern, for example.

Edge needs (license/ToS, CVE/security, RFC spec lookup, incident post-mortems, OSS-health-only audits) are real but rare for a coding agent. They got dropped from this suite — re-add them only if you start hitting them weekly.

## The five agents

| Agent | Color | Use it if |
|---|---|---|
| `internet-researcher-generic` | blue | You're stuck on a non-obvious dev problem and want public-web evidence before guessing again. |
| `internet-researcher-tech-choice` | cyan | You're choosing between 2-4 named libraries, frameworks, runtimes, or vendors. Includes cost. |
| `internet-researcher-debug-stuck` | red | You have a specific error code, signature, or update-induced regression and prior guesses failed. |
| `internet-researcher-api-docs` | blue | You suspect outdated docs, a hallucinated API or package, or version-mismatched syntax. |
| `internet-researcher-shipping-pattern` | magenta | You need real production examples — userscripts, extensions, leaked source, OSS code that ships X. |

All five descriptions are ≤20 words and follow the same "Use this agent if … See body for triggers" shape so routing decisions are uniform.

## Shared discipline

Every agent in the suite enforces the same conventions so they feel like one tool:

### Evidence trail

`.agent-docs/<context-slug>/` with numeric-prefixed files in scan order. `01-intake.md`, `02-search-plan.md`, `03-recon-hits.md`, `04-scrape-<source>.md` (one per high-value source), `05-synthesis.md`, `06-<specialty-output>.md` (recommendation, fix-recipe, etc.). Specialist agents add specialty files (`04-registry.md`, `04-impl-<source>.md`, `04-pricing-pages.md`, etc.).

### `.gitignore` safety

On first write to `.agent-docs/`, every agent runs:

```sh
grep -qxF '.agent-docs/' .gitignore 2>/dev/null || printf '\n.agent-docs/\n' >> .gitignore
```

The folder is scratchpad. Never committed unless explicitly asked.

### Budgets (ceilings, not targets)

| Resource | Max | Typical |
|---|---|---|
| Tool calls | 500 | <100 |
| Search calls | 1000 | <30 |
| URL visits / scrapes | 250 | <20 |
| Search rounds | 8 | 2-4 |

The maxes anchor expectations ("this is real research, take the budget you need") without inviting padding ("typical is much less, stop early when confidence is high").

### Search thinking — taught, not recipe-baked

The earlier draft of this suite hardcoded `site:reddit.com/r/<community>/comments` style query templates. That was wrong — it teaches agents to fill in a recipe instead of to think. The shipping suite teaches a META instead:

> Before every search call, decide which **source class** holds the highest-quality answer for this exact question, and re-pose the query to retrieve THAT class. Pack 5-15 keywords per recon call, each targeting a different class.

The source classes the agents mine (uniform across all five):

1. **Vendor authoritative documents** — official docs, changelogs, release notes, RFCs, advisories.
2. **Project-internal trackers** — maintainer issues, PRs, commits.
3. **Practitioner forums** — Reddit, HN, dev blogs from named teams. Always scraped raw to preserve vote weighting and per-comment attribution.
4. **Registry metadata** — npm/PyPI/crates timelines, repo cadence, download trends.
5. **Vendor status pages + community megathreads** — real-time regression confirmation. The fast path for "it worked yesterday".
6. **Source-of-truth artifacts** — OSS code, leaked sourcemaps, extension source dumps, sourcemaps from production webapps.

Each agent's body has one illustrative bad-vs-good rewrite — a single example — not a four-row recipe table.

### Tool selection (canonical ladder)

- `mcp__research-powerpack__smart-web-search` — ranked + classified results into context. Pack 15-50 keywords across distinct source classes per call.
- `mcp__research-powerpack__raw-web-search` — output to file or to a subagent; community-forum permalink discovery.
- `mcp__research-powerpack__smart-scrape-links` — docs / blogs with extraction schema. ≤5 URLs per call, ≤7 facets.
- `mcp__research-powerpack__raw-scrape-links` — community-forum threads (always raw), unknown shapes, full markdown. ≤5 per call.
- `mcp__research-powerpack__start-research` — long autonomous session with stable goal.
- `WebFetch` — single-URL fallback.

### Quote discipline

Every numeric, versioned, priced, or behavior claim cites a verbatim quote from a scraped source with access date. If you cannot quote it, mark it as inference and flag the gap.

### Output contract

The final reply from every agent has the same shape:

1. Executive summary — one paragraph.
2. Confidence — high / medium / low with reason.
3. Top findings — 3-5 bullets, each with verbatim quote + URL.
4. Contradictions — call out disagreements with per-source attribution.
5. Actionable next step — concrete patch / config / command. Never "consider X".
6. Evidence trail — pointer to `.agent-docs/<context-slug>/` with file index.
7. Source ledger — table at the bottom: URL · access date · source class · key quote.

## How to invoke

```
Agent({
  subagent_type: "internet-researcher-debug-stuck",
  description: "Hunt TCC -1719 fix",
  prompt: "Symptom: `osascript is not allowed assistive access. (-1719)` on macOS 15. We've enabled Accessibility for the app but the error persists when osascript runs from a shell launched by an agent. Already tried: re-granting Accessibility, reboot. Find the canonical fix. Freshness: 2025-2026."
})
```

## What dropped from v1 and why

Removed: `api-semantics` → renamed to `api-docs` (broader scope: existence + version + syntax, not just behavior). `production-pattern` → renamed to `shipping-pattern` (sharper trigger). `vendor-cost` → folded into `tech-choice` (cost is always part of the choice). `migration-path` → folded into `generic` (rare specialist need; the framework changelog-reading discipline lives in `api-docs`). `oss-health`, `security-cve`, `spec-rfc`, `incident-postmortem`, `license-and-tos` → all dropped as too-niche for daily coding-agent use; re-add only when the need actually shows up week over week.

## Empathy

The original 12-agent draft was over-engineered out of imagination. The shipping 5-agent suite is grounded in actual posts from people using Claude Code, Cursor, Aider, and Cline this year — the patterns they hit, the questions they ask, the time they burn. Less is more here.
