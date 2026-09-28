# 06 — Defect Triage and Evidence Contract

Every test execution in `zeoradar-agentic-qa` produces structured, auditable evidence. A test is never marked as passed merely because a command succeeded or the console had no red text.

---

## 1. Case Result Directory Layout

When a test case is executed, its artifacts must be saved to a dedicated result directory alongside the case specification:

```
[suite-directory]/
├── 06-gherkin-case-stage-1-synthesized-answer.md
└── 06-gherkin-result-case-stage-1-synthesized-answer/
    ├── result.md              # Human-readable execution narrative
    ├── evidence.json          # Machine-parsable assertion log
    ├── screenshots/           # Harvested from MacBook via SCP
    │   ├── p3-synthesized-answer.png
    │   └── p4-model-tabs-active.png
    └── network/               # Optional serialized network requests/responses
        └── rpc-chat-stream.json
```

---

## 2. Structured Evidence Schema (`evidence.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "caseId": "CASE-VIS-06",
  "title": "Stage 1 Synthesized Answer Inspector and In-Card Engine/Model Tabs",
  "executedAt": "2026-09-25T17:20:00Z",
  "durationMs": 4820,
  "environment": {
    "appUrl": "[APP_URL]",
    "domain": "[DOMAIN]",
    "country": "TR",
    "language": "tr",
    "viewport": "1440x900",
    "browser": "Ego-Browser 126.0 (MacBook)"
  },
  "outcome": "PASSED",
  "assertions": [
    {
      "step": "Given user is on Studio Forensics view",
      "status": "PASSED",
      "observed": "URL is #/[SLUG]/visibility?workspace=studio"
    },
    {
      "step": "When user clicks Claude model tab",
      "status": "PASSED",
      "observed": "Tab .aei-pipe-engine-tab[data-engine='claude'] gained .active class"
    },
    {
      "step": "Then answer text updates to Claude output with model badge",
      "status": "PASSED",
      "observed": "Model badge displays 'Claude 3.5 Sonnet' with zero latency errors"
    }
  ],
  "visualArtifacts": [
    "screenshots/p3-synthesized-answer.png",
    "screenshots/p4-model-tabs-active.png"
  ],
  "defects": []
}
```

---

## 3. Defect Classification & Severity Matrix

When an agent observes a discrepancy between expected behavior and actual UI/data state, it registers a defect using this rubric:

| Severity Tier | Definition & Impact | Examples in ZeoRadar |
|---|---|---|
| **P0: Blocker** | System crashes, infinite redirect loops, data loss, or total inability to authenticate or seed project. | Login gate permanently rejecting valid credentials; Onboarding wizard hanging infinitely at 100% without project finalization. |
| **P1: Critical** | Core analytical functionality broken, inaccurate data presentation, or critical calculation failures. | KPI scorecards displaying `NaN%` or `undefined`; Benchmark matrix failing to render competitor rows; On-demand run spending credits without executing. |
| **P2: Major** | Feature works partially, unexpected error modal appears, or UX flow is degraded but workaround exists. | Filter chip deselecting but UI table requiring manual page refresh; Citation drawer focus trap broken; 10s undo toast expiring prematurely at 5s. |
| **P3: Polish / Visual** | Visual misalignment, untranslated strings, minor clipping, or styling defects without functional impact. | Turkish special character `İ` rendering as question mark; button text overflowing padding on 390px mobile view; missing tooltip hover state. |

---

## 4. Sentry and Observability Correlation

If a defect involves unexpected HTTP 500s or runtime crashes, the agent correlates the event with Sentry using project conventions:
- Org: `zeo-h1`, Project: `zeo-geo-radar`, Host: `https://de.sentry.io`.
- Extract `X-Request-Id` response header from the network response or `window.__lastRequestId`.
- Query recent errors:
  ```bash
  sentry-cli issues list --status unresolved --query "level:error firstSeen:-1h"
  ```
- Correlate with logs:
  ```bash
  sentry-cli logs list --query "request_id:<uuid>"
  ```
