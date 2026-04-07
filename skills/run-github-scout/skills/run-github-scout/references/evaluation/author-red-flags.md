# Author Red Flags

Detection patterns for author quality concerns.

## Flag 1: Fork-Heavy Profile (penalty: -5)

```bash
gh api graphql -f query='{ user(login:"USERNAME") { originalRepos:repositories(privacy:PUBLIC,isFork:false){totalCount} forkRepos:repositories(privacy:PUBLIC,isFork:true){totalCount} } }' --jq '.data.user | {orig: .originalRepos.totalCount, forks: .forkRepos.totalCount, pct: (if (.originalRepos.totalCount + .forkRepos.totalCount) > 0 then (.forkRepos.totalCount * 100 / (.originalRepos.totalCount + .forkRepos.totalCount) | floor) else 0 end)}'
```

**Threshold:** >50% forks = red flag
**False positive:** Corporate devs (gaearon at 70% from Facebook work). Context matters.

## Flag 2: AI-Wave-Only (penalty: -3)

```bash
gh api graphql -f query='{ user(login:"USERNAME") { createdAt y2022:contributionsCollection(from:"2022-01-01T00:00:00Z",to:"2022-12-31T23:59:59Z"){contributionCalendar{totalContributions}} y2023:contributionsCollection(from:"2023-01-01T00:00:00Z",to:"2023-12-31T23:59:59Z"){contributionCalendar{totalContributions}} } }' --jq '.data.user | {joined: .createdAt[:10], pre_ai_2022: .y2022.contributionCalendar.totalContributions, pre_ai_2023: .y2023.contributionCalendar.totalContributions}'
```

**Threshold:** Account created 2024+ AND combined 2022+2023 contributions = 0
**Note:** Not inherently bad, but flags inexperience. Informational.

## Flag 3: Stale Graveyard (penalty: -3)

```bash
gh search repos --owner=USERNAME --json stargazersCount,pushedAt --jq '[.[] | select(.stargazersCount == 0)] | length'
```

**Threshold:** 10+ repos with 0 stars = mild flag. 20+ = stronger flag.

## Flag 4: No License (penalty: -2)

Detected in the main repo query: `licenseInfo.spdxId` is null.

## Flag 5: Archived/Disabled (penalty: -10)

Detected in the main repo query: `isArchived` or `isDisabled` is true.

## Known False Positives

- **torvalds**: 0 `repositoriesContributedTo` despite being Linux creator (works via email, not GH PRs)
- **gaearon**: 70% fork ratio (corporate React work at Facebook)
- **antirez**: 0 PR reviews (solo craftsman style, Redis is maintained without GH PR process)

**Rule:** Red flags are signals, not verdicts. Always note the flag AND the possible explanation.
