---
name: run-research
description: Use skill if you are researching a coding bug, library choice, architecture trade-off, or API behavior with web search, Reddit validation, and code-attached deep research.
---

# Research Powerpack

Use this skill to run disciplined, multi-source technical research. Do not drift into shallow workflows. A single query, a Google snippet, a Reddit title, or one AI synthesis is not enough for decisions that affect code, dependencies, architecture, or production behavior.

## Activation boundaries

### Use this skill when
- Fixing a bug, runtime error, regression, or version-specific issue you do not fully recognize
- Choosing between libraries, frameworks, vendors, or architectural approaches
- Verifying whether technical guidance is current, deprecated, or contradicted by production experience
- Researching API behavior, limits, auth patterns, migration risk, or ecosystem trade-offs
- Validating AI-generated claims against official documentation and practitioner evidence

### Do not use this skill when
- You already know the exact authoritative URL and can go straight to `scrape_pages`
- The task is internal planning without external research; use `plan-work` instead
- The answer is a trivial single-doc lookup with no real ambiguity
- You only need to operate a browser or tool without doing research synthesis

## Core operating rules

1. `search_google` finds URLs, not answers. Follow it with `scrape_pages` before citing or relying on anything.
2. `search_reddit` finds threads, not evidence. Use `fetch_reddit` when the thread will influence the conclusion.
3. Never conclude from a single source unless this is a trivial official-doc fact check.
4. Treat `deep_research` as synthesis, not proof. Verify critical claims with scraped sources.
5. For debugging, architecture, migration, performance, or config questions, attach relevant code to `deep_research`.
6. Query diversity beats paraphrase repetition. Each query should attack a different angle.
7. Prefer 3-5 high-signal pages and 5-10 high-signal Reddit threads over broad, shallow batches.
8. Default `fetch_reddit` to `fetch_comments=true` and `use_llm=false`.
9. For architecture, security, performance, pricing, or irreversible decisions, verify across 3 source types: official docs, practitioner/community evidence, and one independent third source.

## Workflow selector

| Situation | Start with | Minimum sequence | Escalate when | Key references |
|---|---|---|---|---|
| Bug, error, regression | `search_google` | `search_google -> scrape_pages -> search_reddit` | If fixes conflict, fail, or feel generic, run `deep_research` last with code attached | `references/strategies/research-patterns.md`, `references/workflows/end-to-end-workflows.md`, `references/bug-fixing.md` |
| Library or dependency choice | `search_google` | `search_google -> scrape_pages -> search_reddit -> fetch_reddit` | Finish with `deep_research` using your constraints and code | `references/strategies/research-patterns.md`, `references/library-research.md` |
| Architecture or system design | `deep_research` | `deep_research -> search_reddit -> fetch_reddit -> search_google -> scrape_pages` | Add more verification if sources disagree or the decision is hard to reverse | `references/workflows/end-to-end-workflows.md`, `references/architecture.md` |
| Understand a tool or concept | `deep_research` | `deep_research -> search_google -> scrape_pages` | Add Reddit only if production reality matters | `references/strategies/research-patterns.md`, `references/tools/deep-research.md` |
| Fact check or recency check | `search_google` | `search_google -> scrape_pages` | Add Reddit only if the claim is contested or docs are ambiguous | `references/fact-checking/verification-methods.md` |
| Landscape scan or state-of-the-ecosystem check | `search_reddit` | `search_reddit -> fetch_reddit -> search_google -> scrape_pages` | Use `deep_research` at the end if you need a recommendation, not just a pulse check | `references/workflows/end-to-end-workflows.md` |

## Execution sequence

### 1) Frame the research before calling tools
Write down the actual decision or question, then add the context that changes the answer:
- stack, framework, version, and year
- scale, environment, and deployment model
- reversibility and risk tolerance
- whether the task is a bug, choice, architecture question, verification task, or landscape scan

If you use `deep_research`, use the full structured format: `GOAL`, `WHY`, `KNOWN`, `APPLY`, and 2-5 specific sub-questions. For code-related work, attach the smallest useful set of files and describe what each file should be inspected for.

### 2) Generate diverse queries instead of shallow repeats
- For `search_google`, cover multiple angles such as exact match, official docs, failure mode, comparison, best practice, and advanced production usage.
- For `search_reddit`, include negative-signal queries such as `regret`, `problems`, `switched from`, `not worth it`, and subreddit-targeted queries.
- Add year and version tokens for fast-moving ecosystems.
- Use operators deliberately: `site:`, `-site:`, quotes, `OR`, `intitle:`.

If your queries are minor rewrites of each other, stop and diversify before searching.

### 3) Read the actual sources
- After `search_google`, scrape the best 3-5 URLs immediately.
- After `search_reddit`, fetch the best 5-10 threads if community experience matters.
- With `scrape_pages`, ask for specific extraction targets, not vague summaries.
- With `fetch_reddit`, keep `use_llm=false` unless you are processing a large batch and only need broad synthesis.

Search results are discovery input. Scraped pages and fetched threads are the evidence.

### 4) Validate before concluding
For every claim that affects the recommendation, check:
- source type
- recency
- version or environment assumptions
- whether the source is independent
- whether another source confirms or contradicts it

Use official docs for syntax, defaults, version support, pricing, and changelogs. Use Reddit and practitioner sources for hidden failure modes, migration pain, operational caveats, and real production thresholds. Use `deep_research` to connect the dots, not to replace verification.

### 5) Synthesize to an action, not a bibliography
End with one of these outputs:
- likely cause + fix + caveats + fallback
- recommendation + confidence + trade-offs + conditions
- verified fact + current status + what changed

If sources disagree, explain why. If the answer depends on context, name the context variable that changes the recommendation. Stop when additional tool calls are no longer changing the conclusion.

## Do this, not that

| Do this | Not that |
|---|---|
| Use `search_google` to build a lead list, then `scrape_pages` to read the real content | Quote Google snippets as evidence |
| Use `search_reddit` to discover threads, then `fetch_reddit` to inspect comments and corrections | Treat Reddit titles or top comments as the whole story |
| Use `deep_research` with structured questions and code attachments | Ask one vague question with no files and trust the result blindly |
| Search for negative signal and migration pain | Only search for `best`, `top`, or positive recommendations |
| Verify critical claims against scraped docs or changelogs | Repeat a `deep_research` claim as if it were a citation |
| Run focused batches of high-signal pages and threads | Spray 20-50 weak sources and accept shallow summaries |
| Add year, version, scale, and subreddit context | Rephrase the same generic query multiple times |

## Recovery paths

- **Google results are noisy or SEO-heavy:** add `site:` targets, exclude noisy domains with `-site:`, add exact phrases, and add year/version constraints. See `references/queries/query-formulation.md`.
- **Google returns little signal:** broaden one level of abstraction, then try Reddit for practitioner phrasing and edge cases.
- **Reddit results are stale or one-note:** use `date_after`, target multiple subreddits, and verify against current docs before trusting the thread.
- **`deep_research` feels generic:** reduce question count, strengthen the `GOAL/WHY/KNOWN/APPLY` template, and attach 2-4 focused files with descriptions.
- **Sources conflict:** trust scraped official facts over synthesized claims, then use `references/synthesis/synthesize-findings.md` to map consensus and context splits.
- **You are under time pressure:** run the smallest workflow that can still produce a verified answer, then escalate only if the result is unclear.

## Reference router

### Research method references
- `references/strategies/research-patterns.md` — choose the right pattern before spending tool calls
- `references/workflows/end-to-end-workflows.md` — full step-by-step workflows and escalation points
- `references/queries/query-formulation.md` — query diversification, operators, and expansion strategies
- `references/fact-checking/verification-methods.md` — source validation, recency checks, and triangulation
- `references/synthesis/synthesize-findings.md` — consensus mapping, contradiction handling, and final recommendation formats

### Tool references
- `references/tools/search-google.md` — breadth-first discovery rules and anti-patterns
- `references/tools/scrape-pages.md` — focused extraction targets and scraping failure modes
- `references/tools/deep-research.md` — structured question format, attachment rules, and escalation use cases
- `references/tools/search-reddit.md` — negative-signal query design and subreddit targeting
- `references/tools/fetch-reddit.md` — comment-thread reading strategy and exact-value preservation

### Domain references
- `references/bug-fixing.md`
- `references/library-research.md`
- `references/architecture.md`
- `references/api-integration.md`
- `references/security.md`
- `references/performance.md`
- `references/testing.md`
- `references/frontend.md`
- `references/devops.md`
- `references/language-idioms.md`

Start with the smallest relevant method reference, then add one domain reference only if the task needs domain-specific nuance.
