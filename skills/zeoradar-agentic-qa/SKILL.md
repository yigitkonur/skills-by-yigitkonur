---
name: zeoradar-agentic-qa
description: "Use when testing, verifying, or auditing ZeoRadar (or any-site GEO/AEO radar platform) end-to-end on live production (https://zeoradar.endpoints.lol/) using cognitive Ego Browser agents. Simulates real human user interaction (clicking, typing, inspecting); strictly bans local mock port 8090 execution and backend database injection scripts; steers intake of target website, country, and language; orchestrates account bootstrapping and parallel multi-tab test lanes across 225 Gherkin QA test cases; captures MacBook remote display screenshots via SCP; and generates defect triage reports."
---

# ZeoRadar Agentic QA — Production-First End-to-End Steering & Cognitive Testing Engine

`zeoradar-agentic-qa` is the authoritative orchestrator for testing and verifying ZeoRadar (or any GEO/AEO AI visibility radar platform) end-to-end.

> [!IMPORTANT]
> **The Production-Only & Real-User Mandate**:
> 1. **Live Production Target**: All End-to-End operations, QA audits, and user journey verifications MUST run exclusively against the live production deployment: **`https://zeoradar.endpoints.lol/`**. Local mock servers (e.g. `http://127.0.0.1:8090`) are strictly forbidden for E2E testing.
> 2. **Zero Backend Script Injection**: Fabricating test state by running backend injection scripts (such as inserting records directly into Supabase via service role keys or mock store fixtures) is strictly prohibited. If an entity or workflow needs to exist, it MUST be created by simulating an authentic human user clicking, typing, navigating, and waiting through the real UI in `ego-browser`.
> 3. **Authentic Human Simulation**: Every interaction must follow real user mechanics: typing into input boxes, clicking buttons, waiting for real background workers to finish, inspecting DOM elements, and verifying data persistence.

---

## 1. When to Use

### Use This Skill When:
- Testing or verifying ZeoRadar end-to-end against live production (`https://zeoradar.endpoints.lol/`) exactly like a real human QA engineer.
- Running comprehensive quality audits across all 8 functional pillars (225 Gherkin QA cases across 20 suites).
- Simulating live onboarding, workspace generation, prompt selection, dashboard KPI review, and content studio pipelines directly through browser clicks and typing.
- Bootstrapping a live test account and brand seed sequentially through the UI, then steering parallel browser tabs/subagents without session races.
- Capturing remote MacBook display screenshots and serializing structured evidence (`result.md`, `evidence.json`).

### Do NOT Use This Skill When:
- **Running against local mock servers or dev ports (`127.0.0.1:8090`, `localhost:8080`)**: E2E QA exists to prove live production works. Local mocks defeat this purpose.
- **Using backend database injection scripts as a substitute for UI testing**: Never run scripts like `seed-*-live-data.mjs` or direct Supabase SQL/REST insertions to bypass UI testing.
- **Running isolated unit tests or compiler preflights**: Use `node --check`, `npm run typecheck --prefix backend`, or `node tests/provider-parity.js` directly for code-level gates.
- **Performing static code reviews without browser interaction**: Use `code-review`.

---

## 2. Stage 0: Conversational Intake & Parameter Resolution

Before executing tests, resolve or confirm the testing parameters:
- `[APP_URL]`: **`https://zeoradar.endpoints.lol/`** (Permanently pinned to Live Production).
- `[DOMAIN]`: Monitored brand website domain (e.g. `daikin.com.tr`, `example.com`).
- `[BRAND]`: Monitored brand display name (e.g. `Daikin`, `Acme`).
- `[SLUG]`: Dynamic project workspace slug generated from brand (e.g. `daikin`).
- `[COUNTRY]`: Target market country code (`TR`, `US`, `GB`, `DE`).
- `[LANGUAGE]`: Target language (`tr`, `en`).
- `[COMPETITOR_NAME]`: Primary competitor name (e.g. `Mitsubishi Electric`).
- `[COMPETITOR_DOMAIN]`: Primary competitor domain (e.g. `mitsubishielectric.com.tr`).
- `[SCOPE]`: `smoke` (Steps 01-03), `full` (All 225 cases), or custom pillar.

If operating autonomously (CI or headless mission), resolve defaults silently and log `[INTAKE AUTO-RESOLVE]`:
```text
[INTAKE AUTO-RESOLVE]
Target App URL: https://zeoradar.endpoints.lol/
Target Brand Domain: [DOMAIN]
Target Country: TR
Target Language: tr
Execution Scope: full
```

Detailed intake rules and health gates are documented in [references/01-intake-and-steering.md](references/01-intake-and-steering.md).  
Universal placeholder definitions are documented in [references/05-vocabulary-and-placeholders.md](references/05-vocabulary-and-placeholders.md).

---

## 3. Stage 1: Foundation Lane (Authentic UI Onboarding & Baseline)

Do **NOT** launch parallel subagents immediately. Step 01 must execute sequentially first by driving the real UI:

1. **Task Space Setup**: Launch Subagent 1 (`zeoradar-bootstrap-agent`) in `ego-browser` task space `zeoradar-bootstrap`.
2. **Real Authentication**:
   - Navigate to `https://zeoradar.endpoints.lol/#/auth`.
   - Fill in user credentials (`[USER_EMAIL]`, `[PASSWORD]`) or trigger test login via the UI login button.
   - Assert session token creation and credit balance.
3. **Step-by-Step UI Onboarding**:
   - Navigate to `https://zeoradar.endpoints.lol/#/onboarding`.
   - **Step 1 (Brand Profile)**: Type `[DOMAIN]` into the domain input field via `fillInput()`, select `[COUNTRY]` and `[LANGUAGE]`, and click "Continue".
   - **Step 2 (Engines & Competitors)**: Adjust engine weighting sliders and fill competitor domain `[COMPETITOR_DOMAIN]` via real UI inputs. Click "Continue".
   - **Step 3 (AI Prompts)**: Wait for real background Trigger.dev workers to suggest prompts in the UI. If custom prompts are needed, type into the custom prompt input and click "Add". Select desired prompt checkboxes in the rendered list. Click "Continue".
   - **Step 4 (Finalize & Enter)**: Click the "Enter Workspace" / "Create Project" button in the UI.
4. **Router Settlement**:
   - Await the hash transition from `#/onboarding` to `#/[SLUG]/overview`.
   - Verify that `window.state.slug === '[SLUG]'` and the real workspace header is rendered.
5. **Baseline Session Export**:
   - Write `/tmp/zeoradar-baseline-session.json` containing live cookies, verified workspaceSlug, workspaceId, promptCount, and initial run status.
   - **Strict prohibition**: No mock tokens or artificial database insertions!

---

## 4. Phase 1.5: Project Readiness & Data Settling Gate

Before launching downstream subagents, the parent orchestrator executes an automated gate check:
- **Slug & Tenant Verification**: Verifies URL is `#/:slug/overview` and `window.state.slug` is set on the live origin.
- **Prompt Inventory**: Asserts `window.state.prompts.length >= 10` across multiple intents created through the onboarding flow.
- **Run Status Check**: Inspects `window.state.runs` (detects whether `firstRun` is queued, in-progress, or sealed by real workers).
- **Session Health**: Confirms `/tmp/zeoradar-baseline-session.json` exists with active session credentials and valid workspace context.

Only when Phase 1.5 is GREEN does the orchestrator dispatch parallel subagent waves.  
Detailed edge cases and failure recovery recipes are documented in [references/07-edge-cases-and-readiness-gates.md](references/07-edge-cases-and-readiness-gates.md).

---

## 5. Stages 2–4: Parallel Subagent Waves (Steps 02 to 08)

Once the foundation baseline and project readiness are verified, spawn parallel subagents in dependency waves (strictly capped at max 10 concurrent):

```
Wave A: Core Navigation & Retrieval (Steps 02, 03, 04)
├─ Subagent 2: Step 02 Shell & Navigation (32 cases) ──► suites/step-02-shell-navigation/
├─ Subagent 3: Step 03 Overview Dashboard (33 cases)  ──► suites/step-03-overview-dashboard/
└─ Subagent 4: Step 04 Visibility Matrix  (24 cases)  ──► suites/step-04-visibility-matrix/

Wave B: Operations & Content Pipeline (Steps 05, 06, 07)
├─ Subagent 5: Step 05 Prompt Studio       (21 cases) ──► suites/step-05-prompt-studio/
├─ Subagent 6: Step 06 Agent Analytics     (24 cases) ──► suites/step-06-agent-analytics/
└─ Subagent 7: Step 07 Opportunities & AI (27 cases)  ──► suites/step-07-opportunities-content/

Wave C: Governance & Copilot (Step 08)
└─ Subagent 8: Step 08 Governance & Chat   (40 cases) ──► suites/step-08-governance-settings-chat/
```

Each subagent opens its own Ego-Browser task space (`useOrCreateTaskSpace('zeoradar-suite-0X')`), dynamically executes its assigned Gherkin cases on `https://zeoradar.endpoints.lol/`, and records anomalies.

---

## 6. Cognitive Ego-Browser Testing Protocol

Every subagent acts as an adversarial cognitive human tester using the 5-phase Ego-Browser lifecycle:
1. **Phase 1: Task Space Isolation**: `const task = await useOrCreateTaskSpace('zeoradar-suite-0X')`.
2. **Phase 2: Navigation & Hydration**: `await openOrReuseTab('https://zeoradar.endpoints.lol/#/[SLUG]/...', { wait: true })` + `await wait(2)`.
3. **Phase 3: Semantic Observation & Interaction**:
   - `const snap = await snapshotText()` before any action.
   - Click UI buttons, tabs, switches via verified selectors or `@ref`.
   - Type input via `fillInput()` exactly as a human user would.
4. **Phase 4: State Invariant Assertion**: Evaluate `js()` self-invoking function returning `{ url, state, hasErrors, renderedMetrics }`.
5. **Phase 5: Dedicated Teardown**: `await completeTaskSpace('zeoradar-suite-0X', { keep: false })` in its own final heredoc.

Detailed cognitive testing patterns and anti-patterns are documented in [references/03-ego-browser-cognitive-testing.md](references/03-ego-browser-cognitive-testing.md).

---

## 7. Remote Display Execution & Evidence Harvesting

Ego Browser runs on the physical **MacBook Gateway Host** (`ssh macbook ...`):
1. **Screen Captures**: During test runs, capture views via `await captureScreenshot('/tmp/ego-shots/<case-id>.png')`.
2. **SCP Pull**: Pull screenshots from MacBook to local result folders via `scripts/pull-mac-screenshots.sh <case-id> <dest-dir>`.
3. **Evidence Recording**: Log structured results via `scripts/record-finding.sh <result-dir> <case-id> <outcome> <summary>`.
4. **No Empty Result Dirs**: Result directories are created only when a test is executed.

Remote gateway topology, viewport conventions, and SCP recipes are documented in [references/04-macbook-remote-display-and-scp.md](references/04-macbook-remote-display-and-scp.md).

---

## 8. Stage 5: Convergence, Defect Triage & Reporting

When subagents finish, the parent verifies evidence and compiles a consolidated QA Audit Report classifying findings:
- **P0 (Blocker)**: System crash, infinite loop, or auth gate failure.
- **P1 (Critical)**: Metric calculation errors (`NaN%`, `undefined`), broken core charts.
- **P2 (Major)**: Functional degradation with workaround, drawer focus trap failure.
- **P3 (Polish/Visual)**: Turkish diacritic misrenderings, layout clipping, missing localization.

Defect schemas, Sentry error correlation, and `evidence.json` contracts are documented in [references/06-defect-triage-and-evidence-contract.md](references/06-defect-triage-and-evidence-contract.md).  
Edge case recovery patterns are documented in [references/07-edge-cases-and-readiness-gates.md](references/07-edge-cases-and-readiness-gates.md).

---

## 9. Test Suites Reference Routing

All 20 modular test suites (225 Gherkin test cases + 20 READMEs) are located in `suites/`:
- Step 01: [suites/step-01/auth-onboarding/](suites/step-01/auth-onboarding/) (24 cases)
- Step 02: [suites/step-02/shell-navigation/](suites/step-02/shell-navigation/) (32 cases)
- Step 03: [suites/step-03/overview-dashboard/](suites/step-03/overview-dashboard/) (33 cases)
- Step 04: [suites/step-04/visibility-matrix/](suites/step-04/visibility-matrix/) (24 cases)
- Step 05: [suites/step-05/prompt-studio/](suites/step-05/prompt-studio/) (21 cases)
- Step 06: [suites/step-06/agent-analytics/](suites/step-06/agent-analytics/) (24 cases)
- Step 07: [suites/step-07/opportunities-content/](suites/step-07/opportunities-content/) (27 cases)
- Step 08: [suites/step-08/governance-settings-chat/](suites/step-08/governance-settings-chat/) (40 cases)
- Master Index: [suites/00-index.md](suites/00-index.md)
