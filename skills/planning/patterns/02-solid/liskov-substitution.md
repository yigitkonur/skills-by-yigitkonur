# Liskov Substitution Principle (LSP)

**Objects of a supertype should be replaceable with objects of a subtype without altering the correctness of the program.**

---

## Origin

Formulated by **Barbara Liskov** in her 1987 keynote address "Data Abstraction and Hierarchy" and formally defined with **Jeannette Wing** in the 1994 paper "A Behavioral Notion of Subtyping." Liskov received the Turing Award in 2008, with LSP cited as one of her major contributions. The formal definition: if S is a subtype of T, then objects of type T may be replaced with objects of type S without altering any desirable property of the program (correctness, task performed, etc.).

---

## The Problem It Solves

When subtypes don't honor the contract of their parent type, polymorphism becomes a minefield. Code that works with the parent type silently breaks when handed a subtype. The classic example: a `Square` subclass of `Rectangle`. Code that sets width and height independently -- perfectly valid for rectangles -- produces wrong results for squares, because setting width implicitly changes height. The program is *technically* running but *semantically* broken, and the bug only manifests with certain subtype combinations, making it intermittent and hard to diagnose.

---

## The Principle Explained

LSP defines what it means for a subtype to be a *behavioral* subtype. It's not enough for `S` to have all the methods of `T` (structural compatibility). `S` must also satisfy all the behavioral expectations that callers of `T` rely on. These expectations include:

- **Preconditions cannot be strengthened.** If the parent accepts any positive number, the subtype can't require only even numbers.
- **Postconditions cannot be weakened.** If the parent guarantees a sorted result, the subtype must also return a sorted result.
- **Invariants must be preserved.** If the parent guarantees that balance is never negative, the subtype must maintain that guarantee.
- **History constraint.** The subtype should not introduce state changes that the parent type would not allow.

In practical terms: if you have a function that accepts `Animal`, it should work correctly whether it receives a `Dog`, a `Cat`, or a `Parrot`. If it works for `Animal` but breaks for `Parrot` because parrots throw `UnsupportedOperationException` on `swim()`, that's an LSP violation. The subtype is *lying* about its capabilities.

LSP is the principle that makes polymorphism safe. Without it, you can't trust abstract types. Every function that accepts a base type would need to check `instanceof` for every subtype -- defeating the entire purpose of polymorphism. LSP says: if you claim to be a `T`, you must behave like a `T`.

---

## Code Examples

### BAD: Classic Rectangle-Square violation

```typescript
class Rectangle {
  constructor(
    protected width: number,
    protected height: number,
  ) {}

  setWidth(w: number): void { this.width = w; }
  setHeight(h: number): void { this.height = h; }
  getArea(): number { return this.width * this.height; }
}

class Square extends Rectangle {
  constructor(side: number) {
    super(side, side);
  }

  // Violates LSP: strengthens implicit postcondition
  // Callers of Rectangle expect setWidth to ONLY change width
  setWidth(w: number): void {
    this.width = w;
    this.height = w; // Surprise! Also changes height
  }

  setHeight(h: number): void {
    this.width = h; // Surprise! Also changes width
    this.height = h;
  }
}

// This function works correctly for Rectangle but BREAKS for Square
function doubleWidth(rect: Rectangle): void {
  const originalHeight = rect.getArea() / rect.getArea(); // save state
  rect.setWidth(rect.getArea() / 10 * 2); // Simplified: just set width
  // For a Square, this also changed the height, violating the caller's expectation
}

// Concrete example of the breakage:
function testRectangle(rect: Rectangle): void {
  rect.setWidth(5);
  rect.setHeight(4);
  // Caller expects: area = 5 * 4 = 20
  console.assert(rect.getArea() === 20, `Expected 20, got ${rect.getArea()}`);
  // With a Square: setHeight(4) also sets width to 4, so area = 4 * 4 = 16. FAILS.
}
```

### GOOD: Proper modeling without LSP violation

```typescript
// Option 1: Separate types (no inheritance relationship)
interface Shape {
  area(): number;
}

class Rectangle implements Shape {
  constructor(
    private readonly width: number,
    private readonly height: number,
  ) {}

  area(): number { return this.width * this.height; }

  withWidth(w: number): Rectangle { return new Rectangle(w, this.height); }
  withHeight(h: number): Rectangle { return new Rectangle(this.width, h); }
}

class Square implements Shape {
  constructor(private readonly side: number) {}

  area(): number { return this.side ** 2; }

  withSide(s: number): Square { return new Square(s); }
}

// Both implement Shape. Code that needs area() works with both.
// No false inheritance relationship. No behavioral surprises.
```

### BAD: Subtype that throws on inherited methods

```typescript
interface Bird {
  fly(): void;
  eat(): void;
  sleep(): void;
}

class Sparrow implements Bird {
  fly(): void { /* flaps wings */ }
  eat(): void { /* pecks seeds */ }
  sleep(): void { /* perches and sleeps */ }
}

class Penguin implements Bird {
  fly(): void {
    // LSP violation: this breaks the Bird contract
    throw new Error("Penguins can't fly!");
  }
  eat(): void { /* catches fish */ }
  sleep(): void { /* huddles and sleeps */ }
}

// Any function that iterates birds and calls fly() will crash on Penguin
function migrateFlock(birds: Bird[]): void {
  for (const bird of birds) {
    bird.fly(); // Throws for Penguin -- runtime error, no compile-time warning
  }
}
```

### GOOD: Model capabilities accurately

```typescript
interface Animal {
  eat(): void;
  sleep(): void;
}

interface Flyable {
  fly(): void;
}

interface Swimmable {
  swim(): void;
}

class Sparrow implements Animal, Flyable {
  eat(): void { /* pecks seeds */ }
  sleep(): void { /* perches */ }
  fly(): void { /* flaps wings */ }
}

class Penguin implements Animal, Swimmable {
  eat(): void { /* catches fish */ }
  sleep(): void { /* huddles */ }
  swim(): void { /* torpedo mode */ }
}

// Functions declare exactly what capabilities they need
function migrateFlyingAnimals(flyers: Flyable[]): void {
  for (const flyer of flyers) {
    flyer.fly(); // Type system guarantees this works
  }
}
// Penguin can't be passed to this function -- the type system prevents the bug.
```

### BAD: Violating postconditions in a subtype

```typescript
interface Collection<T> {
  add(item: T): void;
  getAll(): T[]; // Contract: returns items in insertion order
}

class ArrayList<T> implements Collection<T> {
  private items: T[] = [];
  add(item: T): void { this.items.push(item); }
  getAll(): T[] { return [...this.items]; } // Insertion order -- correct
}

class SortedList<T> implements Collection<T> {
  private items: T[] = [];
  add(item: T): void {
    this.items.push(item);
    this.items.sort(); // LSP violation: getAll() no longer returns insertion order
  }
  getAll(): T[] { return [...this.items]; } // Sorted order, NOT insertion order
}

// Code expecting insertion order breaks silently with SortedList
```

### GOOD: Distinct interfaces for distinct contracts

```typescript
interface Collection<T> {
  add(item: T): void;
  getAll(): T[];
  readonly size: number;
}

interface OrderedCollection<T> extends Collection<T> {
  // Contract explicitly states: getAll() returns insertion order
  getAll(): T[];
}

interface SortedCollection<T> extends Collection<T> {
  // Contract explicitly states: getAll() returns sorted order
  getAll(): T[];
}

// Functions that need insertion order use OrderedCollection
// Functions that need sorted order use SortedCollection
// No LSP violation because the contracts are explicit
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Structural Typing (Duck Typing)** | TypeScript and Go use structural typing: if it has the right shape, it's compatible. This handles the *structural* aspect of substitutability but not the *behavioral* aspect. A `Penguin` structurally matches `Bird` even if it throws on `fly()`. |
| **Duck Typing** | "If it quacks like a duck..." Dynamic languages rely on runtime behavior rather than declared types. LSP violations manifest as runtime errors rather than type errors. |
| **Protocol Conformance** | Swift's approach. Types explicitly declare which protocols they conform to, and the compiler enforces structural compatibility. Behavioral conformance is still the programmer's responsibility. |
| **Design by Contract** | Bertrand Meyer's formal approach. Preconditions, postconditions, and invariants are explicitly declared and checked. The most rigorous way to enforce LSP. |
| **Covariance/Contravariance** | Type theory rules that formalize LSP for generic types. Return types should be covariant (more specific in subtypes), parameter types should be contravariant (more general in subtypes). |

---

## When NOT to Apply

- **When inheritance isn't used.** LSP is about subtype relationships. In a purely functional codebase or one using only composition, LSP doesn't directly apply (though the behavioral principle -- "don't lie about capabilities" -- is universal).
- **When the violating behavior is documented and expected.** `ReadonlyArray` in TypeScript "violates" the full `Array` contract by removing mutation methods. But this is explicit, compile-time enforced, and expected. The contract is intentionally narrower.
- **When modeling real-world hierarchies that don't map to behavioral hierarchies.** "A square IS a rectangle" is true in geometry but false in OOP (because mutability breaks the relationship). Don't force real-world taxonomies into inheritance hierarchies.

---

## Tensions & Trade-offs

- **LSP vs. Code Reuse**: Sometimes you want to reuse 90% of a parent class's behavior but override 10% in ways that technically violate LSP. The temptation is strong. The solution is usually composition instead of inheritance.
- **LSP vs. Practical APIs**: Some widely-used APIs violate LSP (Java's `UnsupportedOperationException`, `ReadonlyArray`). These violations are considered acceptable when they're well-documented and caught by the type system.
- **LSP vs. Real-World Modeling**: Real-world "is-a" relationships don't always map to behavioral subtypes. A penguin IS a bird, but `Penguin extends Bird` may violate LSP. OOP inheritance models *behavioral substitutability*, not taxonomic classification.

---

## Real-World Consequences

A logistics company's routing system used a `Vehicle` base class with a `loadCargo(weight: number)` method. `Truck extends Vehicle` worked fine. Then someone added `Bicycle extends Vehicle` for last-mile deliveries. `Bicycle.loadCargo()` silently capped weight at 20kg -- but the routing algorithm didn't know this, because the `Vehicle` interface promised it could handle the assigned weight. Bicycles were assigned 500kg cargo routes. Deliveries failed. The fix required a two-week refactoring: splitting `Vehicle` into `MotorVehicle` and `HumanPowered`, with explicit capacity interfaces. Had LSP been considered when `Bicycle` was added, the team would have designed the interface properly from the start.

---

## Key Quotes

> "What is wanted here is something like the following substitution property: If for each object o1 of type S there is an object o2 of type T such that for all programs P defined in terms of T, the behavior of P is unchanged when o1 is substituted for o2, then S is a subtype of T."
> -- Barbara Liskov

> "Subtypes must be substitutable for their base types."
> -- Robert C. Martin (simplified version)

> "Inheritance is not about sharing code. It's about sharing interface contracts."
> -- Sandi Metz (paraphrased)

---

## Further Reading

- ["Data Abstraction and Hierarchy"](https://dl.acm.org/doi/10.1145/62139.62141) -- Barbara Liskov (1987)
- ["A Behavioral Notion of Subtyping"](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf) -- Barbara Liskov & Jeannette Wing (1994)
- *Agile Software Development: Principles, Patterns, and Practices* -- Robert C. Martin (2003)
- *Effective Java* (3rd Edition) -- Joshua Bloch (2018), Item 10-11 on `equals` contract
- *Object-Oriented Software Construction* -- Bertrand Meyer (1997), Design by Contract chapters
