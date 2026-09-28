# Operating Modes & Authority Routing

Select the operating mode based on task scope and complexity. Unified Herdr eliminates rigid, mandatory management hierarchies for small tasks, replacing them with dynamic, size-based authority.

```
                    ┌────────────────────────────────────────┐
                    │           Incoming Objective           │
                    └───────────────────┬────────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  [ Direct Operation ]          [ Task Execution ]           [ Managed Mission ]
  • Inspection / 1 command      • 1 cohesive delivery        • 3+ implementation lanes
  • Genuinely bounded fix       • Up to 2 independent lanes  • Cross-repo delivery
  • Zero ceremony               • Parent supervises directly • Sustained scarce resources
  • Current or sibling pane     • Writer + paired reviewer   • Dedicated EM agent
  • No EM / PR / DAG / YAML     • Lightweight native reports • state.yaml + immutable YAML
```

---

## 1. Mode 1: Direct Operation

Use for:
- Environment inspection, discovery, or executing a single verification command.
- Quick bug investigation or short independent research.
- Genuinely small, bounded fixes with low blast radius (e.g. fixing a typo, updating a config constant, correcting a documentation link, self-contained test fix).
- *Boundary*: Direct path is reserved for genuinely small/bounded work, NOT arbitrary single-file work. A single-file modification that introduces architectural restructuring, protocol changes, breaking interface shifts, or auth changes requires Mode 2 Task Execution.

### Topology & Execution
- **Topology**: Operate inside the caller's current pane, or split a single sibling pane in the same tab, choosing split direction from projected geometry (horizontal if width $\ge 161$ cols, vertical if height $\ge 41$ lines; pass `--no-focus`).
- **Ceremony**: Zero ceremony.
  - Do NOT spawn an Engineering Manager (EM) agent.
  - Do NOT decompose into GitHub issues.
  - Do NOT open a Git worktree unless concurrent write isolation is explicitly required.
  - Do NOT mandate pull requests or immutable YAML reports.
- **Reporting**: Report outcome directly to the calling user or session in plain text.

---

## 2. Mode 2: Task Execution

Use for:
- A single cohesive feature, bugfix, or refactor.
- Up to two independent areas that do not require continuous cross-agent DAG coordination.

### Topology & Execution
- **Authority**: The parent/root agent directly supervises workers and reviewers.
  - *Authority Invariant*: Assigned executors do NOT infer managerial authority, coordinator roles, or nested subagent spawning without an explicit scope grant and verified native tool support.
- **Topology**:
  - Coupled work: A single writer pane with whole-change ownership, plus an optional side-by-side reviewer pane in the same tab (or separate review tab if width $< 161$ columns).
  - Dirty/concurrent writes: An isolated worktree created via `herdr worktree create`.
  - Read-only research: A separate tab or pane in the existing checkout.
- **Ceremony**: Lightweight engineering discipline.
  - No Engineering Manager agent.
  - Clear task brief detailing objective, owned files, and check commands.
  - Single writer per coupled change; independent reviewer when deliverable requires external verification.
  - Verifiable evidence bound to exact verified commit object ID. Concise native text handback reports.

---

## 3. Mode 3: Managed Mission

Use for:
- Three or more active implementation areas running concurrently.
- Coordinated cross-repository delivery.
- Complex multi-wave workflows requiring state continuity across restarts.
- Sustained allocation of scarce shared resources (e.g. rate-limited model quotas, single-user dev servers).

### Topology & Execution
- **Authority**: Exactly ONE dedicated Engineering Manager (EM) agent in the primary control workspace. The EM owns active state, ticket DAG scheduling, resource allocation, and report intake.
- **Topology**:
  - **Write Isolation**: Worker lanes requiring dirty or concurrent write isolation use dedicated worktree workspaces (`herdr worktree create`).
  - **Read-Only Lanes**: Passive audits, research scouts, and non-mutating inspections **retain the tab or pane route within the existing checkout**, preventing workspace sprawl.
  - **Streaming Reviews**: Reviewer panes spawned inside the task's tab (or review tab) as soon as candidate code is ready.
- **Ceremony**: Full durable reporting contract.
  - Mutable manager checkpoint (`state.yaml`) maintained exclusively by the EM at the run root.
  - Immutable YAML reports (`<task>-a<attempt>-<purpose>.yaml`) authored by workers outside disposable worktrees.
  - Atomic publication pipeline (write `.partial`, syntax/shape/digest validation, atomic rename `mv -n`, no-wait notice).
  - Explicit multi-wave dependency scheduling (dynamically sized based on DAG edges; no arbitrary five-wave cap).

---

## 4. Upgrades, Role Transfers & Invariants

1. **User Overrides**: User preference strictly overrides default routing. If the user requests low-ceremony execution for a large task, or full managed tracking for a small task, honor that choice.
2. **Dynamic Upgrades**: When a Direct Operation or Task Execution uncovers unexpected complexity requiring Mode 3:
   - Transfer state and checkpoint existing sessions.
   - Do NOT duplicate or kill healthy running workers.
   - Designate an EM to absorb coordination handles.
3. **No Recursive Managers**: An EM never spawns another EM. A single coordination layer maintains global sanity.
4. **Harness Neutrality**: An agent harness (Antigravity, Codex, Claude Code) does not dictate its role. Any supported harness can act as worker, reviewer, or manager based on task needs.
5. **No Speculative Downgrades**: Honor user-specified model and effort tiers. Do not silently downgrade reasoning tiers or guess unsupported model names.
