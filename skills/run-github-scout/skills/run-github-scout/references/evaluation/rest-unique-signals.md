# REST-Only Signals

These 6 REST endpoints have NO GraphQL equivalent. They provide signals that GraphQL cannot.

## CRITICAL: 202 Retry Pattern

Stats endpoints return `{}` on first call (GitHub computes on demand). MUST retry:

```bash
fetch_stats() {
  local endpoint="$1"
  local result=$(gh api "$endpoint" 2>&1)
  if [ "$result" = "{}" ] || [ -z "$result" ]; then
    sleep 2
    result=$(gh api "$endpoint" 2>&1)
  fi
  echo "$result"
}
```

## Signal 1: Commit Consistency (52 weeks)

```bash
gh api repos/OWNER/REPO/stats/commit_activity \
  --jq '{
    total_52w: ([.[].total] | add),
    recent_12w: ([.[-12:][].total] | add),
    recent_4w: ([.[-4:][].total] | add),
    avg_week_12w: (([.[-12:][].total] | add) / 12 | floor),
    active_weeks_12w: ([.[-12:][] | select(.total > 0)] | length)
  }'
```

**Quality signal:** Steady weekly commits = maintained. Burst-then-silence = abandoned.
**Scoring:** 0=dead, 3=burst pattern, 6=sporadic, 10=steady weekly

## Signal 2: Owner vs Community Participation

```bash
gh api repos/OWNER/REPO/stats/participation \
  --jq '{
    all_52w: (.all | add),
    owner_52w: (.owner | add),
    community_52w: ((.all | add) - (.owner | add)),
    last_4w: (.all[-4:] | add),
    trend: (if (.all[-4:] | add) > (.all[-8:-4] | add) then "growing" else "declining" end)
  }'
```

**Gotcha:** `owner` counts org-account commits, not individual humans. Often 0 for org-owned repos.
**Scoring:** Growing + community participation = healthy

## Signal 3: Contributor Distribution

```bash
gh api repos/OWNER/REPO/stats/contributors \
  --jq '{
    total: length,
    top3: [sort_by(-.total) | .[:3][] | {login: .author.login, commits: .total}]
  }'
```

**Gotcha:** Capped at 100 contributors. For repos with more, you get top 100 only.
**Gotcha:** If `{}` persists after 3 retries with 5s sleep, mark "stats unavailable." Use `pushedAt` + `history(first:0){totalCount}` from GraphQL as proxy instead.
**Scoring:** 0=1 contributor, 5=2-5, 10=10+

## Signal 4: Code Churn (Additions/Deletions)

```bash
gh api repos/OWNER/REPO/stats/code_frequency \
  --jq '{
    recent_12w_add: ([.[-12:][] | .[1]] | add),
    recent_12w_del: ([.[-12:][] | .[2]] | add),
    churn_ratio: (if ([.[-12:][] | .[1]] | add) > 0 then (([.[-12:][] | .[2] | fabs] | add) * 100 / ([.[-12:][] | .[1]] | add) | floor) else 0 end)
  }'
```

**Scoring:** High deletions relative to additions = refactoring (can be good). Very high churn = unstable.

## Signal 5: Community Health Score

```bash
gh api repos/OWNER/REPO/community/profile \
  --jq '{
    health_pct: .health_percentage,
    license: (.files.license.spdx_id // "none"),
    readme: (if .files.readme then true else false end),
    coc: (if .files.code_of_conduct then true else false end),
    contributing: (if .files.contributing then true else false end),
    issue_template: (if .files.issue_template then true else false end),
    pr_template: (if .files.pull_request_template then true else false end)
  }'
```

**No GraphQL equivalent.** This is the single best REST signal.
**Scoring:** 0=<25%, 5=50%, 10=>75%

## Signal 6: CI Green Rate

```bash
gh api "repos/OWNER/REPO/actions/runs?per_page=20" \
  --jq '{
    total_runs: .total_count,
    recent_20: [.workflow_runs[:20][] | .conclusion] | group_by(.) | map({(.[0] // "null"): length}) | add
  }'
```

**Scoring:** 0=no CI, 5=<70% green, 8=70-85%, 10=>85%

## Signal 7 (Bonus): npm Downloads

Only for repos with a package.json:

```bash
# Step 1: Get package name
PKGNAME=$(gh api repos/OWNER/REPO/contents/package.json --jq '.content' | base64 -d | jq -r '.name')

# Step 2: Get downloads (if published)
curl -s "https://api.npmjs.org/downloads/point/last-week/$PKGNAME" | jq '.downloads'
```

**Scoring:** 0=not on npm, 3=<50/week, 6=50-500/week, 10=>500/week

## Total Cost Per Repo

~8-10 REST calls (including retries for 202s) + 1 bonus npm check = ~10 rate limit points.

## Known Issues

- `rtk` wrapper escapes `!=` in jq. Use `(if .field then true else false end)` instead of `.field != null`
- Branch protection (`branches/main/protection`) returns 404 without admin access — skip it
- Traffic endpoints (`traffic/clones`, `traffic/views`) require push access — skip it
- `stats/participation` owner=0 is normal for org-owned repos
