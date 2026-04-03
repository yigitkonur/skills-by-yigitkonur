# GraphQL User Profile

Deep author assessment. Single user, 6 years of contributions. Cost: 1 rate limit point.

## Pre-check: User vs Org

ALWAYS check first. `user()` errors on org logins:

```bash
gh api graphql -f query='{ repositoryOwner(login:"LOGIN") { __typename login ... on User { name createdAt } ... on Organization { name createdAt } } }' --jq '.data.repositoryOwner | "\(.__typename): \(.login)"'
```

If result is `Organization`, skip personal contribution queries.

## Full Author Profile Query

Replace `USERNAME` with the repo owner's login:

```bash
gh api graphql -f query='{
  user(login:"USERNAME") {
    login name bio company location createdAt
    followers{totalCount} following{totalCount}
    originalRepos:repositories(privacy:PUBLIC,isFork:false){totalCount}
    forkRepos:repositories(privacy:PUBLIC,isFork:true){totalCount}
    starredRepositories{totalCount}
    gists{totalCount}
    organizations(first:10){totalCount nodes{login}}
    repositoriesContributedTo(first:10,contributionTypes:[COMMIT,PULL_REQUEST],includeUserRepositories:false){totalCount nodes{nameWithOwner stargazerCount}}
    pinnedItems(first:6,types:[REPOSITORY]){nodes{...on Repository{nameWithOwner stargazerCount primaryLanguage{name}}}}
    topRepos:repositories(first:10,privacy:PUBLIC,isFork:false,orderBy:{field:STARGAZERS,direction:DESC}){nodes{nameWithOwner stargazerCount primaryLanguage{name} pushedAt isArchived}}
    isDeveloperProgramMember isGitHubStar hasSponsorsListing
    socialAccounts(first:5){nodes{provider url}}
    y2020:contributionsCollection(from:"2020-01-01T00:00:00Z",to:"2020-12-31T23:59:59Z"){totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}}
    y2021:contributionsCollection(from:"2021-01-01T00:00:00Z",to:"2021-12-31T23:59:59Z"){totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}}
    y2022:contributionsCollection(from:"2022-01-01T00:00:00Z",to:"2022-12-31T23:59:59Z"){totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}}
    y2023:contributionsCollection(from:"2023-01-01T00:00:00Z",to:"2023-12-31T23:59:59Z"){totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}}
    y2024:contributionsCollection(from:"2024-01-01T00:00:00Z",to:"2024-12-31T23:59:59Z"){totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}}
    y2025:contributionsCollection(from:"2025-01-01T00:00:00Z",to:"2025-12-31T23:59:59Z"){totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}}
  }
}'
```

## Compact JQ Output

```bash
--jq '.data.user | {
  login, name, company: (.company // "?"), location: (.location // "?"),
  joined: .createdAt[:10],
  followers: .followers.totalCount,
  orig_repos: .originalRepos.totalCount,
  fork_repos: .forkRepos.totalCount,
  fork_pct: (if (.originalRepos.totalCount + .forkRepos.totalCount) > 0 then (.forkRepos.totalCount * 100 / (.originalRepos.totalCount + .forkRepos.totalCount) | floor) else 0 end),
  starred: .starredRepositories.totalCount,
  orgs: .organizations.totalCount,
  upstream_contrib: .repositoriesContributedTo.totalCount,
  top_langs: [.topRepos.nodes[] | .primaryLanguage.name // "?" ] | unique,
  contributions: (to_entries | map(select(.key | startswith("y"))) | map({year: .key, commits: .value.totalCommitContributions, prs: .value.totalPullRequestContributions, reviews: .value.totalPullRequestReviewContributions, total: .value.contributionCalendar.totalContributions}))
}'
```

## Batch Users (up to 5, cost: 1 point)

Safe limits: **5 users x 3 years** OR **4 users x 4 years**.
Beyond this → `RESOURCE_LIMITS_EXCEEDED` error.

```bash
gh api graphql -f query='
fragment U on User {
  login name createdAt company
  followers{totalCount}
  originalRepos:repositories(privacy:PUBLIC,isFork:false){totalCount}
  forkRepos:repositories(privacy:PUBLIC,isFork:true){totalCount}
  starredRepositories{totalCount}
  repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST],includeUserRepositories:false){totalCount}
  topRepos:repositories(first:5,privacy:PUBLIC,isFork:false,orderBy:{field:STARGAZERS,direction:DESC}){nodes{nameWithOwner stargazerCount primaryLanguage{name}}}
  y2023:contributionsCollection(from:"2023-01-01T00:00:00Z",to:"2023-12-31T23:59:59Z"){totalCommitContributions contributionCalendar{totalContributions}}
  y2024:contributionsCollection(from:"2024-01-01T00:00:00Z",to:"2024-12-31T23:59:59Z"){totalCommitContributions contributionCalendar{totalContributions}}
  y2025:contributionsCollection(from:"2025-01-01T00:00:00Z",to:"2025-12-31T23:59:59Z"){totalCommitContributions contributionCalendar{totalContributions}}
}
{
  u0:user(login:"USER0"){...U}
  u1:user(login:"USER1"){...U}
  u2:user(login:"USER2"){...U}
  u3:user(login:"USER3"){...U}
  u4:user(login:"USER4"){...U}
}'
```

## Gotchas

- `organizations` REQUIRES `first:N` — bare `organizations` → error
- `projects` (classic) is DEPRECATED — use `projectsV2(first:N)` if needed
- `user()` REJECTS org logins — always pre-check with `repositoryOwner`
- `repositoriesContributedTo` misses email-patch contributors (torvalds shows 0)
- Contribution years before account creation may return data (git history backdating)
- `primaryLanguage` is null for non-code repos — always use `// "?"` fallback
