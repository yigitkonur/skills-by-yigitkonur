# Function Composition

**Build complex operations by combining simple functions, where the output of one becomes the input of the next.**

---

## Origin / History

Function composition is a mathematical concept predating computing: if `f: A -> B` and `g: B -> C`, then `g . f: A -> C`. In programming, composition became a first-class concept in Haskell with the `.` operator and in ML-family languages. The Unix pipe (`|`) is composition applied to processes: `cat file | grep pattern | sort | uniq` chains small tools into powerful pipelines.

In JavaScript, composition gained practical tooling through libraries like Lodash (`_.flow`, `_.flowRight`), Ramda (`R.pipe`, `R.compose`), and later through TC39 proposals for the pipeline operator (`|>`). Express and Koa middleware stacks are composition in practice — each middleware transforms the request/response and passes it along. The pattern is everywhere once you learn to see it.

---

## The Problem It Solves

Without composition, complex operations are built through one of two approaches: deeply nested function calls (`h(g(f(x)))`) which read inside-out and are hard to follow, or long procedural sequences with intermediate variables that clutter scope and obscure the transformation pipeline.

Composition solves both problems. It lets you define a pipeline of transformations that reads left-to-right (with `pipe`) or right-to-left (with `compose`), without intermediate variables and without nesting. Each step is a small, testable, reusable function. The pipeline itself becomes a named, reusable function.

The deeper benefit is conceptual: composition encourages you to think in terms of data transformations rather than step-by-step instructions. This aligns with how functional programmers model domains — as pipelines of pure functions that transform inputs to outputs.

---

## The Principle Explained

`pipe` applies functions left to right: `pipe(f, g, h)(x)` is `h(g(f(x)))`. `compose` applies functions right to left: `compose(h, g, f)(x)` is also `h(g(f(x)))`. `pipe` is generally preferred because it matches reading order.

Point-free style (also called "tacit programming") defines functions without mentioning their arguments. Instead of `const getName = (user) => user.name`, you write `const getName = prop("name")`. Point-free style is a natural consequence of composition — when you compose functions, the data flows through implicitly. It improves readability when the pipeline is clear and hurts readability when the implicit arguments become hard to track.

Middleware patterns are composition in disguise. Express middleware `(req, res, next) => { ... next(); }` is a function that transforms the request context and yields to the next function. The `app.use()` method composes middleware into a pipeline. Koa took this further with async middleware and the "onion model" — each middleware wraps the next, forming a nested composition.

---

## Code Examples

### BAD: Nested calls and intermediate variables obscuring the pipeline

```typescript
// Nested calls — reads inside-out, hard to follow
const result = formatCurrency(
  applyDiscount(
    calculateSubtotal(
      filterActiveItems(cart.items)
    ),
    cart.discountCode
  )
);

// Intermediate variables — noisy, pollutes scope
const activeItems = filterActiveItems(cart.items);
const subtotal = calculateSubtotal(activeItems);
const discounted = applyDiscount(subtotal, cart.discountCode);
const result = formatCurrency(discounted);
// activeItems, subtotal, discounted are never used again
```

### GOOD: Composition with pipe — reads as a clear transformation pipeline

```typescript
// Type-safe pipe implementation
function pipe<A>(a: A): A;
function pipe<A, B>(a: A, ab: (a: A) => B): B;
function pipe<A, B, C>(a: A, ab: (a: A) => B, bc: (b: B) => C): C;
function pipe<A, B, C, D>(
  a: A,
  ab: (a: A) => B,
  bc: (b: B) => C,
  cd: (c: C) => D,
): D;
function pipe(initial: unknown, ...fns: Array<(arg: unknown) => unknown>): unknown {
  return fns.reduce((acc, fn) => fn(acc), initial);
}

// Clear left-to-right pipeline
const result = pipe(
  cart.items,
  filterActiveItems,
  calculateSubtotal,
  (subtotal) => applyDiscount(subtotal, cart.discountCode),
  formatCurrency,
);
```

### Composable utility functions

```typescript
// Small, reusable, composable functions
const prop = <T, K extends keyof T>(key: K) => (obj: T): T[K] => obj[key];

const gt = (threshold: number) => (value: number): boolean => value > threshold;

const not = <T>(predicate: (x: T) => boolean) => (x: T): boolean => !predicate(x);

const sortBy = <T>(fn: (item: T) => number | string) =>
  (items: readonly T[]): T[] =>
    [...items].sort((a, b) => (fn(a) < fn(b) ? -1 : fn(a) > fn(b) ? 1 : 0));

// Compose them into domain-specific operations
interface Product {
  readonly name: string;
  readonly price: number;
  readonly inStock: boolean;
}

const getAffordableProducts = (maxPrice: number) =>
  (products: readonly Product[]): Product[] =>
    pipe(
      products,
      (ps) => ps.filter((p) => p.inStock),
      (ps) => ps.filter((p) => p.price <= maxPrice),
      sortBy<Product>((p) => p.price),
    );
```

### Middleware as composition — Express/Koa pattern

```typescript
// Express middleware is function composition over (req, res)
import express, { Request, Response, NextFunction } from "express";

// Each middleware is a composable unit
function requestLogger(req: Request, _res: Response, next: NextFunction): void {
  console.log(`${req.method} ${req.path}`);
  next();
}

function authenticate(req: Request, res: Response, next: NextFunction): void {
  const token = req.headers.authorization;
  if (!token) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  // Attach user to request context
  (req as any).user = verifyToken(token);
  next();
}

function validateBody(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      res.status(400).json({ errors: result.error.issues });
      return;
    }
    req.body = result.data;
    next();
  };
}

// Composition: each middleware transforms or gates the pipeline
app.post(
  "/api/orders",
  requestLogger,                   // Log
  authenticate,                     // Gate: reject if no auth
  validateBody(createOrderSchema),  // Gate: reject if invalid body
  createOrderHandler,               // Handle the request
);
```

### Building a compose utility

```typescript
function compose<A, B>(ab: (a: A) => B): (a: A) => B;
function compose<A, B, C>(bc: (b: B) => C, ab: (a: A) => B): (a: A) => C;
function compose<A, B, C, D>(
  cd: (c: C) => D,
  bc: (b: B) => C,
  ab: (a: A) => B,
): (a: A) => D;
function compose(...fns: Array<(arg: unknown) => unknown>): (arg: unknown) => unknown {
  return (arg: unknown) => fns.reduceRight((acc, fn) => fn(acc), arg);
}

// Usage: reads right-to-left (mathematical convention)
const processUser = compose(
  formatForDisplay,    // 3. Format the output
  enrichWithMetadata,  // 2. Add computed fields
  validateUser,        // 1. Validate input
);
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Method chaining (fluent interfaces)** | `builder.setName("x").setAge(5).build()`. Readable, but tied to a specific class. Cannot compose methods from different objects. |
| **Inheritance (template method)** | Override specific steps in a base class algorithm. Rigid, tightly coupled, hard to mix behaviors from multiple sources. |
| **Promise chaining** | `.then(f).then(g).then(h)` is composition for async operations. Limited to Promises; not general-purpose. |
| **Pipeline operator (TC39 proposal)** | `value \|> f \|> g \|> h`. Native syntax, no library needed. Still in proposal stage as of 2025. |
| **RxJS pipe** | `observable.pipe(map(f), filter(g), reduce(h))`. Composition for streams. Powerful but complex for simple transformations. |

---

## When NOT to Apply

- **When a simple function call suffices**: Do not compose `pipe(x, f)`. Just call `f(x)`.
- **When steps have side effects that need ordering guarantees**: Composition implies pure transformation. If step 2 depends on a side effect from step 1, make the dependency explicit rather than hiding it in a pipeline.
- **When the pipeline is one-off**: Creating named composed functions for a single call site adds indirection without reuse benefit.
- **When debugging is a priority**: Pipelines compress multiple operations into one expression. During active debugging, explicit intermediate variables are easier to inspect.

---

## Tensions & Trade-offs

- **Readability vs. Conciseness**: A pipeline of well-named functions is very readable. A pipeline of inline lambdas is not.
- **Type inference vs. Generics**: TypeScript struggles to infer types through long `pipe` chains. You may need explicit type annotations, which reduces the elegance.
- **Point-free vs. Explicit**: `pipe(users, filter(isActive), map(prop("name")))` is clean. `pipe(users, filter(x => x.active && x.age > 18), map(x => x.name))` is arguable. Know when point-free helps and when it obfuscates.
- **Composition vs. Encapsulation**: Composition exposes the transformation steps. Sometimes you want to hide internals behind a named function that does not reveal its implementation.

---

## Real-World Consequences

**Unix philosophy vindicated**: The Unix pipe model — small programs composed via `|` — has been the dominant systems administration paradigm for 50 years. Programs like `grep`, `awk`, `sort`, and `uniq` each do one thing. Composed, they solve problems their authors never anticipated.

**Express middleware ecosystem**: Express's middleware composition model enabled an ecosystem of hundreds of reusable middleware packages — authentication, rate limiting, compression, CORS — that work together because they all conform to the `(req, res, next)` composition interface.

**Data pipeline architectures**: Apache Spark, dbt, and similar tools model data transformations as composed pipelines of pure functions (map, filter, join, aggregate). This composition model enables optimization (the engine can reorder or parallelize steps) and reuse (each transformation is independently testable).

---

## Further Reading

- [Eric Elliott — Composing Software (Leanpub, 2018)](https://leanpub.com/composingsoftware)
- [Mostly Adequate Guide — Chapter 5: Composing Functions](https://github.com/MostlyAdequate/mostly-adequate-guide/blob/master/ch05.md)
- [TC39 Pipeline Operator Proposal](https://github.com/tc39/proposal-pipeline-operator)
- [Koa.js — Middleware Composition (Onion Model)](https://koajs.com/)
- [fp-ts — pipe and flow utilities](https://gcanti.github.io/fp-ts/modules/function.ts.html)
