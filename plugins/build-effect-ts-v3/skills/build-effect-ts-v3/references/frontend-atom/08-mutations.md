# Mutations
Use `Atom.fn`, `runtime.fn`, RPC mutations, or HTTP API mutations for commands, and derive waiting and error UI from the result atom.

## Mutation Shape

Mutation atoms are writable result atoms.
Calling the setter starts the effect and updates the result state.

The source exposes:

- `Atom.fn(effectFn)` for command atoms without services
- `runtime.fn(effectFn)` for commands requiring services
- `AtomRpc.Tag(...).mutation(tag)` for RPC commands
- `AtomHttpApi.Tag(...).mutation(group, endpoint)` for HTTP API commands

All of these integrate with `useAtomSet` and `useAtom`.

## Simple Atom.fn

Use `Atom.fn` for a command with no service requirement.

```typescript
import { Atom, Result, useAtom } from "@effect-atom/atom-react"
import { Effect } from "effect"

const saveDraftAtom = Atom.fn((title: string) =>
  Effect.succeed({ title })
)

export function SaveDraftButton() {
  const [result, saveDraft] = useAtom(saveDraftAtom)

  return {
    waiting: result.waiting,
    label: Result.getOrElse(result, () => ({ title: "Save" })).title,
    onClick: () => saveDraft("Draft")
  }
}
```

Use the result's `waiting` flag instead of a separate React loading state.

## Service-Backed runtime.fn

Use `runtime.fn` when the mutation needs a service from a layer.

```typescript
import { Atom, Result, useAtom } from "@effect-atom/atom-react"
import { Effect } from "effect"

type User = {
  readonly id: string
  readonly name: string
}

class Users extends Effect.Service<Users>()("app/Users", {
  succeed: {
    create: (name: string) => Effect.succeed<User>({ id: "u-1", name })
  }
}) {}

const runtime = Atom.runtime(Users.Default)

const createUserAtom = runtime.fn((name: string) =>
  Effect.gen(function* () {
    const users = yield* Users
    return yield* users.create(name)
  })
)

export function CreateUserDialog() {
  const [result, createUser] = useAtom(createUserAtom)

  return Result.builder(result)
    .onInitial(() => ({
      disabled: false,
      submit: () => createUser("Ada")
    }))
    .onSuccess((user) => ({
      disabled: result.waiting,
      user
    }))
    .render()
}
```

The dialog owns the mutation hook.
The parent passes data and receives an `onSuccess` callback if needed.

## Promise Mode

Use `{ mode: "promise" }` when an event handler needs to await the success
value.

```typescript
import { Atom, useAtomSet } from "@effect-atom/atom-react"
import { Effect } from "effect"

const renameAtom = Atom.fn((name: string) =>
  Effect.succeed({ name })
)

export function RenameAction() {
  const rename = useAtomSet(renameAtom, { mode: "promise" })

  return {
    submit: (name: string) =>
      rename(name).then((user) => user.name)
  }
}
```

The promise mode resolves with the success value or rejects with the squashed
cause.

## Promise Exit Mode

Use `{ mode: "promiseExit" }` when the event handler needs to distinguish
success and failure without losing the error channel.

```typescript
import { Atom, useAtomSet } from "@effect-atom/atom-react"
import { Effect, Exit } from "effect"

const archiveAtom = Atom.fn((id: string) =>
  Effect.succeed({ archivedId: id })
)

export function ArchiveAction() {
  const archive = useAtomSet(archiveAtom, { mode: "promiseExit" })

  return {
    submit: (id: string) =>
      archive(id).then((exit) =>
        Exit.match(exit, {
          onFailure: () => "failed",
          onSuccess: (value) => value.archivedId
        })
      )
  }
}
```

Use this for imperative integration points that still need typed failure
awareness.

## Reactivity Keys

Mutation atoms can invalidate query atoms through `reactivityKeys`.
Use this instead of hand-wired refresh calls when a query is registered with the
same keys.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect, Layer } from "effect"

const runtime = Atom.runtime(Layer.empty)

const countAtom = runtime.atom(
  Effect.succeed(1)
).pipe(
  Atom.withReactivity(["count"])
)

const incrementAtom = runtime.fn(
  () => Effect.succeed(2),
  { reactivityKeys: ["count"] }
)
```

When the mutation finishes, the registered query is invalidated.

## Waiting UI

For mutation UI, derive all loading state from the mutation result.

```typescript
import { Result } from "@effect-atom/atom-react"

declare const result: Result.Result<
  { readonly id: string },
  { readonly _tag: "Denied" }
>

const state = Result.builder(result)
  .onInitial(() => ({ disabled: false, label: "Save" }))
  .onErrorTag("Denied", () => ({ disabled: false, label: "Denied" }))
  .onSuccess(() => ({
    disabled: result.waiting,
    label: result.waiting ? "Saving" : "Saved"
  }))
  .render()
```

This avoids duplicated local flags that drift from the real mutation state.

## Cross-references

See also: [05 React Hooks](05-react-hooks.md), [06 Result Builder](06-result-builder.md), [09 Cache Invalidation](09-cache-invalidation.md), [11 Runtime Bridge](11-effect-runtime-bridge.md), [12 Vercel AI SDK](12-vercel-ai-sdk.md).
