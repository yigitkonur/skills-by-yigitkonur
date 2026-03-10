# Output Templates

Templates for structuring the review output in Phase 7.

## Full review template

```markdown
## PR Review: <PR title> (#<number>)

**Reviewed:** <date>
**Base:** `<base-branch>` ← `<head-branch>`
**Files changed:** <count> (+<additions>/-<deletions>)
**CI status:** <✅ All passing | ⚠️ N failures | ⏳ Pending>

### Summary

<1-2 sentences: What the PR does and whether it achieves its stated goal.>

### Verdict: <✅ Approve | 💬 Comment | 🔄 Request Changes>

<Brief justification for the verdict.>

---

### 🔴 Blockers (<count>)

> Issues that must be fixed before merge.

#### [B1] <Title>
**File:** `path/to/file.ts:42-45`
**Dimension:** Security / Correctness / Data Integrity

<Description of the issue.>

**Evidence:**
<What the code does — quote the relevant lines.>

**Expected:**
<What the code should do.>

**Suggested fix:**
```<language>
<code suggestion>
```

---

### 🟡 Important (<count>)

> Issues that should be addressed but may not block merge.

#### [I1] <Title>
**File:** `path/to/file.ts:78`
**Dimension:** Performance / Error Handling

<Description, evidence, suggestion — same format as blockers.>

---

### 🟢 Suggestions (<count>)

> Non-blocking improvements.

- **[S1]** `path/to/file.ts:105` — <Brief suggestion>
- **[S2]** `path/to/other.ts:23` — <Brief suggestion>

---

### 💡 Questions (<count>)

> Items needing author clarification before a final assessment.

- **[Q1]** `path/to/file.ts:67` — <Question about intent or behavior>
- **[Q2]** General — <Question about approach or scope>

---

### 🎯 Positive Observations

- <Something done well — always include at least one>
- <Good test coverage, clean error handling, clear naming, etc.>

---

### Existing Review Threads

| # | File | Status | Reviewer | Issue |
|---|------|--------|----------|-------|
| 1 | `src/auth/middleware.ts:42` | ✅ Resolved | @alice | Null check |
| 2 | `src/auth/middleware.ts:78` | ⏳ Active | @bob | N+1 query |

---

### File Clusters Reviewed

| Cluster | Files | Lines | Review Depth |
|---------|-------|-------|-------------|
| Auth/Security | 3 | +146/-20 | Deep |
| API Routes | 2 | +112/-5 | Deep |
| Frontend | 3 | +168/-23 | Standard |
| Tests | 4 | +234 | Standard |
| Config | 1 | +2/-1 | Skimmed |

---

### Test Coverage Assessment

<Are the changes adequately tested? What's missing?>
```

## Compact review template (for small PRs <100 lines)

```markdown
## PR Review: <PR title> (#<number>)

**Verdict: <✅ Approve | 💬 Comment | 🔄 Request Changes>**

<2-3 sentence summary covering goal achievement and any findings.>

<Findings if any, using inline format:>
- 🔴 `file:line` — <issue and suggestion>
- 🟡 `file:line` — <issue and suggestion>
- 🟢 `file:line` — <suggestion>
- 🎯 <positive observation>
```

## Finding format (per finding)

Each finding MUST include:
1. **Severity icon** — 🔴/🟡/🟢/💡
2. **Title** — concise description of the issue
3. **File location** — `path/to/file.ts:42` (or line range `42-48`)
4. **Dimension** — which review dimension it falls under
5. **Description** — what's wrong and why it matters
6. **Evidence** — the specific code or behavior
7. **Suggestion** — how to fix it (code block preferred)

## Verdict decision matrix

| Condition | Verdict |
|-----------|---------|
| No blockers, ≤2 important, goal achieved | ✅ Approve |
| No blockers, has questions that need answers | 💬 Comment |
| No blockers, >2 important findings | 💬 Comment (lean toward Request Changes) |
| Any blockers | 🔄 Request Changes |
| Goal validation failed | 🔄 Request Changes |
| CI failing on critical checks | 🔄 Request Changes |
