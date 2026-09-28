# 02 — Agent Workflow and Subagent Triggering Protocol

The `zeoradar-agentic-qa` skill executes testing through a **multi-agent dependency wave architecture**. It decouples authentication state creation from independent functional verification, preventing cross-test data corruption and session race conditions.

---

## 1. When to Trigger Subagents vs Keeping Local

| Condition | Execution Model | Rationale |
|---|---|---|
| **Single specific test case** (e.g. `CASE-VIS-06`) | **Local Parent Execution** | No need for subagent overhead; run directly in active shell pane via `ego-browser`. |
| **Pillar smoke check** (1 suite, e.g. Step 03) | **Single Subagent** | Delegate the single suite to an isolated subagent with its own task space. |
| **Comprehensive suite run** (Multiple steps / 225 cases) | **Dependency Waves (Sequential Foundation -> Parallel Subagents)** | Mandatory to run Step 01 sequentially first to establish an authenticated baseline, then parallelize independent steps across subagents. |

---

## 2. The Dependency Wave Architecture

```
Stage 0: Parent Intake & Health Gate
   │
   ▼
Stage 1: Foundation Lane (Sequential Subagent 1)
   └─► Subagent 1: Step 01 (Auth & Brand Onboarding on https://zeoradar.endpoints.lol/)
          - Authenticates as test user (`e2e-agent@zeogen.com`) via the live UI
          - Verifies credits in billing account
          - Drives brand project onboarding via authentic UI clicks & typing ([DOMAIN], [COUNTRY], engine sliders)
          - Waits for real AI prompt suggestions from background Trigger.dev workers
          - Selects prompts in the UI and clicks Enter Workspace
          - Finalizes real project on production and generates `/tmp/zeoradar-baseline-session.json`
   │
   ▼
Stage 1.5: Project Readiness & Data Settling Gate (Parent Verification)
   - Checks workspaceSlug & workspaceId are settled
   - Verifies promptCount >= 10 across multiple intents
   - Asserts firstRun status (pending/running or sealed baseline)
   - Verifies credits >= 10M
   - Only when PASS: Parent unleashes parallel subagents below!
   │
   ▼
Stage 2: Parallel Wave A — Navigation & Retrieval Forensics (Steps 02, 03, 04)
   ├─► Subagent 2: Step 02 (Shell, Sidebar, ⌘K Command Palette, Themes, Tour) [Read-Only]
   ├─► Subagent 3: Step 03 (Overview Dashboard, KPI Cards, Trend Chart, Geo World Map) [Read-Only]
   └─► Subagent 4: Step 04 (Visibility Matrix, 3-Stage Pipeline, Citation Drawer, Sentiment) [Read-Only]
   │
   ▼
Stage 3: Parallel Wave B — Operations & Content Pipeline (Steps 05, 06, 07)
   ├─► Subagent 5: Step 05 (Prompt Studio, 100-Cap Ring, Run-Now, CSV Ingestion) [Namespaced Mutations]
   ├─► Subagent 6: Step 06 (Agent Analytics, Crawler Classification, CWV Vitals, Volumes)
   └─► Subagent 7: Step 07 (Opportunities Engine, 10s Undo, SSE Content Studio, Slugs)
   │
   ▼
Stage 4: Parallel Wave C — Governance & Copilot (Step 08)
   └─► Subagent 8: Step 08 (Brand Hub OCC 409, CSV Formula Defense, Team RBAC, Copilot)
   │
   ▼
Stage 5: Parent Convergence & Defect Triage
   - Harvest SCP screenshots from MacBook
   - Verify `result.md` and `evidence.json`
   - Produce Consolidated QA Audit Report
```

---

## 3. The Baseline Session Handshake & Readiness Gate

Step 01 subagent outputs `/tmp/zeoradar-baseline-session.json`:
```json
{
  "timestamp": "2026-09-25T17:15:00Z",
  "appUrl": "[APP_URL]",
  "domain": "[DOMAIN]",
  "brand": "[BRAND]",
  "country": "[COUNTRY]",
  "language": "[LANGUAGE]",
  "userEmail": "[USER_EMAIL]",
  "workspaceId": "[WORKSPACE_ID]",
  "workspaceSlug": "[SLUG]",
  "remainingCredits": 10001720,
  "promptCount": 12,
  "firstRunStatus": "running",
  "firstRunPlannedCells": 48,
  "storageTokens": {
    "authSession": "active_production_session",
    "cookieSnapshot": "session_cookies_persisted"
  }
}
```

### Parent Readiness Gate Check (Executed Before Wave A Dispatch)
Before spawning Subagents 2-8, the parent executes:
```bash
node -e "
const fs = require('fs');
const s = JSON.parse(fs.readFileSync('/tmp/zeoradar-baseline-session.json', 'utf8'));
if (!s.workspaceSlug || !s.workspaceId || s.promptCount < 10 || s.remainingCredits < 1000000) {
  console.error('[GATE FAIL] Session not ready:', s); process.exit(1);
}
console.log('[GATE PASS] Project ready for parallel wave dispatch');
"
```
For deep analysis of the 8 edge cases handled by this gate, consult [07-edge-cases-and-readiness-gates.md](./07-edge-cases-and-readiness-gates.md).

Downstream subagents (Steps 02 to 08) read this baseline session in Phase 1 of their Ego Browser lifecycle, restoring the session state directly rather than repeatedly performing onboarding or triggering concurrent registration locks.

---

## 4. Subagent Prompt Requirements

When the parent spawns subagents, each subagent prompt must be completely standalone and follow this structure:
1. **Header**: Assigned Step and Suite folder within `suites/`.
2. **Context Block**: Target `[APP_URL]`, `[DOMAIN]`, `[COUNTRY]`, `[LANGUAGE]`, and path to `/tmp/zeoradar-baseline-session.json`.
3. **Assigned Cases**: List of specific Gherkin test cases to execute (e.g. `01-gherkin-case-*.md`).
4. **Execution Protocol**: Run Ego Browser dynamically (not scripts); capture screenshots on remote MacBook; record observations in `result.md` and `evidence.json`.
5. **Autonomy Grant**: *"You own this testing lane end-to-end. Dynamically adapt your navigation, probe unexpected errors, and report real defects."*

---

## 5. Subagent Handback Contract

Every subagent reports back to the parent with:
1. **Cases Executed**: Count and list of case IDs (e.g. 12/12 executed).
2. **Status Breakdown**: Passed, Failed, Blocked.
3. **Defects Discovered**: Exact error signatures, broken DOM selectors, unlocalized text, or UI overlap notes.
4. **Artifacts Written**: Absolute paths to `result.md`, `evidence.json`, and `/tmp/ego-shots/` images on MacBook.
