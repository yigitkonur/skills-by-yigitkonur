# Integration Environments

Use this file when database/service startup, fixtures, or ephemeral environments dominate CI time.

## Preferred patterns

| Need | Pattern | Why |
|---|---|---|
| Fast DB tests | one service container per worker + reset/truncate | Avoids container restart cost. |
| Isolated parallel DB tests | migrated template database + clone per worker/file | Pays migration once, clones quickly. |
| Cross-service boundaries | contract tests for stable APIs + targeted integration tests | Shrinks full-stack surface without deleting validation. |
| Per-PR environment | copy-on-write branch or ephemeral namespace with TTL | Isolation without shared staging pollution. |
| Local dev speed | Testcontainers reuse | Not a CI isolation primitive. |

## PostgreSQL template pattern

1. Start one PostgreSQL container or service per worker.
2. Run real migrations once into a template database.
3. Mark it as a template or keep it quiescent.
4. Clone per worker/test file:

```sql
CREATE DATABASE test_worker_1 TEMPLATE app_template;
```

PostgreSQL requires no other sessions connected to the source database during copying. Serialize template creation/cloning access accordingly.

## Vitest worker discipline

Do not default to all CPU cores for database-backed suites. Cap workers to database capacity:

```ts
export default {
  test: {
    minWorkers: 4,
    maxWorkers: 4,
  },
};
```

Too many workers can exhaust connections and make the suite slower than fewer workers.

## Fixtures

- Seed at the database layer, not through slow HTTP calls.
- Use factories for per-test data.
- Reset with `TRUNCATE ... RESTART IDENTITY CASCADE` where safe.
- Build template fixtures through real migrations so migration correctness is tested too.

## Testcontainers and lifecycle

- Start containers in global setup once per worker/suite, not per test.
- Validate the current Vitest/Testcontainers lifecycle combination; global setup and resource reapers have had known hangs.
- Testcontainers reuse is for local development loops; CI should start from a fresh container or branch.

## Contract tests

Use contract tests at stable service boundaries to replace a subset of full-stack tests. Keep database/transaction/integration tests for behavior contracts cannot prove.

## Sources

- Testcontainers Node global setup: https://node.testcontainers.org/quickstart/global-setup/ (accessed 2026-07-28)
- PostgreSQL template databases: https://www.postgresql.org/docs/current/manage-ag-templatedbs.html (accessed 2026-07-28)
- Vitest global setup/maxWorkers: https://vitest.dev/config/globalsetup ; https://vitest.dev/config/maxworkers (accessed 2026-07-28)
- Pact JS provider: https://docs.pact.io/implementation_guides/javascript/docs/provider (accessed 2026-07-28)
- Neon branching: https://neon.com/docs/introduction/branching (accessed 2026-07-28)
