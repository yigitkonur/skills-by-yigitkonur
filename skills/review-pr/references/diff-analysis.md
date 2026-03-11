# Diff Analysis Techniques

How to read and understand complex diffs effectively during PR review.

## Understanding unified diff format

```
--- a/src/auth/middleware.ts
+++ b/src/auth/middleware.ts
@@ -42,7 +42,12 @@ export function authMiddleware(req, res, next) {
-  if (user.role === 'admin') {
+  if (user.role === 'admin' || user.role === 'superadmin') {
     return next();
   }
+
+  if (user.permissions?.includes(req.requiredPermission)) {
+    return next();
+  }
+
   return res.status(403).json({ error: 'Forbidden' });
```

**Reading the parts:**
- `--- a/` and `+++ b/` — the file paths (before and after)
- `@@ -42,7 +42,12 @@` — hunk header: starting line and count in old file (`-42,7`) and new file (`+42,12`); the text after `@@` shows the enclosing function name
- Lines starting with `-` — removed from the old version
- Lines starting with `+` — added in the new version
- Lines with no prefix — unchanged context lines (shows surrounding code)

## Diff reading strategies

### Strategy 1: Intent-first reading
1. Read the hunk header to understand WHERE you are in the file
2. Read the context lines (no prefix) to understand the SURROUNDING code
3. Read the `-` lines to understand WHAT WAS THERE
4. Read the `+` lines to understand WHAT REPLACED IT
5. Ask: Does the replacement achieve the same intent? Does it change behavior?

### Strategy 2: Change-type classification
Classify each hunk as:
- **Behavioral change** — logic, conditions, return values changed. HIGH attention.
- **Structural change** — function extraction, class reorganization, file moves. MEDIUM attention.
- **Additive change** — new function, new endpoint, new test. Review as new code.
- **Removal** — code deleted. Check: was it dead code? is anything still referencing it?
- **Cosmetic change** — formatting, renaming, comments. LOW attention (skip if linter exists).

### Strategy 3: When diff is not enough
Situations where you MUST read the full file (use `git show <ref>:<path>` or `gh api repos/{owner}/{repo}/contents/{path}?ref={ref}`):
- The diff shows a change inside a function but you can't see the function signature
- The diff shows a new call to a function defined elsewhere
- The diff modifies error handling but you can't see the try/catch scope
- The diff adds code that depends on variables defined above the hunk
- The diff changes conditional logic but the condition involves variables from outside the hunk

### Strategy 4: Comparing head vs base
When you need to understand the FULL behavior change:
```bash
# Get the base (before) version
git show <base-branch>:<path/to/file>
# Or via API:
gh api repos/{owner}/{repo}/contents/{path}?ref={base-branch}

# Get the head (after) version
git show <head-branch>:<path/to/file>
# Or via API:
gh api repos/{owner}/{repo}/contents/{path}?ref={head-branch}
```
Compare the two versions to understand:
- What function signatures changed
- What imports were added/removed
- What exports changed (API surface)

## Red flags in diffs

| Red flag | What to look for |
|----------|-----------------|
| Large hunk with many changes | Complex refactor — check for behavioral changes hidden in structural changes |
| Deleted error handling | Was this intentional? Check if error is handled elsewhere now |
| New dependency import | Is this dependency necessary? Is it a known secure version? |
| Changed test assertions | Was the test weakened to make it pass? |
| Commented-out code | Why not deleted? If it's "just in case," flag it |
| TODO/FIXME/HACK added | Technical debt being introduced — is it tracked? |
| Magic numbers changed | What do the old and new values mean? |
| Catch block with just console.log | Error swallowed — is this intentional? |
| `any` type added (TypeScript) | Type safety weakened |
| `# type: ignore` or `@ts-ignore` | Type system bypassed |
| `eslint-disable` | Linting rule bypassed — why? |

## Handling large diffs (>500 lines)

1. Start with `gh api repos/{owner}/{repo}/pulls/{N}/files --paginate` to see the file-level summary (additions/deletions per file)
2. Identify the files with the MOST changes — these are your priority
3. Read those file diffs carefully
4. For files with <10 line changes, do a quick scan only
5. Note in your review which files you deeply reviewed vs skimmed

## Steering note: Deprecation and refactor diffs

Deprecation diffs are deceptive: they often look like small, safe changes. The real review target is not the changed lines but the **unchanged call sites** that still use the old API.

When reviewing a deprecation diff:
1. **Search beyond the diff** — use grep or code search to find all call sites of the deprecated API
2. **Check semantic equivalence** — does the new API return the same value/type as the old one?
3. **Verify runtime warnings** — are callers notified they are using a deprecated path?
4. **Check test coverage** — do tests exercise both the old (deprecated) and new paths?
