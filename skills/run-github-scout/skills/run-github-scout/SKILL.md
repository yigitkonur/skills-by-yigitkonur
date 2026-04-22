---
name: run-github-scout
description: "Use skill if you are finding, shortlisting, or comparing GitHub repos for a concrete need and want adaptive discovery, relevance filtering, and optional deeper comparison."
---

# GitHub Repo Scout

Find and shortlist the best-fit GitHub repos for a concrete user need. Default to adaptive discovery, internal relevance filtering, and a markdown shortlist. Deeper comparison, feature matrices, and HTML export are optional end-stage branches.

## Trigger boundary

**Use when:** "find the best open-source X for Y", "what GitHub repos fit this use case?", "compare repos for this stack/problem", "I need a shortlist of tools like this", or "find similar repos on GitHub".

**Do NOT use when:** the task is generic technical research without repo-discovery intent, a codebase-local question, or a non-GitHub product comparison. Use `run-research` for broad web research that is not centered on GitHub repositories.

## Default stance

- **Shortlist first.** The default deliverable is an in-conversation markdown shortlist.
- **Search small, then refine.** Start with 3-6 broad angles, then run at most one refinement round unless results are still materially weak.
- **Filter before expanding.** Read descriptions, names, topics, stars, and recent activity before inventing more searches.
- **Research Power Pack / MCP web tools are optional.** Use them when they help naming or landscape discovery. Never require them.
- **Keep deep work top-N only.** Feature matrices, code reads, and HTML export happen only after a useful shortlist exists.

## Capability check

Choose the leanest path that can still answer the request.

| Path | Use when | Default tools |
|---|---|---|
| **GitHub-only** | The problem is clearly named, the category is repo-centric, or GitHub search already surfaces relevant candidates. | `gh search repos`, GitHub web/API, repo READMEs |
| **Augmented** | Naming is fuzzy, the landscape is broad, category labels are unclear, or first-pass GitHub search is thin/noisy. | GitHub search plus optional MCP/web research to learn better terms |

Rules:
- If MCP/web research is unavailable, continue on the GitHub-only path.
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
- Read `references/search/web-search-patterns.md` only if you need the augmented branch.

### 3. Run a small first pass

Start with **3-6 search angles**, not a giant hypothesis list.

Minimum useful angle set:
1. direct phrasing of the user's need
2. broader category phrasing
3. known examples or well-known alternatives
4. one unexpected-naming branch

Add a fifth or sixth angle only when a hard constraint matters (language, deployment model, self-hosted, etc.).

Use short, broad queries first. Read `references/search/search-methodology.md`, `references/search/gh-search-syntax-cheatsheet.md`, and `references/search/output-format-recipes.md` if you need exact search patterns.

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

Use `references/search/dedup-and-rank.md` when you need a repeatable shortlist assembly step.

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

Use `references/search/search-diversity-examples.md` for worked examples of first-pass plus refinement loops.

### 6. Produce the default output

Default output is **markdown in the conversation**, not mandatory files.

Deliver:
1. a one-paragraph recommendation or framing note
2. a compact markdown table
3. a grouped shortlist (`Best fits`, `Worth a look`, `Ruled out / why`)
4. notable gaps or uncertainty

Recommended table:

```markdown
| Repo | Why it fits | Useful signals | Caveat |
|---|---|---|---|
| owner/repo | Best match for X because Y | 4.2k stars, pushed 2026-04, MIT | Docs thin |
```

If the user is satisfied with the markdown shortlist, stop there.

### 7. Offer optional deepen

Only deepen after the markdown shortlist is useful.

Optional branches:
- **light deeper comparison** — compare the top 3-5 repos side by side
- **code-level evaluation** — verify feature evidence and implementation maturity in the top few repos
- **feature matrix** — only if the user wants explicit capability coverage
- **HTML/export** — only if the user wants a persistent artifact

If the user asks for files, create them from the **final shortlisted dataset only**. Do not create `.githubresearch/` or other artifact trees unless the user wants export or report output.

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
- `references/evaluation/evaluation-methodology.md` for the light default path and deepen triggers
- `references/evaluation/rest-unique-signals.md` for cheap repo signals
- `references/evaluation/graphql-repo-deep-dive.md` for optional single-repo deep evidence
- `references/evaluation/code-level-analysis.md` for optional code-level checks

## Orchestration rules

Default execution model: **hybrid lean**.

- The main agent owns intent parsing, search strategy, filtering, and synthesis.
- Batch or parallelize queries when helpful, but keep the reasoning central.
- Use subagents only for:
  - very large landscapes
  - explicit deep-dive requests
  - optional feature-matrix generation
  - top-N code-level review

If you dispatch help, read `references/subagent-prompts.md`. Subagents gather evidence; the main agent still writes the final shortlist or comparison.

## Output contract

Unless the user asks for a different format, show work in this order:

1. interpreted need summary
2. chosen search path and why
3. first-pass shortlist result
4. refined shortlist and recommendation
5. optional deepen choices if more confidence or export is useful

## Reference routing

Load only the branch you need.

| File | Read when |
|---|---|
| `references/search/search-methodology.md` | Default starting point for first-pass plus refinement search. |
| `references/search/search-diversity-examples.md` | You need examples of good first-pass angles or refinement pivots. |
| `references/search/gh-search-syntax-cheatsheet.md` | You need valid `gh search repos` qualifiers or OR rules. |
| `references/search/output-format-recipes.md` | You want token-efficient `gh` output or markdown-ready capture. |
| `references/search/web-search-patterns.md` | GitHub-only search is thin or noisy, or naming is fuzzy and web augmentation would help. |
| `references/search/dedup-and-rank.md` | You are turning raw candidates into a grouped shortlist. |
| `references/evaluation/evaluation-methodology.md` | You are checking repo quality signals or deciding whether to deepen. |
| `references/evaluation/rest-unique-signals.md` | You need cheap repo signals beyond the initial search output. |
| `references/evaluation/graphql-repo-deep-dive.md` | You need a single-repo deep evidence query for a top candidate. |
| `references/evaluation/code-level-analysis.md` | You need README, file-tree, or source evidence for the top few repos. |
| `references/subagent-prompts.md` | The landscape is large, or the user explicitly wants deeper comparison work delegated. |
| `references/quality-gates.md` | Decide whether to stop, refine once, or deepen. |
| `references/report-template.html` | The user explicitly wants an HTML export after the shortlist is stable. |

## Guardrails

- Do not treat Research Power Pack or MCP web research as mandatory.
- Do not default to `.githubresearch/` or any persistent artifact tree.
- Do not pad searches with 20 hypotheses, 100-call ceilings, or wave theater.
- Do not escalate to deep evaluation before you have filtered the first-pass results.
- Do not read whole READMEs for every candidate; read intros or targeted sections for the top few.
- Do not let optional deep-dive work become the default path by accident.
- Stop when the shortlist is good enough and new searches mostly repeat the same field.
- Be explicit about gaps, uncertainty, and what you did **not** verify.
