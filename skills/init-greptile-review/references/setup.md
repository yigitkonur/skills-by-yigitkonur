# Greptile Setup & Installation

Complete guide to installing Greptile, connecting repositories, and initial configuration.

---

## What Greptile Is

Greptile is an AI code review agent that hooks into GitHub and GitLab pull requests. It indexes your entire codebase, reads `.greptile/` configuration files on each PR (from the source branch), and posts semantic inline comments, summaries, confidence scores, and status checks.

Key characteristics:
- **Not a linter** — uses LLMs for semantic understanding of intent, architecture, and cross-file implications
- **Full codebase indexing** — builds a searchable vector index of your entire repo using hybrid semantic/keyword retrieval
- **Config-as-code** — review behavior is controlled by `.greptile/` files checked into the repo
- **Cascading configs** — monorepos can override settings per directory

---

## GitHub Installation

### Step 1: Install the GitHub App

1. Go to [GitHub Marketplace — Greptile](https://github.com/marketplace/greptile)
2. Click **Install** → choose **All repositories** or **Select repositories**
3. Authorize with your GitHub account (OAuth)
4. You are redirected to the Greptile dashboard at `app.greptile.com`

### Step 2: Verify Repository Indexing

After installation, Greptile begins indexing selected repositories:

```
Dashboard → Repositories → Your repo → Status
```

| Status | Meaning | Action |
|--------|---------|--------|
| Indexing | Initial codebase vectorization in progress | Wait (5-30 min for 10k LoC) |
| Indexed | Ready for reviews | None — start creating PRs |
| Failed | Indexing error | Check repo access, re-trigger from dashboard |
| Not Connected | App not installed for this repo | Re-install from GitHub Marketplace |

Indexing scales approximately linearly with codebase size. Incremental re-indexing on PRs takes under 1 minute.

### Step 3: Required GitHub Permissions

| Permission | Access | Purpose |
|------------|--------|---------|
| Contents | Read | Read codebase files for indexing |
| Metadata | Read | Repository metadata |
| Pull requests | Read/Write | Read PR diffs, post review comments |
| Checks | Write | Post pass/fail status checks |
| Commit statuses | Write | Report review status on commits |

### Step 4: Webhook Events (Automatic)

The GitHub App automatically registers for these webhook events:

| Event | Trigger | Greptile Action |
|-------|---------|-----------------|
| `pull_request.opened` | New PR created | Full review |
| `pull_request.synchronize` | New commits pushed to PR | Re-review (if `triggerOnUpdates: true`) |
| `pull_request.reopened` | Closed PR reopened | Full review |
| `check_suite.requested` | Check suite initiated | Status check update |

---

## GitLab Installation

### Step 1: Add Webhook

1. Go to your GitLab project → **Settings** → **Webhooks**
2. Add webhook URL: `https://api.greptile.com/v1/webhooks/gitlab`
3. Paste the secret token from your Greptile dashboard
4. Select trigger: **Merge request events**
5. Click **Add webhook**

### Step 2: API Access Token

Create a GitLab project access token with these scopes:

| Scope | Purpose |
|-------|---------|
| `read_api` | Read project and MR data |
| `read_repository` | Read codebase for indexing |
| `api` | Post review comments on MRs |

Add the token in the Greptile dashboard under **Settings → GitLab Integration**.

### Step 3: Verify

1. Create a test merge request
2. Check the Greptile dashboard for review activity
3. Review should appear within 2-3 minutes

---

## Dashboard Overview

The Greptile dashboard at `app.greptile.com` provides:

### Repositories Tab
- View all connected repos and their indexing status
- Re-trigger indexing manually
- View lines of code indexed, last update timestamp

### Reviews Tab
- Browse all posted reviews
- View/edit individual comments
- Regenerate reviews on demand

### Custom Context Tab
- **Rules**: View active rules, "Last Applied" timestamp, add dashboard-level rules
- **Suggested Rules**: After ~10 PRs, Greptile auto-suggests rules based on patterns observed
- **Files**: Context file mappings

### Settings Tab
- Organization-wide defaults (strictness, comment types)
- API key management
- Notification integrations (Slack, Teams)
- Billing and usage

### Analytics Tab
- Review frequency and timing
- Bug type distribution histogram
- Average review latency (typically 10-60 seconds per PR)

---

## Configuration File Placement

### Recommended: `.greptile/` folder

```
repo-root/
└── .greptile/
    ├── config.json    ← Primary configuration
    ├── rules.md       ← Prose rules (optional)
    └── files.json     ← Context file mappings (optional)
```

### Legacy: `greptile.json`

Single file at repo root. Supports all parameters but is less organized.

**Important**: If both `.greptile/` and `greptile.json` exist, `.greptile/` wins and `greptile.json` is **silently ignored**.

### Monorepo: Cascading `.greptile/` folders

```
repo-root/
├── .greptile/
│   ├── config.json         ← Root: applies everywhere
│   ├── rules.md            ← Prose: applies everywhere
│   └── files.json          ← Context: applies everywhere
├── packages/
│   ├── api/
│   │   └── .greptile/
│   │       └── config.json ← Extends root, can override
│   ├── payments/
│   │   └── .greptile/
│   │       └── config.json ← strictness: 1 (stricter)
│   └── internal-tools/
│       └── .greptile/
│           └── config.json ← strictness: 3, disabledRules: [...]
```

---

## Detecting Existing Greptile Configuration

Before creating new config, check if Greptile is already set up. Run these commands from the repository root:

```bash
# Check for .greptile/ directory (recommended format)
find . -type d -name '.greptile' -not -path '*/node_modules/*' 2>/dev/null

# Check for legacy greptile.json
find . -type f -name 'greptile.json' -not -path '*/node_modules/*' 2>/dev/null

# Check for child configs in a monorepo
find . -type f -path '*/.greptile/config.json' -not -path '*/node_modules/*' 2>/dev/null
```

| Finding | Action |
|---|---|
| No config found | New setup — proceed with this guide |
| Root `.greptile/` exists | Tune existing — read current config, extend carefully |
| Root `greptile.json` exists | Migrate to `.greptile/` — see Troubleshooting reference |
| Both exist | Remove `greptile.json` — `.greptile/` silently wins |
| Child configs exist | Map the hierarchy before changing root config |

---

## Detecting Existing Linters and Formatters

Greptile should not duplicate what linters already cover. Inventory existing quality tools:

```bash
# Config files near repo root
find . -maxdepth 2 -type f \( \
  -name '.eslintrc*' -o -name 'eslint.config.*' -o \
  -name 'prettier.config*' -o -name '.prettierrc*' -o \
  -name 'biome.json' -o -name 'biome.jsonc' -o \
  -name '.stylelintrc*' -o -name 'stylelint.config*' -o \
  -name '.rubocop.yml' -o -name '.rubocop_todo.yml' -o \
  -name '.golangci.yml' -o -name '.golangci.yaml' -o \
  -name 'pyproject.toml' -o -name 'setup.cfg' -o -name '.flake8' -o -name '.pylintrc' \
\) 2>/dev/null

# Check package.json devDependencies (JavaScript/TypeScript)
python3 - <<'PY'
from pathlib import Path
import json

package_json = Path("package.json")
if not package_json.exists():
    print("package.json not found")
else:
    try:
        dev = json.loads(package_json.read_text()).get("devDependencies", {})
    except Exception as exc:
        print(f"Could not parse package.json: {exc}")
    else:
        linters = [name for name in dev if any(tag in name.lower() for tag in ("eslint", "prettier", "biome", "stylelint", "lint", "oxlint"))]
        print("Linters/formatters:", ", ".join(linters) if linters else "none found in devDependencies")
PY
```

If both the config-file scan and the manifest scan come up empty, treat the repo as lacking dedicated lint/format tooling until repo-specific evidence says otherwise.

| Tools found | Impact on Greptile config |
|---|---|
| ESLint + Prettier | Drop `"style"` from `commentTypes`. Do not write rules about formatting, imports, or naming |
| Biome | Same as ESLint+Prettier (Biome covers both) |
| Only ESLint (no formatter) | Consider including `"style"` in `commentTypes` |
| No linters at all | Include `"style"` in `commentTypes`. Consider rules for basic code quality |
| Language-specific (RuboCop, golangci-lint, Pylint) | Do not duplicate their rule categories in Greptile |

---

## Finding Context-Worthy Files

Context files (`files.json`) give the reviewer reference material. Search for candidates:

```bash
# Database schemas
find . -type f \( -name '*.prisma' -o -name 'schema.rb' -o -name 'models.py' \) -not -path '*/node_modules/*' 2>/dev/null

# API specifications
find . -type f \( -name 'openapi*' -o -name 'swagger*' -o -name '*.graphql' -o -name '*.proto' \) -not -path '*/node_modules/*' 2>/dev/null

# Architecture documentation
find . -maxdepth 3 -type f \( -path './docs/*' -o -name 'architecture.md' -o -name 'ARCHITECTURE*' -o -name 'ADR*' \) ! -name 'README*' ! -name 'CHANGELOG*' 2>/dev/null | head -20
find . -type f -path '*/docs/*.md' -not -name 'README*' -not -name 'CHANGELOG*' 2>/dev/null | head -10

# Shared type definitions
find . -type f \( -name 'types.ts' -o -name 'types.d.ts' -o -name 'shared-types*' \) -not -path '*/node_modules/*' 2>/dev/null | head -10
```

**Only include files that help validate correctness.** A Prisma schema helps validate model field usage. A README does not help review code changes. See `config-spec.md` for qualifying criteria.

---

## First Configuration

Minimal working config to verify the setup:

```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "excludeAuthors": ["dependabot[bot]", "renovate[bot]"],
  "ignorePatterns": "dist/**\nbuild/**\nnode_modules/**\npackage-lock.json\nyarn.lock",
  "rules": [
    {
      "id": "canary",
      "rule": "No TODO comments allowed in production code.",
      "scope": ["src/**"],
      "severity": "low"
    }
  ],
  "statusCheck": true
}
```

### Verification Steps

1. Commit and push `.greptile/config.json` to the branch you will use as the PR's source branch. If you seed the default branch first, cut the test branch from that updated commit so the config is still present on the source branch.
2. Create or update a PR from that source branch that includes a `// TODO: test` comment in a scoped file
3. Wait 2-3 minutes for Greptile to review
4. Verify the canary rule fires
5. Check dashboard → Custom Context → Rules → "Last Applied" timestamp updates
6. Remove the canary rule once verified

---

## Configuration Precedence

Rules and settings cascade with this priority (highest wins):

```
1. Org-enforced rules (dashboard, admin-only) — cannot be overridden
2. .greptile/ folder (per-directory, cascading)
3. greptile.json (repo root, single-file)
4. Dashboard settings (org-wide defaults)
```

### Inheritance in Monorepos

| Parameter | Child Behavior |
|-----------|---------------|
| `strictness` | **Overrides** parent |
| `commentTypes` | **Overrides** parent |
| `triggerOnUpdates` | **Overrides** parent |
| `rules` | **Extends** parent (adds new rules to inherited set) |
| `disabledRules` | **Disables** specific parent rules by `id` |
| `ignorePatterns` | **Extends** parent patterns |

---

## Authentication & API Keys

### Dashboard API Key

Generate at: `app.greptile.com` → **Settings** → **API Keys**

Use for:
- Programmatic review triggers via REST API
- Codebase search queries
- Configuration management

### API Authentication

```bash
curl -X POST https://api.greptile.com/v1/repos/{owner}/{repo}/reviews \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"branch": "main"}'
```

### Rate Limits

| Tier | Rate Limit | Concurrent Reviews |
|------|-----------|-------------------|
| Hobby | 20/min | 5 |
| Pro | 60/min | 25 |
| Team | 100/min | 50 |
| Enterprise | Custom | Custom |

---

## Uninstalling

### GitHub
1. Go to GitHub → **Settings** → **Applications** → **Greptile**
2. Click **Uninstall**
3. This revokes all webhooks and removes the app
4. Optionally delete `.greptile/` folder from repositories

### GitLab
1. Remove the webhook from **Settings** → **Webhooks**
2. Revoke the project access token
3. Optionally delete `.greptile/` folder from repositories

### Data Retention
- Greptile retains indexed data for 30 days after uninstall
- Contact support for immediate deletion
- Review comments posted to GitHub/GitLab remain (they are owned by the platform)

---

## Platform Comparison

| Feature | GitHub | GitLab |
|---------|--------|--------|
| Installation | App Marketplace (one-click) | Manual webhook + token |
| Auto webhooks | Yes | Manual |
| Status checks | Native Checks API | MR widget |
| Block merges | Required status check | MR approval rule |
| Inline comments | Yes | Yes |
| Summary comments | Yes | Yes |
| Setup time | ~2 minutes | ~5 minutes |
