# Enhancement Layers — Detailed Guide

## Layer 1: Narrative Structure

Every prompt should tell a story. The agent needs three beats:

**Beat 1 — Situation:** Where are we? What exists right now?
```
"We have a FastAPI backend with SQLAlchemy models in src/models/.
The user table has email, name, and created_at fields."
```

**Beat 2 — Problem:** What needs to change? What's broken or missing?
```
"We need to add password reset functionality. Currently there's no
password reset endpoint or token generation."
```

**Beat 3 — Done:** What does the world look like when this is finished?
```
"When done: POST /auth/reset-password accepts an email, generates a
time-limited token, and sends a reset link. A second endpoint
POST /auth/confirm-reset accepts the token + new password."
```

**When the user gives a one-liner like "add password reset":**
You construct all three beats from context and reasonable assumptions. Note your assumptions.

## Layer 2: Thinking Steering

Tell the agent HOW to approach the problem, not just what the answer should be.

**Framing the mental model:**
```
"Think about this as a state machine problem — the user has states:
active, reset-requested, reset-confirmed. Design the flow around
state transitions."
```

**Sequencing the approach:**
```
"Start by reading the existing auth middleware to understand how
tokens work in this codebase. Then design the reset flow to be
consistent with that pattern."
```

**Preventing wrong approaches:**
```
"This is a migration task, not a rewrite. Don't redesign the schema —
add columns to the existing table."
```

## Layer 3: Failure Pre-emption

Predict the top 2-3 ways the agent will go wrong and block them:

| Common failure | Pre-emption |
|---|---|
| Over-scoping | "Only modify the auth module. Don't touch user registration." |
| Wrong abstraction | "Use the existing email service, don't create a new one." |
| Missing edge case | "Handle: expired tokens, already-used tokens, non-existent emails." |
| Infinite generation | "Maximum 3 files changed. If more are needed, list them and ask." |
| Guessing instead of checking | "If you're unsure about the database schema, read the migration files first." |

**The anti-refactor clause** (add when the task is a targeted change):
```
"Do NOT refactor surrounding code, add docstrings to unchanged functions,
or 'improve' anything outside the direct scope of this task."
```

## Layer 4: Context Injection (Code-Aware)

For coding agents, respect what they can already do:

**DO inject:**
- Specific file paths the user mentioned: "The auth routes are in `src/routes/auth.ts`"
- Architecture constraints: "This is a monorepo — changes in packages/api affect packages/web"
- Non-obvious context: "We use Drizzle ORM, not Prisma — the migration syntax is different"

**Do NOT inject:**
- "You can use the terminal to run commands" — they know
- "Read the file first" — they will
- "Make sure to test" — the verification layer handles this
- Technology basics — "FastAPI is a Python web framework" — the agent knows

## Layer 5: Verification and Halt

Every enhanced prompt must end with these three things:

**Verification step** — how to confirm the work is correct:
```
"After implementing, run `npm test` and verify the new tests pass.
Check that existing tests still pass too."
```

**Done signal** — the specific condition that means "stop":
```
"You're done when: the password reset flow works end-to-end,
tests pass, and no existing tests are broken."
```

**Halt condition** — when to stop and ask instead of guessing:
```
"If the email service requires credentials you don't have access to,
stop and ask — don't mock it or skip it."
```

**Examples of good halt conditions:**
- "If you need to modify more than 5 files, pause and list them first"
- "If the existing tests are failing BEFORE your changes, report that instead of trying to fix them"
- "If the API version is unclear, ask — don't assume"
