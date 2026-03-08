# Open-Closed Principle (OCP)

**Software entities should be open for extension but closed for modification.**

---

## Origin

Formulated by **Bertrand Meyer** in his 1988 book *Object-Oriented Software Construction*. Meyer's original version relied on implementation inheritance: you extend a class by subclassing it, leaving the original class unchanged. **Robert C. Martin** later reinterpreted OCP to emphasize polymorphism and abstractions (interfaces) rather than inheritance, which is the version most widely used today. Martin's restatement: "You should be able to extend the behavior of a system without having to modify that system."

---

## The Problem It Solves

Every time you modify existing code, you risk breaking something that already works. The modification must be tested, reviewed, and deployed -- along with everything that depends on the modified code. In a system without OCP, adding a new payment method means editing the payment processing function (adding another `if/else` or `switch` case). Every change to that function risks breaking all existing payment methods. The file becomes a merge conflict magnet: every developer adding a new feature touches the same function.

---

## The Principle Explained

OCP asks you to design modules so that new behavior can be added by writing *new* code, not by changing *existing* code. The key mechanism is abstraction: define a stable interface (closed for modification), and allow new implementations of that interface (open for extension). When the system needs to handle a new case, you add a new class that implements the interface -- the existing code remains untouched.

This principle is powerful in the right context but dangerous when misapplied. Making code "open for extension" has a cost: you need to identify the correct extension points, define appropriate abstractions, and accept the indirection that abstractions introduce. If you guess wrong about where extension will be needed, you've added complexity for no benefit. If you guess right, adding new features becomes trivially easy and risk-free.

The pragmatic approach: don't make everything extensible from day one. Write simple, direct code. The *first* time you need to modify a module to add a new variation, refactor it to be open-closed. Now the second, third, and fourth variations are cheap. This "fool me once" strategy balances YAGNI (don't add abstractions speculatively) with OCP (make the code extensible where you've proven extension is needed).

---

## Code Examples

### BAD: Modification required for every new case

```typescript
// Adding a new shape requires modifying this function
function calculateArea(shape: Shape): number {
  switch (shape.type) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rectangle":
      return shape.width * shape.height;
    case "triangle":
      return 0.5 * shape.base * shape.height;
    // To add "ellipse", you MUST modify this function.
    // Every modification risks breaking existing calculations.
    default:
      throw new Error(`Unknown shape: ${shape.type}`);
  }
}

// Same pattern in a more realistic setting
function processPayment(payment: Payment): ProcessingResult {
  switch (payment.method) {
    case "credit_card":
      return processCreditCard(payment);
    case "paypal":
      return processPayPal(payment);
    case "bank_transfer":
      return processBankTransfer(payment);
    // Adding Apple Pay? Modify this function.
    // Adding crypto? Modify this function.
    // Each modification risks breaking all existing payment flows.
    default:
      throw new Error(`Unsupported payment method: ${payment.method}`);
  }
}
```

### GOOD: Extension without modification

```typescript
// --- Shape hierarchy: open for extension, closed for modification ---

interface Shape {
  area(): number;
}

class Circle implements Shape {
  constructor(private readonly radius: number) {}
  area(): number { return Math.PI * this.radius ** 2; }
}

class Rectangle implements Shape {
  constructor(
    private readonly width: number,
    private readonly height: number,
  ) {}
  area(): number { return this.width * this.height; }
}

// Adding a new shape: write a NEW class. No existing code changes.
class Ellipse implements Shape {
  constructor(
    private readonly semiMajor: number,
    private readonly semiMinor: number,
  ) {}
  area(): number { return Math.PI * this.semiMajor * this.semiMinor; }
}

// This function works with ANY shape, present or future
function totalArea(shapes: readonly Shape[]): number {
  return shapes.reduce((sum, shape) => sum + shape.area(), 0);
}
```

### GOOD: Strategy pattern for payment processing

```typescript
// --- Payment processing: open for extension ---

interface PaymentProcessor {
  readonly methodId: string;
  process(payment: Payment): Promise<ProcessingResult>;
  validate(payment: Payment): ValidationResult;
}

class CreditCardProcessor implements PaymentProcessor {
  readonly methodId = "credit_card";

  async process(payment: Payment): Promise<ProcessingResult> {
    // Credit card-specific processing
    return { success: true, transactionId: "cc_123" };
  }

  validate(payment: Payment): ValidationResult {
    if (!payment.cardNumber) return { valid: false, error: "Card number required" };
    return { valid: true };
  }
}

class PayPalProcessor implements PaymentProcessor {
  readonly methodId = "paypal";

  async process(payment: Payment): Promise<ProcessingResult> {
    return { success: true, transactionId: "pp_456" };
  }

  validate(payment: Payment): ValidationResult {
    if (!payment.email) return { valid: false, error: "PayPal email required" };
    return { valid: true };
  }
}

// Registry: adding a new processor = registering it, not modifying existing code
class PaymentService {
  private processors: Map<string, PaymentProcessor> = new Map();

  register(processor: PaymentProcessor): void {
    this.processors.set(processor.methodId, processor);
  }

  async processPayment(payment: Payment): Promise<ProcessingResult> {
    const processor = this.processors.get(payment.method);
    if (!processor) {
      throw new UnsupportedPaymentMethodError(payment.method);
    }

    const validation = processor.validate(payment);
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }

    return processor.process(payment);
  }
}

// Adding Apple Pay: write ApplePayProcessor, register it. Done.
// No existing code was modified. No existing tests were affected.
```

### BAD: Over-applying OCP -- abstractions for things that won't change

```typescript
// "What if we need to change how we format dates someday?"
interface DateFormatter {
  format(date: Date): string;
}

class IsoDateFormatter implements DateFormatter {
  format(date: Date): string { return date.toISOString(); }
}

class DateFormatterFactory {
  create(type: string): DateFormatter {
    switch (type) {
      case "iso": return new IsoDateFormatter();
      default: throw new Error("Unknown");
    }
  }
}

// Three classes, one factory, for something that will never change.
// Just use date.toISOString() directly.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Monkey Patching** | Modifying existing code at runtime (common in Ruby, Python, JavaScript). Achieves "extension" but violates "closed for modification" because the original behavior is altered. Fragile and hard to debug. |
| **Aspect Weaving** | AOP tools inject behavior into existing code without modifying it directly. Cross-cutting concerns (logging, transactions) are "woven" in at compile or load time. Achieves OCP for cross-cutting concerns. |
| **Extension Methods** | C#/Kotlin feature that adds methods to existing types without modifying them. Achieves syntactic extension without modification, though the original class's internals remain inaccessible. |
| **Decorator Pattern** | Wraps an existing object to add behavior without modifying the original. A pure OCP technique: the original class is untouched, and new behavior is layered on. |
| **Plugin Architecture** | An architectural pattern where the core system defines extension points and plugins provide implementations. OCP at the system level. |

---

## When NOT to Apply

- **When the variations are known and stable.** If your system handles exactly three payment methods and will never handle more, a simple `switch` statement is clearer than a strategy pattern.
- **When you can't predict the extension points.** OCP requires you to identify *where* extension will happen. If you guess wrong, you've added abstraction in the wrong place and the real extension still requires modification.
- **For internal/private code.** OCP is most valuable for code with many consumers (libraries, frameworks, shared modules). Internal code that has one caller can be modified freely.
- **During initial development.** The first implementation should be simple. Refactor toward OCP when you see the second variation arriving.

---

## Tensions & Trade-offs

- **OCP vs. KISS**: OCP introduces interfaces, registries, and indirection. For simple cases, this complexity isn't justified. Apply OCP when the cost of modifying existing code (risk, coordination, testing) exceeds the cost of the abstraction.
- **OCP vs. YAGNI**: OCP wants extension points. YAGNI says don't build them until needed. Resolution: build the extension point when you add the second implementation. The first case is just direct code.
- **OCP vs. Readability**: Following an polymorphic dispatch through an interface to find the actual implementation is harder than reading a `switch` statement. The payoff comes when there are many implementations or they change frequently.
- **OCP vs. Debuggability**: Debugging through abstract interfaces and registries is harder than debugging concrete `switch` statements. Stack traces show the interface, not the implementation.

---

## Real-World Consequences

An e-commerce platform's discount calculation was a single 800-line function with nested `if/else` chains for every discount type: percentage off, buy-one-get-one, loyalty points, coupon codes, seasonal sales, employee discounts, and bundle deals. Adding a new discount type required modifying this function, which was touched by every developer on the team. Merge conflicts were daily occurrences. After a particularly nasty incident where a Black Friday sale modification accidentally disabled the loyalty points discount (losing the company significant customer goodwill), the team refactored to a `DiscountStrategy` interface with a registry. New discount types became new classes -- deployed independently, tested independently, and completely isolated from existing discounts.

---

## Key Quotes

> "Software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification."
> -- Bertrand Meyer

> "When a single change to a program results in a cascade of changes to dependent modules, the design smells of rigidity."
> -- Robert C. Martin

> "OCP is the heart of OO design. Conformance to this principle yields the greatest benefits of OO: flexibility, reusability, and maintainability."
> -- Robert C. Martin

---

## Further Reading

- *Object-Oriented Software Construction* -- Bertrand Meyer (1988, 2nd Edition 1997)
- *Agile Software Development: Principles, Patterns, and Practices* -- Robert C. Martin (2003)
- *Design Patterns* -- Gamma, Helm, Johnson, Vlissides (1994), especially Strategy and Decorator patterns
- *Head First Design Patterns* -- Freeman & Robson (2004)
- ["The Open-Closed Principle"](https://blog.cleancoder.com/uncle-bob/2014/05/12/TheOpenClosedPrinciple.html) -- Robert C. Martin
