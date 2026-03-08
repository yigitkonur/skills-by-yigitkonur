# Higher-Order Functions

**Functions that take functions as arguments or return functions as results, enabling powerful abstractions over behavior.**

---

## Origin / History

Higher-order functions are a direct inheritance from lambda calculus (Alonzo Church, 1930s), where functions are the only primitive and naturally accept other functions. Lisp (1958) was the first mainstream language to treat functions as first-class values. The concept was refined through ML (1973) and Haskell (1990), which added sophisticated type systems for reasoning about function types. In JavaScript, higher-order functions have been available since the language's creation (1995) — `Array.prototype.sort` takes a comparator function — but their idiomatic use exploded with ES5's `map`, `filter`, and `reduce` (2009) and ES6's arrow functions (2015).

Partial application and currying trace back to Moses Schonfinkel (1924) and Haskell Curry (1958). These techniques transform multi-argument functions into chains of single-argument functions, enabling reuse and composition.

---

## The Problem It Solves

Without higher-order functions, common patterns must be duplicated. Filtering an array of users by age, filtering orders by status, and filtering products by price all share the same structure — iterate, test a condition, collect results — yet without abstraction, you write three separate loops. Higher-order functions capture the pattern (filtering) and parameterize the variation (the predicate).

More broadly, higher-order functions solve the problem of behavioral abstraction. When you need to vary what happens at a specific point in an algorithm, you have two choices: inheritance (template method pattern) or higher-order functions. The functional approach is lighter weight, more composable, and does not require class hierarchies.

---

## The Principle Explained

A higher-order function is any function that does at least one of: (1) takes one or more functions as arguments, or (2) returns a function as its result. `map`, `filter`, and `reduce` are the canonical examples of the first kind. Factory functions and decorators are examples of the second kind.

Partial application is the technique of fixing some arguments of a function, producing a new function that takes the remaining arguments. Currying is the specific case where a function of N arguments is transformed into N functions of one argument each. These techniques enable point-free style — defining functions without explicitly mentioning their arguments — which can make data pipelines more readable (or less, if overused).

The power of higher-order functions lies in composition. Small, focused functions can be combined into complex behaviors without creating intermediate variables or deep nesting. A pipeline like `users.filter(isActive).map(toDisplayName).sort(byLastName)` reads as a clear sequence of transformations, each step reusable independently.

---

## Code Examples

### BAD: Duplicated iteration logic with no abstraction

```typescript
interface User {
  name: string;
  age: number;
  active: boolean;
}

// Three functions with identical structure, differing only in the condition
function getActiveUsers(users: User[]): User[] {
  const result: User[] = [];
  for (const user of users) {
    if (user.active) result.push(user);
  }
  return result;
}

function getAdultUsers(users: User[]): User[] {
  const result: User[] = [];
  for (const user of users) {
    if (user.age >= 18) result.push(user);
  }
  return result;
}

function getUserNames(users: User[]): string[] {
  const result: string[] = [];
  for (const user of users) {
    result.push(user.name);
  }
  return result;
}

// Every new requirement means another copy-paste loop
```

### GOOD: Higher-order functions abstracting the pattern

```typescript
interface User {
  readonly name: string;
  readonly age: number;
  readonly active: boolean;
}

// Reusable predicates — small, testable, composable
const isActive = (user: User): boolean => user.active;
const isAdult = (user: User): boolean => user.age >= 18;
const toName = (user: User): string => user.name;

// Usage: compose behaviors without writing loops
const activeAdultNames = (users: readonly User[]): string[] =>
  users.filter(isActive).filter(isAdult).map(toName);

// Combine predicates with a higher-order function
function and<T>(...predicates: Array<(x: T) => boolean>): (x: T) => boolean {
  return (x: T) => predicates.every((pred) => pred(x));
}

const isActiveAdult = and(isActive, isAdult);
const optimizedNames = (users: readonly User[]): string[] =>
  users.filter(isActiveAdult).map(toName);
```

### Partial application and currying

```typescript
// Curried function: each argument returns a new function
function filterByField<T>(field: keyof T) {
  return function (value: T[keyof T]) {
    return function (items: readonly T[]): T[] {
      return items.filter((item) => item[field] === value);
    };
  };
}

const filterByStatus = filterByField<User>("active");
const getActiveUsers = filterByStatus(true);
// getActiveUsers is now a reusable function: User[] -> User[]

// Generic partial application utility
function partial<A, B extends unknown[], R>(
  fn: (first: A, ...rest: B) => R,
  firstArg: A,
): (...rest: B) => R {
  return (...rest: B) => fn(firstArg, ...rest);
}

function multiply(a: number, b: number): number {
  return a * b;
}

const double = partial(multiply, 2);
const triple = partial(multiply, 3);
console.log(double(5));  // 10
console.log(triple(5));  // 15
```

### Functions returning functions (decorators / wrappers)

```typescript
// Retry decorator — higher-order function returning an enhanced function
function withRetry<A extends unknown[], R>(
  fn: (...args: A) => Promise<R>,
  maxRetries: number,
  delayMs: number,
): (...args: A) => Promise<R> {
  return async (...args: A): Promise<R> => {
    let lastError: unknown;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn(...args);
      } catch (error) {
        lastError = error;
        if (attempt < maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
      }
    }
    throw lastError;
  };
}

// Usage: wrap any async function with retry behavior
const fetchUserData = async (id: string): Promise<User> => {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
};

const resilientFetch = withRetry(fetchUserData, 3, 1000);
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Imperative loops with mutation** | Explicit control flow. More familiar to beginners, but duplicates iteration patterns across the codebase. |
| **Method chaining (fluent interfaces)** | Similar readability to HOF pipelines, but requires builder objects. Less composable — the chain is tied to the object. |
| **Template Method (OOP pattern)** | Uses inheritance to parameterize behavior. Heavier than passing a function. Creates coupling to a base class. |
| **Strategy pattern (OOP)** | Encapsulates behavior variation in objects. More ceremony than HOFs, but provides named, discoverable strategies. |
| **Visitor pattern** | Double-dispatch to vary behavior over a type hierarchy. Complex, but solves problems HOFs alone cannot. |

---

## When NOT to Apply

- **Point-free obscurity**: `compose(map(prop("name")), filter(propEq("active", true)))` is elegant to FP veterans but opaque to most teams. If the point-free version is harder to read than the explicit version, use the explicit version.
- **Deeply nested callbacks**: Higher-order functions that take functions that take functions create "callback pyramid" shapes. Flatten with named functions or async/await.
- **Performance-sensitive hot loops**: `Array.prototype.map` creates a new array and a closure per call. In tight loops over millions of elements, a `for` loop with mutation is faster. Measure first.
- **When a simple `if` statement suffices**: Do not abstract a single conditional into a predicate factory. The abstraction costs more than the duplication saves.

---

## Tensions & Trade-offs

- **Abstraction vs. Readability**: Higher-order functions compress code, but overly abstract pipelines require the reader to hold multiple function signatures in their head simultaneously.
- **Reusability vs. Indirection**: A curried utility function is reusable, but every caller must trace through the indirection to understand what it does.
- **Type inference vs. Explicit types**: TypeScript can infer HOF types well, but complex generic HOFs sometimes produce inscrutable error messages.
- **Debugging**: Stack traces through anonymous arrow functions show `anonymous` or `<lambda>`. Use named function expressions for debuggability.

---

## Real-World Consequences

**Express middleware stack**: Express.js is fundamentally a higher-order function pattern. Each middleware is a function `(req, res, next) => void`, and the framework composes them into a pipeline. This design enabled an enormous ecosystem of reusable middleware — auth, logging, CORS, compression — all without inheritance.

**React hooks as higher-order composition**: Custom hooks like `useDebounce`, `useLocalStorage`, and `useAuth` are higher-order patterns that compose behavior into components without wrapper hierarchies. They replaced higher-order components (HOCs), which were themselves a higher-order function pattern that became unwieldy.

**Lodash and Ramda adoption**: These utility libraries are essentially catalogs of higher-order functions. Teams that adopted them reported significant reductions in hand-written loop code — but also reported onboarding difficulty when new developers were unfamiliar with `_.flow`, `_.partial`, or `R.pipe`.

---

## Further Reading

- [MDN — Array.prototype.map / filter / reduce](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)
- [Mostly Adequate Guide — Chapter 4: Currying](https://github.com/MostlyAdequate/mostly-adequate-guide/blob/master/ch04.md)
- [Eric Elliott — Composing Software (Leanpub, 2018)](https://leanpub.com/composingsoftware)
- [Ramda Documentation — Practical Functional JavaScript](https://ramdajs.com/)
- [Kyle Simpson — Functional-Light JavaScript (Manning, 2017)](https://github.com/getify/Functional-Light-JS)
