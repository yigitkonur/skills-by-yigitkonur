# Optional Single-Repo Deep Dive

Use this only for a top candidate when lightweight signals are not enough.

## Query

```bash
gh api graphql -f query='{
  repository(owner:"OWNER",name:"REPO") {
    nameWithOwner
    description
    url
    stargazerCount
    createdAt
    pushedAt
    isArchived
    isDisabled
    licenseInfo { spdxId }
    primaryLanguage { name }
    repositoryTopics(first:15) { nodes { topic { name } } }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first:0) { totalCount }
        }
      }
    }
    openIssues: issues(states:OPEN) { totalCount }
    mergedPRs: pullRequests(states:MERGED) { totalCount }
    releases { totalCount }
    latestRelease: releases(first:1, orderBy:{field:CREATED_AT, direction:DESC}) {
      nodes { tagName publishedAt }
    }
    mentionableUsers(first:0) { totalCount }
  }
}' --jq '.data.repository'
```

## What this answers

- topic vocabulary the repo uses about itself
- rough commit volume
- issue, PR, and release activity
- contributor count proxy
- whether maintenance looks healthy enough for the shortlist

## Rule

Use this on the top few repos only. If the markdown shortlist is already clear, skip it.
