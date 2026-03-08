# God Object (God Class)

## Origin

The term emerged in the object-oriented programming community in the 1990s, popularized by Arthur Riel in *Object-Oriented Design Heuristics* (1996) and by the anti-pattern literature of Brown et al. in *AntiPatterns* (1998). Also known as the "Blob" or "Monster Class."

## Explanation

A God Object is a single class or module that knows too much or does too much. It centralizes a disproportionate amount of the system's logic and data, making it the dependency hub that everything else revolves around. It violates the Single Responsibility Principle so thoroughly that it becomes responsible for everything.

God Objects form naturally: a class starts small, grows because "it's convenient to put this here," and eventually becomes the gravitational center of the codebase. Every new feature touches it. Every bug leads back to it. Every refactoring attempt is blocked by it.

## TypeScript Code Examples

### Bad: The God Object

```typescript
// app/AppManager.ts — 3,000 lines and growing

export class AppManager {
  private db: Database;
  private cache: Redis;
  private mailer: EmailService;
  private logger: Logger;
  private config: Config;
  private users: Map<string, User>;
  private sessions: Map<string, Session>;
  private orders: Map<string, Order>;
  private inventory: Map<string, Product>;
  private notifications: Queue;

  // User management
  createUser(data: UserInput): User { /* ... */ }
  deleteUser(id: string): void { /* ... */ }
  updateUserProfile(id: string, data: Partial<User>): User { /* ... */ }
  authenticateUser(email: string, password: string): Session { /* ... */ }
  resetPassword(email: string): void { /* ... */ }

  // Order management
  createOrder(userId: string, items: Item[]): Order { /* ... */ }
  cancelOrder(orderId: string): void { /* ... */ }
  refundOrder(orderId: string): void { /* ... */ }
  calculateShipping(order: Order): number { /* ... */ }
  applyDiscount(orderId: string, code: string): void { /* ... */ }

  // Inventory management
  addProduct(product: Product): void { /* ... */ }
  updateStock(productId: string, quantity: number): void { /* ... */ }
  checkAvailability(productId: string): boolean { /* ... */ }

  // Notifications
  sendEmail(to: string, subject: string, body: string): void { /* ... */ }
  sendPush(userId: string, message: string): void { /* ... */ }
  sendSMS(phone: string, message: string): void { /* ... */ }

  // Reporting
  generateSalesReport(dateRange: DateRange): Report { /* ... */ }
  generateUserReport(): Report { /* ... */ }
  exportToCSV(report: Report): string { /* ... */ }

  // ... 50 more methods covering every concern in the system
}
```

### Good: Decomposed into Focused Services

```typescript
// users/UserService.ts
export class UserService {
  constructor(
    private readonly userRepo: UserRepository,
    private readonly passwordHasher: PasswordHasher
  ) {}

  async create(data: UserInput): Promise<User> {
    const hashedPassword = await this.passwordHasher.hash(data.password);
    return this.userRepo.create({ ...data, password: hashedPassword });
  }

  async findById(id: string): Promise<User | null> {
    return this.userRepo.findById(id);
  }
}

// auth/AuthService.ts
export class AuthService {
  constructor(
    private readonly userRepo: UserRepository,
    private readonly sessionStore: SessionStore,
    private readonly passwordHasher: PasswordHasher
  ) {}

  async authenticate(email: string, password: string): Promise<Session> {
    const user = await this.userRepo.findByEmail(email);
    if (!user) throw new AuthError("INVALID_CREDENTIALS");
    const valid = await this.passwordHasher.verify(password, user.password);
    if (!valid) throw new AuthError("INVALID_CREDENTIALS");
    return this.sessionStore.create(user.id);
  }
}

// orders/OrderService.ts
export class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly inventoryService: InventoryService,
    private readonly pricingService: PricingService
  ) {}

  async create(userId: string, items: ReadonlyArray<OrderItem>): Promise<Order> {
    for (const item of items) {
      const available = await this.inventoryService.checkAvailability(item.productId);
      if (!available) throw new OrderError("ITEM_UNAVAILABLE", item.productId);
    }
    const total = await this.pricingService.calculateTotal(items);
    return this.orderRepo.create({ userId, items, total });
  }
}

// notifications/NotificationService.ts
export class NotificationService {
  constructor(private readonly channels: ReadonlyArray<NotificationChannel>) {}

  async send(userId: string, notification: Notification): Promise<void> {
    const userPrefs = await this.getUserPreferences(userId);
    const channel = this.channels.find((c) => c.type === userPrefs.preferredChannel);
    if (channel) await channel.send(userId, notification);
  }
}
```

## Decomposition Strategies

1. **Extract by domain:** Group methods that operate on the same data into a dedicated service.
2. **Extract by responsibility:** Separate "what to do" from "how to do it" (e.g., business logic vs. notification delivery).
3. **Strangler fig:** Create new services alongside the God Object, migrate callers one at a time, delete methods from the God Object as they become unused.
4. **Event-driven decomposition:** Replace direct method calls with events, allowing services to react independently.

## Alternatives and Related Concepts

- **Single Responsibility Principle (SRP):** Each class should have one reason to change.
- **Domain-Driven Design:** Bounded contexts prevent God Objects at the architectural level.
- **Microservices:** The architectural-scale solution (but can create "distributed God Objects" if done poorly).
- **Facade Pattern:** Sometimes confused with God Objects, but facades delegate to focused services rather than containing all logic.

## When NOT to Apply (When a Large Class Is Acceptable)

- **Orchestrators:** A class that coordinates other services without containing business logic itself is not a God Object — it is a mediator.
- **Framework entry points:** Express's `app`, React's root component, or a CLI's main function naturally touches many concerns.
- **Early prototypes:** Concentrating logic in one place during exploration is fine. Refactor before production.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| God Object (keep it) | Everything in one place, easy to find | Impossible to test, impossible to parallelize work |
| Full decomposition | Clean separation, independent testing | More files, more indirection, harder to trace |
| Gradual strangler fig | Low risk, incremental improvement | Long transition period, two patterns coexist |
| Event-driven decomposition | Loose coupling, independent deployment | Eventual consistency, debugging complexity |

## Real-World Consequences

- **WordPress `wp-includes/post.php`:** Over 4,000 lines handling everything related to posts — creation, deletion, metadata, revisions, attachments, and more. A classic God Object in procedural form.
- **Rails monoliths:** `ApplicationController` subclasses that accumulate every concern: auth, logging, error handling, feature flags, analytics tracking.
- **Android's `Activity`:** The original Android `Activity` class encouraged God Object patterns, leading Google to introduce Fragments, ViewModels, and Jetpack Compose.
- **Any codebase's `utils.ts`:** The file that starts as "a few helpers" and grows to 2,000 lines of unrelated functions.

## Detection Signals

- File exceeds 500 lines
- Class has more than 10 public methods
- Most imports in the project point to one file
- Test file for the class is larger than the class itself
- "Where should I put this?" is always answered with the same file

## Further Reading

- Riel, A. (1996). *Object-Oriented Design Heuristics*
- Brown, W. et al. (1998). *AntiPatterns: Refactoring Software, Architectures, and Projects in Crisis*
- Martin, R. (2003). *Agile Software Development: Principles, Patterns, and Practices*
- Fowler, M. (2018). *Refactoring* — "Large Class" smell
