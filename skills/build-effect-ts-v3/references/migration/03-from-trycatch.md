# From Try Catch
Use this guide to replace exception control flow with typed tagged errors and targeted recovery.

## Core Difference

Language exceptions are untyped and can skip across code that did not intend to handle them. Effect failures are values in the error channel. They compose through `Effect.gen`, can be handled by tag, and do not require language-level exception handling inside the workflow.

Keep language exception handling at foreign boundaries only. Inside Effect code, fail with typed errors and recover with Effect combinators.

## Side-by-side: JSON Parsing

| Legacy exception boundary | Effect boundary |
|---|---|
| ```typescript
type Settings = { readonly theme: string };

function parseSettings(input: string): Settings {
  try {
    return JSON.parse(input) as Settings;
  } catch (cause) {
    throw new Error("Invalid settings");
  }
}
``` | ```typescript
import { Data, Effect } from "effect";

type Settings = { readonly theme: string };

class SettingsParseError extends Data.TaggedError("SettingsParseError")<{
  readonly input: string;
  readonly cause: unknown;
}> {}

const parseSettings = (
  input: string,
): Effect.Effect<Settings, SettingsParseError, never> =>
  Effect.try({
    try: () => JSON.parse(input) as Settings,
    catch: (cause) => new SettingsParseError({ input, cause }),
  });
``` |

`Effect.try` is the synchronous equivalent of `Effect.tryPromise`. Use it when a legacy API may throw before returning a value.

## Side-by-side: Branching Failures

| Legacy thrown branches | Effect tagged branches |
|---|---|
| ```typescript
type User = { readonly id: string; readonly active: boolean };

function requireActive(user: User): User {
  if (!user.active) {
    throw new Error("Inactive user");
  }
  return user;
}
``` | ```typescript
import { Data, Effect } from "effect";

type User = { readonly id: string; readonly active: boolean };

class InactiveUserError extends Data.TaggedError("InactiveUserError")<{
  readonly id: string;
}> {}

const requireActive = (
  user: User,
): Effect.Effect<User, InactiveUserError, never> =>
  user.active
    ? Effect.succeed(user)
    : Effect.fail(new InactiveUserError({ id: user.id }));
``` |

For branch failures inside `Effect.gen`, use `return yield*` so the early exit is visible:

```typescript
import { Effect } from "effect";

const loadActiveUser = (
  id: string,
): Effect.Effect<User, UserLoadError | InactiveUserError, never> =>
  Effect.gen(function* () {
    const user = yield* loadUser(id);
    if (!user.active) {
      return yield* new InactiveUserError({ id: user.id });
    }
    return user;
  });
```

## Recovery with Tags

| Legacy recovery | Effect recovery |
|---|---|
| ```typescript
async function loadTheme(raw: string): Promise<string> {
  try {
    return parseSettings(raw).theme;
  } catch {
    return "system";
  }
}
``` | ```typescript
import { Effect } from "effect";

const loadTheme = (raw: string): Effect.Effect<string, never, never> =>
  parseSettings(raw).pipe(
    Effect.map((settings) => settings.theme),
    Effect.catchTag("SettingsParseError", () => Effect.succeed("system")),
  );
``` |

Prefer `Effect.catchTag` when a single error has a known fallback. Prefer `Effect.catchTags` when each error gets a different handler.

## Multiple Error Handlers

```typescript
import { Data, Effect } from "effect";

class UnauthorizedError extends Data.TaggedError("UnauthorizedError")<{
  readonly userId: string;
}> {}

class MissingProfileError extends Data.TaggedError("MissingProfileError")<{
  readonly userId: string;
}> {}

const profileLabel = (
  userId: string,
): Effect.Effect<string, never, never> =>
  loadProfile(userId).pipe(
    Effect.map((profile) => profile.label),
    Effect.catchTags({
      UnauthorizedError: () => Effect.succeed("private"),
      MissingProfileError: () => Effect.succeed("missing"),
    }),
  );
```

This keeps recovery local and type-directed. If a new tagged error is added upstream, the compiler can expose places that no longer handle all cases.

## Unknown Causes at Boundaries

External code can still throw unknown values. Normalize those values once:

```typescript
import { Data, Effect } from "effect";

class UnknownLibraryError extends Data.TaggedError("UnknownLibraryError")<{
  readonly operation: string;
  readonly cause: unknown;
}> {}

const callLibrary = (
  input: string,
): Effect.Effect<string, UnknownLibraryError, never> =>
  Effect.try({
    try: () => legacyLibraryFormat(input),
    catch: (cause) => new UnknownLibraryError({ operation: "legacyLibraryFormat", cause }),
  });
```

Do not spread unknown failures throughout the domain. Translate once, then work with the tagged type.

## Defects vs Expected Errors

Not every exception should become a typed domain error. Use typed failures for expected operational or domain cases. Let defects remain defects when they indicate a programmer mistake that should not be recovered from locally.

| Failure | Migration choice |
|---|---|
| Invalid user input | Tagged error |
| Remote timeout | Tagged error |
| Missing optional record | Tagged error or `Option` |
| Impossible invariant broken | Defect or a narrow internal failure |
| Third-party parser threw | Boundary tagged error |

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| `try` block around `yield* someEffect` | Use `Effect.catchTag` or `Effect.catchAll` |
| Throwing from inside `Effect.gen` | `return yield* new TaggedError(...)` or `Effect.fail(...)` |
| One generic `Error` for every branch | Distinct tagged errors per recovery path |
| Catching all failures before the caller can decide | Catch only where the fallback is part of the business rule |
| Re-throwing transformed errors | Return a failed effect with the transformed error |

## Migration Steps

1. Find `try` blocks that protect JSON parsing, SDK calls, filesystem calls, or validation.
2. Define tagged errors with the fields needed for recovery and diagnostics.
3. Replace synchronous throwing boundaries with `Effect.try`.
4. Replace promise throwing boundaries with `Effect.tryPromise`.
5. Replace local fallback `catch` blocks with `Effect.catchTag` or `Effect.catchTags`.
6. Keep broad catch-all recovery at application boundaries, not deep helpers.

## Cross-references

See also: [02-from-promise.md](02-from-promise.md), [04-from-fp-ts.md](04-from-fp-ts.md), [05-from-neverthrow.md](05-from-neverthrow.md), [07-gradual-adoption.md](07-gradual-adoption.md).
