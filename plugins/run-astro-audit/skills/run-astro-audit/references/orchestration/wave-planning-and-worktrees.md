# Wave Planning & Worktree Isolation Protocol

This guide establishes the rules for organizing repository audit topics into dependency waves, spinning up isolated Git worktrees, managing hardware concurrency, and executing multi-agent missions without branch cross-contamination.

---

## 1. Concurrency Ceiling & Batching Rules

### The Strict 10-Agent Concurrency Guardrail

- **Maximum 10 Parallel Subagents**: Never launch more than 10 subagents simultaneously in any single wave.
- **Sub-Wave Batching**: If a planned wave contains more than 10 workloads, batch them sequentially into sub-waves:
  - Example: Wave 6 (20 workloads) $\rightarrow$ **Wave 6a** (Workloads 51–60, 10 workers) $\rightarrow$ **Wave 6b** (Workloads 61–70, 10 workers).
- **Resource Protection**: Respect host memory, V8 heap limits, and Git lock files.

```
  [ Wave 1: Workloads 01-10 ] (10 agents) ──► Complete & Verified
              │
  [ Wave 2: Workloads 11-20 ] (10 agents) ──► Complete & Verified
              │
  [ Wave 3: Workloads 21-30 ] (10 agents) ──► Complete & Verified
              │
  [ Wave 4: Workloads 31-40 ] (10 agents) ──► Complete & Verified
              │
  [ Wave 5: Workloads 41-50 ] (10 agents) ──► Complete & Verified
              │
  [ Wave 6a: Workloads 51-60 ] (10 agents) ──► Complete & Verified
              │
  [ Wave 6b: Workloads 61-70 ] (10 agents) ──► Complete & Verified
```

---

## 2. Git Worktree Allocation & Directory Structure

Subagents must NEVER develop directly on `main` or in a shared directory. Each subagent is assigned a dedicated, isolated Git worktree.

### Worktree Naming Conventions

- **Worktree Path**: `.worktrees/wt-<id>` (e.g. `.worktrees/wt-64`)
- **Branch Name**: `fix/audit-<id>` (e.g. `fix/audit-64`)

### Provisioning Recipe

From the repository root:

```bash
# Ensure target branch does not already exist locally
git branch -D fix/audit-<ID> 2>/dev/null || true

# Add isolated worktree checked out from origin/main
git worktree add -B fix/audit-<ID> .worktrees/wt-<ID> origin/main

# Verify isolated worktree state
git -C .worktrees/wt-<ID> status
```

---

## 3. Network Port & Cache Isolation

When running dev servers, preview servers, or Cloudflare tunnels across parallel worktrees, port collisions will corrupt state. Follow these strict assignments:

| Environment             | Primary Repo (`main`) |     Subagent Worktrees (`wt-*`)     | Invariant Rule                                                                             |
| :---------------------- | :-------------------: | :---------------------------------: | :----------------------------------------------------------------------------------------- |
| **Vite Dev Server**     |        `4321`         |           `4322` – `4329`           | Isolated Vite pre-bundle cache: `node_modules/.vite-dev-<port>` with `--ignore-lock`.      |
| **Compiled Preview**    |        `8788`         |           `8789` – `8799`           | Pass `--ignore-lock`. Never combine `--ignore-lock` with `--background` (Astro CLI crash). |
| **Live Tunnel Daemons** |    Port-bound PID     | `.tmp/cloudflared-live-${PORT}.pid` | Strictly port-isolated PID/log files. NEVER run blind `pkill -f cloudflared`.              |

---

## 4. Worktree Lifecycle Laws

### Zero Premature Destruction Mandate

1. **Never Kill Before Remote Push & PR**:
   - NEVER invoke `manage_subagents(Action: 'kill')` or remove a worktree (`rm -rf` / `git worktree remove`) while its branch has unpushed commits.
   - Killing a subagent prematurely permanently destroys its worktree and unmerged code.
2. **Serial Merge Queue**:
   - Integrate completed subagent PRs serially, one by one.
   - Rebase remaining active worktrees against `origin/main` if conflicting paths are touched.
3. **Safe Retirement & Cleanup**:
   - Only after a PR is merged or safely pushed to GitHub (`origin/fix/audit-<id>`), retire the worktree:
     ```bash
     git worktree remove .worktrees/wt-<ID> --force
     git worktree prune
     ```
