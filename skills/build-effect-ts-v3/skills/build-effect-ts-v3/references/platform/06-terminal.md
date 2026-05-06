# Terminal
Use `Terminal` for typed command-line display and input instead of direct standard input/output calls.

## Service Shape

`Terminal.Terminal` is a service tag. The service exposes:

| Member | Use |
|---|---|
| `columns` | Current terminal width |
| `rows` | Current terminal height |
| `isTTY` | Whether input/output is interactive |
| `display(text)` | Write text to standard output |
| `readLine` | Read one line |
| `readInput` | Read raw input events through a scoped mailbox |

Node provides `NodeTerminal.layer`; Bun provides `BunTerminal.layer`.
`NodeContext.layer` and `BunContext.layer` include their runtime terminal layer.

## Display

```typescript
import { Effect } from "effect"
import { Terminal } from "@effect/platform"
import { NodeContext, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const terminal = yield* Terminal.Terminal
  const columns = yield* terminal.columns

  yield* terminal.display(`Terminal width: ${columns}\n`)
})

program.pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

Use `Effect.logInfo` for logs and diagnostics; use `Terminal.display` for
intentional user-facing CLI output.

## Read a Line

```typescript
import { Effect } from "effect"
import { Terminal } from "@effect/platform"

export const askName = Effect.gen(function* () {
  const terminal = yield* Terminal.Terminal

  yield* terminal.display("Name: ")
  const name = yield* terminal.readLine

  return name.trim()
})
```

`readLine` can fail with `QuitException` when the user exits the prompt. Handle
that at the CLI boundary if the program should print a friendly message.

## TTY-aware Output

```typescript
import { Effect } from "effect"
import { Terminal } from "@effect/platform"

export const renderStatus = (message: string) =>
  Effect.gen(function* () {
    const terminal = yield* Terminal.Terminal
    const interactive = yield* terminal.isTTY

    if (interactive) {
      yield* terminal.display(`${message}\n`)
    } else {
      yield* Effect.logInfo(message)
    }
  })
```

TTY checks are useful when the same program can be used by humans and scripts.

## Raw Input

`readInput` returns a scoped mailbox of input events. Use it for interactive
programs that need key-level behavior.

```typescript
import { Effect } from "effect"
import { Terminal } from "@effect/platform"

export const waitForKey = Effect.scoped(
  Effect.gen(function* () {
    const terminal = yield* Terminal.Terminal
    const input = yield* terminal.readInput
    const event = yield* input.take

    return event.key.name
  })
)
```

Because raw input is scoped, the terminal mode is restored when the scope
closes.

## Custom Quit Behavior

Node exposes `NodeTerminal.make(shouldQuit?)` for custom low-level terminal
construction. Most programs should use `NodeTerminal.layer`, but custom layers
can be useful for applications where a specific key combination quits.

```typescript
import { Layer } from "effect"
import { NodeTerminal } from "@effect/platform-node"

export const TerminalLive = Layer.scoped(
  NodeTerminal.make((input) => input.key.ctrl && input.key.name === "d")
)
```

Provide this custom layer in place of `NodeTerminal.layer`.

## Anti-patterns

- Using terminal display for structured logs.
- Reading input in library code that should accept parameters.
- Ignoring `QuitException` in user-facing prompts.
- Assuming terminal dimensions exist in non-interactive contexts.
- Mixing direct host standard I/O with `Terminal.Terminal`.

## Cross-references

See also: [01-overview.md](01-overview.md), [05-command.md](05-command.md), [11-node-context.md](11-node-context.md), [12-node-runtime.md](12-node-runtime.md)
