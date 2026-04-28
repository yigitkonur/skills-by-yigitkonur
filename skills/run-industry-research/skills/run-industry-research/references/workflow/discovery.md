# Discovery Workflow

How to find the entities (products, projects, vendors, providers) that belong in the corpus — before any pack research starts.

Read this in **Phase 1** of the run-industry-research workflow.

## Why discovery is its own phase

Most "industry research" failures are discovery failures: the corpus researches the wrong set or misses category-defining entities. Discovery is not a single search — it's a structured pass that decomposes the topic, runs diverse queries, triages candidates, and tiers them before any deep research begins.

Skipping this phase leads to: missing the obvious leader nobody mentioned, including 5 dead projects, treating two competitors at different category tiers as comparable, or padding the list with adjacent solutions that don't actually compete.

## Phase 1 has TWO outputs

Discovery produces both:

1. **The entity list** — `_meta/discovered-entities.md` with every candidate tiered (core / secondary / discovered-only)
2. **The deep category understanding** — a 1-2 paragraph note (in `_meta/research-plan.md` or shown inline) summarizing what the vertical's buyers actually care about, captured BEFORE Phase 2 template authoring

The second output is what enables Phase 2 to write maximalist templates that match the vertical. Without it, templates default to generic and miss vertical-specific axes.

### The deep category pre-pass

Before locking the entity list, study the category itself. Answer these questions, capturing each in 1-2 sentences:

| Question | Why it matters for templates (Phase 2) |
|---|---|
| What axes do real buyers compare on? | Determines the cross-criterion list (each becomes a comparison template) |
| What pricing primitives are native here? (browser-hour, GB-second, per-API-call, per-seat, per-credit, per-action…) | Pricing template needs the right unit |
| What practitioner channels matter? (specific subreddits, HN, Discord servers, forums, trade pubs) | Audience template needs the right venues |
| What regulatory/compliance angles apply? (HIPAA, SOC2, GDPR, PCI, FERPA, jurisdictional rules…) | Security/compliance template needs the right regimes |
| What benchmark traditions exist? (public leaderboards, vendor-claimed-only, buyer-run pilots) | Benchmarks template needs the right reproducibility expectations |
| What does lock-in / exit-path look like? | Buyer-fit template needs the right migration scenarios |
| What recent shifts has the category seen? (last 12 months) | Overview template needs the right framing |

Capture the answers as a "category-understanding note" alongside the discovered-entities list. This note is the input to Phase 2.

## Sub-question decomposition

Before searching, decompose the topic into 3-5 orthogonal sub-questions that surface different candidate sets. Single broad searches return the same top 10 results everyone has already seen.

### How to decompose

Pick sub-questions that intersect different dimensions:

| Dimension | Example sub-question |
|---|---|
| **Tier** | Who are the incumbents vs. challengers vs. open-source alternatives? |
| **Form factor** | Which run as cloud SaaS vs. self-hosted vs. embedded library? |
| **Target user** | Which serve enterprise vs. mid-market vs. solo developers? |
| **Geography** | Which dominate the EU/Asia markets that are missing from US-centric lists? |
| **Recency** | Which launched in the last 12 months and don't appear in older comparisons? |
| **Maturity** | Which are production-grade vs. early access vs. waitlist-gated? |
| **Adjacency** | Which solve the same problem with a fundamentally different approach? |

### Example: cloud browser category

Sub-questions used in the worked-example corpus:

1. Which AI-native cloud browser platforms exist as commercial SaaS in 2025?
2. Which incumbent traditional browser-automation services have repositioned for AI agents?
3. Which open-source projects compete in the same space (with optional hosted offerings)?
4. Which adjacent categories overlap (computer-use platforms, agent runtimes, scraping APIs)?
5. Which platforms are gated/waitlist-only and might be over-counted in marketing?

Each sub-question surfaces a different candidate cluster. Five sub-questions returned ~25 distinct candidates; tiered down to 12 `core`.

## Search execution

### With research-powerpack MCP (preferred)

Use `mcp__research-powerpack__start-research` with a research brief that names the sub-questions. The MCP runs multi-source discovery and returns a consolidated candidate list.

```
mcp__research-powerpack__start-research:
  brief: |
    Discover entities in the [topic] category. Decompose into these sub-questions:
    1. [sub-question 1]
    2. [sub-question 2]
    ...
    Return a candidate list with: name, vendor/maintainer, URL, one-line description,
    apparent tier (incumbent / challenger / niche / adjacent), and the sub-question(s)
    that surfaced it.
```

For targeted follow-ups on specific candidates, use `mcp__research-powerpack__web-search`:

```
mcp__research-powerpack__web-search: "[candidate name] alternatives 2025"
mcp__research-powerpack__web-search: "[candidate name] vs [known competitor]"
```

For extracting candidate lists from category review pages:

```
mcp__research-powerpack__scrape-links: "https://example-review-site.com/[category]"
```

### Fallback path (no MCP)

Dispatch parallel Explore subagents — one per sub-question — to run `WebSearch` rounds and report back a candidate list. See `references/agents/research-powerpack-and-explore.md` for the parallel-Explore dispatch recipe.

If even Explore is unavailable, run sequential `WebSearch` queries against each sub-question.

## Search keyword templates

Use these keyword shapes when running web searches per sub-question:

| Goal | Keyword shape |
|---|---|
| Find category leaders | `[category name] best 2025`, `[category name] top alternatives`, `[category name] comparison` |
| Find challengers | `[category name] alternatives to [incumbent]`, `[incumbent] vs`, `switched from [incumbent]` |
| Find open-source | `[category name] open source`, `[category name] github`, `self-hosted [category name]` |
| Find recent entrants | `[category name] launched 2024`, `[category name] product hunt`, `Show HN [category]` |
| Find adjacent | `[problem statement] tools`, `[underlying technology] platforms` |
| Find practitioner mentions | `reddit [category]`, `hackernews [category] discussion` |
| Find geographic outliers | `[category name] europe`, `[category name] asia 2025` |

Each search should produce candidates the previous search did not. If three searches in a row return the same names, you're saturated; move on.

## Candidate triage

For each candidate, capture:

```markdown
| Candidate | URL | One-line | Surfaced by | Status | Tier candidate |
|---|---|---|---|---|---|
| [Name] | [Vendor URL] | [What it is in one line] | [Sub-question #] | active / dead / waitlist / acquired | core / secondary / discovered-only |
```

### Status check (≤1 minute per candidate)

- **Active** — last commit/release in the past 6 months OR active marketing/sales motion
- **Dead** — last commit >18 months, abandoned domain, founders moved on
- **Waitlist** — gated access, no public docs, no public pricing
- **Acquired** — folded into a parent product; verify whether the parent or the original brand is still the canonical entity

### Tier classification

| Tier | Criteria | Output in corpus |
|---|---|---|
| **Core** | Directly comparable, high buyer relevance, sources sufficient for full pack, likely decision candidate | Full evidence pack + standalone profile page |
| **Secondary** | Relevant but adjacent, early-stage, region-specific, or source-limited | Compact evidence pack (subset of subfolders) OR profile-only |
| **Discovered-only** | Surfaced in searches but not worth full treatment | Single row in `_meta/discovered-entities.md` |

**Promotion rule:** a `secondary` entity that turns out to change the rankings, the pricing economics, the adoption interpretation, or the category boundaries during Phase 4-5 should be promoted to `core`.

## De-duplication

Two common pitfalls:

| Pitfall | Example | Fix |
|---|---|---|
| Same product, different names | `Browser-Use` (the open-source library) appears under "tools", "frameworks", and "agent SDKs" | Pick the canonical name from the project's own README; alias the others in the discovered-entities row |
| Sub-product confusion | `Cloudflare Browser Run` is a sub-feature of `Cloudflare Workers` | Decide whether to treat as standalone (its own entity) or as a feature of the parent (one entity) — usually based on whether buyers evaluate it independently |
| Brand reorganization | `Browse.dev` was renamed `Meteor` mid-research | Use the current name in the slug; mention the old name in `00-overview/` |
| Acquisition swallow | Original brand vs. acquirer brand | Use whichever has the active product page; cross-reference the other |

When in doubt, check whether buyers evaluating the category would compare the entities side-by-side. If yes, separate. If no, consolidate.

## Discovered-entities file format

The `_meta/discovered-entities.md` file is the corpus's canonical entity catalog. It must persist beyond discovery — Phase 4-5 agents read it to understand scope.

Required columns:

```markdown
| Slug | Name | Vendor | URL | Tier | Status | Surfaced by | Notes |
|---|---|---|---|---|---|---|---|
| airtop | Airtop | Airtop AI | https://airtop.ai | core | active | Sub-Q1, Sub-Q2 | YC-backed; AI-native browser |
| browser-use | Browser-Use | open source | https://github.com/browser-use/browser-use | discovered-only | active | Sub-Q3 | Library, not a hosted service |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

Plus narrative sections:

- **In-scope rationale** — one paragraph explaining what made the cut and why
- **Out-of-scope** — adjacent products that almost made it, with the boundary rule used
- **Watch list** — early-stage entities that may promote in future passes

## Discovery completeness check

Before locking the discovery list and starting Phase 2 (template authoring):

- [ ] Each sub-question surfaced at least 3 distinct candidates
- [ ] At least one candidate came from a non-incumbent search angle (open-source, geographic, recent)
- [ ] Every candidate has a status (active/dead/waitlist/acquired) with a source
- [ ] Every candidate has a tier (core/secondary/discovered-only) with a one-line rationale
- [ ] No two entities are duplicates under different names
- [ ] Any "obvious" candidate that didn't surface is explicitly noted (and a reason given)
- [ ] **Deep category pre-pass complete** — all 7 questions in the table above are answered; category-understanding note is captured
- [ ] Both outputs (entity list AND category-understanding note) are ready to feed Phase 2 template authoring

## Common discovery failures

| Failure | Symptom | Recovery |
|---|---|---|
| Echo chamber | Top 10 lists keep returning the same 5 names | Add geography, form-factor, or open-source sub-questions |
| Marketing-only signal | Only vendor pages found, no practitioner discussion | Add Reddit/HN search, accept that practitioner sparsity is a finding |
| Dead-project trap | Candidate is included but hasn't shipped in 2 years | Status check before tier assignment |
| Adjacent overload | List is 40 entities including 25 adjacent solutions | Tighten the category definition; move adjacents to `_meta/adjacent-categories.md` |
| Single-tier blindness | Only commercial SaaS discovered, missing open-source alternatives | Add an explicit open-source sub-question |
| Premature deep dive | Researching one candidate in depth before the list is complete | Tier first, research second |

## Worked example reference

For a complete discovery walkthrough on a real category, see `references/workflow/worked-example-cloud-browsers.md`. The cloud-browsers corpus surfaced 25 candidates across 5 sub-questions, tiered to 12 `core` + 8 `secondary` + 5 `discovered-only`, before any pack research started.
