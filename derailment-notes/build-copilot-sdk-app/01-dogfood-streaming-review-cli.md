# Derailment Test: build-copilot-sdk-app on "Streaming Code-Review CLI"

Date: 2025-07-11
Skill under test: build-copilot-sdk-app
Test task: Build a streaming CLI tool that reviews staged git diffs using custom tools, hooks, session persistence, and BYOK
Method: Follow SKILL.md steps literally, suppress domain knowledge

---

## Pre-scan summary

- **SKILL.md**: 241 lines, decision tree with 8 branches, 3 quick-start examples
- **References**: 10 files (~2,800 lines total)
- **External deps**: Node.js >= 20, Copilot CLI, @github/copilot-sdk, tsx, zod (not mentioned)
- **Branching**: Decision tree routes to 10 reference files by topic

---

## Friction points

### Quick start / Project setup

**F-01 — ESM module type not mentioned** (P0)
The Quick start says `npm install @github/copilot-sdk tsx` but the SDK only ships ESM exports.
Running `npx tsx minimal.ts` fails with `ERR_PACKAGE_PATH_NOT_EXPORTED` because `package.json`
lacks `"type": "module"`. No mention of this requirement anywhere in the skill.
Root cause: S1 (Missing prerequisite)
Fix: Add `npm pkg set type=module` and ESM warning callout to Quick start.

**F-02 — No `npm init` before `npm install`** (P1)
Quick start jumps straight to `npm install` without creating `package.json` first.
An executor in a new directory gets `ENOENT: no such file or directory`.
Root cause: S1 (Missing prerequisite)
Fix: Add `npm init -y` before install command.

**F-08 — No `node --version` verification shown** (P2)
Skill says "Requires Node.js >= 20" in prose but doesn't show a verification command.
Root cause: S1 (Missing prerequisite)
Fix: Add `node --version` check to prerequisites section.

**F-09 — `zod` not in install command** (P1)
Custom tool examples use `import { z } from "zod"` but `zod` is not in the
`npm install` command. Executor hits `Cannot find module 'zod'`.
Root cause: S1 (Missing prerequisite)
Fix: Add `zod` to install command.

### Session persistence

**F-03 — createSession vs resumeSession decision logic missing** (P1)
`createSession` with an existing sessionId starts FRESH (does not restore context).
Only `resumeSession` does. The try/catch resume-or-create pattern is buried in
`advanced-patterns.md` (~line 300).
Root cause: M4 (Missing decision criteria)
Fix: Add explicit "Create-or-resume pattern" subsection.

### Streaming

**F-04 — Streaming idle handler doesn't exit process** (P1)
The idle handler only logs but never calls `session.disconnect()` or `client.stop()`.
Process hangs indefinitely after completion.
Root cause: M4 (Missing execution detail)
Fix: Add cleanup to idle handler.

### BYOK

**F-05 — BYOK without model doesn't error at createSession** (P2)
Session creation succeeds silently without model; error surfaces only at send time.
Root cause: O2 (Misleading description)
Fix: Clarify pitfall wording.

### Hooks

**F-06 — Hooks void return not documented as valid** (P2)
Returning void from hooks is valid (no-op) but not documented.
Root cause: M6 (Missing edge case)
Fix: Add void return note to hooks.md.

### Events

**F-07 — Parallel tool event interleaving not shown** (P2)
No streaming example shows how to correlate interleaved tool events using `toolCallId`.
Root cause: M5 (Missing scaling guidance)
Fix: Add parallel tool events subsection.

---

## What worked well

1. **Decision tree routing** — Immediately directed to correct reference files. Zero wrong turns.
2. **defineTool API** — Zod schema -> tool worked on first try. SDK auto-detects Zod v4.
3. **Streaming events** — `assistant.message_delta` fired reliably with correct `deltaContent`.
4. **Hooks** — `onPreToolUse`, `onPostToolUse` fired with documented input shapes.
5. **sendAndWait** — Blocking pattern returned correct response.
6. **approveAll** — Single import for unattended permission handling.
7. **Type reference** — All 47 event types documented with full data shapes.
8. **Reference file organization** — 10 files with clear, non-overlapping topics.

---

## Priority summary

| Priority | Count | Friction points |
|----------|-------|----------------|
| P0       | 1     | F-01           |
| P1       | 4     | F-02, F-03, F-04, F-09 |
| P2       | 4     | F-05, F-06, F-07, F-08 |

## Metrics

| Metric | Value |
|--------|-------|
| Total steps attempted | 15 |
| Clean passes | 7 |
| Clean pass rate | 47% |

## Root cause distribution

| Code | Category | Count | Friction points |
|------|----------|-------|----------------|
| S1   | Missing prerequisite | 4 | F-01, F-02, F-08, F-09 |
| M4   | Missing decision criteria | 2 | F-03, F-04 |
| M5   | Missing scaling guidance | 1 | F-07 |
| M6   | Missing edge case | 1 | F-06 |
| O2   | Misleading description | 1 | F-05 |
