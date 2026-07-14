# Effect-TS v4 Syntax — Strictly Forbidden in v3 Code
Use this quarantine page to recognize syntax from another major line and rewrite it to Effect v3 before it leaks into any other file.

## Symptom — Bad Code
The symptom is a token that looks plausible but does not belong in this v3 skill. The wrong token must stay on this page only.

❌ WRONG: ServiceMap.Service is v4 syntax; do not write it in v3 code.
✅ v3 equivalent: use Context.Tag from `import { Context } from "effect"`.

❌ WRONG: ServiceMap.Reference is v4 syntax; do not write it in v3 code.
✅ v3 equivalent: use Context.Reference from `import { Context } from "effect"`.

❌ WRONG: Schema.TaggedErrorClass is v4-style syntax for this skill; do not use it in v3 examples.
✅ v3 equivalent: use Schema.TaggedError or Data.TaggedError from `import { Schema, Data } from "effect"`.

❌ WRONG: Effect.catch(...) is v4 catch-all shorthand; do not use the bare catch form in v3 code.
✅ v3 equivalent: use Effect.catchAll, Effect.catchTag, or Effect.catchTags.

❌ WRONG: Effect.forkChild is v4 syntax; do not use it in v3 code.
✅ v3 equivalent: use Effect.fork.

❌ WRONG: Effect.forkDetach is v4 syntax; do not use it in v3 code.
✅ v3 equivalent: use Effect.forkDaemon.

❌ WRONG: Schema.makeUnsafe is v4 construction syntax; do not use it in v3 code.
✅ v3 equivalent: use Schema.decodeUnknownSync for checked synchronous decoding.

❌ WRONG: Result module is v4 syntax; do not import or model core v3 outcomes with it.
✅ v3 equivalent: use Either for values or Exit for completed Effect outcomes.

❌ WRONG: import "effect/unstable/..." is v4 unstable import style; do not use it in v3 code.
✅ v3 equivalent: import from "@effect/platform" or a named v3 package when the API is outside core `effect`.

## Why Bad
These tokens train agents to mix major lines. Even when a nearby concept exists in v3, the name, import, or recovery API differs enough to produce invalid or misleading code.
Keeping every forbidden token quarantined here makes repository-wide leakage checks meaningful. If a search finds one of these names outside this file, rewrite that file to the v3 equivalent.

## Fix — Correct Pattern
Use only the v3 equivalents named directly after each wrong line above. In normal reference files, write the v3 pattern directly and do not mention the forbidden token at all.

```typescript
import { Context, Data, Effect, Either, Exit, Schema } from "effect"

class Database extends Context.Tag("Database")<
  Database,
  { readonly query: Effect.Effect<ReadonlyArray<string>> }
>() {}

class UserNotFoundError extends Data.TaggedError("UserNotFoundError")<{
  readonly id: string
}> {}

const UserId = Schema.String
const parseUserId = Schema.decodeUnknownSync(UserId)

declare const loadUser: (id: string) => Effect.Effect<string, UserNotFoundError>

const program = loadUser(parseUserId("u-1")).pipe(
  Effect.catchTag("UserNotFoundError", () => Effect.succeed("anonymous"))
)

const asEither: Either.Either<string, UserNotFoundError> = Either.right("ok")
const asExit: Exit.Exit<string, UserNotFoundError> = Exit.succeed("ok")
void program
void asEither
void asExit
```

## Cross-references
See also: [migration overview](../migration/01-overview.md), [context tags](../services-layers/02-context-tag.md), [schema decoding](../schema/10-decoding.md), [AI hallucinations](18-ai-hallucinations.md).
