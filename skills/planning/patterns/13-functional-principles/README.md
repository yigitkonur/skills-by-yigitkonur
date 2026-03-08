# 13 - Functional Principles

Functional programming is not about using a specific language — it is a set of principles that make code more predictable, testable, and composable. These principles apply in any language, but they are especially powerful in TypeScript where the type system can enforce many of them at compile time.

---

## Contents

| # | Principle | Summary | File |
|---|-----------|---------|------|
| 1 | [Pure Functions](./pure-functions.md) | No side effects, same input always produces the same output. Enables testing, caching, and safe parallelism. |
| 2 | [Immutability](./immutability.md) | Data never changes after creation. New values are derived from old ones via structural sharing. Eliminates shared mutable state bugs. |
| 3 | [Higher-Order Functions](./higher-order-functions.md) | Functions that accept or return functions. Enables map/filter/reduce, decorators, partial application, and currying. |
| 4 | [Railway-Oriented Programming](./railway-oriented-programming.md) | Either/Result types for composable error handling. Happy path flows naturally; errors propagate without manual checks. |
| 5 | [Algebraic Data Types](./algebraic-data-types.md) | Sum types (tagged unions) and product types with exhaustive pattern matching. Makes illegal states unrepresentable. |
| 6 | [Function Composition](./function-composition.md) | Build complex operations by chaining simple functions via pipe/compose. Middleware patterns as real-world composition. |
| 7 | [Declarative vs. Imperative](./declarative-vs-imperative.md) | Describe WHAT you want, not HOW. SQL, React, and Terraform as declarative success stories. |

---

## How These Principles Interrelate

```
Pure Functions ──enables──→ Memoization / Caching
     │                          │
     └──requires──→ Immutability ──enables──→ Safe Concurrency
                        │
                        └──supports──→ Structural Sharing (Immer)

Higher-Order Functions ──enables──→ Function Composition
         │                                    │
         └──enables──→ Partial Application    └──expresses──→ Middleware Patterns

Railway-Oriented Programming ──uses──→ Algebraic Data Types (Result/Either)
              │                                    │
              └──enables──→ Composable Errors      └──enables──→ Exhaustive Handling

Declarative Style ──leverages──→ All of the above
```

---

## When to Start

If you are new to functional principles, start with:

1. **Pure Functions** — the most impactful single change you can make to any codebase
2. **Immutability** — the natural companion to purity
3. **Higher-Order Functions** — you already use these (map, filter, reduce); now understand the theory

Then progress to:

4. **Algebraic Data Types** — discriminated unions are TypeScript's best type system feature
5. **Function Composition** — connect the dots between small pure functions
6. **Railway-Oriented Programming** — when error handling becomes complex
7. **Declarative vs. Imperative** — the overarching philosophy that ties it all together

---

## Key Takeaway

Functional programming is not all-or-nothing. Each principle stands on its own and delivers value independently. A codebase with pure functions and immutable data is dramatically better than one without, even if it uses classes, loops, and try/catch everywhere else. Adopt incrementally, measure the impact, and go deeper where it helps.
