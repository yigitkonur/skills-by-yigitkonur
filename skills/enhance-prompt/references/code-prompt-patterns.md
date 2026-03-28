# Code Prompt Patterns

Patterns specific to prompts that target coding agents (Claude Code, Codex, Aider, etc.)

## The File-Path Anchor

If the user mentions specific files, anchor the prompt to them:

```
# Weak:
"Fix the authentication bug"

# Enhanced:
"Fix the auth token refresh bug in src/middleware/auth.ts. The token
expiration check on line ~45 doesn't account for clock skew."
```

File paths give the agent a starting point. Without them, it searches the entire codebase.

## The Tech Stack Declaration

State the stack ONLY when non-obvious or when the agent might guess wrong:

```
# Needed (non-obvious stack choice):
"This project uses Bun, not Node — use Bun.serve() not Express."

# NOT needed (obvious from project files):
"This is a React project" — the agent will see package.json
```

## The Scope Fence

Coding agents love to "improve" things. Fence the scope:

```
"Scope: ONLY these changes:
1. Add the /reset-password endpoint
2. Add the token generation util
3. Add tests for both

Do NOT: refactor existing auth code, update docs, add types to
unchanged files, or reorganize imports."
```

## The Verification Ladder

For code changes, verification should be specific:

```
"Verification:
1. Run `npm test` — all tests pass (including new ones)
2. Run `npm run lint` — no new warnings
3. Manual check: curl the new endpoint and confirm 200 response
4. Confirm no unintended changes: `git diff --stat` shows only expected files"
```

## The "Read Before Write" Pattern

For unfamiliar codebases, tell the agent to orient first:

```
"Before making changes:
1. Read src/routes/ to understand the routing pattern
2. Read src/middleware/auth.ts to understand the auth flow
3. Check src/utils/ for existing helper functions you can reuse
Then implement using the patterns you observed."
```

## The Migration vs Greenfield Signal

Agents approach existing code differently from new code. Be explicit:

```
# Migration (modify existing):
"This is an EXISTING endpoint. Modify it to also accept JSON body
in addition to query params. Don't break the existing query param
interface — it must remain backwards-compatible."

# Greenfield (create new):
"Create a NEW endpoint /api/v2/users that returns paginated results.
There is no v1 to be compatible with."
```

## Anti-Patterns to Block

Common coding agent mistakes to pre-empt:

| Agent tendency | Block with |
|---|---|
| Creates test framework from scratch | "Use the existing test setup in tests/setup.ts" |
| Adds excessive error handling | "Match the error handling style of existing endpoints" |
| Installs new dependencies | "Use only existing dependencies unless absolutely necessary" |
| Rewrites touched files entirely | "Surgical changes only — minimize diff" |
| Adds TypeScript types to every file it reads | "Only add types to new code you write" |
| Creates helper/util files for one-time use | "Inline the logic — no new util files for single-use functions" |
