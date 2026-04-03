# Getting Started with Devin Review

Complete setup guide for enabling Devin Review (Bug Catcher) on your GitHub repositories.

---

## What Devin Review Is

Devin Review is an AI code review tool by Cognition Labs that integrates with GitHub PRs. It analyzes diffs using the Bug Catcher engine, classifies findings as **Bugs** (severe / non-severe) or **Flags** (investigate / informational), and posts inline comments synced to GitHub.

Three ways to access Devin Review:

| Method | Who | How |
|--------|-----|-----|
| **Web dashboard** | Devin users | `https://app.devin.ai/review` — shows all open PRs grouped by assignment |
| **URL swap** | Anyone (public PRs) | Replace `github.com` with `devinreview.com` in any PR URL |
| **CLI** | Anyone with repo access | `npx devin-review <PR-URL>` inside a local clone |

---

## Prerequisites

1. **GitHub account** with access to the repositories you want to review
2. **Devin account** at `https://app.devin.ai` — sign up and connect your GitHub identity
3. **Organization admin access** (for org-wide auto-review and auto-fix configuration)
4. **Private dependency access** — if your project uses private npm registries, pip indexes, or Go module proxies, ensure Devin has the necessary credentials or network access to resolve them during analysis

---

## Step-by-Step Setup

### 1. Install the Devin GitHub App

1. Navigate to your Devin organization settings or the GitHub Marketplace listing for Devin
2. Click **Install** → select your GitHub organization or personal account
3. Choose repository scope:
   - **All repositories** — Devin can review any repo in the org
   - **Only select repositories** — pick specific repos
4. Grant the requested permissions:
   - Read access to PRs, comments, and metadata
   - Write access to reviews and comments
5. Complete the installation — webhook auto-configures for PR events

### 2. Enroll for Auto-Review

Auto-review means Devin automatically reviews PRs without manual trigger. Two enrollment paths:

#### Self-Enrollment (Any User)

1. Go to `Settings > Review` in the Devin dashboard
2. Click **"Add myself (@yourusername)"**
3. Alternatively, from any PR page, click the settings icon and toggle **"Me (@username)"**

No admin rights required. Once enrolled, Devin auto-reviews PRs where you are the author, reviewer, or assignee.

#### Admin Enrollment

Organization admins can configure broader auto-review:

| Setting | Location | Effect |
|---------|----------|--------|
| **Add repositories** | `Settings > Review > Repositories` | Auto-review **all** PRs in selected repos |
| **Add users** | `Settings > Review > Users` | Auto-review PRs for specific GitHub usernames |
| **Insert link in PR description** | `Settings > Review` (enabled by default) | Adds a Devin Review link to every PR body |

### 3. Configure Custom Review Rules (Optional)

By default, Devin reads `**/REVIEW.md` files. To add additional instruction file patterns:

1. Go to `Settings > Review > Review Rules`
2. Type a glob pattern (e.g., `docs/**/*.md`, `*.review-rules`)
3. Click **Add**

Devin also automatically reads these files when present:

| File | Pattern | Purpose |
|------|---------|---------|
| `REVIEW.md` | `**/REVIEW.md` | Primary review guidelines (always read) |
| `AGENTS.md` | `**/AGENTS.md` | Agent behavior instructions |
| `CLAUDE.md` | `**/CLAUDE.md` (case-insensitive) | Claude-specific coding standards |
| `CONTRIBUTING.md` | `**/CONTRIBUTING.md` (case-insensitive) | Contribution workflow and standards |
| `.cursorrules` | Root only | Cursor IDE rules |
| `.windsurfrules` | Root only | Windsurf IDE rules |
| `.cursor/rules` | Directory | Cursor directory rules |
| `*.rules` | Any level | Custom rule files |
| `*.mdc` | Any level | Markdown configuration files |
| `.coderabbit.yaml` / `.coderabbit.yml` | Root only | Existing review-tool configuration that may overlap with your guidance |
| `greptile.json` | Root only | Existing review-tool configuration that may overlap with your guidance |

Files inside agent-style subdirectories such as `.agents/`, `.devin/`, `.cursor/`, and `.github/` are treated as belonging to their parent directory for scoping purposes. For example, `src/.agents/REVIEW.md` scopes to `src/`.

### 4. Create Your REVIEW.md

Create a `REVIEW.md` file at the root of your repository. This is the primary mechanism for customizing what the Bug Catcher looks for.

Start with a root `REVIEW.md`. Add scoped `REVIEW.md` files later only when a subdirectory has materially different review risks that do not belong in the root file.

```markdown
# Review Guidelines

## Critical Areas
- All changes to `src/auth/` must be reviewed for security implications.

## Conventions
- All public functions require explicit return types.

## Ignore
- Auto-generated files in `src/generated/` do not need review.
```

See `references/review-md/format-and-directives.md` for the complete format specification.

### 5. Enable Auto-Fix (Optional)

Auto-Fix lets Devin propose code changes alongside bug findings:

| Method | Location | Who Can |
|--------|----------|---------|
| **Per-PR toggle** | PR review settings popover → **Enable Autofix** | Any reviewer |
| **Embedded view** | Devin Review view → settings popover → **Enable Autofix** | Any reviewer |
| **Global setting** | `Settings > Customization > Pull request settings > Autofix settings` | Org admins only |

Global Auto-Fix modes:

- **Respond to specific bots only** → add `devin-ai-integration[bot]` to the allow-list
- **Respond to all bot comments** → Auto-Fix triggers on any bot comment

When Auto-Fix is enabled globally, the per-PR toggle appears enabled but is immutable.

### 6. Verify Setup

Open a test PR (or push a commit to an existing PR) and confirm:

1. Devin posts a review within 2-5 minutes
2. Findings are classified as Bugs or Flags
3. Inline comments appear on the correct diff lines
4. If Auto-Fix is enabled, code suggestions appear alongside bug findings

> Having issues? See `references/troubleshooting/common-issues.md`

### First PR Checklist

After setup, open a real (or canary) PR and verify:

- [ ] Devin posts inline comments on the PR diff
- [ ] Comments reference specific `REVIEW.md` sections (not generic advice)
- [ ] Critical violations (e.g., security, data loss) are flagged as **Bugs**
- [ ] Ignore patterns work — no comments on generated/excluded files
- [ ] No false positives on auto-generated code (protobuf, OpenAPI, etc.)

**Expected results:** 2–5 minute review latency, findings classified as Bug or Flag, comments on correct diff lines.

**Tip:** Keep a dedicated "canary PR" branch with known issues to re-test after any `REVIEW.md` change.

---

## Setting Up for Teams

**Rollout strategy:**

1. Start with one developer self-enrolled — validate signal quality
2. After ~5 reviewed PRs, assess findings accuracy
3. Hold a 15-minute team review of Devin's findings — calibrate expectations
4. Expand enrollment incrementally (more users → more repos)

**Common pitfalls:**

- **Too many rules at once** — start with 3–5 critical rules, add more after validation
- **Not explaining to the team** — share what Devin checks and what it ignores
- **Ignoring false positives** — add ignore patterns promptly or the team loses trust

---

## Upgrading Your Configuration

Revisit `REVIEW.md` when:

- **Monthly audit** — prune stale rules, adjust severity based on real findings
- **Post-incident** — add rules that would have caught the issue
- **Post-tool-adoption** — update for new linters, formatters, or frameworks
- **Post-refactor** — update file paths, module names, and ignore patterns

**Upgrade workflow:**

1. Branch → edit `REVIEW.md` → open a test PR against the branch
2. Verify Devin applies updated rules correctly
3. Merge to main

---

## Reviewing PRs from Forks

- The base repository's `REVIEW.md` applies to all fork PRs — fork contributors cannot override it
- Consider this when writing rules: fork authors may not know your internal conventions
- Link your `REVIEW.md` in `CONTRIBUTING.md` so external contributors understand review expectations

---

## Auto-Review Triggers

Devin auto-reviews when any of these events occur:

| Event | Behavior |
|-------|----------|
| **PR opened** (non-draft) | Full review of the PR diff |
| **Commits pushed** to an open PR | Incremental review of new changes |
| **Draft marked ready** | Full review triggered |
| **Enrolled user added** as reviewer or assignee | Review triggered for that PR |

Draft PRs are ignored until marked ready for review.

---

## CLI Setup

For local review (useful for private repos or pre-push checks):

```bash
# Install and run in one command
cd path/to/repo
npx devin-review https://github.com/owner/repo/pull/123
```

How the CLI works:

1. **Git-based diff extraction** — reads local git history for the PR branch
2. **Isolated worktree checkout** — creates a temporary `git worktree` (no stashing or branch switching)
3. **Diff sent to Devin servers** for analysis
4. **Security** — starts a localhost server with a secure token; only local processes can use it
5. **Cleanup** — worktree is automatically removed after review completes

Read-only operations permitted in the worktree: `ls`, `cat`, `pwd`, `file`, `head`, `tail`, `wc`, `find`, `tree`, `stat`, `du`, plus grep/glob pattern searches.

If you're logged into a Devin account with org access, the CLI session can be transferred to that account for multi-device sharing.

---

## Permissions Reference

| Action | Who |
|--------|-----|
| Write `REVIEW.md` | Anyone with repo write access |
| Self-enroll for auto-review | Any user with connected GitHub |
| Add repos for auto-review | Org admins |
| Add users for auto-review | Org admins |
| Enable auto-fix | Org admins |
| Configure custom review rule patterns | `Settings > Review` |
| View review dashboard | Any enrolled user |

### Enterprise Scope

- Settings propagate across all orgs in the enterprise
- Only primary org admins can edit org-wide settings
- Non-primary org members can only self-enroll

### Comment Attribution

| Action | Attributed To |
|--------|---------------|
| Bug/Flag comments from auto-review | `devin-ai-integration[bot]` |
| User comments in Devin Review UI | User's GitHub identity |
| Commits from user-initiated chat edits | `devin-ai-integration[bot]` |
| GitHub Suggested Changes | Standard GitHub attribution |

---

## Auto-Review Limitations

- **Not available** for public repos that aren't connected to your Devin organization
- **Large PRs** (500+ changed lines) may take longer or hit token limits — consider breaking into smaller PRs
- **Draft PRs** are skipped until marked ready for review
- **"No Issues Found"** summary comments do not trigger Auto-Fix

---

## Dashboard Overview

The Devin Review dashboard at `https://app.devin.ai/review` displays:

- **Assigned to you** — PRs where you are an assignee
- **Authored by you** — PRs you created
- **Review requested** — PRs where your review is requested

For Devin-authored PRs, an orange **"Review"** button appears in the Devin chat interface.

Quick URL shortcut: replace `github.com` with `devinreview.com` in any PR link to jump directly to the Devin Review view. Private PRs require sign-in.
