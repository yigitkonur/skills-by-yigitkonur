# Scope Disambiguation — What to Audit

Phase 1 Step 1 picks a scope. Wrong scope → wrong audit — too narrow misses real gaps, too broad produces noise and a 100-row table the user won't read. This file is the picking guide.

## The four default scopes

Without user guidance, match the request to one of these.

### Session scope

**Definition**: Every task this conversation has been asked to address, since the session started.

**When to use**: User says "audit what we just did", "check what we finished today", "wrap up this session".

**Sources to scan**:
- Messages: from the first user message to now
- Tool trace: every Edit/Write/Bash call this session
- TodoList: current state
- Git: commits made during the session (use commit timestamps / session start as boundary)
- Tests: runs during this session
- Bash: filesystem ops this session

**Risk**: session boundaries can be fuzzy. If you can't tell when the "current session" started, pick the most recent user message that opened a distinct ask.

### Plan scope

**Definition**: The tasks in a specific named plan — a plan file on disk, a TodoList, or a numbered list in a user message.

**When to use**: User references a plan ("check the plan at `docs/implementation-plan.md`", "audit the items from your TodoList", "go through the six points I listed earlier").

**Sources to scan**:
- The plan itself (primary)
- Cross-reference: messages, tool trace, git, tests for each plan item
- TodoList: if that's the plan

**Risk**: plans are rarely exhaustive. The audit may surface `Not Planned` tasks that emerged from implementing the plan. Include them with explicit status; don't silently drop.

### Branch scope

**Definition**: Everything on the current git branch since it diverged from the base (usually `main`).

**When to use**: User says "audit this branch", "check what's in this PR", "before I merge, what's done".

**Sources to scan**:
- Git: `git log origin/main..HEAD` and `git diff origin/main...HEAD`
- Messages / tool trace: for context on why each commit was made
- Tests: branch-local runs
- PR body + linked issue: for declared scope

**Risk**: branch scope can hide tasks that were deferred or queued but not committed. Cross-check with messages and TodoList.

### PR scope

**Definition**: The commits + TODO comments + linked issues on an open PR.

**When to use**: User references a PR ("audit PR #42", "is PR #42 ready to merge").

**Sources to scan**:
- PR body and description
- Linked issues
- Commits on the PR
- Reviewer comments (if any exist — check via `gh pr view $N --json reviews,comments`)
- TODO comments in changed files (`grep -rn "TODO\|FIXME" <changed-paths>`)
- CI status (`gh pr checks $N`)

**Risk**: PR scope can miss out-of-PR follow-ups the author planned. Ask if there's a companion plan.

## Custom scopes

If the user explicitly lists what's in scope, use that list verbatim. E.g.:

> "Audit these five things: 1. auth flow, 2. session storage, 3. the OAuth callback, 4. the rate-limit rule, 5. the deploy script."

→ audit exactly these five, under session or branch source scan (ask which).

Custom scopes are allowed to be narrower than default scopes — if the user says "only audit the auth work", treat auth-related artifacts as in scope and mark other work as `Out of Scope` with rationale.

## Picking when the user is ambiguous

If the user's request is "audit what's done" without a clear scope hint:

1. If there's an active TodoList in the session → default to **session scope** (the TodoList is the anchor)
2. Else if the current git branch has commits ahead of main → default to **branch scope**
3. Else if there's a plan file referenced anywhere → default to **plan scope**
4. Else → default to **session scope**, and state the choice

Always state the picked scope in the audit's intro. The user can course-correct with one message.

## When to split an audit

Sometimes the picked scope is correct but produces too large a table (100+ tasks). Split strategies:

### Split by domain

Backend tasks + frontend tasks + docs tasks as separate audits, each a focused table. Useful when the session covered multiple domains.

### Split by branch of work

If the session had a main feature + drive-by fixes + refactors, audit each cluster separately.

### Split by priority

If most tasks are low-priority polish, split into "shipping-critical" (full audit) and "polish backlog" (summary-only with statuses, no evidence per row).

When splitting, produce one intro + table per split. Do not bury splits in sections of a single document; they read as separate audits.

## When to narrow an audit

If the picked scope is broader than needed, narrow explicitly:

- User asks "audit what's done" right after a focused sub-session on one topic → narrow to that topic, state the narrowing
- Session has been multi-day with lots of noise → narrow to the most recent productive block

Narrowing is legitimate; hiding work from the user is not. If you narrow, the audit intro must say "narrowed from <broader scope> because <reason>" so the user can expand if they want.

## When scope is unresolvable

Very occasionally, the user's ask genuinely doesn't map to any scope. E.g.:

> "Audit what's done."

…in a session with no TodoList, no git history, no plan file, and only one message ("audit what's done").

Options:

1. **Ask once** for a scope — legitimate use of a clarifying question
2. **Scan what's available** (messages + whatever else exists) and produce a minimal audit with a note that scope was unclear

Do not produce a fake audit with no real scope. The table would be empty or generic, which misleads.

## Scope-change mid-audit

If mid-Phase-1 the audit reveals the scope itself was wrong — e.g., the user asked for "session scope" but the real ask is actually "branch scope" — pause once, re-declare scope, restart Phase 1. Do not try to patch a scope mismatch mid-table.

## Out-of-scope rows

`Out of Scope` rows are legitimate but require documentation per `status-taxonomy.md`. Typical uses:

- User mentioned something in passing but explicitly said "not this session"
- The audit caught a tangential concern that belongs to a different skill / different session / different project
- Something came up during tool use (e.g., Edit opened an unrelated file) that isn't part of the intended work

Do not use `Out of Scope` to hide work you don't want to do. That's a rationalization — see `rationalizations.md`.
