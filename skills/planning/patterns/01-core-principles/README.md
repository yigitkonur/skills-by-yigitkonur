# 01 -- Core Principles

Foundational software design principles that transcend any specific paradigm, language, or architecture. These principles form the bedrock upon which all other patterns and practices are built.

---

## Principles Index

| # | Principle | One-Liner | File |
|---|-----------|-----------|------|
| 1 | [DRY](./DRY.md) | Every piece of knowledge must have a single, authoritative representation. | `DRY.md` |
| 2 | [YAGNI](./YAGNI.md) | Don't build it until you have a concrete, immediate need for it. | `YAGNI.md` |
| 3 | [KISS](./KISS.md) | Prefer the simplest solution that adequately solves the problem. | `KISS.md` |
| 4 | [Separation of Concerns](./separation-of-concerns.md) | Divide a program into distinct sections, each addressing a separate concern. | `separation-of-concerns.md` |
| 5 | [Command-Query Separation](./command-query-separation.md) | Methods should either change state or return data, never both. | `command-query-separation.md` |
| 6 | [Composition Over Inheritance](./composition-over-inheritance.md) | Assemble behavior from small components rather than deep class hierarchies. | `composition-over-inheritance.md` |
| 7 | [Encapsulation](./encapsulation.md) | Hide implementation details; expose only a stable public interface. | `encapsulation.md` |

---

## How These Principles Interrelate

These seven principles are not independent axioms -- they form a web of reinforcing (and sometimes conflicting) ideas.

**Reinforcing relationships:**

- **DRY + Separation of Concerns**: SoC helps you identify *where* knowledge belongs. DRY ensures each piece of knowledge lives in only one place.
- **KISS + YAGNI**: Both push toward simplicity but from different angles. KISS says "don't overcomplicate the solution." YAGNI says "don't solve problems that don't exist yet."
- **Encapsulation + CQS**: CQS makes encapsulation more effective by ensuring queries don't secretly mutate state. If your object follows CQS, callers can trust that reads are safe.
- **Composition + Encapsulation**: Composition works best when components are well-encapsulated. Each component hides its internals and exposes a clean interface for others to compose with.

**Tension relationships:**

- **DRY vs. KISS**: Eliminating duplication often means adding abstractions, which adds complexity. The resolution: only DRY out duplication that represents the same knowledge and causes real maintenance pain.
- **DRY vs. YAGNI**: DRY can push you to create abstractions before you fully understand the pattern. YAGNI says wait. The Rule of Three mediates: tolerate duplication until you've seen it three times.
- **Encapsulation vs. KISS**: Heavy encapsulation (private fields, accessor methods, invariant checks) adds code. For simple data types, it's overkill. Match the level of encapsulation to the complexity of the invariants.

---

## Decision Framework

When principles conflict (and they will), use this priority guide:

1. **Correctness first** -- If encapsulation is needed to protect critical invariants (security, money, data integrity), it trumps KISS and YAGNI.
2. **Simplicity second** -- If the codebase is understandable and working, don't add abstractions just to satisfy DRY or SoC.
3. **Maintainability third** -- If duplication is causing actual bugs or slow changes, DRY and SoC earn their keep.
4. **Flexibility last** -- Don't build for imaginary future requirements. Let structure emerge from real needs.

---

## Next Section

Continue to [02 -- SOLID Principles](../02-solid/README.md) for the five principles of object-oriented class design.
