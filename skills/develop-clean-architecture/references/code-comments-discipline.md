---
title: Let Code Speak — Comments Explain Why Not What
impact: MEDIUM
impactDescription: reduces misleading docs, keeps codebase honest and maintainable
tags: code, comments, documentation, clarity
---

## Let Code Speak — Comments Explain Why Not What

A comment is a failure to express intent in code — except when it explains *why* a decision was made. Comments that restate what code does become lies when the code changes but the comment doesn't.

**Incorrect (redundant, misleading, noisy comments):**

```typescript
// User service class — handles user operations
class UserService {
  // Constructor
  constructor(private readonly repo: UserRepository) {}

  // Get user by ID
  // @param id - the user id
  // @returns the user
  async getUser(id: string): Promise<User> {
    // Find the user in the repository
    const user = await this.repo.findById(id);

    // Check if user exists
    if (!user) {
      // Throw not found error
      throw new UserNotFoundError(id);
    }

    // Return the user
    return user;
  }

  // Added by John on 2023-05-12
  // Modified by Sarah on 2023-06-01 to add validation
  // Modified again on 2023-07-15 to fix edge case
  async updateEmail(userId: string, email: string): Promise<void> {
    const user = await this.repo.findById(userId);
    // await this.legacyValidator.check(email); // old validation
    // await this.otherLegacyMethod(email); // removed in v2
    await this.repo.updateEmail(userId, email);
  } // end updateEmail
}
```

**Correct (comments explain why, code explains what):**

```typescript
class UserService {
  constructor(private readonly repo: UserRepository) {}

  async getUser(id: string): Promise<User> {
    const user = await this.repo.findById(id);
    if (!user) {
      throw new UserNotFoundError(id);
    }
    return user;
  }

  async updateEmail(userId: string, newEmail: string): Promise<void> {
    const user = await this.getUser(userId);

    // RFC 5321 §4.5.3.1.3 limits local-part to 64 chars, but our legacy
    // payment provider truncates at 48. Keep this until Stripe migration (PROJ-2847).
    if (newEmail.split('@')[0].length > 48) {
      throw new EmailLocalPartTooLongError(newEmail);
    }

    user.changeEmail(newEmail);
    await this.repo.save(user);
  }
}

/**
 * Calculates the compounding discount for multi-year enterprise contracts.
 * Each subsequent year receives a 2% incremental discount, capped at 15%.
 *
 * @param contractYears - Duration in whole years (1-10)
 * @param baseAnnualCents - Annual price before discount, in cents
 * @returns Total contract value in cents
 * @throws {@link InvalidContractTermError} if years outside 1-10 range
 */
function calculateEnterpriseContractTotal(
  contractYears: number,
  baseAnnualCents: number,
): number {
  let totalCents = 0;

  for (let year = 0; year < contractYears; year++) {
    // Cap at 15% — finance approved this ceiling in Q3 2024 pricing review
    const discountRate = Math.min(year * 0.02, 0.15);
    totalCents += baseAnnualCents * (1 - discountRate);
  }

  return Math.round(totalCents);
}

// TODO(PROJ-3201): Replace with event-driven sync once Kafka consumer is live
async function syncUserToLegacyCrm(user: User): Promise<void> {
  await legacyCrmClient.upsert(mapUserToCrmContact(user));
}
```

**When NOT to use this pattern:**
- Public library APIs benefit from JSDoc on every export — consumers can't read the source
- Complex regex or bitwise operations need inline clarification of *what*, not just *why*
- Legal/license headers are required by compliance regardless of readability

**Benefits:**
- Comments stay accurate because they document stable decisions, not volatile logic
- Code is the single source of truth — no divergence between comment and behavior
- Commented-out code is eliminated, reducing confusion and dead-code noise

Reference: [Clean Code Chapter 4 — Comments](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
