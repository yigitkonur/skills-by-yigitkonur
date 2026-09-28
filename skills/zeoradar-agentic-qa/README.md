# ZeoRadar Agentic QA — Production-First End-to-End Steering & Cognitive Testing Engine

> **Skill ID**: `zeoradar-agentic-qa`  
> **Target Environment**: **`https://zeoradar.endpoints.lol/` (Live Production Only)**  
> **Execution Paradigm**: Cognitive Human Simulation via Ego Browser (MacBook Display Gateway)  
> **Zero-Mock Law**: Strictly NO local mock servers (port 8090/8080) and NO backend database injection scripts  
> **Context**: 8 Steps · 20 Modular Test Suites · 225 Gherkin QA Test Cases · 20 Domain Dictionaries  

`zeoradar-agentic-qa` equips AI agents and human QA engineers to thoroughly test, verify, and audit ZeoRadar (or any GEO/AEO visibility radar platform) end-to-end on live production.

Rather than relying on brittle script replays, synthetic local mocks, or backend database injection scripts (which fake what a user must experience), agents act as real, inquisitive human testers using `ego-browser`: typing inputs, clicking buttons, observing live DOM semantics, reasoning over rendered states, evaluating invariants, probing boundary conditions, and capturing visual display evidence.

---

## 🚀 Quick Start

### 1. Trigger the Skill
Ask your AI assistant:
- *"Test zeoradar with daikin.com.tr for Turkey in Turkish on production"*
- *"Run full agentic QA on live zeoradar"*
- *"Audit the visibility matrix and prompt studio on zeoradar production"*

### 2. Mandatory Production Target
All E2E QA operations target live production:
- `[APP_URL]`: **`https://zeoradar.endpoints.lol/`**
- `[DOMAIN]`: Brand website under test (e.g. `daikin.com.tr`).
- `[COUNTRY]`: Target market (e.g. `TR`, `US`, `GB`, `DE`).
- `[LANGUAGE]`: Target language (e.g. `tr`, `en`).
- `[SCOPE]`: `smoke` (critical paths) or `full` (all 225 cases).

---

## 🏗️ Architecture & Directory Layout

```
zeoradar-agentic-qa/
├── SKILL.md                                 # Master routing & orchestration logic (< 500 lines)
├── README.md                                # Overview and quick start (this file)
├── references/                              # Progressive disclosure technical guides
│   ├── 01-intake-and-steering.md            # Production intake & connectivity health gates
│   ├── 02-agent-workflow-and-lane-triggering.md # Multi-wave subagent triggering protocol
│   ├── 03-ego-browser-cognitive-testing.md  # 5-phase Ego-Browser lifecycle & cognitive checks
│   ├── 04-macbook-remote-display-and-scp.md # Remote MacBook execution & SCP evidence pull
│   ├── 05-vocabulary-and-placeholders.md    # [DOMAIN], [COUNTRY] universal parameter dictionary
│   ├── 06-defect-triage-and-evidence-contract.md # Defect severity scale & evidence schemas
│   └── 07-edge-cases-and-readiness-gates.md # Edge cases & Phase 1.5 Project Readiness Gate
├── suites/                                  # 20 Modular Test Suites (225 Gherkin Cases)
│   ├── 00-index.md                          # Master test suite index & traceability matrix
│   ├── step-01/auth-onboarding/             # 24 Gherkin cases + 2 READMEs
│   ├── step-02/shell-navigation/            # 32 Gherkin cases + 3 READMEs
│   ├── step-03/overview-dashboard/          # 33 Gherkin cases + 3 READMEs
│   ├── step-04/visibility-matrix/           # 24 Gherkin cases + 2 READMEs
│   ├── step-05/prompt-studio/               # 21 Gherkin cases + 2 READMEs
│   ├── step-06/agent-analytics/             # 24 Gherkin cases + 2 READMEs
│   ├── step-07/opportunities-content/       # 27 Gherkin cases + 2 READMEs
│   └── step-08/governance-settings-chat/    # 40 Gherkin cases + 4 READMEs
└── scripts/                                 # Lightweight telemetry & harvesting helpers
    ├── record-finding.sh                    # Serializes result.md and evidence.json
    └── pull-mac-screenshots.sh              # Pulls /tmp/ego-shots/ from MacBook via SCP
```

---

## ⚡ The 5-Phase Cognitive Testing Loop (Live Production)

```bash
ssh macbook "ego-browser nodejs << 'EOF'
// Phase 1: Task Space Isolation
const task = await useOrCreateTaskSpace('zeoradar-suite-03');

// Phase 2: Navigation & Wait
await openOrReuseTab('https://zeoradar.endpoints.lol/#/[SLUG]/overview', { wait: true });
await wait(2);

// Phase 3: Semantic Observation & Interaction (Real user clicking)
const snap = await snapshotText();
await click('.ct-switch[data-action=\"ov-compare\"]', { label: 'Toggle Compare' });
await wait(1);

// Phase 4: State Invariant Assertion
const state = await js(String.raw\`(() => ({
  url: window.location.href,
  active: document.querySelector('.ct-switch.on') !== null,
  hasErrors: !!window.__lastError
}))()\`);
cliLog('Asserted State: ' + JSON.stringify(state));

// Capture remote display screenshot on MacBook
await captureScreenshot('/tmp/ego-shots/case-ov-02-compare.png');
EOF"

# Phase 5: Dedicated Teardown Heredoc
ssh macbook "ego-browser nodejs << 'EOF'
await completeTaskSpace('zeoradar-suite-03', { keep: false });
EOF"
```

---

## 📜 Evidence & Reporting

Each executed test produces:
- `result.md`: Human-readable summary of actions and observations.
- `evidence.json`: Machine-verifiable structured log of step assertions.
- `screenshots/*.png`: High-DPI screenshots pulled from MacBook display.
- **Defect Matrix**: Categorizes anomalies by severity: `P0 (Blocker)`, `P1 (Critical)`, `P2 (Major)`, `P3 (Polish/Visual)`.
