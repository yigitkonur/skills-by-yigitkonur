---
name: run-github-scout
description: Use skill if you are finding, shortlisting, or comparing GitHub repositories for a concrete need through adaptive discovery and repo evidence.
version: 1.0.0
---

# GitHub Repo Scout

Find and shortlist the best-fit GitHub repos for a concrete user need. Default to adaptive discovery, internal relevance filtering, and a markdown shortlist in the conversation. Deeper comparison, feature matrices, and HTML export are optional end-stage branches — never the default.

This skill is **lean by design**. The shape is opposite to corpus research: no folder tree, no wave dispatch, no MAX-N ceilings, no template authoring. The default deliverable is a few markdown sections in chat.

## Prerequisites and pinned defaults

| Item | Default |
|---|---|
| Auth check | Run `gh auth status` before non-trivial scouts. Prefer authenticated `GH_TOKEN` or `GITHUB_TOKEN` for higher limits and stable API behavior. |
| Search help | Treat `gh search repos --help` as the source of supported JSON fields and flags. |
| Rate-limit check | Before large searches or deep dives, run `gh api rate_limit --jq '.resources | {core, search, graphql}'`. |
| Query limits | Default query limit: 20. First pass: 3-6 angles. Refinement: 1-4 queries. Deep dive: top 3-5 repos only. |

## GitHub tool contract

- Use `gh search repos` for discovery.
- Use `gh api repos/OWNER/REPO...` only for shortlisted metadata.
- Use `gh api graphql` only for top-N deep evidence when REST, README, and search signals are insufficient.
- Use direct `curl` only when `gh` is unavailable.
- Use web/MCP tools for naming or landscape augmentation only; final repo truth comes from GitHub.
- `run-issue-tree` also uses `gh`, but its intent is GitHub Issue planning/execution, not repo discovery.

Rate-limit rules:
- Search has its own rate bucket; do not fire unbounded search waves.
- Prefer fewer diverse queries over paraphrase spam.
- Check remaining `search`, `core`, and `graphql` limits before GraphQL or deep API work.
- If limits are low, stop at metadata/README evidence and disclose the limit instead of pushing through.
- Verify current GitHub behavior against official rate-limit docs before hardcoding exact numbers: https://docs.github.com/rest/rate-limit (accessed 2026-05-09).

## Bundled scripts

Resolve scripts relative to this skill directory. They are conveniences, not a replacement for fit judgment.

| Script | Use when |
|---|---|
| `scripts/gh-search.sh` | You need compact, repeatable TSV capture from `gh search repos`. See `scripts/gh-search.md`. |
| `scripts/score-repos.sh` | You need a cheap signal sort from captured rows. It scores metadata only, never semantic fit. See `scripts/score-repos.md`. |

## Trigger boundary

**Use when:** "find the best open-source X for Y", "what GitHub repos fit this use case?", "compare repos for this stack/problem", "I need a shortlist of tools like this", or "find similar repos on GitHub".

**Redirect when:**

- The task is broad technical research without a repo-discovery focus → use `run-research`.
- The user wants broad market/category/vendor corpus work, especially 5+ entities or non-GitHub product comparisons → use `run-industry-research` when available; in this checkout, the equivalent corpus skill is `run-corpus-research`.
- The question is codebase-local or about a non-GitHub product → not this skill.

`run-github-scout` and `run-research` differ in subject: this skill is GitHub-centric and discovery-oriented; `run-research` is open-web and decision-oriented. `run-github-scout` and `run-industry-research`/`run-corpus-research` differ in shape: this skill produces a shortlist in conversation; corpus research produces a multi-file evidence tree. Some tasks (e.g., "research 8 GitHub-hosted SaaS-style projects with deep multi-axis comparisons and source ledgers") warrant a corpus skill instead even though the entities are repos.

## Default stance

- **Shortlist first.** The default deliverable is an in-conversation markdown shortlist.
- **Search small, then refine.** Start with 3-6 broad angles, then run at most one refinement round unless results are still materially weak.
- **Filter before expanding.** Read descriptions, names, topics, stars, and recent activity before inventing more searches.
- **`run-research` is optional, not required.** Invoke it for the augmented branch when GitHub-only search is thin and naming or landscape discovery would help. Built-in `WebSearch` is also sufficient for light naming clues.
- **Keep deep work top-N only.** Feature matrices, code reads, and HTML export happen only after a useful shortlist exists.

## Capability check

Choose the leanest path that can still answer the request.

| Path | Use when | Default tools |
|---|---|---|
| **GitHub-only** | The problem is clearly named, the category is repo-centric, or GitHub search already surfaces relevant candidates. | `gh search repos`, GitHub web/API, repo READMEs |
| **Augmented** | Naming is fuzzy, the landscape is broad, category labels are unclear, or first-pass GitHub search is thin/noisy. | GitHub search plus `run-research` (preferred for disciplined web augmentation) or built-in `WebSearch` (lighter fallback) |

Rules:
- If `run-research` and `WebSearch` are both unavailable, continue on the GitHub-only path.
- If web research is available, use it to discover better names, categories, and community-curated alternatives, then map those back to GitHub repos and filter there.
- Do not ask the user to install a research tool just to run this skill.

## Default workflow

### 1. Interpret the request

Extract the search contract before touching GitHub:
- core problem or job to be done
- must-haves
- exclusions
- ecosystem or language constraints
- maturity expectations (production-ready, active, permissive license, etc.)
- known examples or anti-examples

Ask clarifying questions only when the answer would materially change the search. If the user's request already pins the use case and constraints, skip questions entirely.

### 2. Choose the search path

- Use the **GitHub-only** path by default.
- Switch to the **Augmented** path if you hit ambiguous naming, broad category noise, or community terminology problems.
- Read `references/web-augment.md` only if you need the augmented branch — it explains when and how to invoke `run-research` for naming and landscape discovery.

### 3. Run a small first pass

Start with **3-6 search angles**, not a giant hypothesis list.

Minimum useful angle set:
1. direct phrasing of the user's need
2. broader category phrasing
3. known examples or well-known alternatives
4. one unexpected-naming branch

Add a fifth or sixth angle only when a hard constraint matters (language, deployment model, self-hosted, etc.).

Use short, broad queries first. Prefer `scripts/gh-search.sh` for common capture; read `references/search.md`, `references/gh-syntax.md`, and `references/gh-output.md` if you need exact search patterns.

### 4. Filter internally before searching again

Treat the first pass as raw material, not the final answer.

For each candidate, classify it as:
- **relevant** — clearly fits the job
- **maybe relevant** — plausible but needs more evidence
- **off-topic** — wrong category, dead end, or obvious mismatch

Filter using the cheapest signals first:
- repo name
- description
- topics
- stars
- recent activity or pushed date
- archived status
- license presence

Read README intros only for borderline or high-potential candidates. Harvest better terms from relevant and maybe-relevant repos before expanding search.

Use `references/dedup-and-rank.md` when you need a repeatable shortlist assembly step.
Use `scripts/score-repos.sh` only as a cheap metadata sort; do not let it override user-fit evidence.
Read `references/quality-gates.md` after first-pass classification to decide whether to stop, refine once, augment, or deepen.

### 5. Run one refinement pass

Refine only after the first classification pass tells you what is missing.

Good reasons to refine:
- too few relevant repos
- too much off-topic noise
- naming mismatch between user language and repo language
- a promising subcategory emerged from candidate descriptions or topics

Refinement rules:
- use 1-4 better queries, not a whole new search machine
- expand only the gaps you observed
- stop when new searches mostly repeat known repos

Use `references/search-examples.md` for worked examples of first-pass plus refinement loops.

### 6. Produce the default output

Default output is **markdown in the conversation**, not mandatory files.

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
| [owner/repo](https://github.com/owner/repo) | Strong fit for X | README says Y; topics include Z | stars, pushed date, license, activity | Not verified: A |
```

Require repo links in the table unless a URL is unavailable.

For each `Best fits` repo, include a lightweight evidence pack:
- why it matches the user's must-haves
- evidence source used: description, topics, README, API, or code
- cheap quality signals checked
- caveats and unverified claims
- last checked date when external state matters

If the user is satisfied with the markdown shortlist, stop there.

### 7. Offer optional deepen

Only deepen after the markdown shortlist is useful.
Check `references/quality-gates.md` before deepening; most scouts should stop at the markdown shortlist.

Each branch consumes only the final shortlisted dataset; do not restart discovery.

- **light deeper comparison** — top 3-5 side-by-side on fit, evidence, signals, and caveats
- **code-level evaluation** — top few repos only; verify must-have features, README/onboarding, tests/CI, and maturity risks
- **feature matrix** — explicit capability coverage table with evidence notes or `unknown`
- **HTML/export** — persistent report from the stable markdown shortlist

If the user asks for files, create them from the **final shortlisted dataset only**. Do not create `.githubresearch/` or other artifact trees unless the user wants export or report output.

HTML export data contract for `references/report-template.html`:
- Generate HTML only after the markdown shortlist is stable.
- Fill `[TOPIC]`, `[DATE]`, `[ROW_COUNT]`, `[RECOMMENDATION]`, `[SEARCH_PATH_NOTE]`, and `[GAPS_NOTE]`.
- Each row must provide repo URL/name, fit, evidence, signals, and caveat/unknown.
- Grouped notes come from the same `Best fits`, `Worth a look`, and `Ruled out / why` groups.

## Default evaluation rules

Use light, fast, rate-limit-aware signals by default:
- topic, description, or README match to the user's need
- stars
- recent activity or pushed date
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
- Use subagents only for:
  - very large landscapes
  - explicit deep-dive requests
  - optional feature-matrix generation
  - top-N code-level review
- When web augmentation is the gap and a subagent is dispatched for it, the subagent's brief embeds the `run-research` skill discipline (so the subagent uses the 5-tool toolkit correctly without re-deriving it). See `references/subagent-prompts.md` for the integration block.

If you dispatch help, read `references/subagent-prompts.md`. Subagents gather evidence; the main agent still writes the final shortlist or comparison.

## Reference routing

Load only the branch you need. References are flat on disk and grouped here by decision point.

### Search/discovery

| File | Read when |
|---|---|
| `references/search.md` | Default starting point for first-pass plus refinement search. |
| `references/search-examples.md` | You need examples of good first-pass angles or refinement pivots. |
| `references/gh-syntax.md` | You need valid `gh search repos` qualifiers or OR rules. |
| `references/gh-output.md` | You want token-efficient `gh` output or markdown-ready capture. |
| `references/web-augment.md` | GitHub-only search is thin/noisy, or naming is fuzzy and web augmentation would help. |

### Evaluation/deepening

| File | Read when |
|---|---|
| `references/evaluate.md` | You are checking repo quality signals or deciding whether to deepen. |
| `references/evaluate-rest.md` | You need cheap repo signals beyond the initial search output. |
| `references/evaluate-graphql.md` | You need a single-repo deep evidence query for a top candidate. |
| `references/evaluate-code.md` | You need README, file-tree, or source evidence for the top few repos. |

### Orchestration

| File | Read when |
|---|---|
| `references/subagent-prompts.md` | The landscape is large, or the user explicitly wants deeper comparison work delegated. |

### Output/export

| File | Read when |
|---|---|
| `references/dedup-and-rank.md` | You are turning raw candidates into a grouped shortlist. |
| `references/report-template.html` | The user explicitly wants an HTML export after the shortlist is stable. |

### Stop/refine gates

| File | Read when |
|---|---|
| `references/quality-gates.md` | Decide whether to stop, refine once, augment, or deepen. |

## Guardrails

- Do not treat `run-research` or web augmentation as mandatory.
- Do not default to `.githubresearch/` or any persistent artifact tree.
- Do not pad searches with 20 hypotheses, 100-call ceilings, or wave theater.
- Do not escalate to deep evaluation before you have filtered the first-pass results.
- Do not read whole READMEs for every candidate; read intros or targeted sections for the top few.
- Do not let optional deep-dive work become the default path by accident.
- Stop when the shortlist is good enough and new searches mostly repeat the same field.
- Be explicit about gaps, uncertainty, and what you did **not** verify.
