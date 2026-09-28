# 07 — Deep Edge Cases & Project Readiness Gates

This guide provides the authoritative technical reference for handling edge cases during end-to-end ZeoRadar testing, along with the precise contract for the **Phase 1.5 Project Readiness & Data Settling Gate**.

---

## 1. Why the 2-Stage Gated Architecture is Mandatory

In ZeoRadar, testing cannot treat the application as a static collection of independent URLs. Downstream pillars (Overview Dashboard, Visibility Matrix, Prompt Studio, Content Studio, Copilot) are **statefully dependent** on an active workspace containing:
1. A settled workspace slug and tenant ID.
2. An AI-seeded prompt inventory (`window.state.prompts.length >= 10`).
3. An initialized measurement baseline (`window.state.answers` or an active `firstRun` job).

If an orchestrator spawns parallel subagents prematurely while Onboarding is still polling suggestions or saving the project, downstream subagents will encounter blank screens, missing DOM selectors, `NaN%` calculations, or routing redirections back to `#/onboarding`.

---

## 2. The 8 Critical Edge Cases & Defensive Invariants

### Edge Case 1: Trigger.dev / Backend Suggestion Polling Timeout
- **Symptom**: During Onboarding Step 3 (Prompts), AI generates suggestions via background Trigger.dev tasks (`api/v1/onboarding/suggest-prompts`). Polling budget is 5 minutes (`OB_POLL_BUDGET_MS = 300000`). If background queues are under load or the LLM takes >60s, the UI remains in `lv.sg.phase === "polling"`.
- **Failure Mode**: A naive agent clicks "Continue" or attempts finalization before prompts arrive. The UI rejects the action with toast: `"Select at least one prompt before continuing."`
- **Defensive Invariant**:
  ```javascript
  // Ego-Browser Assertion inside Subagent 1:
  await waitFor(async () => {
    const snap = await js(`() => {
      const lv = window.obLiveState ? window.obLiveState() : null;
      const prompts = lv && lv.draft ? lv.draft.prompts : [];
      return { phase: lv && lv.sg ? lv.sg.phase : null, count: prompts.length };
    }`);
    return snap.phase === "done" && snap.count >= 10;
  }, { timeoutMs: 90000 });
  ```
  If background suggestions take time or fail, the agent must simulate a real user adding custom prompts through the UI controls (typing into the prompt input field and clicking "Add Prompt"). **Under no circumstances may an agent inject prompts into `draft.prompts` in memory or execute database seeding scripts.** Synthetic injection invalidates E2E testing.

---

### Edge Case 2: Router Hash Settlement Race
- **Symptom**: Calling `window.obEnterWorkspace()` triggers `orch.switchTenant(function () { return obProvider().bootstrap(); })` followed by `exitOnboarding()`. This involves an asynchronous tenant re-bootstrap, generation change, and router hash transition to `#/:slug/overview`.
- **Failure Mode**: Downstream subagents that immediately navigate to `#/:slug/prompts` or inspect tokens before the router has settled will land on the generic asset directory (`#/`) or trigger 404 views.
- **Defensive Invariant**:
  Subagent 1 must verify that the router has fully transitioned before writing `/tmp/zeoradar-baseline-session.json`:
  ```javascript
  await waitFor(async () => {
    return await js(`() => {
      return Boolean(
        window.location.hash.includes("/overview") &&
        window.state &&
        window.state.slug &&
        window.state.route === "app"
      );
    }`);
  }, { timeoutMs: 15000 });
  ```

---

### Edge Case 3: Initial Measurement Run In-Flight (`firstRun` State)
- **Symptom**: When a project is finalized, `firstRun` is queued or running:
  - `p.runs.some(r => r.status === "running" || r.status === "pending")`
  - Answers array is not yet sealed (`isEmptyState: true`).
  - Dashboard renders:
    ```html
    <span class="ov-kpi-val-pending">Measuring…</span>
    <span class="ov-kpi-delta in-progress">⏳ Measurement in progress (32 cells)</span>
    <div class="ov-kpi-chart ov-skeleton-wrap">...</div>
    ```
- **Failure Mode**: Downstream subagents in Step 03 (Overview) or Step 04 (Matrix) assert static metric values (e.g. `expect(visScore).toBeGreaterThan(0)`) and fail.
- **Defensive Invariant**:
  Subagents 3 and 4 must inspect `isRunInProgress`:
  - If `isRunInProgress === true`: Assert that the pending badge and skeleton loading states conform to spec, or await run sealing via `waitFor(() => !state.runs.some(r => r.status === 'running'))`.
  - If sealed with 1 run: Assert the single-run baseline badge:
    `<span class="ov-kpi-delta">Baseline established (1 run)</span>`.
  - Never assert historical delta percentages (`▲ +X.X%`) when only one run exists.

---

### Edge Case 4: Zero-Prompt or Low-Prompt Distribution
- **Symptom**: Brand onboarding returns only 1-2 prompts, or all prompts belong to a single intent (e.g. only "Navigational").
- **Failure Mode**: Step 04 Visibility Matrix filters (Informational, Commercial, Transactional) return empty tables. Step 05 Prompt Studio 100-cap ring shows skewed counts. Step 07 Opportunities Engine cannot calculate content gaps.
- **Defensive Invariant**:
  The readiness gate asserts that the accepted prompt set has at least 10 items spanning multiple intents:
  ```javascript
  const intents = new Set(window.state.prompts.map(p => p.intent || p.type));
  if (window.state.prompts.length < 10 || intents.size < 2) {
    throw new Error("Prompt diversity check failed before wave dispatch");
  }
  ```

---

### Edge Case 5: Cross-Tab Mutation & LocalStorage Contamination
- **Symptom**: Multiple subagents run parallel browser tabs within the same workspace. If Subagent 5 (Prompt Studio) deletes a prompt or creates new clusters while Subagent 4 (Visibility Matrix) is checking cell counts, race conditions occur.
- **Failure Mode**: Flaky test failures, disappearing DOM rows, or modal state collisions.
- **Defensive Invariants**:
  1. **Wave Partitioning**:
     - **Wave A (Steps 02, 03, 04)**: Strictly **Read-Only Forensic Verification**. No subagent in Wave A may trigger mutations.
     - **Wave B (Steps 05, 06, 07)**: Mutation lanes. Subagent 5 (Prompt Studio) must namespace test prompts with prefix `[E2E-TMP]` and delete only its own temporary prompts during teardown.
     - **Wave C (Step 08)**: Governance & Copilot. Settings modifications must be reverted before completing the task space.
  2. **Ego-Browser Task Space Isolation**: Every subagent runs inside its own isolated task space: `useOrCreateTaskSpace('zeoradar-suite-0X')`.

---

### Edge Case 6: Credit Exhaustion Mid-Execution
- **Symptom**: Triggering `run-now` (Step 05) or AI content drafts (Step 07) consumes credits. If balance reaches 0, the application displays `#modal-credit-exhausted` and locks the interface.
- **Defensive Invariant**:
  - Pre-flight verifies that `credits >= 10,000,000` on the test account `e2e-agent@zeogen.com`.
  - In local or mock test environments, ensure `window.state.mockStore` or credit bypass is active so tests never fail due to billing locks.

---

### Edge Case 7: SSE Stream Stalls & Reconnects (Content Studio & Copilot)
- **Symptom**: Server-Sent Events (SSE) stream for article generation (`/api/v1/content/generate`) or Copilot chat (`/api/v1/chat`) drops due to network hiccup or proxy timeout.
- **Defensive Invariant**:
  Ego-Browser testing scripts must listen for stream lifecycle events:
  - If `.cs-stream-error` or `.chat-retry-btn` appears, trigger one retry click and assert that the stream recovers without crashing the page shell.
  - Implement a 30s timeout guard on streaming states.

---

### Edge Case 8: Stale Onboarding Seed & Storage Drift
- **Symptom**: Previous interrupted onboarding sessions leave `zeo-ob-draft` or `zeo-mock-seed` keys in `localStorage`. New tabs opening `/` or `/:slug` might be redirected to the wizard.
- **Defensive Invariant**:
  Subagent 1 explicitly runs cleanup after finalization:
  ```javascript
  if (typeof window.zeoClearPersistedOnboardingSeed === "function") {
    window.zeoClearPersistedOnboardingSeed();
  }
  localStorage.removeItem("zeo-ob-draft");
  ```

---

## 3. The Phase 1.5 Project Readiness Gate Protocol

The Parent Orchestrator executes this exact verification script immediately after Subagent 1 finishes, and **BEFORE** dispatching Waves A, B, and C:

```bash
# Parent Readiness Gate Verification Script
node -e "
const fs = require('fs');
const sessionPath = '/tmp/zeoradar-baseline-session.json';

if (!fs.existsSync(sessionPath)) {
  console.error('[GATE FAIL] Baseline session file does not exist!');
  process.exit(1);
}

const session = JSON.parse(fs.readFileSync(sessionPath, 'utf8'));

// 1. Validate Core Workspace Identifiers
if (!session.workspaceSlug || !session.workspaceId) {
  console.error('[GATE FAIL] Missing workspaceSlug or workspaceId in baseline session');
  process.exit(1);
}

// 2. Validate Credit Balance
if (session.remainingCredits < 1000000) {
  console.error('[GATE FAIL] Insufficient credits:', session.remainingCredits);
  process.exit(1);
}

// 3. Validate Prompt Seed Count
if (!session.promptCount || session.promptCount < 10) {
  console.error('[GATE FAIL] Insufficient prompts seeded:', session.promptCount);
  process.exit(1);
}

console.log('[GATE PASS] Project Readiness Verified:', {
  slug: session.workspaceSlug,
  prompts: session.promptCount,
  credits: session.remainingCredits,
  firstRunStatus: session.firstRunStatus || 'in-progress'
});
process.exit(0);
"
```

Only when this gate exits with code `0`, the parent proceeds to launch parallel subagents in Waves A, B, and C.
