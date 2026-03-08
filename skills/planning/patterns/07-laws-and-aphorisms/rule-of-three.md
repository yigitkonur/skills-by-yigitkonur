# Rule of Three

## Origin

Multiple sources converge on this principle. Don Roberts (as cited by Martin Fowler in *Refactoring*): "The first time you do something, you just do it. The second time you do something similar, you wince at the duplication, but you do the duplicate thing anyway. The third time you do something similar, you refactor."

Also present in the Unix philosophy and in various software engineering traditions as a guard against premature abstraction.

## Explanation

Do not abstract on the first occurrence. Do not abstract on the second. On the third, you have enough examples to see the real pattern and create a good abstraction. Abstracting too early — from one or two examples — leads to wrong abstractions that are harder to change than the duplication they replaced.

This is the bridge between two competing principles:
- **DRY (Don't Repeat Yourself):** Duplication is waste.
- **YAGNI (You Ain't Gonna Need It):** Do not build abstractions you do not need yet.

The Rule of Three resolves the tension: tolerate duplication until you have enough evidence to abstract correctly.

## TypeScript Code Examples

### Bad: Abstracting After First Occurrence

```typescript
// First endpoint: GET /users
// Developer immediately creates a "generic endpoint factory"

function createEndpoint<T>(
  path: string,
  model: string,
  transform?: (data: unknown) => T,
  middleware?: Function[],
  cache?: { ttl: number; strategy: "lru" | "fifo" },
  pagination?: { default: number; max: number },
  auth?: { required: boolean; roles?: string[] },
): Router {
  // 150 lines of generic framework code
  // to handle ONE endpoint that exists so far.
  // Every future endpoint will be forced into this abstraction,
  // even if it doesn't fit.
}

// When the second endpoint has different needs (file upload,
// streaming, WebSocket), the abstraction must be contorted
// or bypassed, making it worse than no abstraction at all.
```

### Good: Wait for Three Occurrences, Then Abstract

```typescript
// Occurrence 1: Just write it
app.get("/users", async (req, res) => {
  const users = await db.users.findAll();
  res.json({ data: users, total: users.length });
});

// Occurrence 2: Duplicate it, note the similarity
app.get("/products", async (req, res) => {
  const products = await db.products.findAll();
  res.json({ data: products, total: products.length });
});

// Occurrence 3: Now the pattern is clear — extract it
app.get("/orders", async (req, res) => {
  const orders = await db.orders.findAll();
  res.json({ data: orders, total: orders.length });
});

// NOW abstract — with three examples, the real pattern is visible:
function createListEndpoint<T>(
  path: string,
  findAll: () => Promise<T[]>
): void {
  app.get(path, async (_req, res) => {
    const items = await findAll();
    res.json({ data: items, total: items.length });
  });
}

createListEndpoint("/users", () => db.users.findAll());
createListEndpoint("/products", () => db.products.findAll());
createListEndpoint("/orders", () => db.orders.findAll());

// The abstraction is minimal and correct because three real
// examples informed its design.
```

### The Danger of Wrong Abstractions

```typescript
// Abstracted too early from two examples: user and product search.
// Both happened to search by "name."

function genericSearch<T>(collection: string, term: string): Promise<T[]> {
  return db.query(`SELECT * FROM ${collection} WHERE name ILIKE '%${term}%'`);
}

// Third case: order search. Orders don't have a "name" field.
// They search by order number, date range, and customer.
// The abstraction doesn't fit. Options:
//   1. Contort the abstraction (add parameters, conditionals)
//   2. Bypass it (duplicate code anyway)
//   3. Rewrite it (wasted earlier effort)

// If we had waited for three examples, we would have seen
// that search is not as uniform as it appeared from two cases.
```

## The DRY-YAGNI Balance

```
Duplication Count  |  Action            |  Principle
-------------------+--------------------+------------
1st occurrence     |  Just write it     |  YAGNI
2nd occurrence     |  Note it, tolerate |  Rule of Three
3rd occurrence     |  Refactor/abstract |  DRY
```

The Rule of Three is the heuristic that tells you when DRY should override YAGNI.

## Alternatives and Related Concepts

- **AHA Programming (Avoid Hasty Abstractions):** Kent C. Dodds's formalization of the same idea.
- **WET (Write Everything Twice):** A humorous alternative to DRY that makes the same point.
- **Sandi Metz's "duplication is far cheaper than the wrong abstraction":** The definitive quote on premature abstraction.
- **Refactoring:** Martin Fowler's approach — refactor when patterns emerge, not before.

## When NOT to Apply

- **Known, well-understood patterns:** If you have built the same CRUD API 50 times, you do not need three occurrences to know the pattern. Use your existing abstraction.
- **Security-critical code:** Do not duplicate authentication logic twice waiting for a third. Abstract it on the first occurrence because correctness is paramount.
- **Exact duplicates:** If you literally copy-paste the same 50 lines, even two occurrences justify extraction. The Rule of Three applies to *similar* code, not *identical* code.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Abstract immediately (DRY zealotry) | No duplication | Wrong abstractions, rigid code |
| Never abstract (no DRY) | Maximum flexibility | Maintenance nightmare, bugs from inconsistency |
| Rule of Three | Right abstractions from real patterns | Temporary duplication, discipline required |
| AHA (Avoid Hasty Abstractions) | Same as Rule of Three, more nuanced | Requires judgment on what "hasty" means |

## Real-World Consequences

- **Enterprise Java frameworks:** Over-abstracted from too few examples, producing `AbstractSingletonProxyFactoryBean` — abstractions that make simple things complex.
- **React component libraries:** Teams that abstract a "generic form component" from one form end up fighting the abstraction for every subsequent form that is slightly different.
- **Microservice extraction:** Teams that extract a microservice after the second use case often get the service boundary wrong. Wait for three distinct consumers to see the real boundary.

## The Sandi Metz Quote

> "Duplication is far cheaper than the wrong abstraction. Prefer duplication over the wrong abstraction."

This is the Rule of Three in one sentence. Duplication is a known cost with linear growth. The wrong abstraction is an unknown cost with exponential growth — it infects every future use case.

## Further Reading

- Fowler, M. (2018). *Refactoring: Improving the Design of Existing Code* (2nd ed.)
- Metz, S. (2016). "The Wrong Abstraction" — sandimetz.com
- Dodds, K.C. (2020). "AHA Programming" — kentcdodds.com
- Hunt, A. & Thomas, D. (1999). *The Pragmatic Programmer* — DRY principle
