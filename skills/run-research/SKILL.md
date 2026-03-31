---
name: run-research
description: >-
  Use skill if you are researching a bug, library choice, architecture trade-off, or technical question where current web evidence, Reddit experience, and multi-source synthesis matter.
---

# Multi-Source Technical Research

You have five research tools. Using them in the right order, at the right depth, with the right parameters is what separates shallow answers from decision-grade research.

## Tool prerequisites

This skill requires five MCP tools: `web-search`, `scrape-links`, `search-reddit`, `get-reddit-post`, and `deep-research`. If any of these tools are not available in your current environment, install the research MCP server first:

```bash
npx -y @anthropic-ai/claude-code@latest mcp add research-server -y -- npx -y mcp-remote@latest https://research.yigitkonur.com/mcp --allow-http
```

After installation, restart your session. All five tools will then appear in your tool list.

## Your Tools
**`web-search`** runs up to 100 parallel Google searches and returns consensus-ranked URLs with an aggregated summary. That summary alone often reframes your entire approach — it shows you what the landscape looks like before you read a single page. Always start here.

**`scrape-links`** fetches 1–50 pages and extracts exactly what you ask for. Always use `use_llm=true` with pipe-separated extraction targets like `"pricing|features|limitations|compatibility|when NOT to use"`. The specificity of your targets determines the quality of what comes back. Group thematically similar URLs in the same call — they share context and extract more coherently.

**`search-reddit`** runs 3–50 parallel Reddit searches and returns ranked thread URLs. Reddit tells you what actually happens in production: what breaks, what costs more than advertised, what people quietly regret, and what the docs forgot to mention.

**`get-reddit-post`** fetches full comment trees from 2–50 Reddit posts. Always use `fetch_comments=true` and `use_llm=false`. Reddit data comes through a structured API — no navigation, no ads, no boilerplate. The raw threaded comments ARE the signal. The best insights are never in the post title — they're in the corrections, the "EDIT: solved it", the "after 6 months in production..." replies, and the specific numbers people share.

**`deep-research`** runs 1–10 parallel research questions with AI synthesis across multiple sources. Its power scales with your KNOWN field — the more specific evidence you feed it from earlier steps, the sharper and more actionable its output becomes. Use the structured template: GOAL → WHY → KNOWN → APPLY → SPECIFIC QUESTIONS. Attach code files when debugging or evaluating architecture.

## The Research Loop

### 1. Search first — always, without exception
Every research task begins with `web-search`. Before Reddit. Before deep-research. Before you think you already know the answer. The aggregated view across dozens of search results creates a landscape understanding that no single source provides.

Write keywords that attack genuinely different angles — you can run up to 100 in parallel. Exact error messages in quotes. Official docs with `site:`. Comparison queries. Failure modes. Year-pinned queries for fast-moving ecosystems. Negative signal (`"problems with"`, `"regret"`, `"switched from"`). If your keywords are minor rewrites of each other, stop and diversify before searching.

Use search operators aggressively: `site:` for authoritative domains, `"exact phrases"` for error messages, `-site:` to exclude SEO farms, `intitle:` for focused results, `OR` for variant matching.

### 2. Read what matters

Search results are leads, not evidence. After `web-search`, scrape the most promising URLs with `scrape-links`. You can process up to 50 pages — pick the 3–10 that look highest-signal.

Your extraction targets determine everything:
- Strong: `"root cause|fix steps|version affected|workarounds|breaking changes|migration path"`
- Weak: `"tell me about this page"`

Aim for 4–8 pipe-separated targets per call. Each target should name a specific category of information you need.

### 3. Hear from practitioners
Official documentation tells you how things should work. Reddit tells you how they actually work. After you understand the official story, check what real developers experience.

Use `search-reddit` with diverse queries — up to 50. Cover multiple angles: direct topic, subreddit-targeted (`r/node`, `r/ExperiencedDevs`), comparisons (`"X vs Y"`), negative signal (`"regret"`, `"not worth it"`, `"broke in production"`), year-specific, and scale-specific queries. At least a quarter of your queries should hunt for negative signal — developers who warn you are often more useful than those who recommend.

Then fetch the best threads with `get-reddit-post`:
- Always `fetch_comments=true`
- Always `use_llm=false`
- Pick 5–10 high-engagement threads (10+ comments) rather than 30 shallow ones
- Comment budget is ~1000 total — fewer threads means richer context per thread

Look for: "EDIT: this fixed it" (confirmed solutions), "after X months in production" (battle-tested experience), specific numbers (latency, cost, scale), corrections in reply chains, and dissenting views with substantive arguments.

### 4. Synthesize with evidence

For complex questions, use `deep-research` to pull everything together. By this point your KNOWN field should overflow with findings from steps 1–3. Include specific data points, version numbers, Reddit quotes, and scraped facts — not vague summaries.

Ask 2–3 focused questions rather than 5–10 scattered ones. Each question gets a share of the 32K token budget, so fewer questions means deeper analysis. Attach relevant code files for bugs, `package.json` for library decisions, config files for infrastructure questions.

### 5. Verify what matters
Before finalizing: cross-check any claim that could change your recommendation. Scrape the official changelog for version-specific facts. Run a targeted search for counter-evidence. Compare what Reddit says with what the docs promise.

Stop when additional tool calls stop changing your conclusion.

## Matching Depth to Stakes

You decide how deep to go based on the question, not a rigid formula:

| Situation | Typical path | Why |
|---|---|---|
| Quick fact check | web-search → scrape 2–3 pages | Authoritative source settles it |
| Error diagnosis | web-search → scrape → search-reddit | Error messages are highly searchable; Reddit has "same issue" threads |
| Library comparison | Full loop: all 5 tools | Multi-dimensional decision needs benchmarks, community signal, and synthesis |
| Architecture decision | Full loop, starting broad | Expensive to reverse — need maximum evidence |
| Production incident | web-search (3 focused keywords) → scrape top 2–3 | Speed matters — apply first plausible fix, iterate |
| Landscape/trend check | web-search → search-reddit → get-reddit-post | Community pulse matters more than official docs |

But these aren't rigid sequences. If web-search surfaces a clear answer with strong consensus, stop. If Reddit reveals the docs are wrong, go deeper. If deep-research raises a new question, run another search round. Let the evidence guide your depth.
## Output

Match your output format to the question type:

**Decisions:** Comparison table with criteria sourced from research + clear recommendation + confidence level + conditions that would change the answer + what to avoid and why. Include a **counter-arguments section** that anticipates objections and responds with evidence — this is where you preempt "but what about..." questions. Format as Q&A pairs: the objection in bold, then your evidence-backed response. The strongest decision documents don't just recommend — they defend the recommendation against the best arguments for the alternatives.

**Bug fixes:** Likely root cause with evidence + fix pattern showing before → after + caveats and edge cases + fallback if the fix doesn't work. Start with an **immediate stabilization section** — what can be deployed in 15 minutes to stop the bleeding while root cause investigation continues. Practitioners need something to ship NOW and something to ship after diagnosis. Separate the two clearly.

**Evaluations:** Options ranked by fit for the user's context + "best for [scenario A]" vs "best for [scenario B]" + specific risks per option.

**Fact checks:** Current verified status + what changed and when + sources confirming and contradicting.

**All output types:** Cite sources with specificity — Reddit usernames and dates (`u/username, Mon YYYY`), GitHub issue numbers, blog post authors and dates, version numbers. "Reddit consensus" is not a citation. `u/jsmith (Mar 2025, r/node): "exact quote"` is a citation. When you cite a number (latency, cost, scale threshold), name where that number came from.

When sources disagree, explain why — different versions, different scale, different context. When the answer depends on the user's situation, name the variable that flips the recommendation.
## What Separates Good Research from Bad

**Query diversity is everything.** Five angles on one topic beats fifty paraphrases. Exact error in quotes, `site:` for official docs, "switched from X" for migration stories, "problems with X at scale" for hidden issues, year-tagged for recency.

**Negative signal reveals truth.** People who succeed rarely post about it. People who fail explain exactly what went wrong. Always search for failures, regrets, and pain alongside recommendations.

**The KNOWN field is deep-research's biggest quality lever.** Feed it specific findings — version numbers, benchmark data, Reddit quotes, pricing tiers — and it produces analysis tailored to your situation. Feed it nothing and it produces a textbook answer.

**Specific extraction beats vague extraction.** `"pricing tiers|free tier limits|overage costs|API rate limits|SLA"` returns structured data. `"what does this cost"` returns prose.

**Raw Reddit > summarized Reddit.** The API delivers clean structured data. `use_llm=true` throws away the exact code snippets, version strings, config values, and authority signals that make Reddit research actionable.

## What to Avoid

- Treating search snippets as evidence (they're leads, not citations)
- Following tool-generated "Next Steps" suggestions instead of your own research plan
- Fetching 30+ Reddit threads at 30 comments each (shallow) instead of 5–10 at 100–200 each (rich)
- Calling deep-research first with empty KNOWN (gather evidence first, then synthesize)
- Paraphrasing the same query instead of genuinely diversifying angles
- Stopping at one source for anything that influences a decision (triangulate across source types)
- Using `use_llm=true` on `get-reddit-post` (Reddit data is already clean)
- Using vague extraction targets on `scrape-links` (specificity determines quality)
## References

Consult these when you need deeper guidance on a specific aspect:

- `references/tools.md` — Detailed parameters, token budgets, failure modes, and composition patterns for each tool
- `references/workflows.md` — Step-by-step research workflows for common scenarios: bug fixing, library evaluation, architecture decisions, security audits, performance optimization, and more
- `references/synthesis.md` — How to weigh sources, resolve contradictions, handle uncertainty, and distill findings into actionable recommendations