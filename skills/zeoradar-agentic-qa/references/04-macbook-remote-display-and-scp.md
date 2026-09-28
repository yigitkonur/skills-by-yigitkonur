# 04 — MacBook Remote Display Execution and SCP Evidence Harvesting

In the Zeo development topology, `ego-browser` runs as a native Chromium instance with real display rendering on the physical **MacBook Gateway host** (`macbook`). The Linux development host commands it over SSH.

---

## 1. Remote Gateway Topology

```
┌─────────────────────────────────┐           SSH (Commands & Heredocs)           ┌────────────────────────────────┐
│       LINUX DEV HOST            │ ────────────────────────────────────────────► │      MACBOOK GATEWAY HOST      │
│  (80 vCPUs, Agent Orchestrator) │                                               │  (Physical Display, Ego-Browser)│
│                                 │ ◄──────────────────────────────────────────── │                                │
│   Local Result Directory:       │           SCP (Screenshots & Traces)          │   Remote Scratch Directory:    │
│   suites/.../01-result-.../     │                                               │   /tmp/ego-shots/              │
└─────────────────────────────────┘                                               └────────────────────────────────┘
```

---

## 2. Capturing Screenshots on the MacBook

During Phase 3 and Phase 4, the agent triggers screenshot captures inside Ego Browser:

```js
// Capture full page or active viewport on MacBook display
const shotPath = '/tmp/ego-shots/case-vis-06-stage-1.png';
await captureScreenshot(shotPath, { fullPage: false });
cliLog('Screenshot captured to MacBook display: ' + shotPath);
```

### Viewport Standards
| Mode | Dimensions | Flags / Setup |
|---|---|---|
| **Desktop (Standard)** | `1440 x 900` | Default browser window sizing. |
| **Mobile Drawer / Responsive** | `390 x 844` (iPhone 14) | Emulated viewport or mobile window resizing to trigger `.side-open` and compact layouts. |

---

## 3. SCP Evidence Harvesting Recipe

After a test case or suite completes on the MacBook, the agent or helper script pulls the captured screenshot artifacts back to the local repository filesystem:

```bash
# Target local directory for the test case
LOCAL_RESULT_DIR="/root/dev/zeo-geo-radar/.agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/06-gherkin-result-case-stage-1-synthesized-answer/screenshots"
mkdir -p "$LOCAL_RESULT_DIR"

# Pull captured shots via SCP
scp macbook:/tmp/ego-shots/case-vis-06-*.png "$LOCAL_RESULT_DIR/"

# Remove temporary files on MacBook to prevent disk bloat
ssh macbook "rm -f /tmp/ego-shots/case-vis-06-*.png"
```

---

## 4. Redaction & Security Contract

Before saving screenshots or network payloads into persistent case evidence directories:
1. **Redact Sensitive Secrets**: Mask API keys, Stripe customer IDs, JWT tokens, Supabase database URLs, and test passwords.
2. **Deterministic File Naming**: Format screenshot filenames as `<case-id>-<phase>-<descriptor>.png` (e.g. `case-vis-06-p3-model-tabs.png`).
3. **No Empty Result Directories**: A result directory (`*-result-*`) must **only** be created when an actual test execution has occurred. Never commit empty result directories.
