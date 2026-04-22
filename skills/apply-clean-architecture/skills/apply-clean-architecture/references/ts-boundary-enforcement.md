---
title: Enforce Architectural Boundaries with Automated Tooling
impact: MEDIUM-HIGH
impactDescription: prevents architecture erosion, catches layer violations before code review
tags: ts, boundaries, enforcement, tooling
---

## Enforce Architectural Boundaries with Automated Tooling

Architecture rules expressed only in documentation erode within weeks. Use automated tools — dependency-cruiser, eslint-plugin-boundaries, or Nx module boundaries — to make layer violations fail CI. The compiler enforces types; these tools enforce architecture.

**Incorrect (relying on convention and code review):**

```typescript
// ARCHITECTURE.md says "domain must not import from infrastructure"
// But nothing enforces it — violations slip through reviews

// domain/entities/Order.ts — VIOLATION nobody caught
import { PrismaClient } from '@prisma/client'  // Domain depends on infrastructure!
import { sendEmail } from '../../infrastructure/email/sendgrid'  // Direct infra import!

export class Order {
  private prisma = new PrismaClient()

  async complete(): Promise<void> {
    await this.prisma.order.update({  // Persistence logic inside entity
      where: { id: this.id },
      data: { status: 'completed' }
    })
    await sendEmail(this.customerEmail, 'Order completed')  // Infra in domain
  }
}

// After 6 months: 47 domain files import from infrastructure
// Refactoring cost: weeks of untangling
```

**Correct (automated tooling catches violations in CI):**

```typescript
// .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    {
      name: 'domain-cannot-import-infrastructure',
      severity: 'error',
      comment: 'Domain layer must not depend on infrastructure',
      from: { path: '^src/domain' },
      to: { path: '^src/infrastructure' }
    },
    {
      name: 'domain-cannot-import-application',
      severity: 'error',
      comment: 'Domain layer must not depend on application layer',
      from: { path: '^src/domain' },
      to: { path: '^src/application' }
    },
    {
      name: 'application-cannot-import-infrastructure',
      severity: 'error',
      comment: 'Application layer must use ports, not direct infra imports',
      from: { path: '^src/application' },
      to: { path: '^src/infrastructure' }
    },
    {
      name: 'no-circular-dependencies',
      severity: 'error',
      comment: 'Circular dependencies break clean architecture',
      from: {},
      to: { circular: true }
    }
  ]
}

// .eslintrc.cjs — alternative with eslint-plugin-boundaries
module.exports = {
  plugins: ['boundaries'],
  settings: {
    'boundaries/elements': [
      { type: 'domain', pattern: 'src/domain/*' },
      { type: 'application', pattern: 'src/application/*' },
      { type: 'infrastructure', pattern: 'src/infrastructure/*' },
      { type: 'presentation', pattern: 'src/presentation/*' }
    ]
  },
  rules: {
    'boundaries/element-types': [2, {
      default: 'disallow',
      rules: [
        { from: 'domain', allow: ['domain'] },
        { from: 'application', allow: ['domain', 'application'] },
        { from: 'infrastructure', allow: ['domain', 'application', 'infrastructure'] },
        { from: 'presentation', allow: ['application', 'presentation'] }
      ]
    }]
  }
}

// CI pipeline step — fails fast on violations
// .github/workflows/ci.yml
// - name: Check architecture boundaries
//   run: npx dependency-cruiser src --config .dependency-cruiser.cjs --output-type err
```

**When NOT to use this pattern:**
- Tiny projects with 1-2 developers where the entire codebase fits in one mental model
- Early prototyping phase where layer boundaries are still being discovered
- Monorepos already using Nx — prefer Nx module boundary rules over separate tooling

**Benefits:**
- Architecture violations caught in seconds, not days of code review
- New developers cannot accidentally break layer rules
- Dependency graph is documented as code, not wiki pages
- CI integration means violations never reach the main branch
- Incremental adoption — start with one rule, add more as architecture stabilizes

Reference: [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) | [eslint-plugin-boundaries](https://github.com/javierbrea/eslint-plugin-boundaries)
