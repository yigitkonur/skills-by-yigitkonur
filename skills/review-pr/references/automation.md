# Automation and Tooling for Code Review

How to use automated tools to augment manual review. The goal is to let machines handle what they're good at (consistency, completeness, speed) so human reviewers can focus on what they're good at (context, intent, design).

---

## The Review Pipeline

Structure the review pipeline so automated checks run first, human review focuses on what machines miss.

```
PR Opened
  │
  ├── Layer 1: Formatting & Style (automated, blocks merge)
  │   └── Prettier, ESLint, Black, gofmt, Ruff
  │       → If these catch issues, do NOT duplicate them in manual review
  │
  ├── Layer 2: Type Checking (automated, blocks merge)
  │   └── TypeScript compiler, mypy, pyright, go vet
  │       → Type errors are objective — let the compiler find them
  │
  ├── Layer 3: Security Scanning (automated, alerts reviewer)
  │   └── Semgrep, CodeQL, Snyk, Dependabot, GitGuardian
  │       → Review scanner output for false positives
  │       → True positives should be 🔴 Blockers
  │
  ├── Layer 4: Test Execution (automated, blocks merge)
  │   └── Unit tests, integration tests, E2E tests
  │       → Check for: new tests added? existing tests still pass?
  │
  ├── Layer 5: AI Review (automated, informs reviewer)
  │   └── GitHub Copilot Review, CodeRabbit, AI-generated summaries
  │       → Use as a starting point, not a substitute
  │       → Verify AI findings — false positive rate is ~30%
  │
  └── Layer 6: Human Review (manual, final decision)
      └── Focus on: correctness, security, design, intent, context
          → This is where the skill's Phase 1-7 workflow applies
```

### What to Skip in Manual Review

If the project has proper CI/CD, do NOT manually check for:

| Automated Check | Tool | Skip In Manual Review |
|-----------------|------|----------------------|
| Code formatting | Prettier, Black, gofmt | ✅ Skip |
| Import ordering | ESLint, isort | ✅ Skip |
| Unused imports/variables | ESLint, Ruff | ✅ Skip |
| Type errors | TypeScript, mypy | ✅ Skip |
| Known vulnerability in dependencies | Snyk, Dependabot | ✅ Skip (but verify update plan) |
| Test failures | CI test runner | ✅ Skip (but note in review if failing) |
| Spelling in comments | CSpell | ✅ Skip |

### What Machines Miss (Focus Here)

| Category | Why Machines Miss It | Manual Focus |
|----------|---------------------|-------------|
| Business logic correctness | Machines don't know the domain | Does the code do what the PR says it should? |
| Authorization logic | Context-dependent | Are the right users allowed to do the right things? |
| Race conditions | Require reasoning about concurrent execution | Read-then-write without atomicity? |
| Error handling completeness | Machines can't judge "good enough" | Are all error paths handled meaningfully? |
| API design quality | Subjective, convention-dependent | Is the API consistent with existing patterns? |
| Cross-file coordination | Most tools analyze single files | Did all coupled systems get updated together? |
| Intent vs implementation | Requires reading the PR description | Does the code match the stated goal? |

---

## Using CI Status in Review

### Reading CI Results

```bash
# Quick check — is CI passing?
gh pr checks <N> --repo owner/repo

# Detailed view — which specific checks failed?
gh pr view <N> --repo owner/repo --json statusCheckRollup \
  --jq '.statusCheckRollup[] | "\(.conclusion // .status)\t\(.name)"'

# Get logs for a failed check
gh run list --repo owner/repo --branch <head-branch> --limit 5
gh run view <run-id> --repo owner/repo --log-failed
```

### CI Status Decision Matrix

| CI Status | Review Action |
|-----------|--------------|
| All green | Proceed with review normally |
| Tests failing | Note in review. Ask: is the failure related to the PR's changes? |
| Lint/format failing | Do NOT raise style issues — CI already caught them |
| Security scan failing | Read the scan output. Escalate if true positive. |
| Build failing | Note in review. Author likely knows. |
| Checks pending | Proceed but caveat: "CI not yet complete" |
| No checks configured | Note absence — suggest adding CI if appropriate |

---

## Integrating Static Analysis Results

### Semgrep

Semgrep finds security and correctness bugs using pattern-matching rules. When a project uses Semgrep:

- Check if Semgrep rules ran on the PR (look for a check in CI)
- If Semgrep flagged issues, they appear as check annotations or bot comments
- Verify Semgrep findings — some may be false positives
- Do not re-flag issues Semgrep already caught

### CodeQL

GitHub's code scanning with CodeQL finds security vulnerabilities. When available:

- Check the "Security" tab on the PR for CodeQL alerts
- CodeQL alerts on the PR's changes are high-confidence findings
- Treat CodeQL security alerts as 🔴 Blockers unless clearly false positive

### Dependency Scanners

When Dependabot, Snyk, or npm audit finds vulnerabilities:

```bash
# Check for dependency vulnerability alerts
gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[0:5] | .[] | {package: .security_advisory.summary, severity: .security_advisory.severity}'
```

- New dependencies with known CVEs should be flagged
- Updates to dependencies that fix CVEs should be fast-tracked
- Lockfile-only changes from dependency scanners are usually safe to approve

---

## AI Review Tools Integration

### Working Alongside AI Reviews

When an AI tool (Copilot Review, CodeRabbit, etc.) has already reviewed the PR:

1. **Read the AI review first** — treat it as a first-pass review
2. **Do not duplicate AI findings** — if the AI caught it, acknowledge and move on
3. **Verify AI findings** — AI has ~30% false positive rate; check the important ones
4. **Focus on what AI missed** — intent validation, cross-file coordination, business logic
5. **Override AI severity** — AI may overweight style issues; recalibrate to your scale

### What AI Reviews Do Well

- Catching null/undefined issues
- Spotting missing error handling
- Finding potential type errors
- Detecting common vulnerability patterns (SQL injection, XSS)
- Summarizing what the PR does

### What AI Reviews Do Poorly

- Understanding business requirements
- Evaluating design decisions in context
- Detecting race conditions
- Assessing blast radius across the codebase
- Calibrating severity to the team's norms
- Understanding when "unusual" code is intentional

---

## Pre-Commit Hooks and Local Checks

When evaluating whether a project has adequate automation:

### Essential Checks (should block merge)

| Check | Tool Examples | Purpose |
|-------|---------------|---------|
| Formatting | Prettier, Black, gofmt | Eliminates style debates |
| Linting | ESLint, Ruff, clippy | Catches common mistakes |
| Type checking | tsc, mypy, pyright | Catches type errors at compile time |
| Tests | jest, pytest, go test | Verifies behavior |
| Secrets scanning | GitGuardian, detect-secrets | Prevents credential leaks |

### Valuable Checks (should warn, may not block)

| Check | Tool Examples | Purpose |
|-------|---------------|---------|
| Code coverage | c8, coverage.py | Monitors test coverage trends |
| Bundle size | bundlewatch, size-limit | Prevents frontend bloat |
| License compliance | license-checker | Prevents license conflicts |
| API contract | openapi-diff, Pact | Detects breaking API changes |
| Performance | Lighthouse CI, k6 | Detects performance regressions |

### When to Suggest Adding Automation

If during review you find yourself repeatedly flagging the same type of issue, suggest automation:

```markdown
💡 I noticed several formatting inconsistencies across the changed files.
Consider adding Prettier to the CI pipeline — it would catch these
automatically and free up review time for substantive issues.
```

Only suggest this as a general comment, not as a blocker on the current PR. Adding tooling is a separate effort.

---

## Review Efficiency Tips

### Commands for Fast Review Setup

```bash
# One-command local setup
gh pr checkout <N> --repo owner/repo && \
  git diff main...HEAD --stat && \
  echo "---" && \
  gh pr checks <N> --repo owner/repo

# Quick blast radius check
git diff main...HEAD --name-only | \
  xargs grep -l "functionName" 2>/dev/null

# Find all TODOs introduced in this PR
git diff main...HEAD | grep "^+" | grep -i "todo\|fixme\|hack\|xxx"

# Check if tests were added for changed source files
git diff main...HEAD --name-only | \
  grep -v "test\|spec\|__tests__" | \
  while read f; do
    base=$(basename "$f" | sed 's/\.[^.]*$//')
    echo "$f → $(git diff main...HEAD --name-only | grep -c "$base.*test\|$base.*spec") test file(s)"
  done
```

### Parallel Information Gathering

When starting a review, make these calls in parallel to gather all context at once:

```bash
# All in parallel (use & in bash or Promise.all in code)
gh pr view <N> --repo owner/repo --json title,body,state,author,labels,baseRefName,headRefName &
gh api repos/{owner}/{repo}/pulls/{N}/files --paginate &
gh api repos/{owner}/{repo}/pulls/{N}/reviews &
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate &
gh pr checks <N> --repo owner/repo &
wait
```
