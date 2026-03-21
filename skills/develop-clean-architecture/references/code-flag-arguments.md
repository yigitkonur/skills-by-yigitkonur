---
title: Eliminate Flag Arguments — Split Into Distinct Functions
impact: MEDIUM-HIGH
impactDescription: removes hidden branching, makes each function do exactly one thing
tags: code, functions, flag-arguments, srp
---

## Eliminate Flag Arguments — Split Into Distinct Functions

A boolean flag argument announces the function does more than one thing. Uncle Bob calls flag arguments "a truly terrible practice." Split into two distinct, honest functions with clear names.

**Incorrect (flag argument hides two behaviors):**

```typescript
function getUser(id: UserId, includeDeleted: boolean): Promise<User | null> {
  if (includeDeleted) {
    return db.query('SELECT * FROM users WHERE id = $1', [id]);
  }
  return db.query('SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL', [id]);
}

// Caller intent is obscured
const user = await getUser(id, true);   // What does true mean?
const user2 = await getUser(id, false); // What does false mean?
```

**Correct (two distinct, self-documenting functions):**

```typescript
function getActiveUser(id: UserId): Promise<User | null> {
  return db.query('SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL', [id]);
}

function getArchivedUser(id: UserId): Promise<User | null> {
  return db.query('SELECT * FROM users WHERE id = $1 AND deleted_at IS NOT NULL', [id]);
}

// Caller intent is immediately clear
const user = await getActiveUser(id);
const archived = await getArchivedUser(id);
```

**When NOT to use this pattern:**
- Configuration objects with many optional fields — these are not flag arguments
- Private helper methods where the boolean drives a minor variation in a single algorithm

**Benefits:**
- Each function does exactly one thing — SRP at the function level
- No ambiguity at call sites — function name reveals intent
- Easier to test — each function has a single code path
- LSP autocomplete shows all available variants clearly

Reference: [Clean Code, Ch. 3 — Functions: Flag Arguments](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
