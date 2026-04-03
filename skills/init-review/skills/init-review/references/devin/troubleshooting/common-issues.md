# Troubleshooting Devin Review

Common issues, debugging steps, and solutions for Devin Bug Catcher and auto-review.

---

## Quick Diagnostic Checklist

When Devin Review isn't working as expected, check these in order:

| # | Check | How |
|---|-------|-----|
| 1 | GitHub App installed? | Org settings → Integrations → Devin |
| 2 | Auto-review enrolled? | `Settings > Review` → check user/repo enrollment |
| 3 | PR is non-draft? | Draft PRs are skipped until marked ready |
| 4 | REVIEW.md exists? | Check root or relevant subdirectory |
| 5 | REVIEW.md syntax correct? | H2/H3 headers, bullet lists, fenced code blocks |
| 6 | Conflicting instruction files? | Check for contradictions between REVIEW.md, AGENTS.md, CLAUDE.md |
| 7 | Repo is private + connected? | Auto-review unavailable for unconnected public repos |
| 8 | PR reviews too long? | >300 lines or >50 rules dilute focus → trim to essentials |
| 9 | Syntax errors in REVIEW.md? | Malformed markdown (unclosed blocks, bad headers) → validate with linter |
| 10 | Rules too vague? | Generic phrases like "follow best practices" → rewrite with specific, testable criteria |
| 11 | Ignore patterns not working? | Malformed globs (missing `**/`, wrong separators) → fix glob format |

---

## Reviews Not Triggering

### Symptom: No review appears on PR

**Possible causes and fixes:**

| Cause | Fix |
|-------|-----|
| User not enrolled | Self-enroll at `Settings > Review > Add myself` |
| Repo not enrolled for all-PR review | Admin: add repo at `Settings > Review > Repositories` |
| PR is a draft | Mark PR as ready for review |
| GitHub App not installed | Install from GitHub Marketplace |
| Public repo not connected to org | Connect the repo to your Devin organization |
| Webhook misconfigured | Reinstall the GitHub App |

### Symptom: Review triggered but incomplete

**Possible causes:**

- **Very large PR** (500+ changed lines) — may hit token limits. Break into smaller PRs.
- **Binary files dominate the diff** — Bug Catcher focuses on code files; binary changes add noise.
- **Timeout** — very large diffs may time out. The CLI can help: `npx devin-review <PR-URL>`.

---

## Too Many Findings (Noisy Reviews)

### Symptom: Devin flags too many low-value issues

This is the most common complaint. Causes and solutions:

### 1. Missing Ignore Section

The Bug Catcher reviews everything in the diff, including generated files, lock files, and test snapshots.

**Fix:** Add an Ignore section to your REVIEW.md:

```markdown
## Ignore
- Auto-generated files in `src/generated/` do not need review.
- Lock files (package-lock.json, pnpm-lock.yaml) can be skipped.
- Test snapshots in `__snapshots__/` don't need review.
- Build output directories should never be committed.
```

### 2. Vague Rules

Rules like "write clean code" or "follow best practices" generate random, unhelpful findings.

**Fix:** Replace vague rules with specific, testable ones:

| ❌ Vague | ✅ Specific |
|----------|------------|
| "Validate inputs" | "API endpoints must validate request bodies using Zod schemas from `src/schemas/`" |
| "Handle errors" | "Every async function must use try-catch with structured error logging via `src/utils/logger`" |
| "Be secure" | "Never interpolate user input into SQL queries. Use Prisma's parameterized queries" |

### 3. Duplicating Linter Rules

If your REVIEW.md includes rules that ESLint, Prettier, or other linters already enforce, you get duplicate findings.

**Fix:** Check your linter configs before writing REVIEW.md. Only include rules that linters can't catch (architecture decisions, business logic, security patterns).

### 4. REVIEW.md Too Long

Files over 300-500 lines dilute the signal. The Bug Catcher has finite context — more rules means less focus on each one.

**Fix:** Keep under 300 lines. For monorepos, use directory-scoped REVIEW.md files instead of one massive root file.

### 5. All Rules at Same Severity

When every rule uses "must" and "never", nothing stands out.

**Fix:** Use varied phrasing to differentiate severity:
- **Critical**: "Must never", "always required", "severe"
- **Important**: "Use X instead of Y", "do not"
- **Nice-to-have**: "Consider", "prefer", "watch for"

---

## Missing Real Bugs (False Negatives)

### Symptom: Devin misses important issues

### 1. No REVIEW.md or Too Generic

Without specific rules, the Bug Catcher relies on general heuristics which miss repo-specific issues.

**Fix:** Add rules that reference your actual codebase:
```markdown
## Critical Areas
- All changes to `src/auth/` must be reviewed for security implications — this handles JWT validation and session management.
- Payment processing in `src/billing/` requires review for PCI compliance.
```

### 2. Critical Rules Buried at Bottom

The Bug Catcher weights content near the top higher.

**Fix:** Put Critical Areas and Security sections first, before Conventions and Performance.

### 3. No Code Examples

Without Good/Bad examples, the Bug Catcher can't match against specific anti-patterns.

**Fix:** Add a Patterns section with fenced code blocks:
```markdown
## Patterns

### Error Handling
**Good:**
\`\`\`typescript
try {
  return await db.user.findUniqueOrThrow({ where: { id } });
} catch (error) {
  logger.error('getUser failed', { id, error });
  throw new AppError('USER_NOT_FOUND', { cause: error });
}
\`\`\`

**Bad:**
\`\`\`typescript
return await db.user.findUnique({ where: { id } }); // no error handling
\`\`\`
```

### 4. Rules Too Suggestive

"Consider using batch operations" gets classified as informational, not as a bug.

**Fix:** For issues you want flagged as bugs, use imperative language:
- "Database queries inside loops MUST use batch operations"
- "N+1 query patterns are prohibited — use eager loading"

---

## Auto-Fix Not Working

### Symptom: Auto-Fix toggle is grayed out or not appearing

| Cause | Fix |
|-------|-----|
| Not org admin | Only org admins can change global Auto-Fix settings |
| Global mode overrides per-PR | If "Respond to all bot comments" is set globally, per-PR toggle is locked |
| No actionable findings | "No Issues Found" summaries don't trigger Auto-Fix |
| Bot not in allow-list | Add `devin-ai-integration[bot]` to the specific bots list |

### Symptom: Auto-Fix suggestions are wrong

- Auto-Fix generates patches based on the Bug Catcher's understanding of your rules
- If rules are vague, fixes will be vague. Make rules specific.
- Auto-Fix never merges automatically — review suggestions carefully

---

## CLI Issues

### Symptom: `npx devin-review` fails

| Error | Cause | Fix |
|-------|-------|-----|
| "Not a git repository" | Run outside a git repo | `cd` into the repo first |
| "Could not find PR branch" | Local repo doesn't have the PR branch | `git fetch origin pull/<N>/head:pr-<N>` first |
| Network/auth errors | Not logged into Devin | Log in at `app.devin.ai` and ensure org access |
| Timeout | Very large diff | Try on a smaller PR; use `--verbose` for diagnostics |

### CLI Best Practices

```bash
# Ensure you're in the repo root
cd /path/to/repo

# Fetch the PR branch first
git fetch origin

# Run the review
npx devin-review https://github.com/owner/repo/pull/123
```

---

## Monorepo Issues

### Symptom: Subdirectory REVIEW.md not being applied

**Possible causes:**

1. **File not named exactly `REVIEW.md`** — must be uppercase, no prefix/suffix
2. **Nesting too deep** — prefer package/service-level files like `packages/api/REVIEW.md`; deep files such as `packages/api/src/utils/REVIEW.md` usually create more overlap and confusion than signal
3. **Changed files not in that directory** — the scoped REVIEW.md only applies to files within its directory tree

### Symptom: Duplicate findings from root + subdirectory REVIEW.md

Treat root and subdirectory files as overlapping context. Keep the root file cross-cutting, keep subdirectory files local to that subtree, and do not rely on undocumented precedence to resolve contradictions between them.

**Fix:** Don't repeat root rules in subdirectory files:
- **Root**: Cross-cutting concerns (security, general conventions)
- **Subdirectory**: Package-specific rules only

### Debugging Monorepo Scope

To see which `REVIEW.md` files may influence a changed file:

```bash
# List all REVIEW.md files and their depth
find . -name "REVIEW.md" -not -path "./.git/*" | awk -F/ '{print NF-1, $0}' | sort -n

# For a changed file like packages/api/src/handler.ts, inspect the root REVIEW.md
# plus any REVIEW.md under parent directories of that file.
# Keep the root cross-cutting and the scoped file package-specific.
```

---

## Conflicting Instruction Files

### Symptom: Devin gives contradictory review comments

Devin reads multiple instruction files. If they contradict each other:

1. **Check all instruction files**: matching `**/REVIEW.md`, `**/AGENTS.md`, `**/CLAUDE.md`, `**/CONTRIBUTING.md`, `.cursorrules`, `.windsurfrules`, `.coderabbit.yaml`, `.coderabbit.yml`, `greptile.json`
2. **Look for contradictions**: e.g., REVIEW.md says "use Moment.js" but AGENTS.md says "use date-fns"
3. **Resolve**: Pick one source of truth per concern:
   - Review criteria → `REVIEW.md`
   - Coding standards → `AGENTS.md` or `CLAUDE.md`
   - Workflow → `CONTRIBUTING.md`
   - Editor config → `.cursorrules` / `.windsurfrules`

### Detecting Rule Conflicts

Common conflict patterns:

| Conflict Type | Example |
|---------------|---------|
| REVIEW.md vs AGENTS.md | REVIEW.md bans `any` types, AGENTS.md allows them in test files |
| Root vs scoped REVIEW.md | Root requires JSDoc, scoped file says "no doc comments needed" |
| REVIEW.md vs linter config | REVIEW.md enforces 80-char lines but Prettier is set to 120 |

**Detection:** scan for contradictions across instruction files:

```bash
# Find all instruction files
find . \( -name "REVIEW.md" -o -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "CONTRIBUTING.md" -o -name ".cursorrules" -o -name ".windsurfrules" -o -name ".coderabbit.yaml" -o -name ".coderabbit.yml" -o -name "greptile.json" \) -type f -print0 | xargs -0 grep -nE "must|never|always|required|prohibit" 2>/dev/null | sort
```

**Resolution rule:** resolve by concern, not guessed precedence. Keep review criteria in `REVIEW.md`, coding behavior in `AGENTS.md` or `CLAUDE.md`, workflow in `CONTRIBUTING.md`, and style/formatting in linter or editor config.

---

## Validating REVIEW.md Syntax

Common syntax errors that silently break rule parsing:

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing H2/H3 headers | Rules not grouped, random findings | Ensure every section starts with `##` or `###` |
| Unclosed code blocks | Everything after the block treated as code | Match every `` ``` `` open with a `` ``` `` close |
| Tab indentation in lists | Bullets not recognized as list items | Use 2 or 4 spaces, never tabs |
| Empty example blocks | Pattern matching disabled for that rule | Add at least one Good/Bad code example per block |
| Duplicate rule names | Only one gets applied, other silently ignored | Use unique `###` heading names across entire file |

---

## Review Quality Metrics

Track these metrics to measure review effectiveness:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| False positive rate | < 20% | Count findings you dismiss ÷ total findings |
| Actionable rate | > 80% | Count findings that led to code changes ÷ total |
| Critical area coverage | 100% of defined areas | Check that every `## Critical Areas` path gets reviewed |
| Review turnaround | < 5 min after PR opened | Timestamp of first review comment minus PR creation |

**Interpretation:** If false positives are high, tighten Ignore patterns and remove vague rules. If actionable rate is low, add more code examples and strengthen rule language. If critical areas are missed, verify file paths in rules match actual repo structure.

## Auditing Rule Effectiveness

After 10+ reviewed PRs, audit each rule individually:

**Effectiveness score** = (findings that led to code changes) ÷ (total findings from that rule)

| Score | Action |
|-------|--------|
| > 0.8 | Keep — rule is working well |
| 0.5 – 0.8 | Refine — add examples or tighten language |
| < 0.5 | Remove or rewrite — rule generates more noise than signal |
| 0 hits | Check if rule is too specific or path references are outdated |

---

## Review Quality Iteration Playbook

A structured approach to improving review quality over time:

### Week 1: Baseline

1. Create minimal REVIEW.md (Critical Areas + Security + Conventions + Ignore)
2. Open 2-3 real PRs
3. Note: What did Devin catch? What did it miss? What was noise?

### Week 2: Reduce Noise

1. Review false positives from Week 1
2. Add missing Ignore patterns for generated files
3. Remove or soften vague rules
4. Check overlap with linter/CI — remove duplicates

### Week 3: Improve Coverage

1. Review false negatives from Weeks 1-2
2. Add specific rules for missed issues
3. Add code examples (Good/Bad patterns) for common anti-patterns
4. Strengthen language for critical rules

### Week 4: Stabilize

1. Review metrics: fewer false positives, more real bugs caught
2. Share REVIEW.md with the team for feedback
3. Document any repo-specific patterns that emerged
4. Set up periodic review of the REVIEW.md itself (quarterly)

---

## Getting Help

- **Devin Dashboard**: `https://app.devin.ai/review` — check PR status and findings
- **Devin Docs**: `https://docs.devin.ai/work-with-devin/devin-review` — official documentation
- **URL Shortcut**: Replace `github.com` with `devinreview.com` in any PR URL
- **CLI Verbose Mode**: `npx devin-review <URL> --verbose` for detailed diagnostics
