# API Gotchas

All known pitfalls discovered during testing. Reference this when commands fail unexpectedly.

## GraphQL Gotchas

| # | Gotcha | Error | Fix |
|---|---|---|---|
| 1 | `organizations` without pagination | "Must provide first or last" | Always use `organizations(first:10)` |
| 2 | `projects` (classic) deprecated | "Projects (classic) is being deprecated" | Use `projectsV2(first:N)` |
| 3 | `user()` with org login | "Could not resolve to a User" | Pre-check with `repositoryOwner(login:...) { __typename }` |
| 4 | Batch too complex | `RESOURCE_LIMITS_EXCEEDED` | Max: 5 users × 3 years OR 4 × 4 years |
| 5 | `last:N` + `orderBy:DESC` | Returns oldest N, not newest | Use `first:N` + `orderBy:{direction:DESC}` |
| 6 | jq integer overflow | Wrong percentages | Use `* 100.0` or `as $var` pattern |
| 7 | `primaryLanguage` null | jq null propagation | Always use `// "?"` fallback |
| 8 | Pre-account contributions | Unexpected data for early years | Normal — git history backdating |
| 9 | `contributionCalendar` in batch | Adds complexity, may trigger limits | Drop calendar in batch, use `totalCommitContributions` alone |
| 10 | Nonexistent repo in batch | Error for that alias, others still work | Check `.errors[]` alongside `.data` |

## REST Gotchas

| # | Gotcha | Error/Behavior | Fix |
|---|---|---|---|
| 11 | Stats 202 response | Returns `{}` | Sleep 2s, retry once |
| 12 | `rtk` escapes `!=` | Broken jq expression | Use `(if .field then true else false end)` |
| 13 | Branch protection 404 | Requires admin access | Skip for third-party assessment |
| 14 | Traffic endpoints 403 | Requires push access | Skip entirely |
| 15 | `stats/contributors` cap | Max 100 contributors returned | Note limitation in report |
| 16 | `stats/participation` owner=0 | Counts org account, not humans | Normal for org-owned repos |
| 17 | Empty stats after retry | Repo too new or too small | Score as "insufficient data", don't error |

## General

| # | Gotcha | Fix |
|---|---|---|
| 18 | Rate limit (5000 pts/hr) | Check: `gh api graphql -f query='{ rateLimit { remaining resetAt } }'` |
| 19 | base64 README decoding | `gh api repos/O/R/readme --jq '.content' \| base64 -d` |
| 20 | npm package name lookup | `gh api repos/O/R/contents/package.json --jq '.content' \| base64 -d \| jq -r '.name'` |
| 21 | `rtk curl` auto-JSON | Returns schema template, not real data. Use plain `curl -s` for npm API calls |
| 22 | `sleep` is a shell builtin | Do NOT prefix with `rtk`. Use bare `sleep 2` in retry patterns |
| 23 | Parallel error propagation | If one parallel Bash call fails, siblings get cancelled. Run stats retry commands SEQUENTIALLY, not in parallel |
