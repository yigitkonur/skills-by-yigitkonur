# Generated Config Review: dubinc/dub

Validation: All checks pass (valid JSON, valid globs, no duplicate IDs, valid severities).

## Rules (10 generated)
| Rule | Severity | Verdict |
|---|---|---|
| auth-wrapper-required | critical | Semantic, well-scoped |
| rate-limit-check | high | Architecture-specific |
| prisma-transaction-scope | high | Data-integrity |
| stripe-webhook-sig | critical | Security-critical |
| zod-input-validation | medium | Borderline (could overlap TS strict) |
| edge-runtime-no-node | high | Runtime constraint |
| link-cache-invalidation | medium | Domain-specific |
| tinybird-event-schema | medium | Schema conformance |
| workspace-permission-check | high | Authorization layer |
| env-var-validation | low | Could be build-time |

Context files (5): All essential or useful for their paired rules.
