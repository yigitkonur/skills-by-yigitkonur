# Scoring Rubric

29 quality metrics across 3 categories + red flags. Each metric scores 0-10.

## A. Repo Health (default weight: 40%)

| # | Metric | Source | 0 | 5 | 10 |
|---|---|---|---|---|---|
| 1 | Community health | REST community/profile | <25% | 50% | >75% |
| 2 | Commit consistency | REST stats/commit_activity | dead/burst | sporadic | steady weekly |
| 3 | Issue close rate | GraphQL open/closed | <25% | 50% | >75% |
| 4 | PR merge count | GraphQL mergedPRs | 0 | 10-50 | 50+ |
| 5 | Release count | GraphQL releases | 0 | 1-10 | 10+ |
| 6 | CI green rate | REST actions/runs | no CI/<50% | 70% | >85% |
| 7 | npm downloads/week | npm API | not on npm | <500 | >500 |
| 8 | Contributor count | GraphQL mentionableUsers | 1 | 2-5 | 10+ |
| 9 | Discussion activity | GraphQL discussions | disabled | enabled+dead | active (10+) |
| 10 | Vulnerability alerts | GraphQL vulnAlerts | 5+ open | 1-4 | 0 |

## B. Author Profile (default weight: 30%)

| # | Metric | Source | 0 | 5 | 10 |
|---|---|---|---|---|---|
| 11 | Pre-2024 commits | GraphQL y2022+y2023 | 0 | <100/yr | >500/yr |
| 12 | Language depth | User repos by language | 1 lang | diverse scripting | Go/Rust/C systems |
| 13 | Star-giving freq | GraphQL starredRepos | <10 | 10-100 | 100+ |
| 14 | Upstream contributions | GraphQL reposContribTo | 0 | 1-2 repos | 3+ |
| 15 | Author track record | Top repos by stars | 0 notable | 1 repo 50+★ | multiple successful |
| 16 | Account age | createdAt | <1 year | 3-5 years | 10+ years |
| 17 | Followers | followers.totalCount | <10 | 10-100 | 100+ |
| 18 | Org membership | organizations.totalCount | 0 | 1-2 | 3+ |

## C. Code Quality (default weight: 30%)

| # | Metric | Source | 0 | 5 | 10 |
|---|---|---|---|---|---|
| 19 | README quality | REST readme | none/template | basic install+usage | comprehensive+examples |
| 20 | Key file presence | REST contents/ | 0-2 files | 5-6 files | 8+ files |
| 21 | TS/lint strictness | tsconfig.json | no config | lax | strict+CI |
| 22 | Test freshness | Recent commits | no tests | stale | actively maintained |
| 23 | Commit message quality | REST commits | lazy (fix/wip) | mixed | descriptive |
| 24 | PR review culture | REST pulls/reviews | no PRs/self-merge | some reviews | AI review bots active |

## D. Red Flags (subtract from total)

| # | Flag | Detection | Penalty |
|---|---|---|---|
| 25 | Fork-heavy author | >50% fork repos | -5 |
| 26 | AI-wave-only author | Created 2024+ AND 0 pre-2024 | -3 |
| 27 | Stale graveyard author | 10+ dead repos | -3 |
| 28 | Archived/disabled repo | isArchived or isDisabled | -10 |
| 29 | No license | licenseInfo is null | -2 |

## Scoring Formula

```
health_score = average(metrics 1-10) × 10  (normalize to 0-100)
author_score = average(metrics 11-18) × 10
code_score = average(metrics 19-24) × 10
penalties = sum(metrics 25-29)

final = (health × 0.40) + (author × 0.30) + (code × 0.30) + penalties
```

Clamp to 0-100 range.

## Special Cases

**Org-owned repos:** Score all Author metrics (11-18) at 5/10 (neutral). Org profiles lack personal contribution data — this is an information gap, not a penalty.

**AI-bot commits** (swe-agent, copilot, claude): If >50% of recent commits are by bots, score Commit Message Quality at 3/10 and note "AI-authored" in qualitative assessment. Bot commits inflate activity metrics but mask human maintainability.

**CI "action_required":** GitHub reports `action_required` for runs pending human approval. Score same as unknown (3/10) unless context clarifies it's a deliberate review gate (in which case 5/10).

**Stats unavailable:** If REST stats endpoints return `{}` after 3 retries, mark "N/A" and infer from GraphQL commit count + pushedAt date. Don't score 0 — score as "insufficient data" (3/10).

**"Stale" vs "Dead":** A repo with 0 activity in the last 12 weeks but strong historical activity (100+ commits, multiple releases) is "stale" (score commit consistency at 3). A repo with <20 total commits AND 0 recent activity is "dead" (score at 0).

## Custom Feature Fit

The user can add domain-specific metrics (e.g., "supports async", "has server mode").
These replace or supplement the default rubric. Weight them as the user specifies.

## Interpretation

| Score | Label |
|---|---|
| 80-100 | Excellent — production-ready, well-maintained |
| 60-79 | Good — usable, some gaps |
| 40-59 | Fair — functional but risks |
| 20-39 | Weak — significant concerns |
| 0-19 | Avoid — abandoned or problematic |
