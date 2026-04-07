# Code-Level Analysis

Signals that require reading actual code/files, not just API metadata.
These go BEYOND what stars/commits/issues tell you.

## Signal 1: README Quality Assessment

```bash
# Fetch README content
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d
```

**Assess (qualitative, agent judgment):**
- Does it explain WHAT the project does in the first paragraph?
- Does it have installation instructions?
- Does it have usage examples?
- Does it have a screenshot/demo/GIF?
- Is it just a template or actually written?
- Length: <50 lines = minimal, 50-200 = solid, >500 = detailed

**Scoring:** 0=no README/template only, 3=minimal, 6=has install+usage, 10=comprehensive with examples

## Signal 2: Key File Presence

```bash
gh api repos/OWNER/REPO/contents/ \
  --jq '[.[].name] | map(select(test("tsconfig|eslint|jest|vitest|prettier|CHANGELOG|CONTRIBUTING|LICENSE|Makefile|Dockerfile|github|test|spec|__test__|ci";"i")))'
```

**Checklist (each adds 1 point, max 10):**
- [ ] LICENSE file
- [ ] CHANGELOG.md (maintained, not template)
- [ ] CONTRIBUTING.md
- [ ] .github/ directory (CI, templates)
- [ ] tsconfig.json or equivalent config (strict mode?)
- [ ] ESLint/Prettier config (linting discipline)
- [ ] Test directory (test/, spec/, __tests__/)
- [ ] Dockerfile or docker-compose (deployment ready)
- [ ] Makefile or package.json scripts (build automation)
- [ ] CI config (.github/workflows/, .circleci/, etc.)

## Signal 3: TypeScript/Lint Strictness

For TypeScript repos:
```bash
gh api repos/OWNER/REPO/contents/tsconfig.json --jq '.content' | base64 -d | jq '{strict: .compilerOptions.strict, noImplicitAny: .compilerOptions.noImplicitAny, strictNullChecks: .compilerOptions.strictNullChecks}'
```

**Scoring:** 0=no config, 5=exists but lax, 10=strict:true + CI enforcement

## Signal 4: Test Freshness

Check if test files were modified in recent commits:
```bash
gh api "repos/OWNER/REPO/commits?per_page=30" \
  --jq '[.[] | .commit.message] | map(select(test("test|spec|jest|vitest|pytest|cargo test";"i"))) | length'
```

**Scoring:** 0=no test mentions in 30 commits, 5=1-3, 10=5+ (tests actively maintained)

## Signal 5: Source Code Sampling

Read 1-2 key source files to assess code quality:

```bash
# Find the main entry point
gh api repos/OWNER/REPO/contents/src/ --jq '.[].name' 2>/dev/null || \
gh api repos/OWNER/REPO/contents/lib/ --jq '.[].name' 2>/dev/null || \
gh api repos/OWNER/REPO/contents/ --jq '[.[].name | select(test("index|main|app|server|cli";"i"))]'

# Read a key file (pick the main entry)
gh api repos/OWNER/REPO/contents/src/index.ts --jq '.content' | base64 -d | head -100
```

**Assess (qualitative):**
- Is code well-structured with clear functions/classes?
- Are there meaningful comments (not over-commented)?
- Error handling present?
- Type annotations (for TS/Python)?
- Import organization clean?
- No obvious security issues (hardcoded secrets, eval, etc.)?

This is inherently subjective. Provide a brief qualitative note, not a numeric score.

## Signal 6: Recent Commit Quality

```bash
gh api "repos/OWNER/REPO/commits?per_page=10" \
  --jq '.[] | "\(.commit.author.date[:10])\t\(.author.login // .commit.author.name)\t\(.commit.message | split("\n")[0] | .[:60])"'
```

**Assess:**
- Descriptive messages or lazy ("fix", "update", "wip")?
- Single author or multiple contributors?
- Regular cadence or burst?
- Signs of AI review bots in commit messages?

## Signal 7: PR Review Culture

```bash
# Check last 5 merged PRs for review presence
gh api "repos/OWNER/REPO/pulls?state=closed&per_page=5&sort=updated&direction=desc" \
  --jq '[.[] | select(.merged_at)] | .[:5][] | {number, title: (.title | .[:50]), reviewers: [.requested_reviewers[].login]}'
```

Then for each PR with reviews:
```bash
gh api repos/OWNER/REPO/pulls/NUMBER/reviews \
  --jq '.[] | "\(.user.login)\t\(.state)"'
```

**Look for:** CodeRabbit, Greptile, copilot, claude, coderabbit-ai (AI review bot usage = quality signal)

## Cost

3-8 REST API calls per repo (README + contents + commits + PRs + optional file reads).
Keep file reads to 2-3 max to stay token-efficient.
