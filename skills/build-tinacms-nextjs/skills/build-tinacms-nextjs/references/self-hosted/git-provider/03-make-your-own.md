# Custom Git Provider

For GitLab, Bitbucket, on-prem git, or non-git stores, implement the git provider interface yourself. Non-trivial.

## Interface

```typescript
import type { GitProvider } from '@tinacms/datalayer'

class MyCustomProvider implements GitProvider {
  async pull(): Promise<{ content: string; sha: string }> { /* ... */ }
  async put(path: string, content: string, message: string, author?: any): Promise<void> { /* ... */ }
  async delete(path: string, message: string, author?: any): Promise<void> { /* ... */ }
  async getFile(path: string): Promise<{ content: string; sha: string }> { /* ... */ }
}
```

The exact interface may vary by `@tinacms/datalayer` version — check the type definitions.

## Implementation example: GitLab

```typescript
import type { GitProvider } from '@tinacms/datalayer'

class GitLabProvider implements GitProvider {
  constructor(private config: {
    projectId: string
    branch: string
    token: string
    apiUrl: string  // e.g. https://gitlab.com/api/v4
  }) {}

  async getFile(path: string) {
    const res = await fetch(
      `${this.config.apiUrl}/projects/${this.config.projectId}/repository/files/${encodeURIComponent(path)}?ref=${this.config.branch}`,
      { headers: { 'PRIVATE-TOKEN': this.config.token } },
    )
    const data = await res.json()
    return {
      content: Buffer.from(data.content, 'base64').toString('utf-8'),
      sha: data.blob_id,
    }
  }

  async put(path: string, content: string, message: string) {
    await fetch(
      `${this.config.apiUrl}/projects/${this.config.projectId}/repository/files/${encodeURIComponent(path)}`,
      {
        method: 'PUT',
        headers: {
          'PRIVATE-TOKEN': this.config.token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          branch: this.config.branch,
          commit_message: message,
          content,
          encoding: 'text',
        }),
      },
    )
  }

  async delete(path: string, message: string) {
    await fetch(
      `${this.config.apiUrl}/projects/${this.config.projectId}/repository/files/${encodeURIComponent(path)}`,
      {
        method: 'DELETE',
        headers: {
          'PRIVATE-TOKEN': this.config.token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          branch: this.config.branch,
          commit_message: message,
        }),
      },
    )
  }

  async pull() {
    // Implement pulling latest state — read all files, return aggregated content
    // (more complex; see GitHub provider source for reference)
  }
}
```

## Use it

```typescript
// tina/database.ts
import { GitLabProvider } from './git-providers/gitlab'

createDatabase({
  gitProvider: new GitLabProvider({
    projectId: process.env.GITLAB_PROJECT_ID!,
    branch: process.env.GITLAB_BRANCH || 'main',
    token: process.env.GITLAB_TOKEN!,
    apiUrl: process.env.GITLAB_API_URL || 'https://gitlab.com/api/v4',
  }),
  databaseAdapter: /* ... */,
})
```

## What you have to handle

- **Auth** with the git host's API
- **Conflict handling** when commits race
- **Pagination** for large repos (when listing files)
- **Branch operations** (create, list, delete)
- **File encoding** (base64 vs utf-8)
- **Error semantics** (translate provider-specific errors to TinaCMS' expected shape)
- **Retry / backoff** for rate-limited APIs

## Test thoroughly

```typescript
// Roundtrip test
const provider = new GitLabProvider(/* ... */)
await provider.put('test.md', '# Hello', 'Test commit')
const { content } = await provider.getFile('test.md')
console.assert(content === '# Hello', 'Content mismatch')
await provider.delete('test.md', 'Cleanup')
```

Run before going to production.

## When to consider custom

Custom git providers are **a lot of work**. Consider alternatives first:

- **Mirror GitHub repo to GitLab/Bitbucket** — keep TinaCMS pointing at GitHub, mirror to your preferred host
- **Use GitHub's API for write-only, your preferred host for storage** — feasible but unusual
- **Negotiate to use GitHub** — sometimes the easier conversation

Only build custom if you're committed to the platform.

## Reference implementations

Open-source examples in TinaCMS repo or community:

- `tinacms-gitprovider-github` (TinaCMS official) — best reference
- Community-maintained GitLab/Bitbucket providers (may exist; check Discord)

Read source before writing your own — the interface has subtle requirements.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot `pull()` implementation | Indexing fails | Implement pulling all repo files |
| Returned wrong shape from `getFile` | Content corrupt on read | Match `{ content, sha }` exactly |
| Ignored `author` parameter | All commits attributed to PAT | Use the author when present |
| Didn't handle rate limits | Cascading failures during indexing | Add backoff |
| Hardcoded branch | Editorial workflow doesn't work (if you build that) | Make branch a parameter |
