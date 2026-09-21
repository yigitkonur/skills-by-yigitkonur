# Herdr Multi-Agent Parallel E2E Execution

This reference details the orchestration mechanics for scaling `ego-browser` end-to-end testing across a multi-agent parallel fleet using Herdr multiplexer primitives.

---

## 1. Why Parallelize with Herdr & Ego-Browser?

Running a comprehensive suite of 20+ real-user browser journeys sequentially can take 15–30 minutes. 

`ego-browser` natively supports **isolated task spaces**. Each task space:
- Has its own separate tab collection and browsing context.
- Can run concurrently in separate Node.js processes on the same machine.
- Avoids cookie or session collisions with sibling task spaces.

By combining `ego-browser` task spaces with **Herdr split panes**, an Engineering Manager (EM) can dispatch multiple test suites in parallel, observe live PTY progress, and collect reports in minutes.

---

## 2. Fleet Architecture: CTO ➔ EM ➔ Test Workers

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Primary Workspace: Leadership Tab                                               │
├────────────────────────────────────────┬────────────────────────────────────────┤
│ Pane 1: CTO Control                    │ Pane 2: Engineering Manager (EM)       │
│ • Defines target test matrix           │ • Allocates Herdr worker panes         │
│ • Evaluates global test verdicts       │ • Dispatches suite heredocs to workers │
│ • Approves release candidate           │ • Collects structured completion blocks│
│ • Retires EM pane on completion        │ • Closes worker panes on pass/fail     │
└────────────────────────────────────────┴────────────────────────────────────────┘
                                    │
                                    ▼ (Dispatches parallel suites)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Test Fleet Workspaces / Dedicated Tabs                                          │
├───────────────────────┬─────────────────────────┬───────────────────────────────┤
│ Worker Pane A:        │ Worker Pane B:          │ Worker Pane C:                │
│ Suite: Overview       │ Suite: Analytics        │ Suite: Settings & Billing     │
│ Task Space: 'ts-ovw'  │ Task Space: 'ts-anl'    │ Task Space: 'ts-set'          │
│ • Brand asset nav     │ • Agent crawler metrics │ • Profile menu & theme toggle │
│ • Metric cards        │ • Engine filter chips   │ • Stripe portal buttons       │
│ • Executive summaries │ • Web vitals audit      │ • i18n language toggle        │
└───────────────────────┴─────────────────────────┴───────────────────────────────┘
```

---

## 3. Step-by-Step Parallel Dispatch Protocol

### Step 1: Matrix Decomposition (EM)
Partition the test matrix into independent, non-interfering suites:
- `suite_1_overview`: Route `/`, brand cards, overview metrics.
- `suite_2_analytics`: Route `/agentanalytics`, `/volumes`, filter chips.
- `suite_3_settings`: Route `/settings`, `/account`, billing, theme, i18n.

### Step 2: Provision Worker Panes (EM)
Create sibling panes or dedicated tabs without stealing user focus:

```bash
# Example: Creating a 3-worker split in a dedicated E2E tab
TAB_JSON="$(herdr tab create --label "e2e-fleet" --no-focus)"
TAB_ID="$(echo "$TAB_JSON" | jq -r .result.tab.tab_id)"
WORKER_1="$(echo "$TAB_JSON" | jq -r .result.root_pane.pane_id)"

WORKER_2="$(herdr pane split --pane "$WORKER_1" --direction right --no-focus | jq -r .result.pane.pane_id)"
WORKER_3="$(herdr pane split --pane "$WORKER_2" --direction down --no-focus | jq -r .result.pane.pane_id)"
```

### Step 3: Dispatch Test Execution (EM)
Inject the respective suite heredoc into each worker pane via `herdr pane run`:

```bash
# Dispatch Worker 1:
herdr pane run "$WORKER_1" "ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('ts-overview')
await openOrReuseTab('https://zeoradar.endpoints.lol/', { wait: true, timeout: 30 })
// ... Suite 1 logic ...
cliLog('SUITE_STATUS: suite=overview status=PASSED passed=5 failed=0')
EOF
ego-browser nodejs <<'EOF'
await completeTaskSpace('ts-overview', { keep: false })
EOF"

# Dispatch Worker 2:
herdr pane run "$WORKER_2" "ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('ts-analytics')
await openOrReuseTab('https://zeoradar.endpoints.lol/hepsiburada/agentanalytics', { wait: true, timeout: 30 })
// ... Suite 2 logic ...
cliLog('SUITE_STATUS: suite=analytics status=PASSED passed=4 failed=0')
EOF
ego-browser nodejs <<'EOF'
await completeTaskSpace('ts-analytics', { keep: false })
EOF"
```

### Step 4: Active Observation & Output Waiting (EM)
The EM monitors output using Herdr inspection primitives:

```bash
# Wait for completion token in Worker 1:
herdr pane wait-output "$WORKER_1" --match "SUITE_STATUS:" --timeout 180000

# Capture worker buffer:
herdr pane read "$WORKER_1" --source recent-unwrapped --lines 50
```

### Step 5: Clean Retirement & Teardown
Once a worker finishes and reports `status=PASSED`, the EM promptly closes that worker pane to prevent resource bloat:

```bash
herdr pane close "$WORKER_1"
herdr pane close "$WORKER_2"
herdr pane close "$WORKER_3"

# If an entire tab was used:
herdr tab close "$TAB_ID"
```

---

## 4. Structured Handover Block (EM ➔ CTO)

When all parallel test workers finish, the EM emits the aggregate E2E verdict to the CTO:

```text
E2E_VERDICT: status=GREEN total_suites=3 passed=3 failed=0 duration_ms=45000 url="https://zeoradar.endpoints.lol/" sha="6820518"
```
