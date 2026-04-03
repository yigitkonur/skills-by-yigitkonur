# Integration & API Reference

> **When to read this file:** You are setting up CI/CD integration, status checks, merge gating, or programmatic review triggers. For basic setup (install, indexing, permissions), see `setup.md`. For config format, see `config-spec.md`.

CI/CD integration, programmatic review triggers, dashboard API, and webhook configuration.

---

## Greptile API

REST API at `https://api.greptile.com/v1`. Authenticate with Bearer token from the dashboard.

### Authentication

```bash
# Get your API key from: app.greptile.com → Settings → API Keys
export GREPTILE_API_KEY="your-api-key"

curl -H "Authorization: Bearer $GREPTILE_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.greptile.com/v1/repos
```

---

## API Endpoints

### Trigger a Review

Programmatically trigger a review on a specific PR or branch:

```bash
POST /v1/repos/{owner}/{repo}/reviews
```

```bash
curl -X POST "https://api.greptile.com/v1/repos/acme/backend/reviews" \
  -H "Authorization: Bearer $GREPTILE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "branch": "feat/new-auth",
    "commit_sha": "abc123",
    "config": {
      "strictness": 1
    }
  }'
```

Response:
```json
{
  "review_id": "rev_abc123",
  "status": "pending",
  "url": "https://app.greptile.com/reviews/rev_abc123"
}
```

### Poll Review Status

```bash
GET /v1/repos/{owner}/{repo}/reviews/{review_id}
```

Response:
```json
{
  "review_id": "rev_abc123",
  "status": "done",
  "summary": "3 issues found (1 high, 2 medium)",
  "violations": [
    {
      "rule_id": "no-raw-sql",
      "severity": "high",
      "file": "src/db/users.ts",
      "line": 42,
      "message": "SQL string interpolation detected"
    }
  ]
}
```

### Fetch/Update Configuration

```bash
GET  /v1/repos/{owner}/{repo}/config
POST /v1/repos/{owner}/{repo}/config
```

```bash
# Fetch current config
curl "https://api.greptile.com/v1/repos/acme/backend/config" \
  -H "Authorization: Bearer $GREPTILE_API_KEY"

# Update rules
curl -X POST "https://api.greptile.com/v1/repos/acme/backend/config" \
  -H "Authorization: Bearer $GREPTILE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": [
      {"id": "new-rule", "rule": "...", "scope": ["src/**"], "severity": "high"}
    ]
  }'
```

### Codebase Search

Query the indexed codebase semantically:

```bash
POST /v1/workspaces/{workspace_id}/search
```

```bash
curl -X POST "https://api.greptile.com/v1/workspaces/ws_123/search" \
  -H "Authorization: Bearer $GREPTILE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "How does user authentication work?"}'
```

### Organization Rules

```bash
GET /v1/orgs/{org}/rules
```

Returns all organization-enforced rules that cannot be overridden by repository config.

---

## Rate Limits

| Tier | Requests/min | Concurrent Reviews |
|------|-------------|-------------------|
| Hobby | 20 | 5 |
| Pro | 60 | 25 |
| Team | 100 | 50 |
| Enterprise | Custom | Custom |

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

---

## GitHub Status Checks

### Enabling Status Checks

Add to `.greptile/config.json`:
```json
{
  "statusCheck": true
}
```

This:
1. Posts a GitHub Check Run (`greptile/review`) on every PR
2. Reports pass/fail with violation details
3. Suppresses "X files reviewed, no comments" messages

### Blocking Merges with Status Checks

1. Enable `statusCheck: true` in Greptile config
2. Go to GitHub → **Settings** → **Branches** → **Branch protection rules**
3. Add rule for `main` (or your default branch)
4. Check **Require status checks to pass before merging**
5. Search for and add `greptile/review`

Now PRs cannot merge until Greptile review passes.

### Status Check States

| State | Meaning |
|-------|---------|
| `pending` | Review in progress |
| `success` | No high-severity issues found |
| `failure` | One or more high-severity issues found |
| `error` | Review could not complete (config error, timeout) |

---

## GitLab MR Integration

### Blocking Merges on GitLab

1. Configure Greptile webhook (see setup reference)
2. Go to GitLab → **Settings** → **Merge requests**
3. Under **Merge checks**, enable **Pipelines must succeed**
4. Greptile posts status via the MR widget

### MR Approval Rules

Combine Greptile with human approval:
1. GitLab → **Settings** → **Merge request approvals**
2. Add approval rule requiring Greptile check + N human approvals

---

## CI/CD Pipeline Integration

### GitHub Actions

Trigger Greptile review as a step in your CI pipeline:

```yaml
# .github/workflows/greptile-review.yml
name: Greptile Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Greptile Review
        run: |
          curl -X POST \
            "https://api.greptile.com/v1/repos/${{ github.repository_owner }}/${{ github.event.repository.name }}/reviews" \
            -H "Authorization: Bearer ${{ secrets.GREPTILE_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d "{
              \"branch\": \"${{ github.head_ref }}\",
              \"commit_sha\": \"${{ github.event.pull_request.head.sha }}\"
            }"

      - name: Wait for Review
        run: |
          REVIEW_ID=$(curl -s ... | jq -r '.review_id')
          for i in {1..30}; do
            STATUS=$(curl -s \
              "https://api.greptile.com/v1/repos/.../reviews/$REVIEW_ID" \
              -H "Authorization: Bearer ${{ secrets.GREPTILE_API_KEY }}" \
              | jq -r '.status')
            if [ "$STATUS" = "done" ]; then break; fi
            sleep 10
          done
```

### GitLab CI

```yaml
# .gitlab-ci.yml
greptile-review:
  stage: review
  script:
    - |
      curl -X POST \
        "https://api.greptile.com/v1/repos/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}/reviews" \
        -H "Authorization: Bearer $GREPTILE_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"branch\": \"$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME\"}"
  only:
    - merge_requests
```

---

## Manual Review Triggers

### Via PR Comment

Comment on any PR to trigger a manual review:
```
@greptileai review this
```

Or request review of specific aspects:
```
@greptileai review security
@greptileai review performance
```

### Via Dashboard

1. Go to `app.greptile.com` → **Reviews**
2. Find the PR
3. Click **Regenerate Review**

### Via API

```bash
curl -X POST "https://api.greptile.com/v1/repos/acme/backend/reviews" \
  -H "Authorization: Bearer $GREPTILE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"branch": "feat/new-auth"}'
```

---

## Notification Integrations

### Slack

1. Dashboard → **Settings** → **Notifications** → **Slack**
2. Connect your Slack workspace
3. Select channel for review notifications
4. Configure which events trigger notifications:
   - New review posted
   - High-severity issue found
   - Review completed with no issues

### Microsoft Teams

1. Dashboard → **Settings** → **Notifications** → **Teams**
2. Add incoming webhook URL from Teams channel
3. Configure notification filters

---

## Review Output Best Practices

### Recommended defaults for most repositories

```json
{
  "statusCheck": true,
  "updateExistingSummaryComment": true,
  "summarySection": { "included": true, "collapsible": false, "defaultOpen": true },
  "issuesTableSection": { "included": true, "collapsible": true, "defaultOpen": false },
  "fixWithAI": true
}
```

**Why these defaults:**
- `statusCheck: true` — suppresses noisy "X files reviewed, no comments" messages and provides a merge-gatable check
- `updateExistingSummaryComment: true` — prevents comment spam on force-pushes
- Summary always open — the most important section should be immediately visible
- Issues table collapsed — available on demand, doesn't clutter clean PRs
- `fixWithAI: true` — provides actionable fix suggestions alongside comments

### When to override

| Scenario | Override |
|---|---|
| Team doesn't want AI fix suggestions | `"fixWithAI": false` |
| Want sequence diagrams for architecture PRs | `"includeSequenceDiagram": true` |
| PR description should be auto-updated | `"shouldUpdateDescription": true` |
| Only want summary, no inline comments | `"updateSummaryOnly": true` |
| White-label / hide branding | `"hideFooter": true` |

## Review Output Configuration

Control what appears in review comments:

### Summary Comment
```json
{
  "statusCommentsEnabled": true,
  "updateExistingSummaryComment": true,
  "comment": "## Greptile Review"
}
```

### Section Control
```json
{
  "summarySection":          { "included": true,  "collapsible": true,  "defaultOpen": true  },
  "issuesTableSection":      { "included": true,  "collapsible": true,  "defaultOpen": false },
  "confidenceScoreSection":  { "included": true,  "collapsible": true,  "defaultOpen": false },
  "sequenceDiagramSection":  { "included": false, "collapsible": true,  "defaultOpen": false }
}
```

### Additional Features
```json
{
  "fixWithAI": true,
  "includeSequenceDiagram": true,
  "includeConfidenceScore": true,
  "shouldUpdateDescription": false,
  "hideFooter": false
}
```

| Feature | Effect |
|---------|--------|
| `fixWithAI` | Adds AI-generated fix suggestions to comments |
| `includeSequenceDiagram` | Auto-generates sequence/ER/class/flow diagrams |
| `includeConfidenceScore` | Shows confidence level for each comment |
| `shouldUpdateDescription` | Updates PR description instead of posting comment |
| `updateSummaryOnly` | Suppresses inline comments, shows only summary |
| `hideFooter` | Removes Greptile branding from comments |

---

## Cross-Repository Context

Index related repositories for cross-repo validation:

```json
{
  "patternRepositories": ["acme/shared-utils", "acme/api-contracts"]
}
```

Format: `org/repo` — never full URLs.

Use cases:
- Frontend referencing backend API contracts
- Microservices sharing type definitions
- Design system component validation
- Shared utility library patterns

---

## Pricing Reference

| Tier | Price | PRs/month | Key Features |
|------|-------|-----------|-------------|
| Hobby | Free | 100 | Basic reviews, 1 repo, limited model |
| Pro | ~$20-29/dev/mo | Unlimited | All models, scopes, 10+ repos/team |
| Team | ~$49/dev/mo | Unlimited | SSO, analytics, priority support |
| Enterprise | Custom | Unlimited | Private deployment, VPC, custom LLMs, SOC2 |

All tiers include GitHub and GitLab support. OSS projects may qualify for free Pro tier.
