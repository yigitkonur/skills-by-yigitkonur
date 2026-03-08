# Anti-Patterns and Common Mistakes

Common mistakes teams make when writing Copilot code review instruction files, and how to avoid them.

## Table of Contents

1. [File-Level Mistakes](#file-level-mistakes)
2. [Rule-Level Mistakes](#rule-level-mistakes)
3. [Architecture Mistakes](#architecture-mistakes)
4. [Debugging Sequence](#debugging-sequence)
5. [Verification Protocol](#verification-protocol)

---

## File-Level Mistakes

### Exceeding the 4,000-character limit

**The mistake:** Writing a comprehensive instruction file that exceeds 4,000 characters. Content beyond this limit is silently ignored — no warning is shown.

**Why it's bad:** Your most important rules might end up past the cutoff if you put boilerplate or low-priority content first.

**Fix:** Split the file into two or more micro-files with narrower `applyTo` scopes. Aim for 2,500–3,500 characters per file.

### Missing or invalid frontmatter on *.instructions.md

**The mistake:**
```markdown
# TypeScript Rules
- Use strict types
```

**Why it's bad:** Without `applyTo` frontmatter, the file applies to nothing. Copilot ignores it entirely.

**Fix:**
```markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Rules
- Use strict types
```

### Blank lines before frontmatter

**The mistake:**
```markdown

---
applyTo: "**/*.py"
---
```

**Why it's bad:** YAML frontmatter must start at line 1. A blank line before `---` causes the frontmatter to be treated as regular markdown.

**Fix:** Ensure `---` is the very first line of the file with no preceding whitespace or blank lines.

### Wrong file location

**The mistake:** Placing `*.instructions.md` files in `.github/` root or a custom directory like `.github/review-rules/`.

**Why it's bad:** Copilot only reads `*.instructions.md` from `.github/instructions/` directory.

**Fix:** Always place micro-files in `.github/instructions/`. The root `copilot-instructions.md` goes in `.github/`.

---

## Rule-Level Mistakes

### Vague, unactionable rules

**Bad:**
```markdown
- Write good code
- Handle errors properly
- Follow best practices
```

**Why it's bad:** These are too vague for Copilot to act on. It can't determine what "good code" or "best practices" means in your specific context.

**Good:**
```markdown
- All API handlers must wrap async operations in try-catch blocks
- Use `AppError` class for business logic errors, not raw Error
- Log errors with structured format: { error, requestId, userId, action }
```

### Rules that duplicate linters

**Bad:** (when ESLint + Prettier are configured)
```markdown
- Use 2-space indentation
- Add semicolons at end of statements
- Put opening braces on the same line
- Sort imports alphabetically
```

**Why it's bad:** These are already enforced by the linter. Including them wastes your 4,000-character budget on rules that add no value.

**Good:** Focus on semantic rules the linter can't catch:
```markdown
- Custom hooks must start with `use` and accept an options object as the last parameter
- Server Components must not import from `@/lib/client-utils`
- API route handlers must call `requireAuth()` before any data access
```

### Trying to modify Copilot behavior

**Bad:**
```markdown
- Use bold text for critical issues
- Add emoji severity indicators (🔴 🟡 🟢)
- Include a summary table at the top of the review
- Rate overall code quality on a 1-10 scale
```

**Why it's bad:** Copilot code review doesn't support formatting changes, summary modifications, or behavioral overrides. These instructions are ignored and waste character budget.

**Good:** Focus on WHAT to check, not HOW to present it.

### External links

**Bad:**
```markdown
- Follow the TypeScript style guide at https://google.github.io/styleguide/tsguide.html
- See our internal wiki for error handling patterns: https://wiki.company.com/error-handling
```

**Why it's bad:** Copilot cannot follow external links. The linked content is never loaded.

**Fix:** Copy the relevant content directly into the instruction file:
```markdown
## Error Handling Pattern
- Use Result<T, AppError> pattern for all service functions
- Never throw from service layer; return error results
- Controller layer converts error results to HTTP responses
```

### Attempting absolute enforcement

**Bad:**
```markdown
- ALWAYS use exactly this pattern for every function
- NEVER allow any function longer than 30 lines
- MUST reject any PR that doesn't have 100% test coverage
```

**Why it's bad:** Copilot is non-deterministic and advisory. It cannot block PRs or guarantee 100% detection. Heavy-handed language doesn't make it more reliable.

**Good:** State rules clearly but accept that Copilot provides guidance, not enforcement:
```markdown
- Functions should be concise (under ~50 lines) — flag when significantly longer
- New features should include unit tests covering the main path and error cases
```

---

## Architecture Mistakes

### Everything in one file

**The mistake:** Putting TypeScript rules, Python rules, security rules, testing rules, and API conventions all in `copilot-instructions.md`.

**Why it's bad:**
- Easily exceeds 4,000 characters
- TypeScript rules get applied to Python files and vice versa
- Hard to maintain as the project grows

**Fix:** One `copilot-instructions.md` for universal rules + multiple `*.instructions.md` files scoped by `applyTo`.

### Overlapping scopes with conflicting rules

**The mistake:**
```
typescript.instructions.md  → applyTo: "**/*.{ts,tsx}"  → "Prefer interfaces over types"
react.instructions.md       → applyTo: "**/*.{tsx,jsx}" → "Prefer type aliases over interfaces"
```

**Why it's bad:** A `.tsx` file matches both patterns and receives contradictory guidance.

**Fix:** Ensure rules across overlapping files are complementary, not contradictory. Use non-overlapping scopes when rules genuinely differ, or pick one convention and apply it consistently.

### Monorepo files that repeat root rules

**The mistake:** Root `copilot-instructions.md` says "no hardcoded secrets" and `packages-api.instructions.md` repeats "no hardcoded secrets."

**Why it's bad:** Wastes character budget with redundant rules. The root file already applies to all files in the monorepo.

**Fix:** Package-specific files should contain ONLY rules unique to that package. Universal rules belong in the root file only.

### Too many instruction files

**The mistake:** Creating 30+ micro-files with 2-3 rules each.

**Why it's bad:** When too many files match a single PR file, the combined instruction set may be harder for Copilot to prioritize. Maintaining 30 files also becomes a burden.

**Fix:** Aim for 5-12 instruction files total. Combine closely related concerns into a single file when they share the same `applyTo` scope.

---

## Debugging Sequence

When Copilot doesn't seem to follow your instructions:

### Step 1: Verify file location
```bash
ls -la .github/copilot-instructions.md
ls -la .github/instructions/*.instructions.md
```
Confirm files are in the correct directories.

### Step 2: Check character count
```bash
wc -c .github/copilot-instructions.md
for f in .github/instructions/*.instructions.md; do echo "$f: $(wc -c < "$f") chars"; done
```
Any file over 4,000 characters has content being silently dropped.

### Step 3: Validate frontmatter
Open each `*.instructions.md` and verify:
- `---` is on line 1 (no blank lines above)
- `applyTo` is present and quoted
- Closing `---` is present
- Glob pattern actually matches your files

### Step 4: Test glob pattern match
Mentally (or with `find`) check that your glob pattern matches the files you're reviewing:
```bash
# Does **/*.{ts,tsx} match src/components/Button.tsx?
# Yes — ** matches src/components/, *.tsx matches Button.tsx
```

### Step 5: Check for rule conflicts
Read all instruction files that would apply to a specific file and look for contradictions.

### Step 6: Assess rule specificity
Vague rules ("write good code") are effectively noise. Rewrite as specific, measurable directives.

### Step 7: Test incrementally
Comment out most rules and leave only 2-3. If those work, add rules back in small batches to identify what breaks.

---

## Verification Protocol

Before deploying instruction files to a repository, verify:

### Format verification
- [ ] `copilot-instructions.md` is at `.github/copilot-instructions.md`
- [ ] All micro-files are in `.github/instructions/`
- [ ] All micro-files have valid YAML frontmatter with `applyTo`
- [ ] No file exceeds 4,000 characters
- [ ] Frontmatter starts at line 1 with no preceding blank lines

### Content verification
- [ ] No external links (Copilot can't follow them)
- [ ] No UX/formatting modification instructions
- [ ] No rules duplicating existing linter/formatter configuration
- [ ] Rules are specific and measurable
- [ ] Code examples use actual project patterns
- [ ] Security rules are positioned near the top of relevant files

### Architecture verification
- [ ] Universal rules are in `copilot-instructions.md` only
- [ ] Language-specific rules are in `*.instructions.md` with correct `applyTo`
- [ ] No contradictions between overlapping files
- [ ] No redundant rules across files
- [ ] Monorepo package files don't repeat root-level rules
- [ ] Total file count is 5-12 (not too few, not too many)

### Deployment verification
- [ ] Open a test PR touching files that match various `applyTo` patterns
- [ ] Request Copilot review
- [ ] Verify that instructions are reflected in the review comments
- [ ] Note any instructions that seem to be ignored for further refinement
