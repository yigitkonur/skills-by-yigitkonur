# F-03 — Session Resume vs Create (P1, M4)

## Observation

`createSession({ sessionId: "existing-id" })` creates a FRESH session —
it does not restore prior conversation context. Only `resumeSession(id)`
loads previous messages and tool state.

The skill shows both APIs but doesn't explain when to use which.

## Root cause

M4 — Missing decision criteria between two APIs with different semantics.

## Fix applied

Added "Create-or-resume pattern" subsection with try/catch pattern.
