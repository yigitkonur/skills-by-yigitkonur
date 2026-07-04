# Git Provider Overview

The git provider abstraction lets you swap how TinaCMS commits content. GitHub is the only first-party option; others require custom implementation.

## Available

| Provider | Package | Status |
|---|---|---|
| GitHub | `tinacms-gitprovider-github` | First-party, supported |
| GitLab | – | Custom implementation |
| Bitbucket | – | Custom implementation |
| On-prem git | – | Custom implementation |

For the standard self-hosted path, use GitHub. See `references/self-hosted/git-provider/02-github.md`.

## When to use a custom provider

- Your org uses GitLab/Bitbucket/Gitea
- On-prem git server
- Non-git stores (rare — usually you keep git as the canonical store)

Implementing a custom provider is non-trivial. See `references/self-hosted/git-provider/03-make-your-own.md`.

## How TinaCMS uses the git provider

For each content save:

1. Backend resolves the document file path (e.g. `content/posts/launch.md`)
2. Calls `gitProvider.put(path, contents, message, author)`
3. Provider commits and pushes

For deletes:

1. Backend resolves path
2. Calls `gitProvider.delete(path, message, author)`

Reads don't go through the git provider — only writes. Reads come from the indexed DB.

## Branch handling

The git provider commits to the configured branch:

```typescript
new GitHubProvider({
  branch: process.env.GITHUB_BRANCH || 'main',
  // ...
})
```

For Editorial Workflow alternatives in self-hosted (since editorial workflow itself isn't available): editors work on feature branches manually, you wire branch selection into your DIY workflow.

## Author attribution

The git provider sets the commit author:

```typescript
new GitHubProvider({
  // ... base config
  author: (user) => ({
    name: user.username,
    email: user.email,
  }),
})
```

Without this, commits use the GitHub PAT's identity (typically a bot account). With per-user attribution, each editor's identity appears in `git log`.

## Performance

Git operations:

- `put` (commit + push): ~500-2000ms (GitHub API roundtrip)
- `delete`: ~500-1000ms

These are slower than DB writes. For high-frequency editing (e.g. live preview that auto-saves), don't commit on every keystroke — TinaCMS batches saves intelligently.

## Failure modes

| Failure | Cause | Fix |
|---|---|---|
| 401 on push | PAT expired or wrong scopes | Regenerate PAT |
| 422 (validation) | Invalid commit (e.g. binary file content) | Check the content being saved |
| 5xx | GitHub API down | Retry; TinaCMS has built-in backoff |
| Branch protection blocks | Required reviews on the branch | Use a non-protected branch or remove protection |

Always handle these in your auth provider's user feedback — let editors know when a commit fails.

## See also

- `references/self-hosted/git-provider/02-github.md` — GitHub provider details
- `references/self-hosted/git-provider/03-make-your-own.md` — Custom git provider
- `references/tinacloud/09-git-co-authoring.md` — How TinaCloud handles per-editor identity (similar concept)
