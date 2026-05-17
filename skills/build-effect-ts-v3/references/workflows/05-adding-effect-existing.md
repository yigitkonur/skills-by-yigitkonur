# Adding Effect To Existing Code
Introduce Effect v3 into an existing TypeScript codebase gradually, with boundary wrappers, services, layers, and tests.

Use this when the project already has Promise-based modules. Start at a boundary, wrap one workflow in Effect, add typed errors and services, then move the runtime edge outward over time.

## Primitive index

| Primitive | Read first |
|---|---|
| Promise migration and portable utilities | [migration](../migration/02-from-promise.md), [migration](../migration/07-gradual-adoption.md), [migration](../migration/08-portable-utility.md) |
| creating and running Effects | [core](../core/02-creating-effects.md), [core](../core/03-running-effects.md), [core](../core/04-pipelines.md) |
| typed errors and recovery | [error-handling](../error-handling/02-data-tagged-error.md), [error-handling](../error-handling/09-recovery-patterns.md), [error-handling](../error-handling/13-error-remapping.md) |
| services and test layers | [services-layers](../services-layers/02-context-tag.md), [services-layers](../services-layers/06-layer-succeed.md), [testing](../testing/08-test-layers.md) |
| anti-patterns to avoid | [anti-patterns](../anti-patterns/16-effect-promise-confusion.md), [anti-patterns](../anti-patterns/04-runpromise-mid-code.md), [anti-patterns](../anti-patterns/17-type-assertions.md) |

## 1. Package setup

Add Effect without changing the build system.

```typescript
{
  "type": "module",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "effect": "^3.21.2"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

Do not install deprecated schema packages. Schema is imported from `effect`.

## 2. Entry point

If the existing app is Promise-based, keep one bridge function at the edge.

```typescript
import { Effect, Layer, Runtime } from "effect"
import { Billing } from "./billing-effect.js"

const AppLayer = Billing.Default

export const chargeCustomer = async (customerId: string, cents: number) => {
  const runtime = await Effect.runPromise(Effect.runtime<Billing>().pipe(Effect.provide(AppLayer)))
  const program = Effect.gen(function*() {
    const billing = yield* Billing
    return yield* billing.charge(customerId, cents)
  })
  return Runtime.runPromise(runtime)(program)
}
```

This is a temporary migration bridge. Once the outer framework supports Effects directly, replace this with `NodeRuntime.runMain`, a managed runtime, or a route-handler runtime.

## 3. Main Effect orchestration

Move orchestration first. Leave low-level Promise functions wrapped until they can be replaced.

```typescript
import { Effect } from "effect"
import { Billing, PaymentGateway } from "./billing-effect.js"

export const checkout = (customerId: string, cents: number) =>
  Effect.gen(function*() {
    const gateway = yield* PaymentGateway
    const receipt = yield* gateway.charge(customerId, cents)
    const billing = yield* Billing
    yield* billing.record(receipt.id, cents)
    yield* Effect.logInfo("checkout charged", { customerId, cents })
    return receipt
  })
```

Keep the first migrated workflow narrow. Do not convert unrelated helper modules in the same change.

## 4. Per-feature service definitions

Wrap existing Promise functions with typed errors. Do not leak unknown exceptions across the new Effect boundary.

```typescript
import { Effect, Schema } from "effect"
import { legacyCharge, legacyRecordReceipt } from "./legacy-billing.js"

export class PaymentError extends Schema.TaggedError<PaymentError>()("PaymentError", {
  customerId: Schema.String,
  message: Schema.String
}) {}

export class Receipt extends Schema.Class<Receipt>("Receipt")({
  id: Schema.String,
  customerId: Schema.String
}) {}

export class PaymentGateway extends Effect.Service<PaymentGateway>()("app/PaymentGateway", {
  effect: Effect.succeed({
    charge: (customerId: string, cents: number) =>
      Effect.tryPromise({
        try: () => legacyCharge(customerId, cents),
        catch: (error) => new PaymentError({ customerId, message: String(error) })
      }).pipe(Effect.map((receipt) => new Receipt(receipt)))
  })
}) {}

export class Billing extends Effect.Service<Billing>()("app/Billing", {
  effect: Effect.succeed({
    record: (receiptId: string, cents: number) =>
      Effect.tryPromise({
        try: () => legacyRecordReceipt(receiptId, cents),
        catch: (error) => new PaymentError({ customerId: receiptId, message: String(error) })
      }),
    charge: (customerId: string, cents: number) =>
      PaymentGateway.pipe(Effect.flatMap((gateway) => gateway.charge(customerId, cents)))
  })
}) {}
```

## 5. Layer wiring

Provide migrated services through layers and keep legacy objects behind those services.

```typescript
import { Layer } from "effect"
import { Billing, PaymentGateway } from "./billing-effect.js"

export const BillingLayer = Layer.merge(PaymentGateway.Default, Billing.Default)
```

If a legacy dependency is already instantiated by the app, wrap it with `Layer.succeed`. If construction is effectful, use `Layer.effect` and model startup failure explicitly.

## 6. Test layer override

Replace the migrated boundary service in tests. This is the first payoff of the migration.

```typescript
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { PaymentGateway, Receipt } from "../src/billing-effect.js"
import { checkout } from "../src/checkout.js"

const PaymentGatewayTest = Layer.succeed(PaymentGateway, {
  charge: (customerId: string) => Effect.succeed(new Receipt({ id: "r1", customerId }))
})

it.effect("charges through the payment gateway", () =>
  checkout("c1", 1000).pipe(
    Effect.provide(PaymentGatewayTest),
    Effect.map((receipt) => expect(receipt.id).toBe("r1"))
  )
)
```

When a migrated workflow still calls legacy code, test both the wrapper error mapping and the orchestration. Avoid type assertions as a substitute for decoding legacy output.

## Workflow checklist

1. Pick one boundary workflow.
2. Wrap existing Promise calls with `Effect.tryPromise`.
3. Convert unknown rejections into tagged errors.
4. Keep the first runtime bridge at the outer edge.
5. Do not convert unrelated helpers in the same change.
6. Add one test layer before expanding scope.
7. Replace direct legacy calls with service calls.
8. Keep legacy output decoded when it crosses trust boundaries.
9. Move orchestration into `Effect.gen`.
10. Leave pure helper functions pure.
11. Move the runtime edge outward gradually.
12. Remove temporary bridges when the caller becomes Effect-native.
13. Use [Either](../data-types/04-either.md) or [Exit](../error-handling/07-cause-and-exit.md) for value-level outcomes.
14. Avoid broad catch-all recovery around migrated code.
15. Keep migrated modules importable from old code.
16. Keep old tests passing while adding Effect tests.
17. Add config through `Config` when the first Effect service needs it.
18. Add layers only when there is a dependency to provide.
19. Keep the first pull request small.
20. Treat removal of a bridge as a separate semantic change.
21. Review [from try/catch](../migration/03-from-trycatch.md) before converting exception-heavy code.
22. Review [generic error types](../anti-patterns/07-generic-error-types.md) before using `Error`.
23. Review [Effect Promise confusion](../anti-patterns/16-effect-promise-confusion.md) when mixing styles.
24. Verify both the old caller and new Effect workflow.

## 7. Deployment

Deployment should not change during the first migration step. The existing process still starts the application, with one or more Effect bridges at the edges. As Effect moves outward, consolidate bridges into a single runtime per process, route handler, worker, or request scope.

## Cross-references

See also: [greenfield CLI](01-greenfield-cli.md), [Next.js fullstack](04-greenfield-nextjs.md), [microservice](06-microservice.md), [migration overview](../migration/01-overview.md).
