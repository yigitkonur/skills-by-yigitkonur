---
name: develop-clean-architecture
description: Use skill if you are applying Clean Architecture layers, dependency direction, DDD entities, use cases, or strict TypeScript patterns to structure or audit a codebase.
---

# Clean Architecture — TypeScript

Apply Clean Architecture (Robert C. Martin), DDD tactical patterns, Hexagonal/Explicit Architecture
(Herberto Graca), and Clean Code practices to TypeScript codebases. 76 rules across 11 categories.

## Guardrails — never violate these

- **Never** import outer layers from inner layers — domain imports nothing; application imports only domain
- **Never** put ORM decorators or Prisma types on domain entities — use mappers in infrastructure
- **Never** return `null` for domain errors — use a discriminated `Result<T, E>` return. In this repo the result branch uses `ok: true | false`; if `E` is a rich error union, give each error variant an `_tag` for exhaustive handling.
- **Never** use `as any` or `@ts-ignore` without a documented justification comment
- **Never** dispatch domain events before persistence — pull events AFTER `save()`, dispatch AFTER commit
- **Never** share one type across domain/API/DB layers — accept cross-layer duplication, each model serves a different master
- **Never** use barrel files (`index.ts` with `export *`) in application code — use direct imports
- **Never** validate inside domain or use cases — parse at the adapter boundary with Zod, trust inside
- **Always** use `#` private fields on entities (runtime encapsulation) — not the `private` keyword
- **Always** separate `Entity.create()` (validates, emits events) from `Entity.reconstitute()` (loads from DB, no events)
- **Always** wire dependencies in a single composition root (`main.ts`) — the only file that knows all concretions
- **Always** use `import type` for cross-layer type imports — enable `verbatimModuleSyntax: true`
- **Always** require `strict: true` + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes` in tsconfig

## Trigger boundary

**Use this skill when:**
- Designing new modules, services, or bounded contexts
- Reviewing code for architectural or dependency-direction violations
- Refactoring coupled systems toward cleaner layer separation
- Implementing entities, value objects, aggregates, or domain events
- Auditing tsconfig strictness, naming quality, or function design
- Choosing between layered architecture and vertical slices

**Do NOT use this skill when:**
- The task is purely about React/Vue/Angular component rendering (use framework skill)
- The task is about build tooling, CI/CD, or deployment only
- The task is a quick script or throwaway prototype with no long-term maintenance

## Mode detection

Before starting, determine your mode:

| Signal | Mode | Behavior |
|---|---|---|
| "Design", "architect", "structure", "plan" | **Designing** | Propose layer structure, reference [decision-tables.md](references/decision-tables.md) |
| "Review", "audit", "check", "assess" | **Reviewing** | Report findings with severity, never auto-fix, block on guardrail violations |
| "Implement", "write", "create", "add", "build" | **Implementing** | Write code following loaded references, verify with typecheck |
| "Refactor", "migrate", "extract", "move" | **Refactoring** | Apply minimal targeted changes, preserve behavior, verify tests pass |
| Ambiguous | **Ask** | Clarify with the user before proceeding |

## Required workflow

### Step 1 — Classify the task

Identify the primary category and one adjacent category:

| Category | References to load | When |
|---|---|---|
| Dependency Direction | [dep-inward-only](references/dep-inward-only.md), [dep-interface-ownership](references/dep-interface-ownership.md), [dep-dry-vs-duplication](references/dep-dry-vs-duplication.md) | Import direction issues, layer coupling, DRY vs duplication |
| Entity Design | [entity-rich-not-anemic](references/entity-rich-not-anemic.md), [entity-aggregate-roots](references/entity-aggregate-roots.md), [entity-create-reconstitute](references/entity-create-reconstitute.md) | Domain modeling, invariants, aggregates, factories |
| Use Case Isolation | [usecase-orchestrates-not-implements](references/usecase-orchestrates-not-implements.md), [usecase-input-output-ports](references/usecase-input-output-ports.md) | Use case design, port definitions, orchestration |
| Clean Code | [code-error-handling](references/code-error-handling.md), [code-parse-dont-validate](references/code-parse-dont-validate.md), [code-objects-vs-data](references/code-objects-vs-data.md) | Naming, functions, error handling, validation |
| TypeScript Strictness | [ts-strict-config](references/ts-strict-config.md), [ts-branded-types](references/ts-branded-types.md), [ts-result-type](references/ts-result-type.md), [ts-lsp-performance](references/ts-lsp-performance.md) | Type safety, config, branded types, LSP speed |
| Architecture Patterns | [pattern-cqrs-separation](references/pattern-cqrs-separation.md), [pattern-domain-events](references/pattern-domain-events.md), [pattern-vertical-slices](references/pattern-vertical-slices.md) | CQRS, events, vertical slices |
| Boundaries | [bound-composition-root](references/bound-composition-root.md), [adapt-explicit-architecture](references/adapt-explicit-architecture.md), [adapt-controller-thin](references/adapt-controller-thin.md) | Composition root, ports, adapters, controllers |
| Framework Isolation | [frame-domain-purity](references/frame-domain-purity.md), [frame-orm-in-infrastructure](references/frame-orm-in-infrastructure.md) | ORM leaks, framework coupling |
| Testing | [test-testing-pyramid](references/test-testing-pyramid.md), [test-layer-isolation](references/test-layer-isolation.md) | Test strategy, pyramid alignment |

> **Steering note:** Most tasks span two categories. Load the primary reference plus one adjacent.
> If uncertain, scan the category table for keywords matching the user's request.

### Step 2 — Load references

Read the reference file(s) from `references/` identified in Step 1. Read the full file — do not skim.
If a loaded reference example conflicts with the guardrails or repo conventions in this file, follow this file.

If the task involves existing code, also read:
- The project's `tsconfig.json` (compare against [ts-strict-config.md](references/ts-strict-config.md))
- The project's layer structure (identify domain/, application/, infrastructure/ or equivalents)

> **Steering note:** Always check if the project already has an AGENTS.md or architecture docs.
> Adapt your output to match the project's existing naming conventions and layer structure.

### Step 3 — Execute the task

Apply patterns from loaded references. Follow mode-specific behavior:

**In designing mode:**
- Propose folder structure per [comp-screaming-architecture.md](references/comp-screaming-architecture.md) (package-by-component)
- Define port interfaces in application/domain layer, implementations in infrastructure
- Load [decision-tables.md](references/decision-tables.md) for architecture selection based on domain complexity

**In implementing mode:**
- Entities: `#` private fields, `create()` + `reconstitute()` factories, `pullDomainEvents()`
- Use cases: constructor-injected ports, `Result<T,E>` returns, orchestrate-not-implement
- Adapters: thin controllers (parse, delegate, respond), Zod schemas at boundary
- `import type` for all type-only imports across layers

**In reviewing mode:**
- Check every guardrail (top of this file) — violations are automatically CRITICAL
- Check dependency direction: inner layers must never import from outer layers
- Check entity design: no anemic models, no ORM decorators, proper factories
- Flag severity: CRITICAL (guardrail), WARNING (quality degradation), INFO (polish)

**In refactoring mode:**
- Apply minimal changes. One refactoring at a time.
- Preserve public API contracts. Preserve test behavior.
- Load [decision-tables.md](references/decision-tables.md) for anti-pattern recognition table
- For low-complexity requests, the smallest acceptable boundary split is: pure domain logic, one application entry point, boundary parsing in adapters, and one composition root.

> **Steering note:** Never apply Clean Architecture to a simple CRUD app that doesn't need it.
> Check domain complexity first. For LOW complexity, vertical slices + Zod + Result types are sufficient. If the user explicitly asks for a refactor toward cleaner boundaries anyway, do the smallest useful version: isolate pure domain logic, keep one composition root, and move boundary parsing to adapters without forcing extra ceremony.

### Step 4 — Verify

After making changes:

1. Read the project's scripts or workspace docs first, then run the strongest project-native typecheck command available (`npm run typecheck`, `pnpm typecheck`, `tsc --noEmit -p tsconfig.json`, or `npx tsc --noEmit` only if the repo installs TypeScript locally and that command works here)
2. Run tests if configured (`npm test`, `pnpm test`, or project equivalent). If no tests are configured, state that explicitly and fall back to build + typecheck instead of pretending a test step exists.
3. Check imports: no outer-to-inner violations
4. Check entities: `#` private fields, `create`/`reconstitute` separation
5. Check boundaries: ports in consuming layer, implementations in infrastructure

If the project contains TSX but the task is architecture-only, either install the required React runtime/types before typechecking or scope the verification command to the non-UI packages/modules you actually changed. State which path you took.

### Step 5 — Deliver

- **Designing:** Output folder structure, port interfaces, layer diagram
- **Implementing:** Output complete, compilable code with explicit return types
- **Reviewing:** Output structured findings list with severity, file, line references
- **Refactoring:** Output targeted diffs with before/after

> **Steering note:** Always produce a deliverable — code, findings list, or structure. Never end with only commentary.

## Common mistakes to avoid

| Mistake | Why it's wrong | What to do instead |
|---|---|---|
| Applying full Clean Architecture to a simple CRUD app | Over-engineering; 4+ layers for no benefit | Use vertical slices; add layers only when complexity emerges |
| Sharing one type across all layers ("DRY") | DB schema change breaks API; passwordHash leaks | Per-layer models with mappers — each has different change reason |
| Mocking domain entities in tests | Entities are pure — mocking defeats the purpose | Test entities directly; mock only ports in use case tests |
| Dispatching events before commit | Event published, DB rolled back = inconsistency | Pull events after save, dispatch after commit |
| Using `private` keyword on entity fields | Compile-time only — bypassable with `as any` | Use `#` private fields for runtime encapsulation |
| Putting Zod validation inside domain/use cases | Wrong layer — parsing belongs at the adapter boundary | Parse at HTTP boundary with Zod; domain receives trusted types |
| Using barrel `index.ts` in app code | Cascade loads 3x+ modules, causes circular deps | Direct imports from source files |
| One constructor for both creation and DB loading | Duplicate event emission on every load; or skipped validation | `create()` for new entities, `reconstitute()` for DB loads |
| Flagging absence of patterns as violations | Optional patterns (events, CQRS) are not mandatory | Only audit what exists — don't flag absence of optional patterns |

## Reference routing

All references live in `references/`. Load by category:

| Prefix | Category | Count | Key files |
|---|---|---|---|
| `dep-` | Dependency Direction | 7 | [dep-inward-only](references/dep-inward-only.md), [dep-interface-ownership](references/dep-interface-ownership.md), [dep-dry-vs-duplication](references/dep-dry-vs-duplication.md), [dep-acyclic-dependencies](references/dep-acyclic-dependencies.md), [dep-data-crossing-boundaries](references/dep-data-crossing-boundaries.md), [dep-no-framework-imports](references/dep-no-framework-imports.md), [dep-stable-abstractions](references/dep-stable-abstractions.md) |
| `entity-` | Entity Design | 8 | [entity-rich-not-anemic](references/entity-rich-not-anemic.md), [entity-aggregate-roots](references/entity-aggregate-roots.md), [entity-create-reconstitute](references/entity-create-reconstitute.md), [entity-domain-services](references/entity-domain-services.md), [entity-encapsulate-invariants](references/entity-encapsulate-invariants.md), [entity-no-persistence-awareness](references/entity-no-persistence-awareness.md), [entity-pure-business-rules](references/entity-pure-business-rules.md), [entity-value-objects](references/entity-value-objects.md) |
| `usecase-` | Use Case Isolation | 6 | [usecase-orchestrates-not-implements](references/usecase-orchestrates-not-implements.md), [usecase-input-output-ports](references/usecase-input-output-ports.md), [usecase-explicit-dependencies](references/usecase-explicit-dependencies.md), [usecase-no-presentation-logic](references/usecase-no-presentation-logic.md), [usecase-single-responsibility](references/usecase-single-responsibility.md), [usecase-transaction-boundary](references/usecase-transaction-boundary.md) |
| `code-` | Clean Code | 11 | [code-error-handling](references/code-error-handling.md), [code-parse-dont-validate](references/code-parse-dont-validate.md), [code-objects-vs-data](references/code-objects-vs-data.md), [code-comments-discipline](references/code-comments-discipline.md), [code-composition-over-inheritance](references/code-composition-over-inheritance.md), [code-flag-arguments](references/code-flag-arguments.md), [code-function-arguments](references/code-function-arguments.md), [code-immutability](references/code-immutability.md), [code-meaningful-names](references/code-meaningful-names.md), [code-no-side-effects](references/code-no-side-effects.md), [code-small-functions](references/code-small-functions.md) |
| `comp-` | Component Cohesion | 6 | [comp-screaming-architecture](references/comp-screaming-architecture.md), [comp-barrel-file-discipline](references/comp-barrel-file-discipline.md), [comp-common-closure](references/comp-common-closure.md), [comp-common-reuse](references/comp-common-reuse.md), [comp-reuse-release-equivalence](references/comp-reuse-release-equivalence.md), [comp-stable-dependencies](references/comp-stable-dependencies.md) |
| `ts-` | TypeScript Strictness | 11 | [ts-strict-config](references/ts-strict-config.md), [ts-branded-types](references/ts-branded-types.md), [ts-result-type](references/ts-result-type.md), [ts-lsp-performance](references/ts-lsp-performance.md), [ts-boundary-enforcement](references/ts-boundary-enforcement.md), [ts-conditional-types](references/ts-conditional-types.md), [ts-discriminated-unions](references/ts-discriminated-unions.md), [ts-module-structure](references/ts-module-structure.md), [ts-phantom-types](references/ts-phantom-types.md), [ts-satisfies-operator](references/ts-satisfies-operator.md), [ts-verbatim-module-syntax](references/ts-verbatim-module-syntax.md) |
| `pattern-` | Architecture Patterns | 4 | [pattern-cqrs-separation](references/pattern-cqrs-separation.md), [pattern-domain-events](references/pattern-domain-events.md), [pattern-vertical-slices](references/pattern-vertical-slices.md), [pattern-repository-ts](references/pattern-repository-ts.md) |
| `bound-` | Boundary Definition | 7 | [bound-composition-root](references/bound-composition-root.md), [bound-main-component](references/bound-main-component.md), [bound-boundary-cost-awareness](references/bound-boundary-cost-awareness.md), [bound-defer-decisions](references/bound-defer-decisions.md), [bound-humble-object](references/bound-humble-object.md), [bound-partial-boundaries](references/bound-partial-boundaries.md), [bound-service-internal-architecture](references/bound-service-internal-architecture.md) |
| `adapt-` | Interface Adapters | 6 | [adapt-controller-thin](references/adapt-controller-thin.md), [adapt-explicit-architecture](references/adapt-explicit-architecture.md), [adapt-anti-corruption-layer](references/adapt-anti-corruption-layer.md), [adapt-gateway-abstraction](references/adapt-gateway-abstraction.md), [adapt-mapper-translation](references/adapt-mapper-translation.md), [adapt-presenter-formats](references/adapt-presenter-formats.md) |
| `frame-` | Framework Isolation | 5 | [frame-domain-purity](references/frame-domain-purity.md), [frame-orm-in-infrastructure](references/frame-orm-in-infrastructure.md), [frame-di-container-edge](references/frame-di-container-edge.md), [frame-logging-abstraction](references/frame-logging-abstraction.md), [frame-web-in-infrastructure](references/frame-web-in-infrastructure.md) |
| `test-` | Testing Architecture | 5 | [test-testing-pyramid](references/test-testing-pyramid.md), [test-layer-isolation](references/test-layer-isolation.md), [test-boundary-verification](references/test-boundary-verification.md), [test-testable-design](references/test-testable-design.md), [test-tests-are-architecture](references/test-tests-are-architecture.md) |
| — | Decision Tables | 1 | [decision-tables](references/decision-tables.md) (architecture selector, anti-patterns, conflicts, Do/Don't) |

Additional supporting files:
- [_sections.md](references/_sections.md) — Category definitions and impact levels
- [assets/templates/_template.md](assets/templates/_template.md) — Template for adding new rules

## Guardrails — repeated for recall

- Source dependencies point **inward only** — domain never imports outer layers
- Entities use `#` private fields, `create()` + `reconstitute()` factories, `Result<T,E>` returns using the repo's discriminated union convention
- Parse at boundary with Zod — never validate inside domain
- Events dispatched AFTER persistence — never before commit
- Accept cross-layer DTO duplication — DRY ends at the layer boundary
- `main.ts` is the only composition root — the only file that knows all concretions
