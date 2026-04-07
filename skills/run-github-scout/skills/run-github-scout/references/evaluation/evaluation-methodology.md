# Evaluation Methodology

Operating manual for evaluation subagents. Covers quick screening, deep evaluation, and scoring.

## Phase 1: Quick Screen (NO subagents)

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

Read `graphql-batch-repos.md` for the exact pattern.

Output: overview table for user review before committing to deep evaluation.

## Phase 2: Deep Evaluation (subagents, 1 per repo)

**CEILING: Maximum 15 parallel subagents.** If >15 repos, batch in waves.
**THRESHOLD: If evaluating <=3 repos, skip subagents — do it inline.**

Each subagent runs FOUR query types:

1. **GraphQL repo deep dive** (1 API call)
   Read `graphql-repo-deep-dive.md` — copy the exact query template.

2. **REST-only signals** (~8 API calls)
   Read `rest-unique-signals.md` — the 6 endpoints with NO GraphQL equivalent.

3. **Author profile** (1 API call)
   Read `graphql-user-profile.md` — deep author assessment with 6-year contribution history.

4. **Code-level analysis** (3-5 API calls)
   Read `code-level-analysis.md` — README quality, key file presence, source code sampling.

Each subagent returns a structured metrics report. See `eval-subagent-dispatch.md` for the prompt template.

## Phase 3: Score & Report

After all subagents complete:

1. Read all metrics reports
2. Apply scoring rubric from `scoring-rubric.md`
3. Calculate composite score per repo
4. Rank by score descending

**Scoring formula:**
```
Score = (Health x 0.4) + (Author x 0.3) + (Code x 0.3) + RedFlagPenalties
```

Read `scoring-rubric.md` for all 29 metrics with 0-10 scales.

**Output format:**

**Summary table:**
```markdown
| # | Repo | Score | Stars | Health | Author | Code | Flags | Key Strength | Key Risk |
```

**Per-repo analysis** (top 10): 2-3 sentences covering standout metrics, concerns, and recommendation.

## Decision rules

- <=3 repos: evaluate inline (no subagents)
- 4-15 repos: one wave of parallel subagents
- 16-30 repos: two waves of subagents
- User only wants author assessment: skip repo metrics, author-only path
- Feature Fit metrics are CUSTOM per use case
- If a repo doesn't exist or API errors: score 0, note in report
- If author is an org: score all Author metrics at 5/10 (neutral), note as info gap not red flag
