# Separation of Concerns

**Divide a program into distinct sections, each addressing a separate concern -- a cohesive area of functionality or responsibility.**

---

## Origin

Coined by **Edsger W. Dijkstra** in his 1974 paper "On the Role of Scientific Thought." Dijkstra described it as the ability to study one aspect of a problem in isolation, deliberately ignoring the other aspects. The concept was further developed by David Parnas in his seminal 1972 paper "On the Criteria To Be Used in Decomposing Systems into Modules," which demonstrated that decomposition should be based on information hiding rather than functional decomposition.

---

## The Problem It Solves

Without separation of concerns, code devolves into what's colloquially called "spaghetti" -- everything depends on everything, and you can't change one thing without understanding and potentially breaking unrelated things. Business logic gets tangled with UI rendering. Database queries appear inside HTTP handlers. Authentication checks are scattered across every function. The result: changes are expensive, testing is difficult (you can't test business logic without spinning up a database), and multiple developers can't work on different features without merge conflicts.

---

## The Principle Explained

Separation of concerns is the practice of organizing code so that each module, class, or function deals with one distinct aspect of the system. "Concern" is intentionally broad -- it could be a feature (user authentication), a technical layer (database access), a cross-cutting responsibility (logging), or a domain concept (order processing).

The key insight is that **separation enables independent reasoning**. When concerns are properly separated, you can understand, modify, test, and deploy the authentication system without knowing anything about order processing. You can change the database from PostgreSQL to MongoDB without touching business logic. You can redesign the UI without rewriting the API. Each concern becomes a self-contained problem that a developer can fit in their head.

Separation of concerns manifests at multiple levels: within a function (single responsibility), within a module (cohesion), within a service (bounded contexts), and across a system (layered architecture, microservices). The most common mistake is applying it only at one level. Code can have beautiful function-level separation but terrible module-level separation, where every module reaches into every other module's internals.

---

## Code Examples

### BAD: Concerns tangled in a single function

```typescript
// This function handles HTTP, validation, business logic, database access,
// email sending, and error formatting -- all in one place.
async function handleOrderSubmission(req: Request, res: Response): Promise<void> {
  try {
    const { items, customerId } = req.body;

    // Validation (concern 1)
    if (!items || items.length === 0) {
      res.status(400).json({ error: "No items provided" });
      return;
    }

    // Database access (concern 2)
    const customer = await pool.query("SELECT * FROM customers WHERE id = $1", [customerId]);
    if (customer.rows.length === 0) {
      res.status(404).json({ error: "Customer not found" });
      return;
    }

    // Business logic (concern 3)
    let total = 0;
    for (const item of items) {
      const product = await pool.query("SELECT price FROM products WHERE id = $1", [item.productId]);
      total += product.rows[0].price * item.quantity;
    }
    if (customer.rows[0].credit_limit < total) {
      res.status(400).json({ error: "Credit limit exceeded" });
      return;
    }

    // More database access (concern 2 again)
    const order = await pool.query(
      "INSERT INTO orders (customer_id, total) VALUES ($1, $2) RETURNING *",
      [customerId, total]
    );

    // Email notification (concern 4)
    await fetch("https://api.sendgrid.com/v3/mail/send", {
      method: "POST",
      headers: { Authorization: `Bearer ${process.env.SENDGRID_KEY}` },
      body: JSON.stringify({
        to: customer.rows[0].email,
        subject: "Order Confirmation",
        html: `<h1>Order #${order.rows[0].id}</h1><p>Total: $${total}</p>`,
      }),
    });

    // HTTP response formatting (concern 5)
    res.status(201).json({ orderId: order.rows[0].id, total });
  } catch (error) {
    console.error("Order failed:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}
```

### GOOD: Each concern in its own module

```typescript
// --- order-validator.ts --- (Concern: input validation)
interface OrderInput {
  readonly items: ReadonlyArray<{ productId: string; quantity: number }>;
  readonly customerId: string;
}

function validateOrderInput(input: unknown): OrderInput {
  const { items, customerId } = input as Record<string, unknown>;
  if (!Array.isArray(items) || items.length === 0) {
    throw new ValidationError("No items provided");
  }
  if (typeof customerId !== "string") {
    throw new ValidationError("Invalid customer ID");
  }
  return { items, customerId } as OrderInput;
}

// --- order-service.ts --- (Concern: business logic)
async function submitOrder(
  input: OrderInput,
  deps: { customers: CustomerRepo; products: ProductRepo; orders: OrderRepo }
): Promise<Order> {
  const customer = await deps.customers.getById(input.customerId);
  if (!customer) throw new NotFoundError("Customer not found");

  const total = await calculateOrderTotal(input.items, deps.products);

  if (customer.creditLimit < total) {
    throw new BusinessRuleError("Credit limit exceeded");
  }

  return deps.orders.create({ customerId: input.customerId, total });
}

// --- order-notifications.ts --- (Concern: notifications)
async function sendOrderConfirmation(order: Order, customer: Customer): Promise<void> {
  await emailService.send({
    to: customer.email,
    template: "order-confirmation",
    data: { orderId: order.id, total: order.total },
  });
}

// --- order-controller.ts --- (Concern: HTTP layer, orchestration only)
async function handleOrderSubmission(req: Request, res: Response): Promise<void> {
  const input = validateOrderInput(req.body);
  const order = await submitOrder(input, { customers, products, orders });
  await sendOrderConfirmation(order, await customers.getById(input.customerId));
  res.status(201).json({ orderId: order.id, total: order.total });
}
```

### BAD: Leaking concerns through return types

```typescript
// The service layer returns HTTP-specific objects
class UserService {
  async getUser(id: string): Promise<{ status: number; body: unknown }> {
    const user = await this.db.findUser(id);
    if (!user) return { status: 404, body: { error: "Not found" } };
    return { status: 200, body: user };
  }
}
// Now UserService is coupled to HTTP. Can't use it from a CLI tool,
// a message queue consumer, or a scheduled job without fake status codes.
```

### GOOD: Layer-appropriate return types

```typescript
class UserService {
  async getUser(id: string): Promise<User | null> {
    return this.db.findUser(id);
  }
}

// The controller translates domain results to HTTP concerns
class UserController {
  async getUser(req: Request, res: Response): Promise<void> {
    const user = await this.userService.getUser(req.params.id);
    if (!user) {
      res.status(404).json({ error: "User not found" });
      return;
    }
    res.status(200).json(user);
  }
}
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Cross-Cutting Concerns** | Some concerns (logging, authentication, error handling) cut across all modules. SoC struggles with these -- they don't fit neatly into one module. |
| **Aspect-Oriented Programming (AOP)** | A programming paradigm specifically designed to handle cross-cutting concerns. Uses aspects/decorators to inject behavior (logging, transactions) without polluting business logic. |
| **Hexagonal Architecture (Ports & Adapters)** | An architectural pattern that enforces SoC by separating the domain core from external infrastructure through ports (interfaces) and adapters (implementations). |
| **Vertical Slice Architecture** | An alternative to layered separation. Instead of separating by technical concern (UI, business, data), separate by feature. Each "slice" contains all layers for one feature. |

---

## When NOT to Apply

- **Tiny applications.** A 200-line script doesn't need three layers. Over-separating a small program makes it harder to understand by scattering related logic across files.
- **Prototypes and spikes.** When you're exploring a problem space, tangled code is fine. Separate concerns once you understand what the concerns actually are.
- **When separation introduces excessive indirection.** If understanding a request flow requires opening 12 files, you've over-separated. The cure is worse than the disease.
- **Performance-critical inner loops.** Sometimes you intentionally co-locate concerns (data access + transformation) to avoid function call overhead or to enable cache-friendly memory access.

---

## Tensions & Trade-offs

- **SoC vs. Cohesion**: Taken too far, SoC scatters related code across many files. You end up with a "validation" module that validates ten unrelated things. The fix: separate by *domain concern* (all order logic together), not by *technical concern* (all validation in one place).
- **SoC vs. Performance**: Separation often means more function calls, more object allocations, more serialization boundaries. In hot paths, intentionally violating SoC for performance is legitimate.
- **SoC vs. Simplicity (KISS)**: Three layers for a CRUD app is over-engineering. The "right" amount of separation depends on complexity.
- **Horizontal vs. Vertical Separation**: Traditional layered architecture (horizontal) can lead to shotgun surgery -- adding a field requires changing the UI, service, repository, and database. Vertical slices keep everything for one feature together.

---

## Real-World Consequences

A healthcare startup mixed HIPAA-sensitive patient data handling with general application logging. Patient names and medical record numbers appeared in application logs that were shipped to a third-party logging service -- a HIPAA violation discovered during an audit. The fine was substantial, but the real cost was the engineering effort to untangle data handling concerns from logging concerns across the entire codebase. Had these been separated from the start, the logging layer would never have had access to patient data.

---

## Key Quotes

> "Let me try to explain to you, what to my taste is characteristic for all intelligent thinking. It is, that one is willing to study in depth an aspect of one's subject matter in isolation for the sake of its own consistency."
> -- Edsger W. Dijkstra

> "The purpose of abstraction is not to be vague, but to create a new semantic level in which one can be absolutely precise."
> -- Edsger W. Dijkstra

> "We propose instead that one begins with a list of difficult design decisions or design decisions which are likely to change. Each module is then designed to hide such a decision from the others."
> -- David Parnas

---

## Further Reading

- ["On the Role of Scientific Thought"](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD447.html) -- Edsger W. Dijkstra (1974)
- ["On the Criteria To Be Used in Decomposing Systems into Modules"](https://www.win.tue.nl/~wstomv/edu/2ip30/references/criteria_for_modularization.pdf) -- David Parnas (1972)
- *Clean Architecture* -- Robert C. Martin (2017)
- *Hexagonal Architecture*  -- Alistair Cockburn (2005)
- *A Philosophy of Software Design* -- John Ousterhout (2018), Chapter 4: "Modules Should Be Deep"
