# Troubleshooting

Common issues with Copilot code review instructions, debugging sequences, anti-patterns, and verification protocols.

## Table of Contents

1. [Why Reviews Don't Trigger](#why-reviews-dont-trigger)
2. [Why Instructions Are Ignored](#why-instructions-are-ignored)
3. [File-Level Mistakes](#file-level-mistakes)
4. [Rule-Level Mistakes](#rule-level-mistakes)
5. [Architecture Mistakes](#architecture-mistakes)
6. [Debugging Sequence](#debugging-sequence)
7. [Verification Protocol](#verification-protocol)
8. [Non-Determinism](#non-determinism)

---

## Why Reviews Don't Trigger

### Copilot not appearing in Reviewers menu

| Cause | Fix |
|---|---|
| Copilot not enabled for repository | Settings → Copilot → Enable code review |
| No Copilot Business/Enterprise license | Upgrade plan or have org admin enable for members |
| Feature not available for repository visibility | Check plan supports private repos |
| Rate limit exceeded | Wait — default 10 PRs/hour/repo |

### Copilot review requested but no comments appear

| Cause | Fix |
|---|---|
| PR has no code changes (only docs/config) | Copilot reviews code changes only |
| PR changes only binary/generated files | These are automatically skipped |
| PR is too large (>500 changed files) | Copilot may partially review; use `/copilot review path/to/file` |
| Instructions reference unsupported actions | Remove UI formatting or merge-blocking directives |
| Base branch has no instruction files | Commit instructions to the base branch first |

### Reviews not reflecting instruction changes

| Cause | Fix |
|---|---|
| Instructions changed on feature branch only | Copilot reads from the **base branch** — merge instruction changes first |
| Instructions not committed yet | Commit and push to base branch |
| Cache delay | Wait 5-10 minutes after committing; request re-review |
| Copilot review not re-requested | After pushes, click "Request re-review" — it's not automatic |

---

## Why Instructions Are Ignored

### Content truncated

**Symptom:** Rules near the end of a file are consistently ignored.

**Cause:** File exceeds 4,000 characters. Everything past this limit is silently dropped.

**Fix:**
```bash
# Check character count
wc -c .github/copilot-instructions.md
wc -c .github/instructions/*.instructions.md
```

Split files over 4,000 characters into two with narrower `applyTo` scopes.

### Rules too vague

**Symptom:** Copilot produces generic comments unrelated to your specific rules.

**Cause:** Vague rules like "write good code" give Copilot nothing concrete to check.

**Fix:** Rewrite every rule to be specific and measurable:
```
❌ "Handle errors properly"
✅ "All API handlers must wrap async operations in try-catch and return structured error responses"
```

### Wrong file scope

**Symptom:** Rules intended for TypeScript are appearing on Python files, or not appearing at all.

**Cause:** Missing, incorrect, or overly broad `applyTo` pattern.

**Fix:** Verify the glob pattern matches intended files:
```bash
# Test if a pattern matches a specific file
# Does **/*.{ts,tsx} match src/components/Button.tsx?
# Yes — ** matches src/components/, *.tsx matches Button.tsx

# Does src/**/*.ts match packages/api/src/index.ts?
# No — src/ must be at root, not under packages/api/
# Fix: **/src/**/*.ts
```

### Linter rules crowding out semantic rules

**Symptom:** Copilot comments on formatting/style issues instead of architectural or security concerns.

**Cause:** Instruction file is full of rules the linter already handles, leaving no character budget for semantic rules.

**Fix:** Remove all rules that existing linters enforce. Focus on rules requiring understanding of intent.

---

## File-Level Mistakes

### Exceeding the 4,000-character limit

The most common mistake. Content beyond 4,000 characters is silently ignored — no warning.

**Fix:** Aim for 2,500–3,500 characters. If a concern needs more, split into two files with narrower scopes.

### Missing or invalid frontmatter

**Wrong:**
```markdown
# TypeScript Rules
- Use strict types
```

Without `applyTo` frontmatter, the file applies to nothing. Copilot ignores it entirely.

**Right:**
```markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Rules
- Use strict types
```

### Blank lines before frontmatter

**Wrong:**
```markdown

---
applyTo: "**/*.py"
---
```

YAML frontmatter must start at line 1. A blank line before `---` causes the frontmatter to be treated as regular markdown, and `applyTo` is not recognized.

### Wrong file location

`*.instructions.md` files MUST be in `.github/instructions/` directory (or subdirectories). Files in `.github/` root, `.github/review-rules/`, or any other location are ignored.

The root `copilot-instructions.md` goes in `.github/` — NOT in `.github/instructions/`.

### File naming

Files must end with `.instructions.md`. Common mistakes:
```
❌ .github/instructions/typescript.md          (missing .instructions)
❌ .github/instructions/typescript.rules.md     (wrong suffix)
❌ .github/instructions/TypeScript.instructions.md  (use kebab-case)
✅ .github/instructions/typescript.instructions.md
```

---

## Rule-Level Mistakes

### Vague, unactionable rules

**Bad:**
```markdown
- Write good code
- Handle errors properly
- Follow best practices
```

**Good:**
```markdown
- All API handlers must wrap async operations in try-catch blocks
- Use `AppError` class for business logic errors, not raw Error
- Log errors with structured format: { error, requestId, userId, action }
```

### Rules that duplicate linters

**Bad** (when ESLint + Prettier are configured):
```markdown
- Use 2-space indentation
- Add semicolons at end of statements
- Sort imports alphabetically
```

These waste your 4,000-character budget on rules the linter already enforces.

**Good** — focus on semantic rules:
```markdown
- Custom hooks must start with `use` and accept an options object as the last parameter
- Server Components must not import from `@/lib/client-utils`
- API route handlers must call `requireAuth()` before any data access
```

### Trying to modify Copilot behavior

**Ignored silently:**
```markdown
- Use bold text for critical issues
- Add emoji severity indicators (🔴 🟡 🟢)
- Include a summary table at the top of the review
- Rate overall code quality on a 1-10 scale
- Block merge if issues are found
```

Copilot code review cannot change comment formatting, modify the PR overview, or block merges. It only posts "Comment" reviews — never "Approve" or "Request changes."

### External links

**Bad:**
```markdown
- Follow the style guide at https://google.github.io/styleguide/tsguide.html
```

Copilot cannot follow external links. Copy the relevant content directly into the instruction file.

### Attempting absolute enforcement

**Bad:**
```markdown
- NEVER allow any function longer than 30 lines
- MUST reject any PR without 100% test coverage
```

Copilot is non-deterministic and advisory. Heavy-handed language doesn't improve reliability.

**Good:**
```markdown
- Functions should be concise (under ~50 lines) — flag when significantly longer
- New features should include unit tests covering the main path and error cases
```

---

## Architecture Mistakes

### Everything in one file

Putting all rules in `copilot-instructions.md`:
- Easily exceeds 4,000 characters
- Language-specific rules bleed into unrelated file reviews
- Hard to maintain as the project grows

**Fix:** One `copilot-instructions.md` for universal rules + multiple `*.instructions.md` files scoped by `applyTo`.

### Overlapping scopes with conflicting rules

```
typescript.instructions.md  → applyTo: "**/*.{ts,tsx}" → "Prefer interfaces"
react.instructions.md       → applyTo: "**/*.{tsx,jsx}" → "Prefer type aliases"
```

A `.tsx` file matches both and receives contradictory guidance.

**Fix:** Make rules complementary. Use non-overlapping scopes when rules genuinely differ.

### Monorepo files that repeat root rules

Root `copilot-instructions.md` says "no hardcoded secrets" and `packages-api.instructions.md` repeats it.

**Fix:** Package-specific files should contain ONLY rules unique to that package.

### Too many instruction files

Over 20 micro-files with 2-3 rules each:
- Combined instruction set becomes harder for Copilot to prioritize
- Maintenance burden grows
- Diminishing returns per file

**Fix:** Aim for 5-12 files total. Combine closely related concerns sharing the same `applyTo` scope.

---

## Debugging Sequence

When Copilot doesn't follow your instructions, work through these steps in order:

### Step 1: Verify file locations
```bash
ls -la .github/copilot-instructions.md
ls -la .github/instructions/*.instructions.md
```
Confirm files are in the correct directories.

### Step 2: Check character counts
```bash
wc -c .github/copilot-instructions.md
for f in .github/instructions/*.instructions.md; do
  echo "$f: $(wc -c < "$f") chars"
done
```
Any file over 4,000 characters has content being silently dropped.

### Step 3: Validate frontmatter
Open each `*.instructions.md` and verify:
- `---` is on line 1 (no blank lines above)
- `applyTo` is present and quoted
- Closing `---` is present
- Glob pattern actually matches your files

### Step 4: Confirm base branch
Instructions are read from the **base branch** of the PR, not the feature branch:
```bash
# Check which branch the PR targets
git log --oneline main -- .github/copilot-instructions.md
git log --oneline main -- .github/instructions/
```

### Step 5: Test glob pattern match
Verify your glob pattern matches the files being reviewed:
```bash
# Find files matching a glob pattern
find . -path "./src/components/*.tsx" -type f
# Compare against your applyTo: "src/components/**/*.{tsx,jsx}"
```

### Step 6: Check for rule conflicts
Read all instruction files that would apply to a specific file and look for contradictions between them.

### Step 7: Assess rule specificity
Vague rules ("write good code") are effectively noise. Rewrite as specific, measurable directives.

### Step 8: Test incrementally
Comment out most rules, leaving only 2-3. If those work, add rules back in small batches to identify what breaks.

### Step 9: Request re-review
After making changes, push to base branch and explicitly request a re-review. Copilot does NOT re-review automatically.

---

## Verification Protocol

Before deploying instruction files, verify:

### Format verification
```
□ copilot-instructions.md is at .github/copilot-instructions.md
□ All micro-files are in .github/instructions/
□ All micro-files have valid YAML frontmatter with applyTo
□ No file exceeds 4,000 characters
□ Frontmatter starts at line 1 with no preceding blank lines
□ File names use kebab-case.instructions.md format
```

### Content verification
```
□ No external links (Copilot can't follow them)
□ No UX/formatting modification instructions
□ No rules duplicating existing linter/formatter configuration
□ Rules are specific and measurable
□ Code examples use actual project patterns
□ Security rules are positioned near the top of relevant files
□ No attempts to block merges or change review type
```

### Architecture verification
```
□ Universal rules are in copilot-instructions.md only
□ Language-specific rules are in *.instructions.md with correct applyTo
□ No contradictions between overlapping files
□ No redundant rules across files
□ Monorepo package files don't repeat root-level rules
□ Total file count is 5-12 (not too few, not too many)
□ excludeAgent used where rules should only apply to one agent
```

### Deployment verification
```
□ Instruction files committed to base branch (not just feature branch)
□ Test PR opened touching files that match various applyTo patterns
□ Copilot review requested
□ Review comments verified against instruction rules
□ Any ignored instructions refined for specificity
□ Re-review tested after pushing additional commits
```

---

## Non-Determinism

Copilot code review is non-deterministic. The same instruction may produce different results across:
- Different PRs
- Different runs on the same PR (re-review)
- Different file contexts within the same PR

### What this means

- Not every instruction will be followed on every review
- Some reviews may miss violations that others catch
- The same rule may be applied with varying strictness

### How to work with non-determinism

1. **Don't rely on Copilot as the sole enforcer** — use it alongside linters, CI checks, and human review
2. **Write more rules than strictly necessary** — redundancy across related rules increases the chance at least one triggers
3. **Put critical rules at the top** — they're more likely to be processed within context limits
4. **Evaluate over 10+ PRs** — single-PR results are not reliable indicators
5. **Use branch protection rules** for hard requirements — Copilot's "Comment" reviews don't block merges
6. **Iterate based on patterns** — if a rule is consistently ignored, it likely needs to be more specific


---

## Evaluating Existing Instruction Files

When a repository already has instruction files, use this systematic evaluation before making changes. Do not discard existing files without assessment.

### Evaluation checklist

For each existing instruction file, run through this checklist:

| # | Check | Command or method | Expected result |
|---|---|---|---|
| 1 | Character count | `wc -m < file` | Under 4,000 |
| 2 | Frontmatter validity | Check first line is `---`, `applyTo` is quoted string | Valid YAML |
| 3 | File location | File is under `.github/instructions/` (scoped) or `.github/` (root) | Correct directory |
| 4 | Glob coverage | `find . -path "./<applyTo>" -type f \| wc -l` | Matches intended files |
| 5 | SMSA per rule | Each rule is Specific, Measurable, Actionable, Semantic | All four criteria met |
| 6 | Linter overlap | `grep -r "rule-keyword" .eslintrc* biome.json golangci*` | No matches (not duplicated) |
| 7 | Cross-file conflicts | Compare rules across files with overlapping `applyTo` | No contradictions |

### Rating scale

| Rating | Meaning | Action |
|---|---|---|
| Good (5+ checks pass) | Architecture is sound, rules need tightening | Refine in place |
| Fair (3-4 checks pass) | Structure is OK but content is weak | Rewrite rules, keep architecture |
| Poor (0-2 checks pass) | Fundamentally broken architecture | Recreate with justification |

### Common findings and fixes

| Finding | Fix |
|---|---|
| Rules are too vague ("write clean code") | Rewrite with SMSA criteria |
| Root file is bloated (> 3,500 chars) | Move framework-specific rules to scoped files |
| Scoped files duplicate root rules | Remove duplicates from scoped files |
| `applyTo` glob does not match any files | Fix glob or remove file |
| Multiple files with contradicting rules | Narrow scopes or align guidance |

---

## Glob Verification Recipes

Always verify glob patterns match the intended files before committing instruction files.

### Basic verification

```bash
# Test a specific applyTo pattern
find . -path "./src/api/**/*.ts" -type f | head -20

# Count matches
find . -path "./src/api/**/*.ts" -type f | wc -l
```

### Brace expansion verification

```bash
# Test brace expansion patterns
find . -path "./src/**/*.ts" -type f -o -path "./src/**/*.tsx" -type f | head -20

# Note: find does not support {ts,tsx} brace expansion natively.
# Use -o (OR) to combine multiple -path patterns instead.
```

> **Important:** The `find` command does not support `{ts,tsx}` brace expansion. Use `-path "*.ts" -o -path "*.tsx"` to verify patterns that use brace expansion in `applyTo`. GitHub Copilot's glob engine does support brace expansion, but verification with `find` requires the expanded form.

### Coverage analysis

```bash
# Find files NOT covered by any instruction file's applyTo
# Step 1: List all source files
find . -type f -name "*.ts" -o -name "*.tsx" | sort > /tmp/all-files.txt

# Step 2: List files covered by each instruction file's applyTo
find . -path "./src/api/**/*.ts" -type f | sort > /tmp/covered.txt

# Step 3: Find uncovered files
comm -23 /tmp/all-files.txt /tmp/covered.txt
```

---

## Conflict Diagnosis Between Overlapping Scopes

When two instruction files have overlapping `applyTo` patterns, their rules are concatenated for files that match both patterns. This can cause conflicts.

### Diagnosis steps

1. **Identify overlapping files**: Find files that match multiple `applyTo` patterns

```bash
# For each pair of instruction files, check for overlap
find . -path "./pattern-A" -type f | sort > /tmp/scope-a.txt
find . -path "./pattern-B" -type f | sort > /tmp/scope-b.txt
comm -12 /tmp/scope-a.txt /tmp/scope-b.txt  # files in both scopes
```

2. **Compare rules for conflicts**: For each overlapping file, the rules from both instruction files apply. Check whether any rules in file A contradict rules in file B.

3. **Classify the overlap**:
   - **Additive**: Rules complement each other (acceptable)
   - **Redundant**: Same rule in both files (remove from broader scope)
   - **Contradictory**: Rules disagree (fix immediately)

### Resolution strategies

| Overlap type | Fix |
|---|---|
| Additive | No action needed — this is the intended design |
| Redundant | Remove the rule from the broader-scoped file |
| Contradictory | Narrow `applyTo` patterns until scopes no longer overlap, OR align the rules |
