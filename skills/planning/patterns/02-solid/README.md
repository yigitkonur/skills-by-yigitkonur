# 02 -- SOLID Principles

The five principles of object-oriented class design, introduced by **Robert C. Martin** and given the SOLID acronym by **Michael Feathers**. These principles guide the design of classes and modules to be maintainable, flexible, and robust.

---

## Principles Index

| # | Principle | Acronym | One-Liner | File |
|---|-----------|---------|-----------|------|
| 1 | [Single Responsibility](./single-responsibility.md) | **S**RP | A class should have one, and only one, reason to change. | `single-responsibility.md` |
| 2 | [Open-Closed](./open-closed.md) | **O**CP | Open for extension, closed for modification. | `open-closed.md` |
| 3 | [Liskov Substitution](./liskov-substitution.md) | **L**SP | Subtypes must be substitutable for their base types. | `liskov-substitution.md` |
| 4 | [Interface Segregation](./interface-segregation.md) | **I**SP | No client should depend on methods it does not use. | `interface-segregation.md` |
| 5 | [Dependency Inversion](./dependency-inversion.md) | **D**IP | Depend on abstractions, not concretions. | `dependency-inversion.md` |

---

## How the Five SOLID Principles Interrelate

SOLID is not five independent rules. The principles form a reinforcing system where each principle supports and enables the others. Understanding their relationships is as important as understanding each principle individually.

### SRP enables OCP

When a class has a single responsibility, it has a single axis of change. This makes it far easier to design extension points because you know *what kind* of extension the class will need. A class with multiple responsibilities would need extension mechanisms for each responsibility, leading to complex, tangled extension points.

### OCP depends on LSP

The Open-Closed Principle works through polymorphism: you extend behavior by providing new implementations of an interface. But this only works if those implementations are truly substitutable (LSP). If a new implementation violates the contract of the interface, the "closed" code that depends on that interface breaks -- defeating the purpose of OCP. LSP is what makes OCP safe.

### ISP supports SRP

Interface Segregation naturally produces single-responsibility interfaces. When you split a fat interface into role-specific interfaces, each resulting interface typically represents one coherent responsibility. ISP at the interface level reinforces SRP at the class level: classes that implement narrow interfaces tend to have focused responsibilities.

### DIP enables OCP

Dependency Inversion is the *mechanism* through which OCP is achieved. By depending on abstractions (interfaces) rather than concretions (implementations), high-level modules become open for extension: provide a new implementation of the interface, and the high-level module gains new behavior without modification.

### ISP enables DIP

Dependency Inversion works best with narrow, focused interfaces (ISP). If you invert a dependency onto a fat interface, the consumer still depends on more than it needs. ISP ensures that the abstractions used for DIP are minimal and client-specific, reducing coupling to its minimum.

### LSP constrains SRP

SRP tells you to give a class one reason to change. LSP tells you that if that class participates in a type hierarchy, its behavior must be consistent with the parent type's contract. A class can't have "its own" single responsibility if that responsibility conflicts with the behavioral contract it inherited.

---

## The SOLID Dependency Chain

```
ISP  -->  DIP  -->  OCP
 |                   ^
 v                   |
SRP  ------------>  LSP
```

Reading this diagram:
- **ISP** produces the narrow interfaces that **DIP** inverts onto.
- **DIP** provides the abstraction mechanism that makes **OCP** possible.
- **SRP** keeps classes focused, which makes **OCP** extension points clean.
- **LSP** ensures that substituting new implementations (for **OCP**) is safe.
- **ISP** and **SRP** reinforce each other: narrow interfaces promote single responsibilities.

---

## Common Misapplications

### Over-SOLID: The Astronaut Architecture

Applying all five principles at maximum intensity produces code where:
- Every class has exactly one method (over-applied SRP)
- Every method has a corresponding interface (over-applied DIP + ISP)
- Every class is designed for extension (over-applied OCP)
- Class hierarchies are fragmented into dozens of micro-interfaces (over-applied LSP + ISP)

The result: a 50-line feature spread across 30 files. No one can follow the flow. Testing is easy but understanding is impossible. The architecture serves the principles instead of serving the users.

### Under-SOLID: The Big Ball of Mud

Ignoring all five principles produces code where:
- God classes handle everything (no SRP)
- Adding features requires modifying core modules (no OCP)
- Subtypes throw `NotImplementedError` (no LSP)
- Every consumer depends on every method (no ISP)
- Business logic imports database drivers directly (no DIP)

The result: changes are terrifying. Tests don't exist because the code is untestable. New features introduce regressions. Developers work around the code instead of with it.

### The Sweet Spot

Apply SOLID principles at architectural boundaries -- where modules meet, where infrastructure connects to business logic, where independently deployable units interact. Inside a module, keep things simple. You don't need DIP between two functions in the same file. You don't need ISP for an interface used by one consumer. You don't need OCP for code that has never needed extension.

**Rule of thumb**: The further you are from the center of your architecture (the domain), the more SOLID matters. Infrastructure boundaries, public APIs, and shared libraries benefit most from rigorous SOLID application. Internal implementation details benefit most from simplicity.

---

## SOLID in Different Paradigms

SOLID was designed for object-oriented programming, but the underlying ideas transcend OOP:

| SOLID Principle | Functional Equivalent |
|----------------|----------------------|
| SRP | Small, focused functions and modules |
| OCP | Higher-order functions, function composition |
| LSP | Parametric polymorphism, consistent function contracts |
| ISP | Narrow function signatures, partial application |
| DIP | Functions as parameters (callbacks), effect systems |

---

## Previous Section

Return to [01 -- Core Principles](../01-core-principles/README.md) for the foundational principles that underpin SOLID.
