---
name: run-github-scout
description: Use skill if you are discovering GitHub repos, shortlisting candidates for a concrete need, or comparing OSS projects with adaptive search and repo evidence.
version: 1.0.0
---

# GitHub Repo Scout

Adaptive GitHub repository **discovery and shortlisting** for a concrete
user need. Default deliverable is a markdown shortlist in conversation
backed by repo evidence. Deeper comparison, feature matrices, and HTML
export are optional end-stage branches — never the default.

This skill is **lean by design**. Opposite shape to corpus research: no
folder tree, no wave dispatch, no MAX-N ceilings, no template authoring.

## When to use this skill

Trigger on phrasings like:

- *"find the best open-source X for Y"* / *"find repos that do …"*
- *"shortlist GitHub projects for …"* / *"what repos fit this stack/use case?"*
- *"alternatives to `owner/repo` on GitHub"* / *"similar repos to …"*
- *"compare GitHub repos for …"* / *"recommend a library that …"*
- *"GitHub-hosted tools/SDKs/CLIs for …"* / *"OSS for …"*
- *"verify this repo is what I think it is"* (verify-first scout)

### Do NOT use this skill when

- The question is a **single technical decision or version/API/CVE/pricing
  lookup** with no repo-discovery focus → use `run-research`.
- The user wants a **multi-file market/category corpus over 5+ entities**
  with per-entity packs and source ledgers → use `run-industry-research`
  (or `run-corpus-research` in this checkout). Repos can still be the
  entities — the discriminator is corpus shape, not the subject.
- The candidates are **not on GitHub** (closed-source SaaS, marketplace
  apps, hosted-only products) → use `run-research` or
  `run-industry-research`.
- The task is **codebase-local** (read this repo, fix this bug, plan
  these issues) → not this skill. For Issues planning specifically use
  `run-issue-tree`.

## Five rules that prevent most derailments

These five upstream-discipline rules catch the bulk of failures. Read
`references/discipline.md` first if any are unfamiliar.

| # | Rule | Why |
|---|---|---|
| 1 | **Verify-first** when the user names a thing | One `gh search repos 'NAME' --limit 5` call confirms category before alternatives. Skipping costs 3-4 wasted searches. |
| 2 | **Pick the star threshold by ecosystem maturity**, not reflex | Young niches (AI agents, MCP) need none; mature ecosystems need `stars:>500`+. Wrong threshold = wrong result set. |
| 3 | **Avoid `topic:`, bare multi-word `OR`, `in:readme` in first-pass** | All three are noise-prone. Use them only after classify proves they help. |
| 4 | **Classify before you deepen** | Typed Relevant / Maybe / Off-topic table is the gate before any README read. Skipping forces guesses. |
| 5 | **Hard ceiling: 5 repos for deep evaluation** | Going to 6+ requires inline justification at the moment of promotion. |

## Prerequisites and pinned defaults

| Item | Default |
|---|---|
| Auth check | Run `gh auth status` before non-trivial scouts. Prefer authenticated `GH_TOKEN` / `GITHUB_TOKEN` for higher limits. |
| Search help | `gh search repos --help` is the source of supported JSON fields and flags. |
| Rate-limit check | Before large searches or deep dives: `gh api rate_limit --jq '.resources | {core, search, graphql}'`. |
| Query limits | First pass: 3-6 angles. Refinement: 1-4 queries. Deep dive: top 3-5 repos only. Default `--limit 20`. |

## GitHub tool contract

- Use `gh search repos` for discovery.
- Use `gh api repos/OWNER/REPO...` only for shortlisted metadata.
- Use `gh api graphql` only for top-N deep evidence when REST/README/search are insufficient.
- Use direct `curl` only when `gh` is unavailable.
- Use web/MCP tools (or `run-research`) for naming/landscape augmentation only; final repo truth comes from GitHub.
- `run-issue-tree` also uses `gh`, but its intent is GitHub Issue planning/execution, not repo discovery.

Rate-limit rules:
- Search has its own bucket; never fire unbounded waves.
- Prefer fewer diverse queries over paraphrase spam.
- If limits are low, stop at metadata/README evidence and disclose the limit instead of pushing through.
- Verify current GitHub behavior against official docs before hardcoding numbers: https://docs.github.com/rest/rate-limit (accessed 2026-05-09).

## Bundled scripts

Resolve scripts relative to this skill directory. They are conveniences,
not a replacement for fit judgment.

| Script | Use when |
|---|---|
| `scripts/gh-search.sh` | Compact, repeatable TSV capture from `gh search repos`. See `scripts/gh-search.md`. |
| `scripts/score-repos.sh` | Cheap signal sort over captured rows. Metadata only — never semantic fit. See `scripts/score-repos.md`. |

## Default stance

- **Shortlist first.** Default deliverable is an in-conversation markdown shortlist.
- **Search small, then refine.** Start with 3-6 broad angles, then run at most one refinement round unless results are still materially weak.
- **Filter before expanding.** Read descriptions, names, topics, stars, and recent activity before inventing more searches.
- **`run-research` is optional, not required.** Invoke it for the augmented branch when GitHub-only search is thin and naming/landscape discovery would help. Built-in `WebSearch` is also sufficient for light naming clues.
- **Keep deep work top-N only.** Feature matrices, code reads, and HTML export happen only after a useful shortlist exists.

## Capability check — pick the leanest path

| Path | Use when | Default tools |
|---|---|---|
| **GitHub-only** | Problem clearly named, category is repo-centric, GitHub search already surfaces relevant candidates. | `gh search repos`, GitHub web/API, repo READMEs |
| **Augmented** | Naming is fuzzy, landscape is broad, category labels unclear, or first-pass GitHub search is thin/noisy. | GitHub search + `run-research` (preferred) or built-in `WebSearch` (lighter fallback) |

Rules:
- If `run-research` and `WebSearch` are both unavailable, continue on the GitHub-only path.
- If web research is available, use it to discover better names/categories/curated alternatives, then map back to GitHub repos and filter there.
- Never ask the user to install a research tool just to run this skill.

## Default workflow

### 0. Verify-first when the user named a thing

If the user mentioned a specific repo, project, or tool by name, the
**first** call verifies what that thing is — not alternatives. One call:
`gh search repos 'NAME' --limit 5 --sort=stars`. Confirm category before
proceeding.

If the named thing is unrelated to what the user is asking for, surface
the mismatch back to the user before continuing. See
`references/discipline.md` §2.

Skip this step only when the user named no specific thing.

### 1. Interpret the request

Extract the search contract before touching GitHub:

- core problem or job to be done
- must-haves
- exclusions
- ecosystem or language constraints
- maturity expectations (production-ready, active, permissive license, etc.)
- known examples or anti-examples (if named, see Step 0)

Ask clarifying questions only when the answer would materially change the
search. If the user's request already pins use case and constraints, skip
questions entirely.

### 2. Choose the search path

- Use the **GitHub-only** path by default.
- Switch to **Augmented** if you hit ambiguous naming, broad category noise, or community terminology problems.
- Read `references/web-augment.md` only if you need the augmented branch — it explains when and how to invoke `run-research` for naming and landscape discovery.

### 3. Run a small first pass

Start with **3-6 search angles**, not a giant hypothesis list.

Minimum useful angle set:
1. direct phrasing of the user's need
2. broader category phrasing
3. known examples or well-known alternatives
4. one unexpected-naming branch

Add a fifth or sixth angle only when a hard constraint matters (language,
deployment model, self-hosted, etc.).

**Pick a star threshold per ecosystem maturity** before launching. Young
niches (AI agents, MCP, agent orchestrators) typically need no threshold
— quality repos exist below 100⭐. Mature ecosystems (web frameworks,
classic CLIs) need `stars:>500` to filter noise. See
`references/discipline.md` §3 for the matrix.

**Avoid `topic:` in first-pass discovery** — it returns spam. **Avoid
bare multi-word `OR` queries** — they parse ambiguously. See
`references/discipline.md` §4 and §5.

Use short, broad queries first. Prefer `scripts/gh-search.sh` for common
capture; read `references/search.md`, `references/gh-syntax.md`, and
`references/gh-output.md` if you need exact search patterns.

### 4. Filter internally before searching again

Treat the first pass as raw material, not the final answer.

**Produce a classify table before any further work** — this is the gate
that prevents drift into deep reading of the wrong candidates:

```markdown
| Repo | Class | Reason | Signals |
|---|---|---|---|
| owner/repo1 | relevant | Direct match for X | 4.2k⭐, pushed 2026-04, MIT |
| owner/repo2 | maybe | Adjacent — wrapper, not engine | 800⭐, active |
| owner/repo3 | off-topic | Tutorial, not implementation | — |
```

Filter using the cheapest signals first:

- repo name
- description
- topics
- stars
- recent activity / pushed date
- archived status
- license presence

Read README intros only for borderline or high-potential candidates.
Harvest better terms from relevant and maybe-relevant repos before
expanding search.

Use `references/dedup-and-rank.md` for the four-stage gate procedure. The
classify table is mandatory; deepening without it is a discipline failure
(see `references/discipline.md` §8). Use `scripts/score-repos.sh` only as
a cheap metadata sort within the classify pass; do not let it override
user-fit evidence. Read `references/quality-gates.md` after first-pass
classification to decide whether to stop, refine once, augment, or
deepen.

### 5. Run one refinement pass

Refine only after the first classification pass tells you what is missing.

Good reasons to refine:

- too few relevant repos
- too much off-topic noise
- naming mismatch between user language and repo language
- a promising subcategory emerged from candidate descriptions or topics

Refinement rules:

- 1-4 better queries, not a whole new search machine
- expand only the gaps you observed
- stop when new searches mostly repeat known repos

Use `references/search-examples.md` for worked examples of first-pass +
refinement loops, including derailment-recovery patterns.

### 6. Produce the default output

Default output is **markdown in the conversation**, not files.

Deliver:
1. a one-paragraph recommendation or framing note
2. a compact table using the stable row schema
3. a grouped shortlist (`Best fits`, `Worth a look`, `Ruled out / why`)
4. evidence packs for `Best fits`
5. notable gaps or uncertainty

Stable row schema:

```markdown
| Repo | Fit | Evidence | Signals | Caveat / unknown |
|---|---|---|---|---|
| [owner/repo](https://github.com/owner/repo) | Strong fit for X | README says Y; topics include Z | stars, pushed, license, activity | Not verified: A |
```

Require repo links in the table unless a URL is unavailable.

For each `Best fits` repo, include a lightweight evidence pack:
- why it matches the user's must-haves
- evidence source used: description, topics, README, API, or code
- cheap quality signals checked
- caveats and unverified claims
- last checked date when external state matters

If the user is satisfied with the markdown shortlist, **stop there**.

### 7. Offer optional deepen

Only deepen after the markdown shortlist is useful. Check
`references/quality-gates.md` before deepening; most scouts should stop
at the markdown shortlist.

Each branch consumes only the final shortlisted dataset; do not restart
discovery.

- **light deeper comparison** — top 3-5 side-by-side on fit, evidence, signals, caveats
- **code-level evaluation** — top few repos only; verify must-have features, README/onboarding, tests/CI, maturity risks
- **feature matrix** — explicit capability coverage table with evidence notes or `unknown`
- **HTML/export** — persistent report from the stable markdown shortlist

**Hard ceiling: 5 repos for deep evaluation.** Going to 6+ requires an
explicit inline justification at the moment the deepening starts — e.g.,
"promoting `owner/repo6` because it surfaced a decision-flipping signal
during classify." Without that justification, stop at 5. See
`references/discipline.md` §10.

If the user asks for files, create them from the **final shortlisted
dataset only**. Do not create `.githubresearch/` or other artifact trees
unless the user wants export or report output.

HTML export data contract for `references/report-template.html`:
- Generate HTML only after the markdown shortlist is stable.
- Fill `[TOPIC]`, `[DATE]`, `[ROW_COUNT]`, `[RECOMMENDATION]`, `[SEARCH_PATH_NOTE]`, `[GAPS_NOTE]`.
- Each row must provide repo URL/name, fit, evidence, signals, caveat/unknown.
- Grouped notes come from the same `Best fits`, `Worth a look`, `Ruled out / why` groups.

## Default evaluation rules

Use light, fast, rate-limit-aware signals by default:

- topic / description / README match to the user's need
- stars
- recent activity / pushed date
- rough maintainer or commit activity
- archived or disabled status
- license presence
- README clarity
- tests or CI presence when cheap to detect

Do **not** default to:

- author follower scoring
- org prestige heuristics
- "AI-wave-only author" style filters
- a giant multi-metric rubric
- mandatory per-repo GraphQL or REST drills across the whole candidate set

If the user wants more confidence, deepen only on the top few repos. Read:

- `references/evaluate.md` for the light default path and deepen triggers
- `references/evaluate-rest.md` for cheap repo signals
- `references/evaluate-graphql.md` for optional single-repo deep evidence
- `references/evaluate-code.md` for optional code-level checks

## Orchestration rules

Default execution model: **hybrid lean**.

- The main agent owns intent parsing, search strategy, filtering, and synthesis.
- Batch or parallelize queries when helpful, but keep the reasoning central.
- Use subagents only for: very large landscapes; explicit deep-dive requests; optional feature-matrix generation; top-N code-level review.
- When web augmentation is the gap and a subagent is dispatched for it, the subagent's brief embeds the `run-research` skill discipline (so the subagent uses the 5-tool toolkit correctly without re-deriving it). See `references/subagent-prompts.md` for the integration block.

If you dispatch help, read `references/subagent-prompts.md`. Subagents
gather evidence; the main agent still writes the final shortlist or
comparison.

## Reference routing

Load only the branch you need. References are flat on disk and grouped here by decision point.

### Search / discovery

| File | Read when |
|---|---|
| `references/discipline.md` | First use of the skill, and any time results feel off-shape. The mental model + noise discipline. |
| `references/search.md` | Default starting point for first-pass plus refinement search. |
| `references/search-examples.md` | You need examples of good first-pass angles, refinement pivots, and derailment-recovery patterns. |
| `references/gh-syntax.md` | You need valid `gh search repos` qualifiers, OR rules, or threshold guidance. |
| `references/gh-output.md` | You want token-efficient `gh` output or markdown-ready capture. |
| `references/web-augment.md` | GitHub-only search is thin/noisy, or naming is fuzzy and web augmentation (via `run-research` or `WebSearch`) would help. |

### Evaluation / deepening

| File | Read when |
|---|---|
| `references/evaluate.md` | You are checking repo quality signals or deciding whether to deepen. |
| `references/evaluate-rest.md` | You need cheap repo signals beyond the initial search output. |
| `references/evaluate-graphql.md` | You need a single-repo deep evidence query for a top candidate. |
| `references/evaluate-code.md` | You need README, file-tree, or source evidence for the top few repos. |

### Orchestration

| File | Read when |
|---|---|
| `references/subagent-prompts.md` | The landscape is large, or the user explicitly wants deeper comparison work delegated. Includes the `run-research` integration block for web-augmentation subagents. |

### Output / export

| File | Read when |
|---|---|
| `references/dedup-and-rank.md` | You are turning raw candidates into a grouped shortlist. The four-stage gate. |
| `references/report-template.html` | The user explicitly wants an HTML export after the shortlist is stable. |

### Stop / refine gates

| File | Read when |
|---|---|
| `references/quality-gates.md` | Decide whether to stop, refine once, augment, or deepen. |

## Guardrails

- Do not treat `run-research` or web augmentation as mandatory.
- Do not default to `.githubresearch/` or any persistent artifact tree.
- Do not pad searches with 20 hypotheses, 100-call ceilings, or wave theater.
- Do not escalate to deep evaluation before you have produced the classify table.
- Do not read whole READMEs for every candidate; read intros or targeted sections for the top few, and skip the badge zone (see `references/evaluate-code.md`).
- Do not let optional deep-dive work become the default path by accident.
- Stop when the shortlist is good enough and new searches mostly repeat the same field.
- Be explicit about gaps, uncertainty, and what you did **not** verify.

## Common derailments (read once)

The five anti-patterns this skill catches most often:

1. **Skipping verify-first** when the user names a thing (cost: 3-4 wasted searches before the mismatch is noticed).
2. **First-pass `topic:` discovery** that returns 100k-star repos with weak relevance.
3. **Bare multi-word `OR` queries** that parse ambiguously and return broad noise.
4. **Skipping the classify table** between first-pass and deepen (forces guessing the top 5).
5. **Deepening 7-10 READMEs** instead of stopping at 5.

If the session feels off-shape, check this list. The fix is almost always
upstream — a missed verify, a noisy qualifier, an unclassified candidate
set. See `references/discipline.md` for full coverage.
