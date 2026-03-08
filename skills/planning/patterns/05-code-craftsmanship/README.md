# 05 - Code Craftsmanship

Principles and practices for writing code that is clean, readable, maintainable, and resilient. These patterns focus on the micro-level decisions -- naming, function design, error handling, data management -- that determine whether a codebase is a pleasure or a burden to work with.

---

## Principles Index

| # | Principle | File | Core Idea |
|---|---|---|---|
| 1 | Clean Code Principles | [clean-code-principles.md](./clean-code-principles.md) | Meaningful names, small functions, no side effects, command-query separation |
| 2 | Deep Modules | [deep-modules.md](./deep-modules.md) | Simple interfaces hiding complex implementations; information hiding |
| 3 | Refactoring and Code Smells | [refactoring-and-code-smells.md](./refactoring-and-code-smells.md) | Recognizing structural problems and safely transforming code |
| 4 | Naming Conventions | [naming-conventions.md](./naming-conventions.md) | Intention-revealing names that eliminate the need for comments |
| 5 | Error Handling Philosophy | [error-handling-philosophy.md](./error-handling-philosophy.md) | Exceptions vs Result types vs error codes; making failure explicit |
| 6 | Immutability and Side Effects | [immutability-and-side-effects.md](./immutability-and-side-effects.md) | Pure functions, immutable data, and side effect isolation |

---

## How These Principles Relate

These six principles form a coherent philosophy of code quality:

- **Clean Code** provides the overarching discipline: care about readability, keep things small, be honest in your interfaces.
- **Deep Modules** refines the abstraction question: "small" means small interface, not necessarily small implementation.
- **Naming** is the first and most impactful clean code practice -- get names right and much of the rest follows.
- **Refactoring** provides the techniques for improving code that has drifted from these principles.
- **Error Handling** addresses the most commonly botched aspect of code design, where clarity matters most.
- **Immutability** provides the ultimate discipline for predictable code: if nothing changes, nothing can go wrong.

---

## Recommended Reading Order

1. Start with **Clean Code Principles** for the foundation
2. Read **Naming Conventions** next -- naming is the first skill to improve
3. Study **Deep Modules** to refine your sense of abstraction boundaries
4. Learn **Error Handling Philosophy** to handle the hard parts correctly
5. Embrace **Immutability and Side Effects** for robustness
6. Use **Refactoring and Code Smells** as an ongoing reference when improving existing code
