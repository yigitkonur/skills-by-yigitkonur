# Match.type
Use `Match.type<Input>()` to build reusable match functions for a known input type.

`Match.type` starts from a type instead of a value. The finalizer returns a
function that accepts the input later.

Use it when a match is a named domain operation, not a one-off local branch.

## Reusable Matcher

```typescript
import { Match } from "effect"

type Delivery =
  | { readonly _tag: "Pending"; readonly id: string }
  | { readonly _tag: "InTransit"; readonly id: string; readonly carrier: string }
  | { readonly _tag: "Delivered"; readonly id: string }
  | { readonly _tag: "Failed"; readonly id: string; readonly reason: string }

const deliveryLabel = Match.type<Delivery>().pipe(
  Match.tag("Pending", (delivery) => `pending ${delivery.id}`),
  Match.tag("InTransit", (delivery) => `with ${delivery.carrier}`),
  Match.tag("Delivered", (delivery) => `delivered ${delivery.id}`),
  Match.tag("Failed", (delivery) => `failed: ${delivery.reason}`),
  Match.exhaustive
)

const label = deliveryLabel({
  _tag: "InTransit",
  id: "delivery-1",
  carrier: "postal"
})
```

The `deliveryLabel` function can be passed, tested, and reused.

## Prefer Type Matchers For Public Helpers

Use `Match.type` when the matcher deserves a name:

```typescript
import { Match } from "effect"

type Access =
  | { readonly _tag: "Guest" }
  | { readonly _tag: "Member"; readonly plan: "free" | "paid" }
  | { readonly _tag: "Admin" }

export const canManageBilling = Match.type<Access>().pipe(
  Match.tag("Guest", () => false),
  Match.tag("Member", (member) => member.plan === "paid"),
  Match.tag("Admin", () => true),
  Match.exhaustive
)
```

This makes the policy visible. The function's signature is inferred as
`(input: Access) => boolean`.

## Lock Branch Return Types

`Match.withReturnType<Return>()` can force every handler to return the same
declared type. In Effect v3 it must be the first operation after the matcher.

```typescript
import { Match } from "effect"

type Route =
  | { readonly _tag: "Home" }
  | { readonly _tag: "Project"; readonly id: string }
  | { readonly _tag: "Settings" }

type Breadcrumb = {
  readonly label: string
  readonly href: string
}

const breadcrumb = Match.type<Route>().pipe(
  Match.withReturnType<Breadcrumb>(),
  Match.tag("Home", () => ({ label: "Home", href: "/" })),
  Match.tag("Project", (route) => ({
    label: "Project",
    href: `/projects/${route.id}`
  })),
  Match.tag("Settings", () => ({ label: "Settings", href: "/settings" })),
  Match.exhaustive
)
```

Use this when a branch accidentally returning a different shape would become an
API problem.

## Type Matcher With Effects

Reusable matchers can return Effects too.

```typescript
import { Effect, Match } from "effect"

type AuditEvent =
  | { readonly _tag: "UserCreated"; readonly userId: string }
  | { readonly _tag: "UserLocked"; readonly userId: string; readonly reason: string }
  | { readonly _tag: "UserDeleted"; readonly userId: string }

const writeAudit = (message: string) =>
  Effect.logInfo(message)

const auditEvent = Match.type<AuditEvent>().pipe(
  Match.tag("UserCreated", (event) => writeAudit(`created ${event.userId}`)),
  Match.tag("UserLocked", (event) => writeAudit(`locked ${event.userId}: ${event.reason}`)),
  Match.tag("UserDeleted", (event) => writeAudit(`deleted ${event.userId}`)),
  Match.exhaustive
)
```

Callers run the returned Effect where their program is already composing Effects.

```typescript
const program = auditEvent({ _tag: "UserCreated", userId: "user-1" })
```

## Type Matchers As Anti-Duplication

If the same `Match.value(input).pipe(...)` appears twice, extract a
`Match.type<Input>()` matcher.

Keep handlers small. If a branch grows beyond a few lines, name the branch
function and call it from the handler:

```typescript
import { Match } from "effect"

type Invoice =
  | { readonly _tag: "Draft"; readonly id: string }
  | { readonly _tag: "Open"; readonly id: string; readonly amount: number }
  | { readonly _tag: "Paid"; readonly id: string; readonly receiptId: string }

const openInvoiceLabel = (invoice: Extract<Invoice, { readonly _tag: "Open" }>) =>
  `open ${invoice.id}: ${invoice.amount}`

const invoiceLabel = Match.type<Invoice>().pipe(
  Match.tag("Draft", (invoice) => `draft ${invoice.id}`),
  Match.tag("Open", openInvoiceLabel),
  Match.tag("Paid", (invoice) => `paid ${invoice.receiptId}`),
  Match.exhaustive
)
```

This keeps the matcher readable while preserving exhaustiveness.

## Value Versus Type

| Need | Use |
|---|---|
| Classify one local value | `Match.value(input)` |
| Export a reusable classifier | `Match.type<Input>()` |
| Keep a domain policy in one place | `Match.type<Input>()` |
| Use a short inline transformation | `Match.value(input)` |

Do not choose `Match.type` because it is more abstract. Choose it because the
function itself is a useful artifact.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-match-value.md](02-match-value.md), [04-match-tag.md](04-match-tag.md), [07-exhaustive-vs-orelse.md](07-exhaustive-vs-orelse.md)
