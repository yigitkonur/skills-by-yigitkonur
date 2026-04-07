# GraphQL Batch Repos

Fetch N repos in ONE GraphQL call using fragments + aliases. Cost: 1 rate limit point regardless of N.

## Pattern

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
  r0:repository(owner:"OWNER0",name:"NAME0"){...R}
  r1:repository(owner:"OWNER1",name:"NAME1"){...R}
  r2:repository(owner:"OWNER2",name:"NAME2"){...R}
  r3:repository(owner:"OWNER3",name:"NAME3"){...R}
  r4:repository(owner:"OWNER4",name:"NAME4"){...R}
}'
```

## TSV Output

```bash
--jq '.data | to_entries[] | .value |
"\(.nameWithOwner)\t\(.stargazerCount)★\t\(.primaryLanguage.name // "?")\t\(.defaultBranchRef.target.history.totalCount) commits\tI:\(.openIssues.totalCount)/\(.closedIssues.totalCount)\tPR:\(.mergedPRs.totalCount)\tR:\(.releases.totalCount)\t\(.pushedAt[:10])"'
```

## Shell Function (Dynamic Building)

```bash
gh_batch_repo_stats() {
  local frag='fragment R on Repository { nameWithOwner stargazerCount forkCount pushedAt primaryLanguage{name} licenseInfo{spdxId} defaultBranchRef{target{...on Commit{history(first:0){totalCount}}}} openIssues:issues(states:OPEN){totalCount} closedIssues:issues(states:CLOSED){totalCount} mergedPRs:pullRequests(states:MERGED){totalCount} releases{totalCount} }'
  local q="$frag {"
  local i=0
  for repo in "$@"; do
    local owner="${repo%%/*}" name="${repo##*/}"
    q+=" r${i}:repository(owner:\"${owner}\",name:\"${name}\"){...R}"
    ((i++))
  done
  q+=" }"
  gh api graphql -f query="$q" --jq '.data | to_entries[] | .value | "\(.nameWithOwner)\t\(.stargazerCount)★\t\(.primaryLanguage.name // "?")\t\(.defaultBranchRef.target.history.totalCount) commits\tI:\(.openIssues.totalCount)/\(.closedIssues.totalCount)\tPR:\(.mergedPRs.totalCount)\tR:\(.releases.totalCount)\t\(.pushedAt[:10])"'
}

# Usage:
gh_batch_repo_stats owner1/repo1 owner2/repo2 owner3/repo3
```

## Limits

- Tested reliably up to 5 repos per batch
- Should work up to ~20 (GitHub's practical alias limit)
- Cost: always 1 rate limit point regardless of batch size
- If a repo doesn't exist: that alias returns error but others still succeed. Check `.errors[]`
