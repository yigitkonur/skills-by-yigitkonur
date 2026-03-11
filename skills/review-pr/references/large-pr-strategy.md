# Reviewing Large PRs

Strategies for reviewing PRs that exceed comfortable review size (>500 lines changed or >15 files). Large PRs have a measurably higher defect escape rate — Google's data shows review quality drops significantly above 200 lines. This reference provides techniques to maintain review quality at scale.

---

## Size Assessment

### PR Size Categories

| Size | Lines Changed | Files | Strategy |
|------|--------------|-------|----------|
| **Small** | < 100 | < 5 | Review everything in detail |
| **Medium** | 100–300 | 5–10 | Standard cluster-based review |
| **Large** | 300–800 | 10–25 | Prioritized review with depth tiers |
| **Very Large** | 800–2000 | 25–50 | Flag size as concern; deep review top clusters only |
| **Massive** | > 2000 | > 50 | Recommend splitting; review only highest-risk areas |

### When Size Is a Finding

Flag PR size as a finding when:

```markdown
🟡 **PR scope exceeds comfortable review size** — 47 files, +1,847/-423

Large PRs have a measurably higher defect escape rate. Consider splitting
along these natural boundaries:

1. Database migrations (Cluster 1) → separate PR, deploy first
2. API changes (Cluster 2) → depends on migrations
3. Frontend updates (Cluster 3) → depends on API changes
4. Test backfill (Cluster 4) → can be independent

This review covers Clusters 1 and 2 in depth. Clusters 3 and 4 were
skimmed for obvious issues only.
```

---

## Chunking Strategies

### Strategy 1: Cluster-Based Chunking

The default approach from Phase 2. Group files by concern, review each cluster as a unit.

```
Cluster 1: Database Migrations    → Review first (highest risk)
Cluster 2: API/Backend Changes    → Review second
Cluster 3: Frontend Changes       → Review third
Cluster 4: Tests                  → Review alongside source clusters
Cluster 5: Config/Docs            → Quick scan only
```

**When to use:** Most PRs. Works well when changes align to clear domains.

### Strategy 2: Dependency-Graph Chunking

Review in dependency order — start with the lowest-level changes that everything else depends on.

```
Layer 1: Types/Interfaces         → Review first (defines contracts)
Layer 2: Data Models/Schemas      → Review second (implements contracts)
Layer 3: Business Logic/Services  → Review third (uses models)
Layer 4: API Routes/Controllers   → Review fourth (exposes services)
Layer 5: Consumers (Frontend/CLI) → Review last (calls API)
```

**When to use:** PRs that introduce a new feature across the full stack. Reviewing bottom-up lets you validate each layer's contract before reviewing its consumers.

### Strategy 3: Risk-Based Chunking

Assign risk scores and review in risk order. Useful when clusters have unequal risk.

| Risk Factor | Score | Rationale |
|------------|-------|-----------|
| Touches auth/security | +3 | High impact if wrong |
| Touches database schema | +3 | Hard to rollback |
| Touches payment/billing | +3 | Financial impact |
| New endpoint without tests | +2 | Likely to have bugs |
| Modifies shared utilities | +2 | Affects many consumers |
| Large diff (>100 lines) in single file | +1 | Complex change |
| Generated code | -2 | Low value to review deeply |
| Documentation only | -2 | Low risk |
| Has corresponding tests | -1 | Tests provide safety net |

Sort files by risk score descending. Deep review the top 30%, standard review the middle 40%, skim the bottom 30%.

### Strategy 4: Incremental Review

For PRs that represent incremental work on a feature branch, review commit-by-commit instead of the full diff.

```bash
# List commits in the PR
gh api repos/{owner}/{repo}/pulls/{N}/commits --jq '.[].sha'

# Review each commit's diff
git show <sha1>
git show <sha2>
# ...
```

**When to use:** PRs with clean, logical commit history where each commit is a self-contained change. Not useful for squash-heavy PRs.

**Limitation:** You lose cross-commit context — an issue introduced in commit 1 and fixed in commit 5 won't be visible when reviewing commit 1.

---

## Depth Tiers

Not every file deserves the same level of scrutiny. Assign depth tiers based on risk and complexity.

### Tier 1: Deep Review (20% of files, 60% of time)

Full line-by-line review with context reading, blast radius tracing, and dimension checklist.

**Applies to:**
- Files in highest-risk clusters (data, auth, API)
- Files with the most lines changed
- Files that other reviewers flagged concerns about
- Files that modify shared interfaces or contracts

**What to do:**
- Read the full diff hunks carefully
- Read the full file for context when hunks are insufficient
- Compare head vs base for behavioral changes
- Trace blast radius for changed function signatures
- Apply the full review dimensions checklist
- Run the actionability filter on every finding

### Tier 2: Standard Review (40% of files, 30% of time)

Read the diff, check for obvious issues, verify test coverage.

**Applies to:**
- Files in medium-risk clusters (business logic, frontend)
- Files with moderate changes (10-50 lines)
- Test files (verify they test the right things)

**What to do:**
- Read diff hunks at normal pace
- Check for: null handling, error handling, obvious logic errors
- Verify test assertions match the changes
- Skip deep blast radius tracing

### Tier 3: Skim Review (40% of files, 10% of time)

Quick scan for red flags. Accept that you might miss subtle issues.

**Applies to:**
- Files in low-risk clusters (docs, config, styling)
- Generated files (lockfiles, compiled output)
- Files with minimal changes (<10 lines)

**What to do:**
- Scan diff for red flags (secrets, commented-out code, TODOs)
- Verify generated files are expected (lockfile changes match package.json changes)
- Do NOT spend time reading full context

---

## Communicating Coverage Limitations

When you cannot deeply review everything, explicitly state what you covered:

```markdown
### Review Coverage

| Cluster | Files | Depth | Notes |
|---------|-------|-------|-------|
| Database Migrations | 3 | 🔍 Deep | Full review with rollback analysis |
| API Routes | 5 | 🔍 Deep | Full review with blast radius check |
| Business Logic | 4 | 📋 Standard | Checked correctness and error handling |
| Frontend | 8 | 👁️ Skim | Scanned for obvious issues only |
| Tests | 6 | 📋 Standard | Verified assertions match changes |
| Config/Docs | 3 | 👁️ Skim | Quick scan, no issues found |

**Note:** This PR changes 29 files (+1,200/-340). Due to size,
Frontend cluster received only a skim review. A dedicated review
of the frontend changes is recommended before merge.
```

---

## Suggesting PR Splits

When a PR should be split, suggest specific split points with clear rationale:

### Good split suggestions

```markdown
🟡 **Recommend splitting this PR into 3 smaller PRs:**

**PR 1: Database migrations** (files: 3, ~120 lines)
- `db/migrations/20240315_*.sql`
- Deploy first, independently testable
- Reduces risk: if migration fails, other changes aren't blocked

**PR 2: API + backend logic** (files: 8, ~450 lines)
- `src/api/**`, `src/services/**`
- Depends on PR 1 (needs new columns)
- Can be reviewed and tested independently

**PR 3: Frontend + tests** (files: 12, ~600 lines)
- `src/components/**`, `tests/**`
- Depends on PR 2 (needs new API endpoints)
- Largest chunk but lowest risk

This split follows the dependency order and allows each PR to be
reviewed with full attention.
```

### When NOT to suggest splitting

- The PR is large because it adds one cohesive feature with tests
- The changes are tightly coupled and can't be deployed independently
- The author already explained why splitting isn't feasible in the PR body
- The PR is a generated migration/refactor where size doesn't indicate complexity

---

## Time Management for Large Reviews

| PR Size | Target Review Time | Approach |
|---------|-------------------|----------|
| Small (<100 lines) | 15-30 minutes | Review everything once |
| Medium (100-300 lines) | 30-60 minutes | One pass with cluster focus |
| Large (300-800 lines) | 60-90 minutes | Two passes: first for context, second for details |
| Very Large (800-2000 lines) | 90-120 minutes | Prioritized review, accept coverage gaps |
| Massive (>2000 lines) | Flag and split | Do not spend >2 hours; recommend splitting |

### The Two-Pass Technique for Large PRs

**Pass 1: Orientation (20% of time)**
- Read PR description and linked issues
- Scan the file list and build clusters
- Read commit messages for the development story
- Identify the highest-risk areas
- Build the review plan

**Pass 2: Detailed Review (80% of time)**
- Work through clusters in priority order
- Apply depth tiers
- Record findings with evidence
- Cross-check coordination between clusters
- Synthesize the review output

This two-pass approach prevents the common mistake of spending 60% of review time on the first few files encountered (often alphabetically first, not highest risk) and rushing through the rest.
