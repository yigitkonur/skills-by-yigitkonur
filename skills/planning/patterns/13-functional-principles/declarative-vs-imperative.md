# Declarative vs. Imperative Programming

**Describe WHAT you want, not HOW to achieve it. Let the system figure out the execution details.**

---

## Origin / History

The declarative/imperative distinction dates to the earliest days of computing. Assembly language and Fortran (1957) were imperative — sequences of instructions modifying state. Lisp (1958) and Prolog (1972) introduced declarative paradigms: Lisp through expressions that describe computations (functional), Prolog through logical rules that describe relationships (logic programming). SQL (1970s, Codd's relational model) became the most commercially successful declarative language — you describe what data you want, not how to traverse indexes.

In modern web development, React (2013) popularized declarative UI: describe what the UI should look like for a given state, and the framework handles DOM updates. Infrastructure as Code (Terraform, Kubernetes YAML) brought declarative thinking to operations: describe the desired state of infrastructure, and the tool converges actual state to desired state.

---

## The Problem It Solves

Imperative code forces the reader to trace every step to understand the intent. A 20-line loop that iterates over an array, checks conditions, accumulates results, and handles edge cases requires mental simulation to understand. The intent — "get the names of active users sorted by signup date" — is buried in the mechanism.

More critically, imperative code tightly couples the intent with the implementation. If you write a hand-optimized traversal of a tree, changing the data structure requires rewriting the traversal. A declarative approach — "give me all nodes matching this predicate" — lets the underlying system choose the best traversal strategy.

Declarative code also enables optimization. A SQL query planner can reorder joins, choose indexes, and parallelize execution precisely because the query says what, not how. An imperative "for each row in table A, find matching rows in table B" locks the execution plan.

---

## The Principle Explained

Imperative programming is a sequence of commands that change program state: "do this, then do this, then do this." Declarative programming is a description of the desired result: "I want this." The distinction is about the level of abstraction.

In practice, all declarative code is executed imperatively at some level — the SQL engine runs imperative algorithms, React performs imperative DOM mutations. The value of the declarative layer is separation of concerns: the programmer focuses on business logic while the framework or runtime handles execution strategy. This separation enables the implementation to improve (better query planner, faster diffing algorithm) without changing the declarative code.

The spectrum between imperative and declarative is continuous, not binary. A for-loop is imperative. `array.filter().map()` is more declarative. A SQL query is highly declarative. A Prolog rule is almost entirely declarative. Most practical code lives in the middle, using declarative patterns where they improve clarity and imperative patterns where fine-grained control is needed.

---

## Code Examples

### BAD: Imperative — HOW to compute the result, step by step

```typescript
interface Order {
  id: string;
  customerId: string;
  items: Array<{ productId: string; quantity: number; unitPrice: number }>;
  status: "pending" | "shipped" | "delivered" | "cancelled";
  createdAt: Date;
}

// Imperative: manually iterate, accumulate, sort
function getTopCustomersByRevenue(
  orders: Order[],
  limit: number,
): Array<{ customerId: string; totalRevenue: number }> {
  // Step 1: Filter to delivered orders
  const delivered: Order[] = [];
  for (let i = 0; i < orders.length; i++) {
    if (orders[i].status === "delivered") {
      delivered.push(orders[i]);
    }
  }

  // Step 2: Calculate revenue per customer
  const revenueMap: Record<string, number> = {};
  for (let i = 0; i < delivered.length; i++) {
    const order = delivered[i];
    let orderTotal = 0;
    for (let j = 0; j < order.items.length; j++) {
      orderTotal += order.items[j].quantity * order.items[j].unitPrice;
    }
    if (revenueMap[order.customerId] === undefined) {
      revenueMap[order.customerId] = 0;
    }
    revenueMap[order.customerId] += orderTotal;
  }

  // Step 3: Convert to array and sort
  const entries: Array<{ customerId: string; totalRevenue: number }> = [];
  for (const customerId in revenueMap) {
    entries.push({ customerId, totalRevenue: revenueMap[customerId] });
  }
  entries.sort((a, b) => b.totalRevenue - a.totalRevenue);

  // Step 4: Take top N
  const result: Array<{ customerId: string; totalRevenue: number }> = [];
  for (let i = 0; i < Math.min(limit, entries.length); i++) {
    result.push(entries[i]);
  }
  return result;
}
```

### GOOD: Declarative — WHAT result we want

```typescript
// Declarative: describe the transformation pipeline
function getTopCustomersByRevenue(
  orders: readonly Order[],
  limit: number,
): Array<{ customerId: string; totalRevenue: number }> {
  const orderTotal = (order: Order): number =>
    order.items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);

  const revenueByCustomer = orders
    .filter((order) => order.status === "delivered")
    .reduce<Record<string, number>>((acc, order) => ({
      ...acc,
      [order.customerId]: (acc[order.customerId] ?? 0) + orderTotal(order),
    }), {});

  return Object.entries(revenueByCustomer)
    .map(([customerId, totalRevenue]) => ({ customerId, totalRevenue }))
    .sort((a, b) => b.totalRevenue - a.totalRevenue)
    .slice(0, limit);
}
```

### SQL as the ultimate declarative language

```typescript
// The same query in SQL — pure declaration of intent
const query = `
  SELECT
    customer_id,
    SUM(quantity * unit_price) AS total_revenue
  FROM orders
  JOIN order_items USING (order_id)
  WHERE status = 'delivered'
  GROUP BY customer_id
  ORDER BY total_revenue DESC
  LIMIT $1
`;

// The database engine decides: which index to use, whether to parallelize,
// how to join, whether to use a hash aggregate or sort aggregate.
// You described WHAT you want. The engine decides HOW.
```

### React as declarative UI

```typescript
// Imperative DOM manipulation
function updateUserListImperative(users: User[]): void {
  const container = document.getElementById("user-list")!;
  // Must manually track what exists, what changed, what to remove
  container.innerHTML = "";
  for (const user of users) {
    const li = document.createElement("li");
    li.textContent = user.name;
    li.className = user.active ? "active" : "inactive";
    li.addEventListener("click", () => selectUser(user.id));
    container.appendChild(li);
  }
}

// Declarative UI — describe what the UI should look like
function UserList({ users }: { users: User[] }): JSX.Element {
  return (
    <ul>
      {users.map((user) => (
        <li
          key={user.id}
          className={user.active ? "active" : "inactive"}
          onClick={() => selectUser(user.id)}
        >
          {user.name}
        </li>
      ))}
    </ul>
  );
}
// React handles the HOW: diffing, batching, minimal DOM updates
```

### Declarative configuration (Terraform-style)

```typescript
// Declarative infrastructure description
interface InfrastructureConfig {
  readonly database: {
    readonly engine: "postgresql";
    readonly version: "15";
    readonly instanceClass: "db.r6g.large";
    readonly storage: { readonly sizeGb: 100; readonly type: "gp3" };
    readonly replicas: 2;
  };
  readonly cache: {
    readonly engine: "redis";
    readonly nodeType: "cache.r6g.large";
    readonly clusters: 3;
  };
}

// The provisioning system converges actual state to this desired state.
// You don't say "create a DB, then create replicas, then create cache..."
// You say "I want this" and the system figures out the steps.
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Imperative with clear structure** | Full control over execution. Sometimes necessary for performance-critical code, I/O sequencing, or complex stateful algorithms. |
| **Hybrid approaches** | Use declarative for the high-level pipeline, drop into imperative for specific steps. Most practical codebases do this. |
| **Domain-Specific Languages (DSLs)** | Custom declarative languages for specific domains (CSS for styling, SQL for queries, Terraform HCL for infrastructure). Powerful but requires learning a new language. |
| **Reactive programming (RxJS)** | Declarative stream transformations. Excellent for event-heavy domains, but the learning curve is steep. |
| **Logic programming (Prolog, Datalog)** | Describe rules and relationships; the engine finds solutions. Extremely declarative but niche applicability. |

---

## When NOT to Apply

- **Performance-critical inner loops**: Declarative abstractions like `map` and `filter` create intermediate arrays. When processing millions of items, an imperative loop that does everything in one pass is significantly faster.
- **Complex stateful algorithms**: Graph algorithms, parsers, and simulations often need explicit state management that declarative styles cannot naturally express.
- **When debugging is the priority**: Declarative pipelines are harder to step through. During active debugging, temporary imperative code with intermediate variables and console.log is pragmatic.
- **When the abstraction leaks**: If you fight the declarative framework more than you use it (complex React effects, Terraform state hacks), the imperative approach may be simpler.

---

## Tensions & Trade-offs

- **Readability vs. Debugging**: Declarative code is easier to read at the intent level but harder to trace at the execution level. When something goes wrong in a SQL query, you need `EXPLAIN ANALYZE` to understand what the engine actually did.
- **Optimization vs. Control**: Declarative systems can optimize better than hand-written code (query planners outperform most developers). But when they optimize poorly, the fix is often opaque — adding hints, rewriting queries, or fighting the framework.
- **Learning curve vs. Productivity**: Declarative patterns (React, SQL, Terraform) require learning the framework's model. The initial learning investment is higher, but long-term productivity is typically better.
- **Abstraction vs. Leakiness**: All declarative abstractions leak eventually. React's `useEffect` cleanup, SQL's optimizer quirks, Terraform's state drift — understanding the imperative layer beneath is eventually necessary.

---

## Real-World Consequences

**SQL query planner evolution**: PostgreSQL's query planner has improved dramatically over 25 years. Queries written in 2000 run faster today without any changes — because the declarative SQL did not prescribe the execution strategy. Imperative code from 2000 would need rewriting to take advantage of modern hardware.

**React's rendering optimizations**: React 18's concurrent rendering, automatic batching, and server components all work because components are declarative. The framework can decide when and how to render. Imperative DOM manipulation cannot be optimized by the framework because the developer has already prescribed the execution.

**Terraform state management challenges**: Terraform's declarative model works beautifully until state drifts (someone manually changes infrastructure). The gap between declared desired state and actual state causes plan/apply failures. Teams learn that declarative infrastructure requires disciplined processes — no manual changes, state locking, import of existing resources.

---

## Further Reading

- [E.W. Dijkstra — On the Role of Scientific Thought (1974)](https://www.cs.utexas.edu/users/EWD/ewd04xx/EWD447.PDF)
- [React Documentation — Thinking in React](https://react.dev/learn/thinking-in-react)
- [Terraform Documentation — Declarative Infrastructure](https://developer.hashicorp.com/terraform/intro)
- [Joe Armstrong — Why Functional Programming Matters (1984, John Hughes)](https://www.cs.kent.ac.uk/people/staff/dat/miranda/whyfp90.pdf)
- [PostgreSQL EXPLAIN Documentation](https://www.postgresql.org/docs/current/using-explain.html)
