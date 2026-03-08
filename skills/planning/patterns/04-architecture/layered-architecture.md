# Layered Architecture

**Organize code into horizontal layers with clear responsibilities, where each layer only depends on the layer directly below it.**

---

## Origin

Layered architecture is one of the oldest and most widespread architectural patterns in software engineering. It was formalized in the context of network protocols (the OSI model, 1977) and applied to software by authors including Frank Buschmann in *"Pattern-Oriented Software Architecture"* (POSA, 1996) and Martin Fowler in *"Patterns of Enterprise Application Architecture"* (2002). The classic three-tier architecture (presentation, business logic, data access) became the default for enterprise applications in the 1990s and remains the implicit starting point for most web applications today.

---

## The Problem It Solves

Without layers, business logic, UI rendering, and database queries become interleaved in the same files. A change to how data is displayed requires modifying the same code that handles business rules and database access. Testing is impossible without a running database and a rendered UI. New team members cannot understand the codebase because there is no organizing principle — every file can depend on every other file.

---

## The Principle Explained

Layered architecture divides the application into horizontal stacks, each with a distinct responsibility. The most common arrangement has three or four layers:

**Presentation Layer** (Controllers, Views, API endpoints): Handles HTTP requests, formats responses, manages user interaction. Contains no business logic — it delegates to the layer below.

**Business Logic Layer** (Services, Domain): Contains the application's core rules, workflows, and domain operations. Independent of how data is stored or presented. This is where the value lives.

**Data Access Layer** (Repositories, DAOs): Handles persistence — database queries, ORM configuration, cache access. Encapsulates storage details so the business layer does not know whether data comes from PostgreSQL, Redis, or an API.

**Infrastructure Layer** (optional, cross-cutting): Logging, configuration, authentication, and other concerns that span multiple layers.

The key rule is the **dependency direction**: each layer depends only on the layer directly below it. The presentation layer calls the business layer, not the data layer. The business layer calls the data layer, not the presentation layer. No layer reaches "around" to call a non-adjacent layer.

---

## Code Examples

### BAD: No layers — everything mixed together

```typescript
// A single file that handles HTTP, business logic, and database access
app.post("/api/orders", async (req, res) => {
  // Input validation (presentation concern)
  if (!req.body.customerId || !req.body.items?.length) {
    return res.status(400).json({ error: "Missing fields" });
  }

  // Business logic (domain concern) mixed with database queries
  const customer = await db.query(
    "SELECT * FROM customers WHERE id = $1",
    [req.body.customerId]
  );

  if (!customer.rows[0]) {
    return res.status(404).json({ error: "Customer not found" });
  }

  // More business logic interleaved with data access
  let total = 0;
  for (const item of req.body.items) {
    const product = await db.query(
      "SELECT * FROM products WHERE id = $1",
      [item.productId]
    );
    if (product.rows[0].stock < item.quantity) {
      return res.status(400).json({ error: `Insufficient stock: ${item.productId}` });
    }
    total += product.rows[0].price * item.quantity;

    // Direct database mutation inside a loop
    await db.query(
      "UPDATE products SET stock = stock - $1 WHERE id = $2",
      [item.quantity, item.productId]
    );
  }

  // Discount logic (business rule) tangled with everything else
  if (total > 100) total *= 0.9;

  const order = await db.query(
    "INSERT INTO orders (customer_id, total, status) VALUES ($1, $2, $3) RETURNING *",
    [req.body.customerId, total, "confirmed"]
  );

  // Response formatting (presentation concern)
  res.status(201).json({
    orderId: order.rows[0].id,
    total: order.rows[0].total,
    message: "Order placed successfully!",
  });
});
```

### GOOD: Clean layered architecture

```typescript
// ============================================
// LAYER 1: PRESENTATION — HTTP handling only
// ============================================

// src/presentation/controllers/order.controller.ts
class OrderController {
  constructor(private readonly orderService: OrderService) {}

  async createOrder(req: Request, res: Response): Promise<void> {
    // Presentation concern: parse and validate HTTP input
    const input = CreateOrderSchema.parse(req.body);

    try {
      // Delegate to business layer — no business logic here
      const result = await this.orderService.createOrder(input);

      // Presentation concern: format HTTP response
      res.status(201).json({
        data: OrderResponseMapper.toResponse(result),
      });
    } catch (error) {
      // Presentation concern: map domain errors to HTTP status codes
      if (error instanceof CustomerNotFoundError) {
        res.status(404).json({ error: error.message });
      } else if (error instanceof InsufficientStockError) {
        res.status(422).json({ error: error.message });
      } else {
        res.status(500).json({ error: "Internal server error" });
      }
    }
  }
}

// Input validation schema — presentation layer
const CreateOrderSchema = z.object({
  customerId: z.string().uuid(),
  items: z.array(z.object({
    productId: z.string().uuid(),
    quantity: z.number().int().positive(),
  })).min(1),
});

// Response mapper — presentation layer
class OrderResponseMapper {
  static toResponse(order: Order): OrderResponse {
    return {
      id: order.id,
      customerId: order.customerId,
      total: order.total,
      status: order.status,
      createdAt: order.createdAt.toISOString(),
    };
  }
}

// ============================================
// LAYER 2: BUSINESS LOGIC — domain rules and orchestration
// ============================================

// src/business/services/order.service.ts
class OrderService {
  constructor(
    private readonly customerRepo: CustomerRepository,
    private readonly productRepo: ProductRepository,
    private readonly orderRepo: OrderRepository
  ) {}

  async createOrder(input: CreateOrderInput): Promise<Order> {
    // Business rule: customer must exist
    const customer = await this.customerRepo.findById(input.customerId);
    if (!customer) throw new CustomerNotFoundError(input.customerId);

    // Business rule: all items must have sufficient stock
    const orderItems: OrderItem[] = [];
    for (const item of input.items) {
      const product = await this.productRepo.findById(item.productId);
      if (!product) throw new ProductNotFoundError(item.productId);
      if (!product.hasStock(item.quantity)) {
        throw new InsufficientStockError(item.productId, item.quantity);
      }
      orderItems.push(new OrderItem(product, item.quantity));
    }

    // Business rule: calculate total with discount
    const subtotal = orderItems.reduce((sum, item) => sum + item.lineTotal, 0);
    const discount = this.calculateDiscount(subtotal);
    const total = subtotal - discount;

    // Orchestrate the write operations
    const order = new Order(generateId(), customer.id, orderItems, total);

    for (const item of orderItems) {
      await this.productRepo.decrementStock(item.productId, item.quantity);
    }
    await this.orderRepo.save(order);

    return order;
  }

  // Business rule: pure logic, easily testable
  private calculateDiscount(subtotal: number): number {
    if (subtotal > 100) return subtotal * 0.1;
    return 0;
  }
}

// Domain models — business layer
class Order {
  readonly createdAt = new Date();
  readonly status = "confirmed";

  constructor(
    readonly id: string,
    readonly customerId: string,
    readonly items: OrderItem[],
    readonly total: number
  ) {}
}

class OrderItem {
  constructor(
    readonly product: Product,
    readonly quantity: number
  ) {}

  get productId(): string { return this.product.id; }
  get lineTotal(): number { return this.product.price * this.quantity; }
}

// ============================================
// LAYER 3: DATA ACCESS — persistence only
// ============================================

// src/data/repositories/order.repository.ts
interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: string): Promise<Order | null>;
  findByCustomerId(customerId: string): Promise<Order[]>;
}

class PostgresOrderRepository implements OrderRepository {
  constructor(private readonly pool: Pool) {}

  async save(order: Order): Promise<void> {
    // Data access concern: SQL, transactions, ORM details
    const client = await this.pool.connect();
    try {
      await client.query("BEGIN");
      await client.query(
        `INSERT INTO orders (id, customer_id, total, status, created_at)
         VALUES ($1, $2, $3, $4, $5)`,
        [order.id, order.customerId, order.total, order.status, order.createdAt]
      );
      for (const item of order.items) {
        await client.query(
          `INSERT INTO order_items (order_id, product_id, quantity, unit_price)
           VALUES ($1, $2, $3, $4)`,
          [order.id, item.productId, item.quantity, item.product.price]
        );
      }
      await client.query("COMMIT");
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async findById(id: string): Promise<Order | null> {
    const result = await this.pool.query(
      "SELECT * FROM orders WHERE id = $1",
      [id]
    );
    if (result.rows.length === 0) return null;
    return this.toDomain(result.rows[0]);
  }

  async findByCustomerId(customerId: string): Promise<Order[]> {
    const result = await this.pool.query(
      "SELECT * FROM orders WHERE customer_id = $1 ORDER BY created_at DESC",
      [customerId]
    );
    return result.rows.map((row) => this.toDomain(row));
  }

  private toDomain(row: Record<string, unknown>): Order {
    // Map database row to domain model
    return new Order(
      row.id as string,
      row.customer_id as string,
      [], // Would load items separately in a real implementation
      row.total as number
    );
  }
}
```

---

## Alternatives & Related Principles

| Pattern | Relationship |
|---|---|
| **Hexagonal Architecture** | Inverts the dependency: business logic does not depend on data access. In layered architecture, the business layer calls the data layer interface, but the direction of dependency is still downward. In hexagonal, the data layer implements interfaces defined by the business layer. |
| **Vertical Slice Architecture** | Organizes by feature instead of by layer. Each feature has its own controller, service, and repository. Trades cross-feature reuse for feature-level cohesion. |
| **Feature Folders** | A softer version of vertical slices: the project structure groups files by feature rather than by layer, but the internal structure of each feature may still follow layers. |
| **Clean Architecture** | Layered with the dependency rule explicitly pointing inward. Entities at the center, use cases next, then adapters, then frameworks. |

---

## When NOT to Apply

- **Complex domain logic**: When the domain is rich, layered architecture's downward dependency direction means the business layer depends on the data layer's abstractions. Hexagonal/Clean Architecture provides better isolation.
- **When layers become pass-through**: If the service layer is just calling the repository and returning the result, the layer adds no value. Consider collapsing thin layers.
- **Microservices with simple logic**: A microservice that reads from a queue and writes to a database may not need formal layers. A single module is sufficient.
- **Frontend applications**: React/Vue applications have their own organizational patterns (component-based, feature-based) that do not map well to traditional layers.

---

## Tensions & Trade-offs

- **Layer purity vs. pragmatism**: Strict layering means the controller cannot directly query the database, even for a simple health check. Pragmatic teams allow exceptions.
- **Horizontal layers vs. vertical features**: Changing a feature requires touching every layer. This is the main argument for vertical slice architecture.
- **Abstraction overhead**: Each layer boundary requires mapping (DTO to entity, entity to database row). This mapping code is tedious and error-prone.
- **"Service layer" bloat**: The business layer often becomes a God service that orchestrates everything, violating the Single Responsibility Principle.
- **Testing at the boundary**: Unit testing a layer requires mocking the layer below. Integration testing requires all layers. Neither is a perfect testing strategy alone.

---

## Real-World Consequences

**Adherence example**: The Spring Framework's default project structure (controller, service, repository) is layered architecture. This convention has enabled millions of developers to quickly understand and contribute to Spring projects. The pattern's simplicity is its greatest strength for typical web applications.

**Limitation example**: A financial services company used strict four-layer architecture. To add a new field to a form, a developer had to modify the API DTO, the service layer mapping, the domain entity, the repository mapping, and the database migration — five files for one field. They eventually moved to vertical slices for new features while keeping layers for existing code.

---

## Key Quotes

> "The most common architecture pattern is the layered architecture pattern, otherwise known as the n-tier architecture pattern." — Mark Richards, *Software Architecture Patterns*

> "Layers are the simplest form of architectural pattern. They are easy to understand, easy to implement, and easy to get wrong." — Frank Buschmann, POSA

> "If your service layer is just delegating to the repository, you don't have a service layer — you have unnecessary indirection." — pragmatic counterpoint

---

## Further Reading

- Buschmann, F. et al. — *Pattern-Oriented Software Architecture, Volume 1* (1996)
- Fowler, M. — *Patterns of Enterprise Application Architecture* (2002)
- Richards, M. — *Software Architecture Patterns* (2015, O'Reilly report)
- Bogard, J. — [Vertical Slice Architecture](https://jimmybogard.com/vertical-slice-architecture/) (the alternative)
- Palermo, J. — [The Onion Architecture](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/) (layered with inverted dependencies)
