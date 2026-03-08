# Single Responsibility Principle (SRP)

**A class should have one, and only one, reason to change.**

---

## Origin

Formulated by **Robert C. Martin** (Uncle Bob) in his 2003 book *Agile Software Development: Principles, Patterns, and Practices*. Martin later refined the definition: a module should be responsible to one, and only one, actor (stakeholder or user group). The earlier formulation ("one reason to change") was widely misinterpreted as "do one thing," so Martin clarified that it's about *who* requests changes, not about the number of methods or lines of code.

---

## The Problem It Solves

When a class serves multiple stakeholders, changes requested by one stakeholder can break functionality relied upon by another. An `Employee` class that handles payroll calculations, generates HR reports, AND saves to the database serves three different departments. When the CFO requests a change to overtime calculations, you risk breaking the HR report format or the database persistence. The class becomes a coordination bottleneck -- every team's changes collide in the same file, merge conflicts multiply, and no one fully understands all the class's responsibilities.

---

## The Principle Explained

SRP is about **cohesion at the stakeholder level**. A class is not violating SRP because it has many methods. It's violating SRP when changes driven by different stakeholders (or different axes of change) converge on the same class. The CFO wants different payroll rules. The CTO wants a different database. The COO wants a different report format. If all three changes require modifying the same class, that class has too many responsibilities.

The practical test is simple: identify who would request changes to this class. If the answer is more than one person (or team, or department), the class probably needs to be split. Each resulting class is responsible to a single actor and can change freely without affecting others.

A common mistake is taking SRP to an extreme, creating classes with a single method each. This scatters related logic across dozens of files and makes the system harder to understand. SRP is not about granularity -- it's about *axes of change*. If three methods always change together for the same reason, they belong in the same class, even if they "do different things" at a surface level.

---

## Code Examples

### BAD: Multiple responsibilities in one class

```typescript
class Employee {
  constructor(
    private id: string,
    private name: string,
    private hourlyRate: number,
    private hoursWorked: number,
  ) {}

  // Responsibility 1: Payroll calculation (changes when CFO changes pay rules)
  calculatePay(): number {
    const basePay = this.hourlyRate * this.hoursWorked;
    const overtime = this.hoursWorked > 40
      ? (this.hoursWorked - 40) * this.hourlyRate * 1.5
      : 0;
    return basePay + overtime;
  }

  // Responsibility 2: Report generation (changes when COO changes report format)
  generateReport(): string {
    return [
      `Employee Report: ${this.name}`,
      `ID: ${this.id}`,
      `Hours: ${this.hoursWorked}`,
      `Pay: $${this.calculatePay().toFixed(2)}`,
      // BUG RISK: calculatePay() is shared between payroll and reports.
      // If the CFO changes the pay formula, reports change too --
      // even if the COO wanted the old formula in reports.
    ].join("\n");
  }

  // Responsibility 3: Persistence (changes when DBA changes schema)
  async save(db: Database): Promise<void> {
    await db.query(
      `INSERT INTO employees (id, name, hourly_rate, hours_worked)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (id) DO UPDATE SET name=$2, hourly_rate=$3, hours_worked=$4`,
      [this.id, this.name, this.hourlyRate, this.hoursWorked],
    );
  }
}
```

### GOOD: Separated by stakeholder/axis of change

```typescript
// --- employee.ts --- (Domain entity: stable core data)
class Employee {
  constructor(
    readonly id: string,
    readonly name: string,
    readonly hourlyRate: number,
    readonly hoursWorked: number,
  ) {}
}

// --- payroll-calculator.ts --- (Changes when: CFO changes pay rules)
class PayrollCalculator {
  private static readonly OVERTIME_THRESHOLD = 40;
  private static readonly OVERTIME_MULTIPLIER = 1.5;

  calculate(employee: Employee): PayStatement {
    const regularHours = Math.min(employee.hoursWorked, PayrollCalculator.OVERTIME_THRESHOLD);
    const overtimeHours = Math.max(0, employee.hoursWorked - PayrollCalculator.OVERTIME_THRESHOLD);

    const regularPay = regularHours * employee.hourlyRate;
    const overtimePay = overtimeHours * employee.hourlyRate * PayrollCalculator.OVERTIME_MULTIPLIER;

    return {
      employeeId: employee.id,
      regularPay,
      overtimePay,
      totalPay: regularPay + overtimePay,
    };
  }
}

// --- employee-report-generator.ts --- (Changes when: COO changes report format)
class EmployeeReportGenerator {
  generate(employee: Employee, payStatement: PayStatement): string {
    return [
      `Employee Report: ${employee.name}`,
      `ID: ${employee.id}`,
      `Hours Worked: ${employee.hoursWorked}`,
      `Regular Pay: $${payStatement.regularPay.toFixed(2)}`,
      `Overtime Pay: $${payStatement.overtimePay.toFixed(2)}`,
      `Total Pay: $${payStatement.totalPay.toFixed(2)}`,
    ].join("\n");
  }
}

// --- employee-repository.ts --- (Changes when: DBA changes schema/database)
class EmployeeRepository {
  constructor(private readonly db: Database) {}

  async save(employee: Employee): Promise<void> {
    await this.db.query(
      `INSERT INTO employees (id, name, hourly_rate, hours_worked)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (id) DO UPDATE SET name=$2, hourly_rate=$3, hours_worked=$4`,
      [employee.id, employee.name, employee.hourlyRate, employee.hoursWorked],
    );
  }

  async findById(id: string): Promise<Employee | null> {
    const row = await this.db.query(`SELECT * FROM employees WHERE id = $1`, [id]);
    return row ? new Employee(row.id, row.name, row.hourly_rate, row.hours_worked) : null;
  }
}
```

### BAD: Over-application -- one method per class

```typescript
// SRP taken to absurd extreme
class EmployeeNameValidator { validate(name: string): boolean { return name.length > 0; } }
class EmployeeEmailValidator { validate(email: string): boolean { return email.includes("@"); } }
class EmployeeAgeValidator { validate(age: number): boolean { return age >= 18; } }
class EmployeePhoneValidator { validate(phone: string): boolean { return phone.length >= 10; } }
class EmployeeAddressValidator { validate(addr: string): boolean { return addr.length > 0; } }

// 5 files, 5 classes -- all change for the same reason (validation rules change)
// and are always used together. This isn't SRP; this is fragmentation.
```

### GOOD: Cohesive validation -- one reason to change

```typescript
// All validation rules change together (same stakeholder: product/ops team)
class EmployeeValidator {
  validate(input: CreateEmployeeInput): ValidationResult {
    const errors: string[] = [];

    if (!input.name || input.name.trim().length === 0) errors.push("Name is required");
    if (!input.email?.includes("@")) errors.push("Valid email is required");
    if (input.age < 18) errors.push("Must be at least 18");
    if (input.phone.length < 10) errors.push("Phone must be at least 10 digits");
    if (!input.address?.trim()) errors.push("Address is required");

    return errors.length === 0
      ? { valid: true }
      : { valid: false, errors };
  }
}
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Common Closure Principle (CCP)** | The package-level version of SRP. Classes that change together belong in the same package. SRP is about class cohesion; CCP is about package cohesion. |
| **Unix Philosophy** | "Do one thing and do it well." Similar spirit but applied to programs and tools rather than classes. `grep` searches, `sort` sorts, `wc` counts -- each does one thing excellently. |
| **Actor-Based Decomposition** | Martin's refined SRP: identify actors (stakeholders) and ensure each module is responsible to exactly one actor. This is more precise than "one reason to change." |
| **Cohesion Metrics** | LCOM (Lack of Cohesion of Methods) quantifies SRP violations. High LCOM means methods in a class don't use the same fields, suggesting the class has multiple responsibilities. |

---

## When NOT to Apply

- **When it leads to trivial classes.** A class with one method that delegates to another one-method class is just indirection, not separation of concerns.
- **Simple CRUD applications.** If the "payroll" is just reading and writing a field, separating it into its own class is ceremony without benefit.
- **Early in development.** When you don't yet know what the axes of change are, splitting prematurely leads to the wrong boundaries. Let the code tell you where the seams should be.
- **When the "actors" are the same person.** In a small startup, the CEO is the CFO, COO, and CTO. The axes of change that SRP protects against don't yet exist.

---

## Tensions & Trade-offs

- **SRP vs. Locality**: Splitting a class into three means understanding a feature requires reading three files. Navigation cost increases. The trade-off is worth it when the feature is complex and the axes of change are real, but not for simple features.
- **SRP vs. KISS**: SRP adds classes and files. KISS says fewer moving parts. Resolution: apply SRP when the cost of entangled changes (bugs, merge conflicts, coordination overhead) exceeds the cost of the additional structure.
- **SRP vs. Cohesion**: Over-applying SRP can reduce cohesion -- related methods end up in different classes. Remember: SRP is about axes of change, not about method count.
- **SRP vs. DRY**: Separating responsibilities sometimes means each resulting class needs its own copy of some shared logic. Be willing to accept a small amount of duplication to maintain clean boundaries.

---

## Real-World Consequences

A payments company had a single `Transaction` class responsible for: validating inputs, applying business rules, formatting for different payment networks (Visa, Mastercard, AMEX), persisting to the database, and sending webhooks. When Visa changed their API format, the developer modifying the Visa formatting code accidentally broke the Mastercard formatting path -- because they shared private helper methods. The bug made it to production and processed 2,000 Mastercard transactions with malformed data. Separating the formatting logic by payment network (each with its own class, its own tests, its own deployment) would have isolated the change completely.

---

## Key Quotes

> "A module should be responsible to one, and only one, actor."
> -- Robert C. Martin (refined definition)

> "Gather together the things that change for the same reasons. Separate things that change for different reasons."
> -- Robert C. Martin

> "The Single Responsibility Principle is about people."
> -- Robert C. Martin

> "Do one thing and do it well."
> -- Unix Philosophy (Doug McIlroy)

---

## Further Reading

- *Agile Software Development: Principles, Patterns, and Practices* -- Robert C. Martin (2003)
- *Clean Architecture* -- Robert C. Martin (2017), Chapter 7
- ["The Single Responsibility Principle"](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html) -- Robert C. Martin (2014 blog post)
- *The Art of Unix Programming* -- Eric S. Raymond (2003)
- *Structured Design* -- Edward Yourdon & Larry Constantine (1979) -- original cohesion/coupling concepts
