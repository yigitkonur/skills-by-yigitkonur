# Herdr Multi-Pane Live Session Audit & Agent Fleet Coordination

Operational manual for auditing skills using live Herdr agent sessions, reconstructing cognitive mental models from terminal scrollbacks, and prompting active agents to achieve 100% compliance.

---

## 1. When to Use Mode B (Herdr Multi-Pane Audit)

Use Mode B instead of synthetic subagents when:
- The user provides explicit Herdr pane handles (e.g. `wJ:p2`, `wH:p4`, `wK:p2`, `wV:p2`, `wG:p6`).
- You are auditing real-world execution traces across multiple repositories or worktrees simultaneously.
- You need to observe how different models (Claude, Codex, Gemini/Agy) interpret the exact same skill instructions in live environments.
- You need to send corrective prompts to live agent sessions to enforce compliance.

---

## 2. Herdr CLI Discovery & Scrollback Retrieval

### Discovery Commands
```bash
# List all active workspaces and their focus state
herdr workspace list

# List all running agents, their statuses, and associated panes
herdr agent list

# List all panes in a specific workspace (e.g., wH)
herdr pane list --workspace wH

# Inspect the caller's current pane context
herdr pane current --current
```

### Scrollback Retrieval Commands
Terminal scrollback contains the raw, unfiltered truth of what the agent saw, thought, ran, and outputted.

```bash
# Read recent output with soft wraps joined (BEST FOR LOGS & TRACES)
herdr pane read <pane-id> --source recent-unwrapped --lines 500

# Read current visible viewport
herdr pane read <pane-id> --source visible

# Read raw detection snapshot
herdr pane read <pane-id> --source detection
```

---

## 3. Cognitive Mental Model Reconstruction Heuristics

In live Herdr sessions, agents rarely emit explicit `[STUCK]` or `[GUESSED]` tags voluntarily unless prompted. You must reverse-engineer the agent's internal state from the terminal scrollback:

### A. Detecting "Premature Completion Illusion" (C1)
- **Symptom in Scrollback**: Agent creates/edits local files, runs a single test or linter, and immediately outputs a final "Migration Complete" summary without running remote deployment or E2E validation gates.
- **Mental Model**: The agent equated *file creation* with *task completion*.
- **Skill Defect**: The workflow lacked rigid Phase Gating with checkable stop-conditions.

### B. Detecting "Destructive / Mutation Hesitation" (C2)
- **Symptom in Scrollback**: Agent encounters existing `.github/workflows/` or external service configs, inspects them, but leaves them untouched without decommissioning or updating them.
- **Mental Model**: The agent feared breaking production or required status checks.
- **Skill Defect**: The skill lacked a non-destructive staged deprecation recipe (Shadow ➔ Flip Check ➔ Neutralize).

### C. Detecting "Tooling & Environment Ignorance" (C3)
- **Symptom in Scrollback**: Agent runs `bash scripts/dev/live-tunnel.sh --help` instead of `start` or `probe`, or skips Cloudflare dashboard setup because it doesn't know about `ego-browser`.
- **Mental Model**: The agent didn't want to lock the session with a background daemon, or didn't know how to authenticate.
- **Skill Defect**: The skill lacked non-blocking `--dry-run`/`probe` commands and explicit headless dashboard fallback payloads.

### D. Detecting "Monorepo & Structural Drift" (S3 / C4)
- **Symptom in Scrollback**: In a monorepo, agent creates scripts in unexpected directories (`scripts/dev/` vs root `scripts/`) or skips the CI build script because root `package.json` had no single build command.
- **Mental Model**: The agent got confused by workspace boundaries.
- **Skill Defect**: The skill lacked explicit Monorepo Workspace recipes.

---

## 4. Live Agent Fleet Coordination (Prompting Running Agents)

When an audit reveals that an active agent stopped prematurely or missed critical deliverables:

### Step 1: Check Agent Readiness
```bash
# Verify the agent is in 'idle' or 'done' state before prompting
herdr agent list | grep <pane-id>
```

### Step 2: Dispatch Targeted Corrective Prompt
Submit specific, actionable, self-contained instructions directly to the agent:

```bash
herdr agent prompt <pane-id> "Please complete Golden Workflow compliance by adding `scripts/ci/cloudflare-ci-build.mjs` matching the monorepo adapter recipe, adding `ci:cloudflare` to package.json, and verifying `npm run ci:cloudflare` passes locally."
```

### Step 3: Monitor Execution
```bash
# Wait for completion or inspect progress
herdr pane read <pane-id> --source recent-unwrapped --lines 100
```

---

## 5. Multi-Repository Cross-Pattern Matrix Template

When conducting a fleet audit, summarize findings in this standard matrix before editing skill files:

| Pane Handle | Repository | Archetype | Delivered Items | Derailments / Omissions | Root Cause Code | Corrective Action |
|---|---|---|---|---|---|---|
| `wJ:p2` | `website-yigitkonur` | Dual-Engine | Scripts, Docs, Local Tests | Tunnel tested with `--help` only | M4, C3 | Add `probe` action |
| `wH:p4` | `aura-monorepo` | Monorepo | Scripts, Docs, Wiki Check | Missed `cloudflare-ci-build.mjs` | S3, C4 | Add Monorepo CI recipe |
| `wK:p2` | `gocmenpsikolog` | Static SSG | Full local build (578p) | Skipped remote triggers | C1, M1 | Add Two-Tier Contract |
| `wV:p2` | `zeo-geo-radar` | No-Build | Contract checks (1060t) | Left 30KB `ci.yml` un-audited | C2, O1 | Add Staged Deprecation |
