# Editorial Workflow for a Multi-editor Team

Setup for a team using TinaCloud Team Plus+ with branch-based PR review.

## Prerequisites

- TinaCloud Team Plus+ ($49/mo) or higher
- Vercel project with preview deployments enabled
- Multiple editors needing approval flow

## Concept

Editors don't save directly to `main`. Instead:

1. Editor saves on a protected branch
2. TinaCloud auto-creates a feature branch + draft PR
3. Editor continues editing on their branch (with Vercel preview)
4. Reviewer approves via GitHub
5. Merge → content publishes to `main` → site rebuilds

Mirrors how engineering teams work, applied to content.

## Setup steps

### 1. Enable Editorial Workflow

TinaCloud → Project Settings → Configuration → Editorial Workflow:

- Toggle **Enable**
- Protected branches: `main` (or your prod branch)
- Refresh

### 2. Configure preview URLs

```typescript
// tina/config.ts
ui: {
  previewUrl: (context) => ({
    url: `https://${process.env.VERCEL_PROJECT_NAME}-git-${context.branch}.vercel.app`,
  }),
}
```

Pattern depends on your Vercel team — check a real preview URL and template it.

### 3. Vercel preview deployments

Vercel auto-creates preview deployments per branch. Verify in Project Settings → Git:

- Preview Deployments: Enabled (default)
- Branches: All non-prod branches

### 4. Invite editors

TinaCloud → Project Settings → Users → Invite. They'll sign in via TinaCloud OAuth.

Each editor needs **GitHub write access** to the repo (otherwise their saves to feature branches fail). Add as collaborators or team members.

### 5. Brief editors on the workflow

Editor instructions:

1. Visit `/admin`
2. Open a document
3. Click Save
4. **Modal appears: "Save to a new branch?"** → enter a branch name (e.g. `tina/draft-2026-05-08-launch-update`)
5. Continue editing on this branch
6. When ready: click "View Pull Request" → review on GitHub → merge

## Branch naming conventions

TinaCloud auto-suggests branch names like `tina/draft-<date>-<random>`. You can override per-save or stick with auto.

For team-wide conventions, use prefixes:

- `tina/feat/<description>` for new content
- `tina/fix/<description>` for corrections
- `tina/edit/<description>` for general edits

Editors type the prefix; TinaCloud handles the rest.

## Reviewer workflow

Reviewers see the PR in GitHub:

1. Visit the draft PR
2. Click the Vercel preview link → see the changes live
3. Review file diffs
4. Comment / request changes via GitHub
5. Approve and merge

Engineering and content teams use the same review loop.

## Multi-editor concurrency

Two editors can edit the same document on different branches:

- Each has their own preview URL
- Independent saves to their respective branches
- When merging the second PR, GitHub resolves conflicts (or asks the merger to)

For coordinated edits (two editors collaborating on the same change), have them work on the same branch. The admin's branch switcher shows existing branches.

## CI integration

Add status checks on the PR:

- Vercel preview deployment status
- Lighthouse score (via `vercel-lighthouse-action`)
- Schema audit (`pnpm dlx @tinacms/cli@latest audit`)

Configure required checks before merge.

## Audit log

Every PR is the audit:

- Who made the change → PR author
- What changed → diff
- When → PR creation/merge timestamps
- Why → commit messages, PR description

Combined with TinaCloud's user dashboard (showing who logged in), you have full attribution.

## Cost considerations

Team Plus tier is $49/mo for 5 users. For 6+ editors, you pay extra per seat or move to Business.

Alternative for large teams: self-hosted TinaCMS with manual PR-based workflow (no Editorial Workflow magic). More friction but no per-seat cost.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Editor doesn't see "Save to branch?" modal | Editorial Workflow not enabled, or branch not protected | Re-check TinaCloud settings |
| Branch switcher missing | Editor's tier doesn't have it | Confirm tier is Team Plus+ |
| Preview URL doesn't match Vercel | `previewUrl` template wrong | Adjust to match Vercel's pattern |
| Editor's saves fail | They lack GitHub write access | Add as repo collaborator |
| Conflicts on merge | Two editors changed the same field | Resolve manually in GitHub |

## When NOT to use Editorial Workflow

- Single editor on a small site (overhead not worth it)
- All edits go through a designated person who knows git
- Free / Team tier (not available)

For solo + small projects, just save directly to `main`. Editorial Workflow shines with 3+ editors needing review.

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot `previewUrl` config | No preview link in admin | Add to `ui` in `tina/config.ts` |
| Editor without GitHub write access | Saves fail | Add as collaborator |
| Vercel preview deployments disabled | No previews | Enable in Vercel project settings |
| Used Editorial Workflow on free tier | Not available | Upgrade to Team Plus |
| Forgot to brief editors on the new flow | Confusion | Provide workflow doc |
