# Comment Correlation

## Why Read Existing Comments First

Most AI review tools operate in a vacuum — they review the PR as if no one has looked at it before. This causes:

- **Duplicate findings**: Flagging issues already raised by human reviewers
- **Contradictory feedback**: Suggesting changes that conflict with resolved discussions
- **Noise**: Adding to an already-long review thread without new value
- **Context blindness**: Missing nuance from prior conversations

Reading existing comments first lets you:

- Avoid duplication entirely
- Build on prior reviewer insights
- Identify unresolved threads that need attention
- Understand the author's intent from their responses

A review that ignores prior discussion is not a review — it's a monologue. The goal is to participate in the conversation, not restart it.

---

## How to Fetch Existing Review State

### Step 1: Fetch All Reviews

```bash
gh api repos/{owner}/{repo}/pulls/{N}/reviews
```

Each review object contains:

| Field          | Description                                              |
|----------------|----------------------------------------------------------|
| `author`       | Who submitted the review                                 |
| `state`        | `APPROVED`, `CHANGES_REQUESTED`, `COMMENTED`, `DISMISSED`|
| `body`         | The review summary text (may be empty for inline-only)   |
| `submitted_at` | When the review was submitted                            |

Build a reviewer summary table from this data:

```
| Reviewer | State              | Date       | Key Concerns                   |
|----------|--------------------|------------|--------------------------------|
| @alice   | CHANGES_REQUESTED  | 2024-03-14 | Auth bypass in middleware       |
| @bob     | COMMENTED          | 2024-03-15 | Performance concern on query    |
| CI Bot   | APPROVED           | 2024-03-15 | All checks passed              |
```

This table tells you immediately: who has looked at this PR, what their stance is, and what they care about. If someone requested changes and those changes haven't been addressed, that context shapes your entire review.

### Step 2: Fetch All Review Comment Threads

```bash
gh api repos/{owner}/{repo}/pulls/{N}/comments --paginate
```

Each thread contains:

| Field         | Description                                                   |
|---------------|---------------------------------------------------------------|
| `isResolved`  | Whether the author marked the thread as resolved              |
| `isOutdated`  | Whether the code has changed since the comment was made       |
| `isCollapsed` | Whether GitHub collapsed it (usually means outdated)          |
| `comments`    | Array of comments in the thread (original comment + replies)  |

Each comment within a thread contains:

| Field       | Description                            |
|-------------|----------------------------------------|
| `path`      | File path the comment is attached to   |
| `line`      | Line number in the diff                |
| `body`      | The comment text                       |
| `author`    | Who wrote the comment                  |
| `createdAt` | Timestamp                              |

### Step 3: Fetch General PR Comments

```bash
gh api repos/{owner}/{repo}/issues/{N}/comments
```

General comments are not attached to specific lines — they appear in the PR conversation tab. These often contain:

- Status updates from the author ("Pushed a fix for the auth issue")
- Discussion about approach or design decisions
- Bot comments (CI results, deployment previews, coverage reports)
- Review summaries from other AI tools

Do not skip these. An author comment saying "I intentionally left the validation loose because the upstream service handles it" changes whether you should flag missing validation.

### Step 4: Build the Already-Reviewed Map

Create a data structure that maps every reviewed location to its current status:

```json
{
  "src/auth/middleware.ts": [
    {
      "lines": [42, 55],
      "issue": "Missing null check on user.role",
      "status": "resolved",
      "reviewer": "@alice",
      "thread_id": "T123"
    },
    {
      "lines": [78, 82],
      "issue": "Performance: N+1 query in loop",
      "status": "active",
      "reviewer": "@bob",
      "thread_id": "T456"
    }
  ],
  "src/api/routes/users.ts": [
    {
      "lines": [15, 20],
      "issue": "Input validation missing",
      "status": "outdated",
      "reviewer": "@alice",
      "thread_id": "T789"
    }
  ]
}
```

Status values and how to determine them:

| Status       | Condition                                                 |
|--------------|-----------------------------------------------------------|
| `resolved`   | `isResolved == true`                                      |
| `active`     | `isResolved == false` AND `isOutdated == false`           |
| `outdated`   | `isOutdated == true` (code changed since comment)         |
| `dismissed`  | Parent review state is `DISMISSED`                        |

---

## How to Use the Already-Reviewed Map During Review

This is the decision tree you follow for every finding you are about to report. Before writing any comment, check the already-reviewed map.

### Rule 1: Do Not Duplicate Resolved Threads

If a thread is marked `resolved`, the reviewer and author agreed on a resolution. Do **NOT** re-raise the same issue unless one of these conditions is true:

1. **The resolution is incorrect** — you can see the code still has the bug despite the thread being marked resolved
2. **The resolution introduced a new problem** — the fix created a different issue
3. **The code changed post-resolution** — a subsequent commit reintroduced the concern

Decision tree:

```
Found an issue on file:line →
  Is there a resolved thread on the same file and overlapping lines?
    YES → Read the thread. Was the concern the same as yours?
      YES → Read the current code. Is the fix actually applied?
        YES → SKIP. Do not comment.
        NO  → RE-RAISE with note: "This was resolved in thread T123,
              but the current code at line X still exhibits the issue."
      NO  → Your concern is different. Proceed with your comment.
    NO  → Proceed with your comment.
```

### Rule 2: Acknowledge Active Unresolved Threads

If a thread is `active` (not resolved, not outdated), another reviewer's concern is still open. Your options:

- **Agree**: "I agree with @bob's observation about the N+1 query on line 78 — this will cause latency issues at scale."
- **Extend**: "Building on @bob's comment, this N+1 pattern also affects the `/admin` endpoint at line 134."
- **Disagree** (rare, but valid): "I think @bob's concern about the N+1 is mitigated by the batch loader on line 90 — but worth confirming."

What you must **NOT** do: post a separate, independent finding about the exact same issue. This fragments the discussion and forces the author to respond in two places.

Decision tree:

```
Found an issue on file:line →
  Is there an active thread on the same file and overlapping lines?
    YES → Read the thread. Is the concern the same?
      YES → Do NOT post a new comment. Instead, reference it
            in your review summary: "I concur with @bob (T456)."
      NO  → Your concern is different. Proceed, but reference
            proximity: "Separately from the discussion at line 78..."
    NO  → Proceed with your comment.
```

### Rule 3: Recheck Outdated Threads

If a thread is `outdated` (code changed since the comment was made), the author may have addressed the concern — or may not have.

Decision tree:

```
Found an issue on file:line →
  Is there an outdated thread on the same file?
    YES → Read the original concern. Read the current code.
      Was the concern addressed by the code change?
        YES → SKIP. Optionally note in summary: "T789: addressed by latest push."
        NO  → RE-RAISE: "Previously flagged by @alice in T789 —
              the concern may still apply after the latest changes."
    NO  → Proceed with your comment.
```

### Rule 4: Detect Patterns Across Threads

Before writing your review, look at the collection of existing threads as a whole:

| Pattern                                    | What It Means                              | Action                                          |
|--------------------------------------------|--------------------------------------------|------------------------------------------------|
| Multiple reviewers flag the same concern   | High confidence it's a real issue          | Elevate severity in your review                 |
| Author pushes back on a finding            | May be valid context you're missing        | Read the pushback carefully before re-raising   |
| Many unresolved threads                    | PR may need significant rework             | Note this in your summary                       |
| All threads resolved                       | Prior reviewers are satisfied              | Focus on what they might have missed            |
| No prior reviews at all                    | You're the first reviewer                  | Full review, no deduplication needed            |

---

## Detecting Review Comment Conventions

Different teams and bots use different conventions. Detect and respect these patterns so you can parse prior comments accurately.

### CodeRabbit / Copilot Bot Comments

Automated review bots typically:

- Use badge or emoji headers to denote sections
- Embed severity in formatting (bold, color indicators, headers)
- Include code suggestions in fenced markdown blocks
- Group findings by file or category

Parse these like human comments. They may have already caught what you would find. If a bot flagged the same issue you see, do not duplicate it — reference it.

### Conventional Comments Format

Some teams use the [Conventional Comments](https://conventionalcomments.org/) format. Look for these label prefixes:

| Label        | Meaning                                    |
|--------------|--------------------------------------------|
| `praise:`    | Positive feedback                          |
| `nitpick:`   | Minor, non-blocking style issue            |
| `suggestion:`| Proposed improvement                       |
| `issue:`     | Something that needs to be fixed           |
| `question:`  | Reviewer needs clarification               |
| `thought:`   | Reviewer thinking aloud, not actionable    |
| `chore:`     | Maintenance task                           |
| `note:`      | FYI, no action needed                      |
| `todo:`      | Should be done but not necessarily now      |
| `security:`  | Security concern                           |
| `bug:`       | Defect found                               |
| `breaking:`  | Breaking change detected                   |

These may also carry decorations that indicate blocking status:

- `(blocking)` — must be resolved before merge
- `(non-blocking)` — can be addressed later
- `(if-minor)` — only fix if the change is small

When you see `(blocking)` on an active thread, treat it as high priority in your summary.

### Emoji Severity Indicators

Some reviewers use emoji to signal severity:

| Emoji          | Meaning              |
|----------------|----------------------|
| 🔴 / ❌ / 🚨  | Critical / Blocker   |
| 🟡 / ⚠️       | Important / Warning  |
| 🟢 / ✅        | Suggestion / Minor   |
| 💡 / ℹ️        | Question / Info      |

Map these to your own severity scale when building the already-reviewed map. A 🔴 on an active thread is a blocking issue — flag it prominently.

---

## Including Existing Review State in Your Output

In the synthesis and output phase, always include a section summarizing the existing review state. This is not optional — it is part of a complete review.

```markdown
### Existing Review Threads

| Thread | File                         | Status        | Reviewer | Issue                                            |
|--------|------------------------------|---------------|----------|--------------------------------------------------|
| T123   | src/auth/middleware.ts:42     | ✅ Resolved   | @alice   | Null check on user.role                          |
| T456   | src/auth/middleware.ts:78     | ⏳ Active     | @bob     | N+1 query in loop                                |
| T789   | src/api/routes/users.ts:15   | ⚠️ Outdated   | @alice   | Input validation — rechecked, now addressed      |

**Summary:** 1 active thread needs resolution. 1 resolved. 1 outdated (addressed by latest push).
```

This gives the PR author a complete picture of review status across all reviewers, not just your findings. It transforms your review from "here are my isolated observations" into "here is the full state of this PR's review."

---

## Quick Reference: The Full Decision Flow

```
For each finding you are about to report:

1. Search already_reviewed map for same file + overlapping lines
   → No match? Post your comment normally.
   → Match found? Continue to step 2.

2. Check thread status:
   → Resolved?
      Read current code. Still broken? Re-raise with context.
      Fixed? Skip entirely.
   → Active?
      Same concern? Reference the existing thread, do not duplicate.
      Different concern? Post separately, note the proximity.
   → Outdated?
      Read current code. Concern addressed? Skip.
      Still present? Re-raise, credit original reviewer.

3. Before finalizing your review:
   → Summarize all existing threads in your output
   → Note any patterns (multiple flags, pushback, unresolved count)
   → Call out active blocking threads explicitly
```

This flow ensures every comment you post adds genuine value to the review conversation.

---

## Conversation-Level Review State

Not all review feedback is inline code comments. Some PRs have strategic discussion in general PR comments — team disagreements about approach, design-level feedback, or scope questions that do not attach to any specific line.

### Classification

| Category | Location | Example | How to handle |
|---|---|---|---|
| **Inline threads** | Attached to specific file + line | "This null check is missing on line 42" | Map to your clusters; deduplicate against your findings |
| **Conversation-level** | General PR comments (not attached to code) | "I disagree with the deprecation approach" | Classify as strategic discussion; summarize in output |

### Handling conversation-level feedback

1. **Read all general PR comments** via `gh api repos/{owner}/{repo}/issues/{N}/comments` or MCP `issue_read` with `get_comments` method
2. **Identify strategic disagreements** — these are approach/design concerns, not code bugs
3. **Do not try to resolve team disagreements** — note both sides in your review state summary
4. **Do not map conversation comments to code lines** — they represent positions, not code issues
5. **Reflect conversation state in your output** using a dedicated section:

```markdown
### Team Discussion State

- **Active debate:** [topic]. @alice argues [position A]; @bob argues [position B].
- **Your observation (if any):** [technical evidence, or "No additional technical evidence to add."]
```

### Steering note

A common mistake is treating conversation-level comments as inline review threads. If a reviewer posts a general comment saying "I think we should use a different approach," that is strategic discussion, not a code-level finding. Summarize it; do not anchor it to a file and line number.

## Steering notes

> These notes capture real mistakes observed during derailment testing.

1. **The most common correlation failure is ignoring bot comments.** Dependabot, CodeQL, and linter bots produce review findings that count as prior review state. Treat them identically to human comments for deduplication.
2. **Resolved threads are not "gone."** A resolved thread means the participants agreed the issue was addressed. Before re-raising the same concern, re-read the current code to confirm the fix was actually implemented. Only re-raise if the bug is still present.
3. **General PR comments (not attached to code lines) represent strategic discussion.** Do not try to map them to specific file:line references. Summarize the positions in your review output under a "Team Discussion" heading.
4. **Thread classification must happen before per-cluster review.** Build the already-reviewed map in Phase 4, not during Phase 6. Skipping Phase 4 leads to duplicate findings -- the single most common review quality failure.
5. **Mixed human-and-bot review state requires priority ordering.** When a human and a bot flagged the same issue, the human's conclusion takes precedence for deduplication purposes.

> **Cross-reference:** See `references/automation.md` for interpreting bot findings and `references/communication.md` for phrasing when extending or referencing existing threads.
