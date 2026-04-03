# Subagent Dispatch Guide

How to dispatch per-repo evaluation subagents for Phase 2.

## When to Dispatch

- **<=3 repos**: Evaluate inline in main context. No subagents.
- **4-15 repos**: One wave of parallel subagents.
- **16-30 repos**: Two waves (first 15, then rest).

## Subagent Prompt Template

For each repo, create a subagent with this prompt. Replace OWNER/REPO and USERNAME.

```
You are evaluating the GitHub repository OWNER/REPO for quality.

Run these commands and report ALL results. Prefix every command with rtk.

## 1. GraphQL Deep Dive (1 API call)

rtk gh api graphql -f query='{ repository(owner:"OWNER",name:"REPO") { nameWithOwner description url stargazerCount forkCount diskUsage createdAt updatedAt pushedAt isArchived isDisabled isFork visibility licenseInfo{spdxId name} primaryLanguage{name} languages(first:5,orderBy:{field:SIZE,direction:DESC}){totalSize edges{size node{name}}} repositoryTopics(first:15){nodes{topic{name}}} defaultBranchRef{name target{...on Commit{history(first:0){totalCount}}}} openIssues:issues(states:OPEN){totalCount} closedIssues:issues(states:CLOSED){totalCount} openPRs:pullRequests(states:OPEN){totalCount} mergedPRs:pullRequests(states:MERGED){totalCount} releases{totalCount} latestRelease:releases(first:1,orderBy:{field:CREATED_AT,direction:DESC}){nodes{tagName publishedAt}} discussions{totalCount} watchers{totalCount} mentionableUsers(first:0){totalCount} vulnerabilityAlerts{totalCount} } }' --jq '.data.repository'

## 2. REST Signals (retry if {} returned)

# Community health
rtk gh api repos/OWNER/REPO/community/profile --jq '{health_pct: .health_percentage, license: (.files.license.spdx_id // "none"), readme: (if .files.readme then true else false end), contributing: (if .files.contributing then true else false end), issue_tpl: (if .files.issue_template then true else false end)}'

# Commit consistency (52 weeks)
rtk gh api repos/OWNER/REPO/stats/commit_activity --jq '{total_52w: ([.[].total] | add), recent_12w: ([.[-12:][].total] | add), recent_4w: ([.[-4:][].total] | add), active_weeks_12w: ([.[-12:][] | select(.total > 0)] | length)}'

# If the above returns {}, wait 2 seconds and retry:
# sleep 2 && rtk gh api repos/OWNER/REPO/stats/commit_activity --jq '...'

# Contributors
rtk gh api repos/OWNER/REPO/stats/contributors --jq '{total: length, top3: [sort_by(-.total) | .[:3][] | {login: .author.login, commits: .total}]}'

# CI green rate
rtk gh api "repos/OWNER/REPO/actions/runs?per_page=20" --jq '{total_runs: .total_count, conclusions: [.workflow_runs[:20][] | .conclusion] | group_by(.) | map({(.[0] // "null"): length}) | add}'

## 3. Author Profile

First check if owner is User or Org:
rtk gh api graphql -f query='{ repositoryOwner(login:"USERNAME") { __typename } }' --jq '.data.repositoryOwner.__typename'

If User, run:
rtk gh api graphql -f query='{ user(login:"USERNAME") { login name bio company location createdAt followers{totalCount} originalRepos:repositories(privacy:PUBLIC,isFork:false){totalCount} forkRepos:repositories(privacy:PUBLIC,isFork:true){totalCount} starredRepositories{totalCount} organizations(first:10){totalCount} repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST],includeUserRepositories:false){totalCount} topRepos:repositories(first:5,privacy:PUBLIC,isFork:false,orderBy:{field:STARGAZERS,direction:DESC}){nodes{nameWithOwner stargazerCount primaryLanguage{name}}} isDeveloperProgramMember isGitHubStar hasSponsorsListing y2022:contributionsCollection(from:"2022-01-01T00:00:00Z",to:"2022-12-31T23:59:59Z"){totalCommitContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}} y2024:contributionsCollection(from:"2024-01-01T00:00:00Z",to:"2024-12-31T23:59:59Z"){totalCommitContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}} y2025:contributionsCollection(from:"2025-01-01T00:00:00Z",to:"2025-12-31T23:59:59Z"){totalCommitContributions totalPullRequestReviewContributions contributionCalendar{totalContributions}} } }' --jq '.data.user'

## 4. Code-Level Analysis

# README content (first 100 lines)
rtk gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | head -100

# Key files present
rtk gh api repos/OWNER/REPO/contents/ --jq '[.[].name]'

# Recent commits (quality check)
rtk gh api "repos/OWNER/REPO/commits?per_page=10" --jq '.[] | "\(.commit.author.date[:10])\t\(.author.login // .commit.author.name)\t\(.commit.message | split("\n")[0] | .[:60])"'

## 5. Score and Report

After collecting all data, provide a structured report:

METRICS:
- stars: X
- commits: X
- issues: X open / X closed (X% close rate)
- PRs merged: X
- releases: X
- community health: X%
- commit consistency: steady/sporadic/burst/dead
- CI green rate: X%
- contributors: X
- author: joined YYYY, X followers, X% fork ratio, pre-2024 activity: X commits
- README quality: minimal/solid/comprehensive
- key files: [list]
- red flags: [list or "none"]

QUALITATIVE NOTES:
- 2-3 sentences about what stands out (good and bad)
```

## Agent Configuration

```python
# When dispatching subagents:
Agent(
    model="sonnet",           # Sonnet is sufficient for data collection
    mode="bypassPermissions", # Needs to run gh commands
    run_in_background=True,   # Parallel execution
)
```

## Collecting Results

After all subagents complete, the main agent reads each result and feeds into the scoring rubric. Look for:
- Missing data (API errors, 404s) → score 0 for that metric
- Null fields → use defaults from scoring-rubric.md
- Org owners → skip personal author metrics, score author section at 50% (neutral)
