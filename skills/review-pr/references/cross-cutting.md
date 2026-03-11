# Cross-Cutting Coordination Checklist

Detailed procedures for detecting issues that span multiple files and clusters. These bugs are invisible when reviewing files in isolation — they only surface when you check how changes coordinate across system boundaries.

---

## The Coordination Matrix

After reviewing all clusters individually, run through this matrix. For each row where the "Changed" column is true, check the "Verify" column.

| Changed | Verify | What Can Go Wrong |
|---------|--------|-------------------|
| API endpoint signature | All callers (frontend, CLI, SDK, other services) | Callers pass old arguments; runtime type errors |
| API response shape | Frontend components that consume it | UI renders stale/broken data; `undefined` access |
| Database schema (add column) | ORM models, queries, seeds, fixtures | Model doesn't expose new column; seeds fail |
| Database schema (remove column) | All queries referencing that column | SELECT crashes; old code still deployed reads it |
| Database schema (rename column) | Every file that references old name | Silent query failures or empty results |
| Environment variable (new) | Docker compose, CI config, deploy scripts, docs | App crashes on deploy — variable undefined |
| Environment variable (rename) | Every file referencing old name | Same as above, but harder to find |
| Shared type/interface | Every file that imports it | Type errors in unconverted consumers |
| Error code/type (new) | Global error handler, client error parsing | Unhandled error type falls through to 500 |
| Middleware order | Route definitions | Auth/validation runs in wrong order |
| Feature flag (new) | All code paths that should check it | Feature partially enabled, inconsistent behavior |
| Shared utility function | All callers | Changed behavior breaks assumptions |
| Configuration schema | Config loading, validation, defaults | App starts with invalid config |
| Event/message format | All subscribers/consumers | Subscribers crash on unexpected shape |

---

## Detection Techniques

### Technique 1: Absence Detection

The most powerful coordination check is looking for what's NOT in the PR.

```
If the PR changes API response shape:
  → Are there any frontend files in the changed file list?
  → If NO → Flag: "API response changed but no frontend consumers updated"

If the PR adds a new env var in code:
  → Is .env.example or docker-compose.yml in the changed file list?
  → If NO → Flag: "New env var referenced but not added to config"

If the PR changes a shared function signature:
  → Count callers using grep
  → Count callers that are in the PR's changed file list
  → If callers_changed < callers_total → Flag with specific file list
```

### Technique 2: Import/Export Tracing

When a file's exports change, trace all importers:

```bash
# Find all files importing the changed module
grep -rn "from.*['\"]\./auth" --include="*.ts" src/
grep -rn "import.*auth" --include="*.py" src/
grep -rn "require.*auth" --include="*.js" src/
```

Compare the importer list against the PR's changed files. Any importer NOT in the PR is a potential coordination gap.

### Technique 3: Configuration Propagation

When a new configuration value appears in application code, verify it exists in all deployment contexts:

```bash
# Find all references to the new config key
grep -rn "NEW_CONFIG_KEY" .

# Should find matches in:
# - Application code (where it's used)
# - .env.example or .env.template
# - docker-compose.yml / docker-compose.override.yml
# - CI/CD config (.github/workflows/, .gitlab-ci.yml)
# - Deployment scripts (terraform, k8s manifests)
# - Documentation (README, deployment guide)
```

### Technique 4: Schema-API-Consumer Chain

For full-stack changes, trace the data flow:

```
Database schema → ORM model → Service layer → API route → API response → Frontend consumer
```

If any link in this chain changed, verify all downstream links are updated:

```
Migration adds column "last_login_at"
  → ORM model: does it include the new field?
  → Service: does it populate the field?
  → API: does it expose the field in responses?
  → Frontend: does it display the field? (may not be needed in this PR)
  → Tests: do they assert on the new field?
```

---

## Common Coordination Failures

### 1. Schema Changed but API Not Updated

```
Symptom: Migration adds a column; API response doesn't include it.
Impact: Feature incomplete — data stored but not accessible.
Detection: Check API serializers/transformers for the new field.
Finding: 🟡 Important — "Migration adds `last_login_at` but the user
          API response in `src/api/serializers/user.ts` doesn't include it."
```

### 2. API Changed but Frontend Not Updated

```
Symptom: API endpoint returns different shape; frontend still expects old shape.
Impact: UI crashes or shows wrong data on the next deploy.
Detection: Search frontend for API endpoint URL or response field names.
Finding: 🔴 Blocker — "Response field `userName` renamed to `username`
          but `src/components/Profile.tsx:23` still reads `data.userName`."
```

### 3. New Endpoint Without Auth

```
Symptom: New API route added; auth middleware not applied.
Impact: Unauthenticated access to protected data.
Detection: Compare new route definition against existing routes' middleware chains.
Finding: 🔴 Blocker — "New endpoint `DELETE /api/users/:id` at
          `src/api/routes/users.ts:45` has no auth middleware, unlike
          the GET and POST handlers above it."
```

### 4. New Env Var Not in Deploy Config

```
Symptom: Code reads process.env.NEW_VAR; not in Docker/CI config.
Impact: App crashes on deploy with undefined variable.
Detection: Grep for the env var name across all config files.
Finding: 🟡 Important — "`STRIPE_WEBHOOK_SECRET` referenced in
          `src/api/webhooks.ts:12` but not added to `.env.example`,
          `docker-compose.yml`, or GitHub Actions secrets."
```

### 5. Shared Type Changed Without Consumer Updates

```
Symptom: Interface/type definition changed; importers not updated.
Impact: Type errors at runtime (dynamic languages) or build breaks (static).
Detection: Trace all imports of the changed type file.
Finding: 🟡 Important — "`UserRole` type in `src/types/user.ts`
          now includes 'superadmin', but `src/auth/guards/role.guard.ts:30`
          only handles 'admin' and 'viewer' in its switch statement."
```

---

## Cross-Cluster Coordination Quick Checks

Run these checks after completing individual cluster reviews:

```
1. Count API endpoints changed → Check that many frontend components updated
2. Count schema fields changed → Check ORM models match
3. Count new env vars → Check deploy configs
4. Count changed exports → Check importers
5. Count new error types → Check error handlers
6. Count feature flags → Check all relevant code paths
```

If any count has a mismatch (e.g., 3 API endpoints changed but 0 frontend files), that's a signal to investigate. The mismatch may be intentional (frontend update in a follow-up PR) or a coordination bug.

---

## Reporting Coordination Findings

Coordination findings are often the highest-value items in a review because they catch bugs that no single-file review would find. Format them with clear cross-references:

```markdown
🟡 **API response changed but frontend consumer not updated**

The API response for `GET /api/users/:id` changed:
- **Added:** `lastLoginAt` field (`src/api/serializers/user.ts:34`)
- **Renamed:** `userName` → `username` (`src/api/serializers/user.ts:28`)

The frontend `ProfileCard` component (`src/components/ProfileCard.tsx:15`)
still references `data.userName`, which will be `undefined` after this change.

Two options:
1. Update `ProfileCard.tsx` in this PR (recommended)
2. If this is intentional for a phased rollout, note it in the PR description
```

Always include both sides of the coordination gap (the change and the unconverted consumer) so the author can see the full picture.
