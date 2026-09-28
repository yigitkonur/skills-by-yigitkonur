# T0001 — Create one project

Template example only. Replace all identities, behavior, and source references
with the allocated task and actual product oracle before submission.

- Spec revision: S001
- Feature/subfeature: Project creation / single submission
- Actor: Assigned test account
- Source: Actual approved product requirement reference
- Priority: P1
- Target/runtime: Assigned generation and adapter
- Resources/reset: Exact account, data namespace, session, and reset recipe
- Exclusions: Explicit decisions only; unavailable coverage remains blocked

## Scenario

```gherkin
Given [S01] the assigned account is signed in with an empty leased project namespace
When [S02] the account submits the unique project name once
Then [E01] exactly one project with that name exists and belongs to that account
```

## Expectations and capture

| Expectation | Observable criterion | Product source | Evidence requirements | Reviews |
|---|---|---|---|---|
| E01 | One matching project and correct owner | Replace with actual contract | ER01 resulting-state image; ER02 structured project/owner response | 2: integrity check |

## Preconditions and failure boundaries

State the exact initial data/session, valid input, needed credentials/tool access,
and expected errors if those are part of the accepted case. Distinguish missing
setup from a product failure. Capture unavailable evidence as a gap.

## Reset and cleanup

Specify the owned objects created, the allowed reset action, and how to prove
reset without affecting other workers. Source/config remains frozen throughout.
