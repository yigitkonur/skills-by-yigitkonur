# Editorial Workflow (Team Plus+)

Branch-based PR review for content changes. Editors edit on per-editor branches, draft PRs auto-open, and merging the PR publishes content. Available on Team Plus tier and above.

## Setup

In TinaCloud Project Settings → Configuration:

1. Toggle **Enable Editorial Workflow**
2. Specify **protected branches** (typically `main`)
3. Refresh the page

After enabling, the admin shows a branch switcher in the top bar.

## How editors interact with it

When an editor saves on a protected branch:

1. A modal prompts them to enter a new branch name (or auto-generates one like `tina/draft-2026-05-08-abc123`)
2. TinaCloud creates the new branch
3. Indexes content on the branch
4. Saves the change to that branch
5. Auto-creates a draft pull request

The editor continues editing on their branch. Subsequent saves go to the same branch.

## Publishing

To publish:

1. Click the branch switcher → "View Pull Request"
2. Review the PR on GitHub
3. Merge to the protected branch

Once merged, the content is on `main` and gets indexed. The site rebuilds (if you've wired up a webhook).

## Per-branch preview deployments

Vercel auto-creates preview deployments per branch. Configure `previewUrl` in `tina/config.ts`:

```typescript
ui: {
  previewUrl: (context) => ({
    url: `https://my-app-git-${context.branch}.vercel.app`,
  }),
}
```

The admin shows a "Preview" link that opens the live preview for that branch.

## Multi-editor workflow

Multiple editors can have their own branches:

- Editor A: `tina/draft-content-page-update-abc`
- Editor B: `tina/draft-blog-post-fix-def`

Each branch is independent. Merging happens via PR review.

## Conflicts

If two editors edit the same field on the same document on different branches:

- Both branches have valid content
- Merging the second PR creates a git merge conflict
- The merger resolves the conflict in their git client

Conflict-resolution UX is the same as any GitHub PR conflict — TinaCMS doesn't auto-resolve.

## CI integration

Each draft branch triggers a Vercel preview deployment. Configure the production deploy to fire only on the protected branch:

```
Vercel: production environment → Branch = main
        preview environment → Branch = (any non-main)
```

Standard Vercel behavior — no extra config.

## Branch switcher UX

The admin's branch switcher (top bar) shows:

- Currently selected branch
- Dropdown of all branches the editor has touched
- Per-branch links: "View Pull Request" (when PR exists)

## When to skip Editorial Workflow

- Solo editor on a small site (overhead not worth it)
- All edits go through git locally (PRs are made by hand)
- Free / Team tier (not available)

For most multi-editor sites, enabling Editorial Workflow pays for itself in saved review time.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Editor on free tier | Editorial Workflow disabled | Upgrade to Team Plus |
| Forgot to set protected branches | Saves go directly to main | Set in Configuration tab |
| Forgot `previewUrl` | No preview link in admin | Add `ui.previewUrl` |
| Vercel preview disabled per-branch | Each editor's branch has no preview | Enable Vercel preview for all branches |
| Merging PR doesn't trigger production deploy | Content not on prod | Verify Vercel deploy hook + branch matching |
