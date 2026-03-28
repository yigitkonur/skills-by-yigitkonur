---
name: run-github-repo-evaluate
description: "Use skill if you are evaluating GitHub repositories for quality, maturity, and maintainer credibility using GraphQL batch queries, REST signals, and code-level analysis."
---

# GitHub Repo Evaluate

Deep-evaluate GitHub repositories across quantitative metrics (API-based) and qualitative signals (code-level). Dispatches parallel subagents for efficient per-repo assessment.

## Trigger boundary

**Use when:** evaluating known repos for quality, comparing candidates, scoring maintainer credibility
**Do NOT use when:** searching for repos (use `run-github-repo-search` instead)

## Workflow

### Phase 1: Quick Screen (main agent, NO subagents)

**CEILING: Maximum 30 repos.** If input list is >30, take top 30 by stars.

Batch repos into groups of 5. For each batch, run ONE GraphQL call:

```bash
gh api graphql -f query='
fragment R on Repository {
  nameWithOwner stargazerCount forkCount
  createdAt pushedAt primaryLanguage{name} licenseInfo{spdxId}
  defaultBranchRef{target{...on Commit{history(first:0){totalCount}}}}
  openIssues:issues(states:OPEN){totalCount}
  closedIssues:issues(states:CLOSED){totalCount}
  mergedPRs:pullRequests(states:MERGED){totalCount}
  releases{totalCount}
}
{
  r0:repository(owner:"O0",name:"N0"){...R}
  r1:repository(owner:"O1",name:"N1"){...R}
  ...
}' --jq '.data | del(.rateLimit) | to_entries[] | .value |
"\(.nameWithOwner)\t\(.stargazerCount)★\t\(.primaryLanguage.name // "?")\t\(.defaultBranchRef.target.history.totalCount) commits\tI:\(.openIssues.totalCount)/\(.closedIssues.totalCount)\tPR:\(.mergedPRs.totalCount)\tR:\(.releases.totalCount)\t\(.pushedAt[:10])"'
```

Read `references/graphql-batch-repos.md` for the exact pattern.

Output: overview table for user to review before committing to deep evaluation.

### Phase 2: Deep Evaluation (subagents, 1 per repo)

For each repo, dispatch a subagent (Sonnet model) with the full evaluation prompt.

**CEILING: Maximum 15 parallel subagents.** If >15 repos, batch in waves.
**THRESHOLD: If evaluating <=3 repos, skip subagents — do it inline.**

Each subagent runs THREE query types:

1. **GraphQL repo deep dive** (1 API call, 1 rate limit point)
   Read `references/graphql-repo-deep-dive.md` — copy the exact query template.

2. **REST-only signals** (~8 API calls, 8 rate limit points)
   Read `references/rest-unique-signals.md` — these 6 endpoints have NO GraphQL equivalent.

3. **Author profile** (1 API call, 1 rate limit point)
   Read `references/graphql-user-profile.md` — deep author assessment with 6-year contribution history.

4. **Code-level analysis** (3-5 API calls)
   Read `references/code-level-analysis.md` — README quality, key file presence, source code sampling.

Each subagent returns a structured metrics report. See `references/subagent-dispatch-guide.md` for the exact prompt template.

### Phase 3: Score & Report (main agent)

After all subagents complete:

1. Read all metrics reports
2. Apply scoring rubric from `references/scoring-rubric.md`
3. Calculate composite score per repo
4. Rank by score descending

**Output format:**

**Summary table:**
```markdown
| # | Repo | Score | Stars | Health | Author | Code | Flags | Key Strength | Key Risk |
```

**Per-repo analysis** (top 10): 2-3 sentences covering standout metrics, concerns, and recommendation.

**Landscape insights**: Common patterns, gaps, trends across evaluated repos.

## Scoring formula

```
Score = (Health × health_weight) + (Author × author_weight) + (Code × code_weight) + RedFlagPenalties
```

Default weights: Health 40%, Author 30%, Code 30%. User can customize.

Read `references/scoring-rubric.md` for all 29 metrics with 0-10 scales.

## Decision rules

- <=3 repos → evaluate inline (no subagents)
- 4-15 repos → one wave of parallel subagents
- 16-30 repos → two waves of subagents
- User only wants author assessment → skip repo metrics, author-only path
- Feature Fit metrics are CUSTOM per use case — user defines what features matter
- If a repo doesn't exist or API errors → score 0, note in report
- If author is an org → use org profile query, score all Author metrics at 5/10 (neutral). Note: org repos lack personal contribution history — this is an information gap, not a red flag.

## Reference routing

| File | Read when |
|---|---|
| `references/graphql-repo-deep-dive.md` | Phase 2 — single repo full query |
| `references/graphql-batch-repos.md` | Phase 1 — batch screening query |
| `references/graphql-user-profile.md` | Phase 2 — author assessment |
| `references/graphql-user-profile.md` (batch section) | Phase 1 — batch author comparison |
| `references/rest-unique-signals.md` | Phase 2 — the 6 REST-only endpoints |
| `references/code-level-analysis.md` | Phase 2 — README, files, source sampling |
| `references/scoring-rubric.md` | Phase 3 — all metrics with scoring scales |
| `references/author-red-flags.md` | Phase 2/3 — detecting red flags |
| `references/api-gotchas.md` | Any phase — known API pitfalls |
| `references/subagent-dispatch-guide.md` | Phase 2 — exact subagent prompt template |
