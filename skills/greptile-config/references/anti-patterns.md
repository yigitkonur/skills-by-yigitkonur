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

## Troubleshooting Chain

When rules are not being applied, reason through this sequence:

```
Is the repo indexed?
  Dashboard → Repos → Status must be "Indexed"
  NO → Wait for indexing, or re-trigger
  ↓
Is the JSON valid?
  Paste into jsonlint.com or run: python -m json.tool config.json
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
  Test with: npx glob "src/api/**/*.ts"
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
