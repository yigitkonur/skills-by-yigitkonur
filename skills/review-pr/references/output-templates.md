# Output Templates

Templates for structuring the review output in the synthesis and output phase.

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

### Template selection rule

- **Compact template** — PRs under 500 changed lines with 5 or fewer findings
- **Full template** — PRs over 500 changed lines, or PRs with more than 5 findings
- **Always include** — at least one 🎯 Praise finding with specific evidence

### Steering note: Present, don't submit

Present the completed review to the user in the conversation. **Do not submit it to GitHub** (via `gh pr review --submit` or MCP tools) unless the user explicitly asks you to submit or post it. This prevents accidental review submissions on the wrong PR or with unintended verdicts.

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **Template selection happens once at the start of Phase 8, not per-finding.** Choose compact or full based on PR size AND finding count, then use that template consistently. Do not mix template formats within a single review.
2. **The compact template is for PRs under 500 changed lines with 5 or fewer findings.** If a small PR has many findings, use the full template -- the compact format cannot accommodate detailed evidence for 6+ issues.
3. **Present the review to the user -- do not auto-submit to GitHub.** Unless the user explicitly says "submit", "post", or "publish", present your review as a chat message. This prevents accidental submissions on the wrong PR or with unintended severity.
4. **The verdict line must match the findings.** If all findings are suggestions and questions, the verdict is Approve or Comment, never Request Changes. Only escalate to Request Changes when at least one finding is a genuine Blocker.
5. **Every template instantiation must include at least one Praise finding.** Reviews with zero positive observations appear adversarial. Find something specific and genuine to acknowledge.

> **Cross-reference:** See `references/severity-guide.md` for verdict-to-severity mapping rules and `references/communication.md` for tone guidance within findings.
