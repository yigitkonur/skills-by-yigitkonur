# GitHub Git Provider

The default git provider for self-hosted TinaCMS. Uses the GitHub REST API with a Personal Access Token.

## Install

```bash
pnpm add tinacms-gitprovider-github
```

## Configuration

```typescript
// tina/database.ts
import { GitHubProvider } from 'tinacms-gitprovider-github'

const gitProvider = new GitHubProvider({
  branch: process.env.GITHUB_BRANCH || 'main',
  owner: process.env.GITHUB_OWNER!,
  repo: process.env.GITHUB_REPO!,
  token: process.env.GITHUB_PERSONAL_ACCESS_TOKEN!,
})
```

Pass to `createDatabase`:

```typescript
createDatabase({
  gitProvider,
  databaseAdapter: /* ... */,
})
```

## Required env vars

```env
GITHUB_OWNER=your-username-or-org
GITHUB_REPO=your-repo-name
GITHUB_BRANCH=main
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxx
```

## Personal Access Token (PAT)

### Classic PAT

GitHub Settings → Developer settings → Personal access tokens (classic) → Generate.

Required scope: `repo` (full repo access). The provider needs read + write access to:

- Repo contents (read/write files)
- Branches (push commits)

### Fine-grained PAT (recommended)

GitHub Settings → Developer settings → Personal access tokens → Fine-grained.

Settings:

| Field | Value |
|---|---|
| Expiration | 90 days (set calendar reminder to rotate) |
| Repository access | Only the specific repo |
| Repository permissions | Contents: Read and write |

Fine-grained PATs are more secure (scoped to specific repos) but can be more brittle to manage.

## GitHub App alternative

For organization-wide deployments, use a GitHub App instead:

1. Create a GitHub App owned by your org
2. Install on the target repo(s)
3. Use the App's installation token

The provider supports App tokens via custom config — see `tinacms-gitprovider-github` README.

## Author attribution

To attribute commits to the editor (rather than the PAT's identity):

```typescript
new GitHubProvider({
  branch,
  owner,
  repo,
  token,
  // Set author from the editor's session
  author: (user: any) => ({
    name: user?.username || 'Tina Editor',
    email: user?.email || 'tina@example.com',
  }),
})
```

The `user` object comes from the auth provider's session (Auth.js, Clerk, etc.).

## Branch protection

If your branch has protection rules requiring:

- PR reviews → use a non-protected branch (or remove the rule for self-hosted)
- Signed commits → not directly supported via PAT (use App-based commits)
- Status checks → may pass-through (test before deploying)

For Editorial Workflow alternatives, use an unprotected branch + manual PR creation.

## Rate limits

GitHub API limits:

- PAT: 5,000 requests/hour
- App: 5,000-15,000 depending on plan

For typical editorial use, well under the limit. Heavy automation (bulk imports) may hit it.

## Custom commit message

Default commit messages are auto-generated:

```
Update content/posts/launch.md
```

To customize:

```typescript
new GitHubProvider({
  // ...
  commitMessage: (path, action, user) => {
    return `${action} ${path}\n\nEditor: ${user?.username}`
  },
})
```

(Verify the API in the package's docs.)

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| 401 Unauthorized | PAT expired or revoked | Regenerate |
| 403 with "must have admin permissions" | PAT scope too narrow | Use full `repo` scope |
| 404 Not Found | Wrong owner/repo | Re-check env vars |
| 422 validation | Invalid commit content | Check the doc being saved |
| 409 conflict | Branch HEAD changed | TinaCMS retries; increase backoff |
| Commits attributed to bot account | Forgot `author` config | Add author function |

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Used `repo:public` scope (read-only) | Saves fail | Use full `repo` write scope |
| PAT rotated but env not updated | 401 on save | Update Vercel env + redeploy |
| Wrong owner (org vs user) | 404 | Match exactly what GitHub shows |
| Branch protection without exception | Saves blocked | Remove protection or use a different branch |
| App-based commits with PAT config | Wrong auth flow | Use App SDK instead |
