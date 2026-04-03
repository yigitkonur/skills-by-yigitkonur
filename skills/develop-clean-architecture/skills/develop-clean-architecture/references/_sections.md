# Sections

This file defines all sections, their ordering, impact levels, and descriptions.
The section ID (in parentheses) is the filename prefix used to group rules.

---

## 1. Dependency Direction (dep)

**Impact:** CRITICAL
**Description:** The Dependency Rule is the architectural foundation. Source code dependencies must point inward only; violations cascade failures across all layers. Includes the DRY-vs-duplication resolution: accept cross-layer duplication since each layer model serves a different master.

## 2. Entity Design (entity)

**Impact:** CRITICAL
**Description:** Enterprise business rules must be framework-agnostic, stable, and completely independent of databases, UI, and external systems. Includes DDD tactical patterns: aggregate roots, domain services, value objects, and the create/reconstitute factory distinction.

## 3. Use Case Isolation (usecase)

**Impact:** HIGH
**Description:** Application-specific business rules orchestrate entities without leaking infrastructure details or depending on presentation concerns.

## 4. Clean Code Fundamentals (code)

**Impact:** HIGH
**Description:** Code-level quality patterns from "Clean Code" — naming with ubiquitous language, function design, error handling (two-error-type model), comments, side-effect discipline, parse-don't-validate, objects vs data structures, flag arguments, composition over inheritance, and immutability. A well-architected system can still be unmaintainable without clean code.

## 5. Component Cohesion (comp)

**Impact:** HIGH
**Description:** Components grouped by business capability enable independent deployment, parallel team development, and controlled change propagation. Includes screaming architecture (package-by-component), barrel file discipline, and stability metrics.

## 6. TypeScript Strictness (ts)

**Impact:** HIGH
**Description:** TypeScript language features that enable or enforce clean architecture at the type system level — branded types, discriminated unions, Result types, strict compiler options (including beyond-strict flags), boundary enforcement tooling, module structure, satisfies operator, phantom types, conditional/mapped types, LSP performance optimization, and verbatimModuleSyntax.

## 7. Architecture Patterns (pattern)

**Impact:** HIGH
**Description:** Modern patterns complementing clean architecture — CQRS for command/query separation (with query-bypasses-domain insight), domain events with full lifecycle and post-commit dispatch, TypeScript-specific repository implementations, and vertical slice architecture as an alternative/complement.

## 8. Boundary Definition (bound)

**Impact:** MEDIUM-HIGH
**Description:** Architectural boundaries isolate volatile from stable elements; Humble Objects maximize testability by separating hard-to-test from easy-to-test code. Includes the Composition Root pattern for dependency wiring.

## 9. Interface Adapters (adapt)

**Impact:** MEDIUM
**Description:** Controllers, presenters, and gateways translate between use cases and external systems without leaking implementation details. Includes Explicit Architecture's primary/secondary port distinction (Herberto Graca).

## 10. Framework Isolation (frame)

**Impact:** MEDIUM
**Description:** Frameworks are details, not architecture. Business logic must never import, reference, or depend on framework-specific types.

## 11. Testing Architecture (test)

**Impact:** MEDIUM
**Description:** Tests are architectural components. Layer isolation enables fast unit tests, while boundaries enable targeted integration tests. Includes the architecture-aligned testing pyramid: domain tests (pure, 40-50%), use case tests (mocked ports, 30-40%), adapter integration tests (real DB, 15-20%), E2E tests (wiring, 5-10%).
