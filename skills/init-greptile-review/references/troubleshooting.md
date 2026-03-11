# Troubleshooting & Verification

Comprehensive debugging guide for Greptile configuration issues. Read before finalizing any output.

---

## Diagnostic Flowchart

When Greptile reviews are not working as expected, follow this chain:

```
Is the repo indexed?
  Dashboard → Repos → Status must be "Indexed"
  ├── "Not Connected" → Install/reinstall GitHub App or GitLab webhook
  ├── "Indexing" → Wait (5-30 min for first index)
  ├── "Failed" → Check repo access permissions, re-trigger from dashboard
  └── "Indexed" → Continue ↓

Is the JSON valid?
  Validate: python -m json.tool .greptile/config.json
  Or paste into jsonlint.com
  ├── Parse error → Fix syntax. Config is SILENTLY ignored on parse failure
  └── Valid → Continue ↓

Does .greptile/ coexist with greptile.json?
  ├── Yes → .greptile/ wins. greptile.json is ignored entirely. Delete one.
  └── No → Continue ↓

Is the config on the correct branch?
  Config is read from the SOURCE branch of the PR, not the target.
  ├── Config only on main → Push to the PR's source branch first
  └── Config on source branch → Continue ↓

Are the scope patterns correct?
  Test globs: npx glob "src/api/**/*.ts"
  Or: find . -path "./src/api/**/*.ts"
  ├── No matches → Fix glob patterns
  └── Matches → Continue ↓

Is strictness filtering the issue?
  strictness: 3 suppresses medium and low severity
  ├── Maybe → Temporarily set strictness: 1 to test
  └── No → Continue ↓

Is the author/branch/label filtered?
  ├── Check excludeAuthors
  ├── Check excludeBranches
  ├── Check disabledLabels
  └── Check includeAuthors (empty = ALL, not none)

Is the PR too large?
  ├── Check fileChangeLimit (0 = skip ALL PRs)
  └── Reduce file count or increase limit

Force trigger:
  Comment @greptileai review this on the PR
```

---

## Common Issues

### Issue 1: Config Silently Ignored

**Symptoms**: Rules not applying, reviews use default settings, no error messages.

**Causes** (check in order):
1. Invalid JSON (comments, trailing commas, syntax errors)
2. Both `.greptile/` and `greptile.json` exist (`.greptile/` silently wins)
3. Config not committed to the source branch of the PR
4. File not named exactly `config.json` inside `.greptile/`

**Fix**:
```bash
# Validate JSON syntax
python -m json.tool .greptile/config.json

# Check for coexistence
ls -la greptile.json .greptile/config.json 2>/dev/null

# Verify on correct branch
git log --oneline -1 -- .greptile/config.json
```

### Issue 2: Scope Not Matching Files

**Symptoms**: Rule exists but never triggers on relevant files.

**Causes**:
1. Scope is a string instead of array: `"scope": "src/**"` vs `"scope": ["src/**"]`
2. Glob pattern too narrow or wrong syntax
3. Scope targets wrong directory structure

**Fix**:
```bash
# Test glob patterns locally
npx glob "src/api/**/*.ts"

# List actual file paths
find . -name "*.ts" -path "*/api/*" | head -20
```

**Common scope mistakes**:
```json
// WRONG: comma-separated string (silently fails)
{ "scope": "src/api/**/*.ts, src/routes/**/*.ts" }

// CORRECT: array of strings
{ "scope": ["src/api/**/*.ts", "src/routes/**/*.ts"] }

// WRONG: missing ** for recursive matching
{ "scope": ["src/*.ts"] }  // only matches src/file.ts, not src/sub/file.ts

// CORRECT: recursive glob
{ "scope": ["src/**/*.ts"] }
```

### Issue 3: ignorePatterns Not Working

**Symptoms**: Files in ignore list still receive review comments.

**Causes**:
1. `ignorePatterns` is an array instead of newline-separated string
2. Patterns too specific (missing recursive glob)
3. Confusion between review ignore and index ignore

**Fix**:
```json
// WRONG: array format
{ "ignorePatterns": ["dist/**", "*.generated.*"] }

// CORRECT: newline-separated string
{ "ignorePatterns": "dist/**\n*.generated.*\nnode_modules/**" }
```

**Important**: `ignorePatterns` only skips **review**, not **indexing**. Files are still indexed and available as context. For indexing exclusions, contact Greptile support.

### Issue 4: Reviews Not Triggering

**Symptoms**: No review posted on new PRs.

**Checklist**:
1. Is the repo indexed? (Dashboard → Repos)
2. Is the PR author excluded? (`excludeAuthors`)
3. Is the target branch excluded? (`excludeBranches`)
4. Does the PR have a disabled label? (`disabledLabels`)
5. Is `skipReview` set to `"AUTOMATIC"`?
6. Does the PR exceed `fileChangeLimit`?
7. Is the author included? (`includeAuthors: []` means ALL)

**Force trigger**: Comment `@greptileai review this` on the PR.

### Issue 5: Too Many Comments (Noise)

**Symptoms**: Greptile comments on trivial issues, every PR gets 20+ comments.

**Fixes**:
1. Increase strictness: `"strictness": 3` (critical only)
2. Remove `"style"` from commentTypes
3. Remove `"info"` from commentTypes
4. Add scope to broad rules
5. Add ignore patterns for test files, generated code
6. Check if rules duplicate what ESLint/Prettier already catches

### Issue 6: "X Files Reviewed, No Comments" Spam

**Symptoms**: Greptile posts empty review summaries on clean PRs.

**Fix**: Use `statusCheck` instead of trying to disable status comments:
```json
{
  "statusCheck": true
}
```

This posts a GitHub status check instead of a comment, which is silent when passing.

**Not the fix**: `statusCommentsEnabled: false` does not suppress these messages.

### Issue 7: includeAuthors Confusion

**Symptoms**: Reviews only for specific authors, or no reviews at all.

**Key insight**: `includeAuthors: []` (empty array) means **ALL authors**. It does NOT mean "no authors."

```json
// Reviews ALL authors (default behavior)
{ "includeAuthors": [] }

// Reviews ONLY these authors
{ "includeAuthors": ["alice", "bob"] }
```

### Issue 8: fileChangeLimit Set to 0

**Symptoms**: No PRs are reviewed at all.

**Cause**: `fileChangeLimit: 0` means **skip ALL PRs**. The minimum is 1.

```json
// WRONG: skips every PR
{ "fileChangeLimit": 0 }

// CORRECT: skip PRs with more than 100 changed files
{ "fileChangeLimit": 100 }

// CORRECT: no limit (omit the field entirely)
{}
```

### Issue 9: patternRepositories Format

**Symptoms**: Cross-repo context not loading.

**Fix**: Use `org/repo` format, never full URLs:
```json
// WRONG
{ "patternRepositories": ["https://github.com/acme/shared-utils"] }

// CORRECT
{ "patternRepositories": ["acme/shared-utils"] }
```

### Issue 10: Dashboard Rules vs Repo Rules Conflict

**Symptoms**: Unexpected rules appearing, or expected rules missing.

**Precedence** (highest wins):
```
1. Org-enforced rules (cannot override)
2. .greptile/ folder
3. greptile.json
4. Dashboard defaults
```

Check the dashboard for org-level rules that may override or conflict with repo-level config.

---

## Verification Protocol

After deploying any configuration change, run this verification:

### Step 1: Validate JSON Locally

```bash
# Validate syntax
python -m json.tool .greptile/config.json > /dev/null && echo "Valid" || echo "INVALID"

# Check for common mistakes
cat .greptile/config.json | python3 -c "
import json, sys
config = json.load(sys.stdin)

# Check scope arrays
for r in config.get('rules', []):
    scope = r.get('scope')
    if isinstance(scope, str):
        print(f'ERROR: Rule {r.get(\"id\", \"unnamed\")} has string scope, must be array')

# Check ignorePatterns
ip = config.get('ignorePatterns')
if isinstance(ip, list):
    print('ERROR: ignorePatterns must be newline-separated string, not array')

# Check strictness
s = config.get('strictness')
if s is not None and s not in [1, 2, 3]:
    print(f'ERROR: strictness must be 1, 2, or 3 (got {s})')

# Check commentTypes
ct = config.get('commentTypes', [])
valid_types = {'logic', 'syntax', 'style', 'info'}
for t in ct:
    if t not in valid_types:
        print(f'ERROR: Invalid commentType {t}')

# Check fileChangeLimit
fcl = config.get('fileChangeLimit')
if fcl is not None and fcl < 1:
    print(f'ERROR: fileChangeLimit must be >= 1 (got {fcl})')

print('Validation complete')
"
```

### Step 2: Deploy Canary Rule

Add a trivially triggerable rule:
```json
{
  "id": "canary",
  "rule": "No TODO comments allowed in production code.",
  "scope": ["**/*.ts"],
  "severity": "low"
}
```

### Step 3: Create Test PR

1. Create a branch with `// TODO: canary test` in a scoped file
2. Open a PR targeting the configured branch
3. Wait 2-3 minutes

### Step 4: Verify Results

| Check | Where | Expected |
|-------|-------|----------|
| Review posted | PR comments | Canary rule triggered |
| Status check | PR checks tab | `greptile/review` visible |
| Dashboard update | Custom Context → Rules → "Last Applied" | Timestamp within last 5 min |
| Indexing status | Dashboard → Repos | "Indexed" |

### Step 5: Clean Up

1. Remove the canary rule from config
2. Close the test PR
3. Verify production rules on the next real PR

---

## Migration: greptile.json → .greptile/

### Step-by-Step

1. Create `.greptile/` directory
2. Extract `customContext.rules` → `.greptile/config.json` `rules` array
3. Extract `customContext.files` → `.greptile/files.json`
4. Extract `instructions` → `.greptile/rules.md`
5. Move top-level settings (`strictness`, etc.) → `.greptile/config.json`
6. Delete `greptile.json`

### Before (greptile.json)
```json
{
  "strictness": 2,
  "instructions": "Focus on security",
  "customContext": {
    "rules": [{ "rule": "No raw SQL", "scope": ["src/db/**"] }],
    "files": [{ "path": "docs/arch.md", "description": "Architecture" }]
  }
}
```

### After (.greptile/ folder)

`.greptile/config.json`:
```json
{
  "strictness": 2,
  "rules": [
    { "id": "no-raw-sql", "rule": "No raw SQL", "scope": ["src/db/**"], "severity": "high" }
  ]
}
```

`.greptile/files.json`:
```json
{
  "files": [
    { "path": "docs/arch.md", "description": "Architecture" }
  ]
}
```

`.greptile/rules.md`:
```markdown
## Security Focus
Focus on security implications in all code changes.
```

**Critical**: Delete `greptile.json` after migration. If both exist, `.greptile/` silently wins and `greptile.json` is ignored.

---

## When to Contact Support

- Indexing stuck in "Failed" state after re-trigger
- Need to exclude files from indexing (not just review)
- API rate limit increase requests
- Self-hosted or VPC deployment questions
- SOC2 compliance documentation
- Data deletion requests
