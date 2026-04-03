# File Organization And Naming

## Use This When
- Setting up a new Convex backend project.
- Deciding where to put a new function file.
- Naming exported functions that Swift will call.
- Reviewing project structure for consistency.

## Recommended Structure

```
convex/
├── schema.ts          ← always first — your DB blueprint
├── auth.config.ts     ← auth provider setup
├── functions.ts       ← userQuery/userMutation (via convex-helpers)
│
├── users.ts           ← CRUD for users table
├── messages.ts        ← CRUD for messages table
├── channels.ts        ← CRUD for channels table
│
├── payments.ts        ← payment flow (mutation + internal action)
├── search.ts          ← full-text search queries
├── crons.ts           ← scheduled jobs
│
└── _generated/        ← auto-generated, never edit
```

## Naming Conventions

### Export Names Map To Swift Function Names

```typescript
// convex/messages.ts
export const list = query(...)           // → "messages:list"
export const getById = query(...)        // → "messages:getById"
export const send = mutation(...)        // → "messages:send"
export const edit = mutation(...)        // → "messages:edit"
export const remove = mutation(...)      // → "messages:remove" (not "delete")
```

From Swift:

```swift
client.subscribe(to: "messages:list", yielding: [Message].self)
try await client.mutation("messages:send", with: ["body": text])
```

### Internal Functions

```typescript
export const getByToken = internalQuery(...)
export const createIfNotExists = internalMutation(...)
export const callDeepgram = internalAction(...)
```

## Rules
1. **One file per entity or feature** — keeps related logic together.
2. **Name exports after what they do** — `list`, `send`, `remove`, not `queryMessages`.
3. **Default to `internal`** — only expose what Swift actually calls.
4. **Keep auth wrappers in `functions.ts`** — `userQuery`/`userMutation` via `convex-helpers`.
5. **Separate `"use node"` actions** — cannot mix with queries/mutations in the same file.
6. **Always include argument validators** — even on internal functions.

## Avoid
- Naming the auth wrapper file `helpers.ts`; the official WorkoutTracker pattern uses `functions.ts` for `userQuery`/`userMutation`.
- Putting multiple unrelated entities in one file.
- Exposing internal functions as public exports.
- Omitting argument validators on internal functions.
- Mixing `"use node"` actions with queries or mutations in the same file.

## Read Next
- [05-internal-functions-and-helpers.md](05-internal-functions-and-helpers.md)
- [04-auth-rules-and-server-ownership.md](04-auth-rules-and-server-ownership.md)
- [01-schema-document-model-and-relationships.md](01-schema-document-model-and-relationships.md)
