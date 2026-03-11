# File Clustering for PR Review

## Why cluster before reviewing

When a PR changes 15 files across API routes, database migrations, frontend components, and tests, reviewing them in alphabetical order is inefficient and error-prone. You miss cross-file relationships, duplicate reviews of the same concern, and fail to catch coordination bugs between layers.

Most tools and reviewers default to alphabetical or directory-sorted file lists. This means you might review `src/api/users.ts` first, then `src/auth/middleware.ts`, then `src/components/UserProfile.tsx`, then `tests/api/users.test.ts` — bouncing between unrelated concerns, losing context with each jump, and never seeing the full picture of any single change.

Clustering groups files by domain/concern so you can:

- **Review related changes together** — an API route, its request validation schema, and its test file form one reviewable unit. Reading them together lets you verify that the test actually covers the new validation logic, rather than reviewing the route now and the test 10 files later when you've forgotten the details.
- **Detect missing coordination** — if the API response shape changed but no frontend consumer was updated, a cluster-based review makes that gap immediately visible. The API cluster is present, the frontend cluster is absent. That absence is the signal.
- **Prioritize by risk** — a database migration that drops a column is more dangerous than a README typo fix. Reviewing the migration first, while you have full attention, prevents the most costly class of missed bugs.
- **Size the review effort per cluster** — knowing that 300 of the 400 changed lines are in auto-generated migration files lets you budget your attention for the 100 lines of hand-written logic that actually need careful review.

---

## The clustering algorithm

### Step 1: Parse file paths

For each changed file, extract three signals:

- **Directory prefix** — everything before the filename. `src/api/routes/users.ts` yields `src/api/routes/`. This is the strongest clustering signal.
- **File extension** — `.ts`, `.sql`, `.md`, `.yml`. Extensions disambiguate files that live in generic directories.
- **File name patterns** — test indicators (`*.test.*`, `*.spec.*`, `test_*`), config indicators (`*.config.*`), and special files (`Dockerfile`, `package.json`).

These three signals together determine which cluster a file belongs to.

### Step 2: Apply cluster rules

Match files to clusters using these rules, evaluated in order. If a file matches multiple clusters, the first match wins (higher priority clusters take precedence):

| Cluster | Pattern matches | Priority |
|---------|----------------|----------|
| **Data/Migration** | `**/migrations/**`, `**/migrate/**`, `**/*schema*`, `**/seeds/**`, `**/fixtures/**`, `*.sql`, `**/prisma/**`, `**/drizzle/**`, `**/alembic/**`, `**/flyway/**` | 1 (highest risk) |
| **Security/Auth** | `**/auth/**`, `**/security/**`, `**/permissions/**`, `**/rbac/**`, `**/*guard*`, `**/*policy*`, `**/*middleware*` (when auth-related) | 2 |
| **API/Routes** | `**/api/**`, `**/routes/**`, `**/controllers/**`, `**/handlers/**`, `**/endpoints/**`, `**/graphql/**`, `**/resolvers/**` | 3 |
| **Core/Business Logic** | `**/services/**`, `**/domain/**`, `**/core/**`, `**/lib/**`, `**/utils/**`, `**/models/**` (non-migration) | 4 |
| **Frontend** | `**/components/**`, `**/pages/**`, `**/views/**`, `**/layouts/**`, `**/hooks/**`, `**/stores/**`, `*.css`, `*.scss`, `*.tsx`/`*.jsx` (in UI directories) | 5 |
| **Infrastructure** | `Dockerfile*`, `docker-compose*`, `.github/**`, `**/ci/**`, `**/deploy/**`, `*.yml`/`*.yaml` (CI/CD), `terraform/**`, `k8s/**`, `helm/**` | 6 |
| **Configuration** | `*.config.*`, `*.env*`, `package.json`, `tsconfig*`, `*.toml`, `pyproject.toml`, `Cargo.toml`, `go.mod` | 7 |
| **Documentation** | `*.md`, `**/docs/**`, `CHANGELOG*`, `LICENSE*`, `*.txt` (documentation) | 8 |
| **Types/Interfaces** | `**/types/**`, `**/interfaces/**`, `**/*.d.ts`, `**/schemas/**`, files with primarily type exports | Paired with consuming cluster |
| **Tests** | `**/__tests__/**`, `**/test/**`, `**/tests/**`, `**/spec/**`, `*_test.*`, `*.test.*`, `*.spec.*`, `test_*.*` | Paired with source |

Note on priority: the number indicates review order, not pattern-matching precedence. A file in `src/auth/middleware.ts` matches Security/Auth (priority 2) even though it could loosely match the middleware pattern. The most specific directory match wins.

### Step 3: Pair tests with source clusters

Tests are not their own review silo. The same applies to type definition files — pair types.ts, *.d.ts, and schema files with the cluster that imports those types. They should be reviewed alongside the code they validate. For each test file:

1. **Strip the test indicator** from the filename to get the implied source name:
   - `user.test.ts` → `user.ts`
   - `test_auth_middleware.py` → `auth_middleware.py`
   - `UserProfile.spec.tsx` → `UserProfile.tsx`

2. **Search the changed file list** for a file matching that source name (ignoring directory differences).

3. **Assign the test to the same cluster** as its matching source file. If `src/api/routes/users.ts` is in the API/Routes cluster, then `tests/api/users.test.ts` joins that cluster.

4. **If no matching source file is changed**, the test goes into a standalone **"Test-only"** cluster. This is itself a review signal — why are tests changing without corresponding source changes? It might be fine (backfilling coverage), or it might indicate the source change is in a different PR and the test is premature.

### Step 4: Handle ambiguous files

Some files resist clean categorization:

- A `utils/formatDate.ts` could be Core/Business Logic or Frontend depending on who consumes it.
- A `middleware/rateLimit.ts` could be Security or API/Routes.
- A `shared/types.ts` touches everything.

For ambiguous files:

1. **Check imports/exports** if you have access to file contents. A utility imported only by frontend components belongs with Frontend. A middleware imported by the auth module belongs with Security/Auth.
2. **Default to the cluster with the most related files** already in this PR. If 5 other files are in the API cluster and this ambiguous file is imported by 3 of them, it goes in API.
3. **When nothing else works**, create a **"Mixed/Other"** cluster. Keep it small — if it has more than 3-4 files, you probably need to refine your clustering rules for this specific codebase.

### Step 5: Order clusters by review priority

Review clusters in this order, allocating attention to the highest-risk areas first:

1. **Data/Migration** — can cause data loss, is hard or impossible to rollback in production, may require coordinated deployment
2. **Security/Auth** — can introduce vulnerabilities, permission escalation, or auth bypass
3. **API/Routes** — can break downstream consumers, mobile apps, or third-party integrations
4. **Core/Business Logic** — can cause incorrect calculations, wrong state transitions, or subtle behavioral bugs
5. **Frontend** — visible to users but typically lower blast radius; broken UI is bad but rarely causes data loss
6. **Infrastructure** — can affect deployments and CI/CD but usually isolated from application logic
7. **Configuration** — usually low risk but worth scanning for accidentally committed secrets or broken dependency versions
8. **Tests** — validate the above; review alongside their paired source cluster
9. **Documentation** — lowest risk; a quick scan for accuracy is sufficient

This ordering is a default. Adjust it for your domain. If you're reviewing a documentation-focused repo, docs move up. If it's a frontend-only project, Frontend becomes priority 1.

---

## Cluster review strategy by size

Not every PR deserves the same depth of review. Use total lines changed to calibrate your approach:

| Total lines changed | Strategy |
|---------------------|----------|
| **< 100 lines** | Review everything in detail. Clustering still helps organize your thinking, but every file gets a careful read. |
| **100–500 lines** | Review the top 3 priority clusters in detail. Scan remaining clusters at a high level, focusing on obvious issues. |
| **500–1000 lines** | Deep review on priority 1–2 clusters. Summary review on clusters 3–4. Skim the rest. Flag the PR size as a concern in your review. |
| **> 1000 lines** | Flag PR size as a blocker. Recommend splitting into smaller PRs along cluster boundaries. If splitting is not possible, deep review only the highest-risk cluster and explicitly note that other clusters were not deeply reviewed. |

The cluster boundaries themselves suggest natural PR split points. A PR with 3 well-defined clusters could often be 3 smaller, independently reviewable PRs.

---

## Output format

After clustering, output a cluster map before starting the file-by-file review. This serves as both a table of contents and a risk assessment. The reviewer (or the person reading your review) can immediately see the shape of the PR.

```
## File Clusters (23 files changed, +482/-156)

### 🔴 Cluster 1: Database Migrations (Priority: CRITICAL)
- db/migrations/20240315_add_user_roles.sql (+45)
- db/migrations/20240315_update_permissions.sql (+28)
→ Review focus: Data safety, rollback plan, backward compatibility

### 🟡 Cluster 2: Auth/Permissions (Priority: HIGH)
- src/auth/middleware.ts (+34/-12)
- src/auth/guards/role.guard.ts (+67)
- src/auth/policies/resource.policy.ts (+45/-8)
→ Review focus: Auth bypass, permission escalation, edge cases

### 🟡 Cluster 3: API Routes (Priority: HIGH)
- src/api/routes/users.ts (+23/-5)
- src/api/routes/admin.ts (+89)
→ Review focus: Input validation, error handling, breaking changes
→ Tests: tests/api/users.test.ts (+34), tests/api/admin.test.ts (+78)

### 🟢 Cluster 4: Frontend (Priority: MEDIUM)
- src/components/UserProfile.tsx (+56/-23)
- src/components/AdminPanel.tsx (+112)
→ Review focus: State management, error states, accessibility

### ⚪ Cluster 5: Config/Docs (Priority: LOW)
- README.md (+12/-3)
- package.json (+2/-1)
→ Review focus: Quick scan only
```

Key elements of this format:

- **Color-coded priority indicators** (🔴🟡🟢⚪) give an instant visual signal of where attention is needed.
- **Line count per file** lets reviewers gauge effort before diving in.
- **Review focus hints** per cluster tell the reviewer what to look for, not just what files exist.
- **Test pairing** is shown inline with the cluster, not in a separate section, so the reviewer sees source and test together.
- **Aggregate stats** at the top (total files, total additions/deletions) frame the overall size.

---

## Cross-cluster coordination checks

Individual clusters reviewed in isolation can still miss systemic issues. After reviewing each cluster on its own, run these cross-cluster coordination checks:

| If this cluster changed... | Check this cluster too... | For... |
|---------------------------|--------------------------|--------|
| Data/Migration | API Routes | Are new columns/fields exposed correctly in API responses? Are removed fields handled gracefully? |
| Data/Migration | Tests | Are migration rollback tests present? Is seed data updated? |
| API Routes | Frontend | Are API consumers updated for new, changed, or removed endpoints? Are request/response types in sync? |
| API Routes | Documentation | Is the API documentation (OpenAPI specs, README) updated to reflect endpoint changes? |
| Auth/Security | All other clusters | Are new endpoints and pages properly protected? Do new API routes require authentication? |
| Configuration | Infrastructure | Are new environment variables propagated to deployment configs, Docker files, and CI/CD pipelines? |
| Core/Business Logic | Tests | Are new logic branches, edge cases, and error paths covered by tests? |
| Frontend | API Routes | If the frontend adds a new API call, does the corresponding backend route exist in this PR or already in main? |
| Infrastructure | Configuration | Do CI/CD changes align with any new config requirements (new secrets, changed build steps)? |

The most dangerous coordination failures are:

1. **Schema changed but API not updated** — the API will serve stale or broken data.
2. **API changed but frontend not updated** — the UI will break for users on the new version.
3. **New endpoint added without auth** — an unprotected route goes to production.
4. **New env var in code but not in deploy config** — the app crashes on deploy because the variable is undefined.

If any of these coordination gaps appear during review, flag them as blocking issues regardless of how clean the individual clusters look. A PR where every file is perfect in isolation but the files don't coordinate is still a broken PR.

---

## Adapting clusters per codebase

The cluster rules above are defaults. Real codebases have their own conventions:

- **Monorepos** need an extra layer: cluster first by package/service, then by concern within each package.
- **Microservices** might have each service in its own directory — treat each service directory as a top-level boundary.
- **Non-standard layouts** (e.g., a Go project with `cmd/`, `internal/`, `pkg/`) need custom pattern mappings. Map `internal/` → Core/Business Logic, `cmd/` → API/Routes, etc.
- **Generated code** (protobuf outputs, GraphQL codegen, ORM models) should be noted but reviewed lightly — focus on the source definitions, not the generated output.

When you encounter a new codebase, spend 30 seconds scanning the top-level directory structure before applying cluster rules. Adjust the patterns to match what you see. The goal is not to follow the rules rigidly but to group related changes together so you can review them as coherent units.
