# GraphQL Repo Deep Dive

Single-repo "everything" query. Cost: 1 rate limit point. Copy-paste ready.

## The Query

Replace `OWNER` and `NAME` with the target repo.

```bash
gh api graphql -f query='{
  repository(owner:"OWNER",name:"NAME") {
    nameWithOwner description url homepageUrl
    stargazerCount forkCount diskUsage
    createdAt updatedAt pushedAt
    isArchived isDisabled isFork isTemplate visibility
    licenseInfo{spdxId name}
    primaryLanguage{name}
    languages(first:5,orderBy:{field:SIZE,direction:DESC}){
      totalSize edges{size node{name}}
    }
    repositoryTopics(first:15){nodes{topic{name}}}
    defaultBranchRef{
      name
      target{...on Commit{
        history(first:0){totalCount}
      }}
    }
    openIssues:issues(states:OPEN){totalCount}
    closedIssues:issues(states:CLOSED){totalCount}
    openPRs:pullRequests(states:OPEN){totalCount}
    mergedPRs:pullRequests(states:MERGED){totalCount}
    releases{totalCount}
    latestRelease:releases(first:1,orderBy:{field:CREATED_AT,direction:DESC}){
      nodes{tagName publishedAt isPrerelease}
    }
    discussions{totalCount}
    watchers{totalCount}
    mentionableUsers(first:0){totalCount}
    vulnerabilityAlerts{totalCount}
  }
  rateLimit{cost remaining}
}' --jq '.data.repository'
```

## Compact JQ Output

For token-efficient structured output:

```bash
--jq '
.data.repository |
  (.languages.totalSize) as $lt |
{
  repo: .nameWithOwner,
  stars: .stargazerCount,
  forks: .forkCount,
  watchers: .watchers.totalCount,
  disk_mb: ((.diskUsage // 0) / 1024 * 10 | floor / 10),
  created: .createdAt[:10],
  pushed: .pushedAt[:10],
  archived: .isArchived,
  license: (.licenseInfo.spdxId // "none"),
  lang: (.primaryLanguage.name // "?"),
  langs: [.languages.edges[:5][] | "\(.node.name) \(if $lt > 0 then (.size * 1000 / $lt | floor / 10) else 0 end)%"],
  topics: [.repositoryTopics.nodes[].topic.name],
  commits: .defaultBranchRef.target.history.totalCount,
  issues_open: .openIssues.totalCount,
  issues_closed: .closedIssues.totalCount,
  issue_close_pct: (if (.openIssues.totalCount + .closedIssues.totalCount) > 0 then (.closedIssues.totalCount * 100 / (.openIssues.totalCount + .closedIssues.totalCount) | floor) else 0 end),
  prs_merged: .mergedPRs.totalCount,
  releases: .releases.totalCount,
  latest_release: (.latestRelease.nodes[0].tagName // "none"),
  discussions: .discussions.totalCount,
  contributors: .mentionableUsers.totalCount,
  vuln_alerts: .vulnerabilityAlerts.totalCount
}'
```

## Fields Intentionally EXCLUDED

| Field | Why Excluded |
|---|---|
| `contributingGuidelines.body` | Token bomb — 6000+ chars. Check file existence via REST instead |
| `branchProtectionRules` | Returns empty `[]` without admin access on repo |
| `codeOfConduct` | Often null, low signal value |
| `fundingLinks` | Rarely populated |
| `description` (in batch) | Can be long; include only in single-repo queries |

## Gotchas

- `history(first:0){totalCount}` — Zero-cost trick for commit count without fetching nodes
- `releases(first:1,orderBy:{field:CREATED_AT,direction:DESC})` — Use `first:1` + `DESC` for newest. `last:1` + `DESC` returns OLDEST
- `(.languages.totalSize) as $lt` — Must capture as variable; nested `.edges[]` loses parent scope
- `mentionableUsers(first:0){totalCount}` — Contributor count proxy (no direct field exists)
- If repo doesn't exist: GraphQL returns errors array, not null. Check `.errors` in response
