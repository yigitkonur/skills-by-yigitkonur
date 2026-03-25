# Anti-Patterns, Troubleshooting, and Verification

Read this before finalizing any Greptile configuration output.

---

## Anti-Patterns

### 1. Vague rules
```json
{ "rule": "Follow best practices" }
{ "rule": "Write clean code" }
{ "rule": "Be careful with this code" }
```
**Problem:** The LLM has no concrete criteria to evaluate against.
**Fix:** Make every rule a pass/fail checklist item with specific, measurable criteria.

### 2. Comma-separated scope
```json
{ "scope": "**/*.ts, **/*.js" }
```
**Problem:** `scope` must be an array. A string will silently fail to match.
**Fix:** `{ "scope": ["**/*.ts", "**/*.js"] }`

### 3. Comments in JSON
```json
{
  // This is a comment — INVALID JSON
  "strictness": 2
}
```
**Problem:** JSON does not support comments. Parse error causes the entire config to be silently ignored.
**Fix:** Remove all comments. Use `rules.md` for documentation.

### 4. Trailing commas
```json
{
  "strictness": 2,
  "rules": [],
}
```
**Problem:** Invalid JSON. Config silently ignored.
**Fix:** Remove trailing comma after the last element.

### 5. Array-format ignorePatterns
```json
{ "ignorePatterns": ["dist/**", "*.generated.*"] }
```
**Problem:** `ignorePatterns` expects a newline-separated string.
**Fix:** `{ "ignorePatterns": "dist/**\n*.generated.*" }`

### 6. Rules a linter should handle
```json
{ "rule": "Use semicolons at end of statements" }
{ "rule": "Indent with 2 spaces" }
```
**Problem:** Wastes Greptile's semantic reasoning on syntactic trivia that ESLint/Prettier already handles.
**Fix:** Use Greptile only for rules that require understanding — architecture, security, cross-file implications.

### 7. Unscoped high-volume rules
```json
{ "rule": "Use async/await instead of callbacks" }
```
**Problem:** Fires on every file including config, scripts, tests — creates noise.
**Fix:** Add `"scope": ["src/**/*.ts"]` to target production code only.

### 8. Full URLs in patternRepositories
```json
{ "patternRepositories": ["https://github.com/acme/shared-utils"] }
```
**Problem:** Format must be `org/repo`, not a URL.
**Fix:** `{ "patternRepositories": ["acme/shared-utils"] }`

### 9. Wrong way to suppress status messages
**Problem:** Setting `statusCommentsEnabled: false` does not suppress "X files reviewed, no comments" messages.
**Fix:** Use `{ "statusCheck": true }` instead.

### 10. Expecting ignorePatterns to affect indexing
**Problem:** `ignorePatterns` only skips review, not indexing. Large binaries are still indexed and may cause errors.
**Fix:** For indexing exclusions, contact Greptile support.

---

## Agent Steering — Common Execution Mistakes

These are mistakes that AI agents commonly make when executing the init-greptile-review skill. Each entry describes the mistake, why it happens, and how to avoid it.

### Mistake 1: Dumping 20+ generic rules
**What happens:** Agent generates a long list of "best practice" rules copied from general coding guidelines, not tied to the specific repository.
**Why:** The agent treats rule generation as a brainstorming exercise instead of an evidence-based process.
**Prevention:** Every rule must reference a specific file path, library, or pattern observed in the repository. If you can't point to concrete evidence, don't write the rule.

### Mistake 2: Duplicating linter coverage
**What happens:** Rules like "use semicolons", "prefer const", "no console.log" that ESLint/Prettier already handle.
**Why:** The agent doesn't check what linters exist before writing rules.
**Prevention:** In Phase 1, inventory all linters/formatters. In Phase 4, for each rule ask: "Could ESLint/Pylint/RuboCop catch this?" If yes, delete the rule.

### Mistake 3: Unscoped rules firing on everything
**What happens:** Rules with `scope: ["**/*.ts"]` that fire on config files, test files, scripts, and everything else.
**Why:** The agent defaults to broad globs instead of targeting the specific directories where the rule matters.
**Prevention:** Every rule scope should target specific directories (e.g., `src/api/**/*.ts`), not the entire repo.

### Mistake 4: Forgetting the output format
**What happens:** Agent outputs raw JSON or code blocks only, without the file tree, local file writes, reasoning annotations, or canary test.
**Why:** Phase 6 output requirements are easy to skip under pressure to "just ship the config."
**Prevention:** Use the output checklist: file tree → write files in the repo when filesystem access exists (unless the user asked for draft-only output) → file contents → reasoning annotations → canary rule → migration notes. If any is missing, you're not done.

### Mistake 5: Using array format for ignorePatterns
**What happens:** `"ignorePatterns": ["dist/**", "node_modules/**"]` — silently fails.
**Why:** Most config systems use arrays. Greptile's ignorePatterns is a newline-separated string.
**Prevention:** Always use `"ignorePatterns": "dist/**\nnode_modules/**"` (string with `\n`).

### Mistake 6: Setting strictness:1 globally
**What happens:** Agent sets the strictest level repo-wide, creating excessive noise on every PR.
**Why:** Agent assumes "stricter is better" without considering the signal-to-noise tradeoff.
**Prevention:** Use `strictness: 2` as default. Only use `1` for security/payments/compliance paths. Use `3` for internal tools.

### Mistake 7: Including READMEs and changelogs in files.json
**What happens:** Context files include `README.md` and `CHANGELOG.md` which provide no actionable review context.
**Why:** Agent treats any markdown file as a potential context file.
**Prevention:** Context files must provide information needed to validate correctness (schemas, API specs, architecture docs). READMEs describe the project; they don't help review code changes.

### Mistake 8: Skipping the canary test
**What happens:** Config is deployed but never verified. Silent failures go unnoticed.
**Why:** Canary testing seems optional or tedious.
**Prevention:** Always include a canary rule in the output. Explain to the user: add canary → open test PR → verify → remove canary.

---

## Troubleshooting Chain

When rules are not being applied, reason through this sequence:

```
Is the repo indexed?
  Dashboard → Repos → Status must be "Indexed"
  NO → Wait for indexing, or re-trigger
  ↓
Is the JSON valid?
  Paste into jsonlint.com or run: python3 -m json.tool config.json
  NO → Fix syntax errors — config is silently ignored on parse failure
  ↓
Does .greptile/ coexist with greptile.json?
  YES → .greptile/ wins. greptile.json is ignored entirely.
  ↓
Is the config on the source branch of the PR?
  Config is read from source branch, not target.
  NO → Push config to the PR's source branch
  ↓
Is the scope correct? Do the globs match the changed files?
  Test with a recursive glob check (see troubleshooting.md → Issue 2)
  NO → Fix glob patterns
  ↓
Is strictness too high?
  strictness: 3 suppresses medium/low severity issues
  MAYBE → Temporarily set strictness: 1 to test
  ↓
Is the author excluded? → Check excludeAuthors
Is the branch excluded? → Check excludeBranches
Is the PR too large? → Check fileChangeLimit
  ↓
Force trigger: comment @greptileai review this on the PR
```

---

## Testing & Verification Protocol

After deploying any config change:

### Step 1 — Canary test
Add a trivially triggerable rule:
```json
{
  "id": "canary",
  "rule": "No TODO comments allowed in production code.",
  "scope": ["**/*.ts"],
  "severity": "low"
}
```
Create a PR with `// TODO: canary test` and verify Greptile catches it within 2-3 minutes.

### Step 2 — Check indexing status
Dashboard → Repositories → Your repo → Status must be "Indexed".
If "Indexing" or "Failed", config will not be applied.

### Step 3 — Verify "Last Applied" timestamp
Dashboard → Custom Context → Rules tab → "Last Applied" column.
- Timestamp updates within 2-3 min → config is working
- Stuck on "Never" → repo not indexed or rule never triggered
- Force trigger: comment `@greptileai review` on any open PR

### Step 4 — Remove canary rule
Once verified, remove the canary rule to avoid noise.

---

## Preflight Checklist

Run through this checklist before delivering any Greptile configuration:

### JSON validity
- [ ] `python3 -m json.tool .greptile/config.json` passes
- [ ] No comments in JSON (invalid syntax, causes silent ignore)
- [ ] No trailing commas (invalid JSON)

### Format correctness  
- [ ] Every `scope` is an array of strings: `["src/**"]`
- [ ] `ignorePatterns` is a newline-separated string: `"dist/**\nnode_modules/**"`
- [ ] `strictness` is exactly 1, 2, or 3
- [ ] `commentTypes` only contains `"logic"`, `"syntax"`, `"style"`, `"info"`
- [ ] `patternRepositories` uses `org/repo` format, never full URLs

### Rule quality
- [ ] 5-10 rules maximum (start lean)
- [ ] Every rule is tied to specific repo evidence (file paths, libraries, patterns)
- [ ] No rule duplicates what a linter can catch
- [ ] Every rule has a `scope` array targeting relevant directories
- [ ] Every disableable rule has a unique `id`
- [ ] Rules tell the developer what TO DO, not just what to avoid

### Context files
- [ ] Every `files.json` path points to a file that actually exists
- [ ] Context files are scoped to relevant directories
- [ ] No READMEs, changelogs, or generic docs in context files

### Output completeness
- [ ] File tree showing `.greptile/` structure
- [ ] If filesystem access exists, the `.greptile/` files were written or updated in the repo before printing them
- [ ] Complete file contents for every generated file
- [ ] Reasoning annotations tied to repo evidence
- [ ] Canary test rule included
- [ ] Migration notes (if replacing greptile.json)
