---
name: run-codex-exec
description: Use skill if you are orchestrating multiple parallel codex exec agents in git worktrees with auto-commit wrappers and a live stream monitor for observability.
---

# Run Codex Agents in Parallel via `codex exec` + Git Worktrees

You are an orchestrator. You dispatch coding work to multiple `codex exec` agents running in their own git worktrees. You do not type the code yourself. You write tight prompts, you watch a monitor, you merge commits as they land. The quality of the prompts determines everything.

## When to reach for this

Pick this skill when ANY of the following are true:

- You have 2+ plans / tasks that touch disjoint files. Parallelism wins.
- You have one large plan that will take >10 minutes of agent time and you want live feedback without hand-holding.
- You have access to the `codex` CLI (`codex-cli 0.121.0+`) on the local machine.
- You want the agent's work to auto-commit so the orchestrator doesn't babysit completion.
- The work is isolable in a git worktree (no cross-file coupling that would cause constant merge conflicts).

Do NOT reach for this skill when:

- The work is a single < 5 minute task. Just run `codex exec` directly in the cwd.
- The work spans shared files across all plans (e.g., every plan edits `schema.prisma`). The merge pain will outweigh the parallelism benefit. Serialize those.
- You don't have codex authenticated. Run `codex` once first to log in.

## The core loop

```
setup-worktree  ─→  codex-wrapper.sh  ─────────────────→  git merge
    (per plan)        │                                      ↑
                      ├─ codex exec (writes code)            │
                      ├─ auto-commit                         │
                      └─ post-verify tsc/tests               │
                                                             │
                                          codex-monitor.sh ──┘
                                          (streams events every 60s)
```

The monitor runs the whole time. Each agent commits to its own branch. When the monitor says an agent is done (`agent-done-committed` flag), you merge its branch to main and resolve any conflicts.

## Pre-flight, once per project

**Fast path:** run the bootstrap script from the skill's `scripts/` directory with your project as cwd. It does all 5 manual steps, detects missing `.gitignore` / tsconfig excludes, and prints the next commands you need.

```bash
cd /path/to/your/repo
bash /path/to/run-codex-exec/scripts/bootstrap.sh
# or pass a custom monitor root:
bash /path/to/run-codex-exec/scripts/bootstrap.sh /tmp/my-monitor
```

**Manual path** (what bootstrap does — do these by hand if you prefer):

1. Decide on an observability root (e.g. `/tmp/my-project-monitor/`). Everything writes there — logs, baseline SHA, per-worktree output files.
2. Pin the **baseline commit**: `git rev-parse HEAD > $MONITOR_ROOT/baseline.sha`. Monitor rules compute deltas from this.
3. Make sure your project's `.gitignore` excludes whatever worktree directory you'll use (typically `.worktrees/`). Without this, `git status` pollutes. See `references/worktree-patterns.md`.
4. If your project uses TypeScript/vitest/eslint: exclude `.worktrees/**` from each of those configs — otherwise sibling-worktree noise bleeds into the main workspace. Not needed for Python/Rust/Go/static-HTML.
5. Copy `scripts/codex-monitor.sh`, `scripts/codex-wrapper.sh`, `scripts/setup-worktree.sh`, and `scripts/codex-json-filter.sh` into your monitor root, `chmod +x` them.

## Choose a mode: streaming OR auto-commit wrapper

The skill supports two complementary orchestration modes. Pick one per run — they don't conflict but they serve different needs.

| | Streaming (`--json` + filter) | Wrapper (`codex-wrapper.sh`) |
|---|---|---|
| **When** | Single interactive task; you want to see every agent step live | Fan-out N parallel agents and walk away |
| **Observability** | Event-by-event notifications via Monitor tool | One line per tick from `codex-monitor.sh` |
| **Completion signal** | Stream ends | Auto-commit + post-verify line |
| **Parallelism** | One Monitor per agent | One Monitor for the whole fleet |
| **Setup** | Just `codex exec --json ... | codex-json-filter.sh` | Needs a worktree + wrapper invocation |
| **Reference** | `references/json-streaming.md` | `references/workflow-playbook.md` |

Rule of thumb: 1 agent → streaming; 2+ agents → wrapper. Both lean on the same underlying `codex exec` CLI, so your task prompt is portable between them.

## Dispatching a single plan

Start small. Get one plan landing cleanly before fanning out.

```bash
# 1. Create a worktree for the plan
./setup-worktree.sh wave1-reports wave1/reports-scheduled-pipeline

# 2. Launch monitor in a background that streams to stdout every 60s.
#    (In Claude Code: use the Monitor tool pointing at the script.)
./codex-monitor.sh &

# 3. Dispatch the agent
./codex-wrapper.sh wave1-reports p1-reports "Your full task prompt here" &

# 4. Watch monitor events. When you see `agent-done-committed`, go check.
```

When the wrapper finishes, the agent's branch has one or more new commits. Main is untouched. You review, then merge.

## Dispatching multiple plans in parallel

```bash
# Create all worktrees first
./setup-worktree.sh wave2-A wave2/plan-a
./setup-worktree.sh wave2-B wave2/plan-b
./setup-worktree.sh wave2-C wave2/plan-c

# Launch monitor (one instance total, no matter how many agents)
./codex-monitor.sh &

# Dispatch all agents
./codex-wrapper.sh wave2-A p2-plan-a "prompt A..." &
./codex-wrapper.sh wave2-B p2-plan-b "prompt B..." &
./codex-wrapper.sh wave2-C p2-plan-c "prompt C..." &
```

Expect 2× `codex exec` processes per wrapper (parent node + child codex binary). With 6 wrappers you'll see 12 codex procs — normal.

## Writing the task prompt

The prompt is the only lever you have once the agent is running. Tight prompts ship. Vague prompts ruminate for 40 minutes and bail. `references/prompt-template.md` has the full template; the key points:

**Open with a bypass prefix.** Codex loads all installed skills on startup. Many start with guidance like `superpowers:using-superpowers` that pushes agents toward meta-skills (brainstorming, writing-plans) instead of doing the task. Short-circuit this:

```
YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES. DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING IMMEDIATELY. THE TASK:
```

Then the actual task:

- One specific plan file path to read first
- The concrete deliverables as an ordered list (schema, action, UI, test)
- Style constraints as hard facts (TS strict+, TanStack Query, existing return shape)
- Definition of done (tsc = 0, vitest pass, eslint = 0, ≥N commits)

**Don't over-prescribe the method.** Say WHAT needs to exist, not HOW to write each function. The agent is smart; let it choose the approach.

## Observing progress

The monitor emits one line per tick (default 60s). Each line has:

```
18:15:22Z  procs=codex:N/wrap:M  commits=main:X/all:Y  (note)  [flags]  :: per-worktree summary
```

Flags to act on:

- `silent-edit` — agent started writing code. Normal. No action.
- `agent-done-committed` — wrapper exited, commits landed. **Time to review and merge.**
- `streak:Nx` (N≥6 with no commits) — agent stuck. Check its log for rate-limit 503s or ruminating loops.
- `main-dirty:N` — main branch has uncommitted changes. Fix this; nothing else should touch main during parallel work.
- `size-drift:+Nfiles` — file count changed without a commit. Could be generated files, cache dumps. Usually benign.

Full rule reference: `references/observability-rules.md`.

## What a typical agent run looks like

Timeline for a medium-complexity plan (real data from shipping p3-integrations-google-sync OAuth):

- **0–2 min:** codex reads plan files, orients itself. No file edits yet.
- **2–10 min:** codex writes code via `apply_patch` or native edits. Worktree dirty-count grows steadily.
- **10–12 min:** codex runs `tsc`, `vitest` internally, patches final issues.
- **12–14 min:** wrapper auto-commits, runs post-verify, exits.
- **Total:** ~800 seconds. Runtimes vary from 300s (small plan) to 2500s (paired big plan like config-editor + alert-FSM).

Expect ~30% of agents to bail before writing anything on the first dispatch. Common causes in `references/troubleshooting.md`. Re-dispatching after a codex backend cool-off (~13 min for the 503 rate limit) usually works on the second try.

## Merging back to main

When an agent is `agent-done-committed` and its post-verify shows `tsc_errors=0`:

```bash
# From main workspace
git merge --no-ff -X ours wave2/plan-a -m "merge: ship wave2/plan-a"
```

`-X ours` tells git to resolve trivial conflicts (typically `todo.md` updates that every agent touched) by keeping main's version. For substantive conflicts git will still stop and let you resolve.

**Common conflict hotspots:**

- `prisma/schema.prisma` — multiple agents added fields to the same model. Union them manually.
- `src/lib/query-keys.ts` — multiple agents added keys. Both belong; union them.
- `src/lib/queue.ts` — worker registrations. Union.
- Any shared pipeline file (e.g. `aggregating.ts`) — real logic merge, resolve carefully.

After any merge: run `npx prisma generate` (if schema changed), `npx tsc --noEmit`, `npx vitest run`. If tsc errors, fix them in a `fix(post-merge): ...` commit on main before merging the next branch. `references/workflow-playbook.md` has the full recipe.

## When things go wrong

- **Agent bailed with no commits.** Wrapper log will show `[wrapper] no changes`. Check the codex stdout for `503 Service Unavailable` — rate limit. Wait ~15 min, reset the worktree to current main, re-dispatch.
- **Agent committed but post-verify shows tsc errors.** Fix them yourself in a `fix(...)` commit on the agent's branch, then merge. Codex's commits often have 1–10 small type issues that are trivial to patch.
- **Multiple agents hit the same rate limit simultaneously.** They all bail around the same time. Wait, re-dispatch the failed ones. Don't re-dispatch the successful ones.
- **Monitor stops firing events.** Its 1-hour default timeout hit. Re-arm it. The wrappers and codex procs keep running regardless of the monitor.
- **You see runaway codex procs (hundreds).** You have stale `codex resume` sessions from past interactive runs. Kill them: `pkill -f "codex resume"`. Monitor only cares about `codex exec` procs, so this won't affect counts but it does eat resources.

See `references/troubleshooting.md` for the full catalogue.

## Two honest gotchas

1. **Codex will load its own installed skills.** If your project has `superpowers:*` or similar meta-skills installed for Codex, they will be invoked on every `codex exec`. This wastes 20k–80k tokens on rumination before any code is written. The SUBAGENT-STOP prefix in your prompt helps but isn't a guarantee. If you see agents consistently ruminating for 10+ minutes without writing, consider a stripped codex config (remove ~/.codex/skills or similar).
2. **Auto-commit is a load-bearing design decision.** Without it, you need a separate signal for "this codex run is done" (normal exit isn't enough — agents can exit clean after bailing). The commit IS the signal. Without auto-commit, use the MCP-based `run-codex-subagents` skill instead — it has `wait-task`.

## What you'll find in this skill

- `scripts/bootstrap.sh` — one-command pre-flight: creates monitor root, copies scripts, pins baseline, flags missing .gitignore / tsconfig excludes
- `scripts/codex-monitor.sh` — the observability loop (rule engine, osascript notifications, stdout stream)
- `scripts/codex-wrapper.sh` — the per-agent wrapper (codex exec → auto-commit → post-verify); auto-detects TS/Python/Rust/Go projects
- `scripts/setup-worktree.sh` — create a worktree, link shared node_modules + .env, regenerate Prisma
- `scripts/codex-json-filter.sh` — pipe `codex exec --json` through this to get one compact line per event for the Monitor tool
- `references/workflow-playbook.md` — the canonical 4-step orchestration recipe
- `references/observability-rules.md` — every flag explained with what to do
- `references/prompt-template.md` — the SUBAGENT-STOP prefix + DoD structure
- `references/troubleshooting.md` — the full failure catalogue from real dispatches
- `references/worktree-patterns.md` — naming, reset, delete, reuse
- `references/codex-exec-reference.md` — every `codex exec` flag that matters
- `references/mission-gravity.md` — prompt-writing philosophy (gravity not walls, ceilings not floors)
- `references/json-streaming.md` — how to pair `codex exec --json` + `codex-json-filter.sh` + Monitor tool for live event streams
- `references/language-recipes.md` — `POST_VERIFY_CMD` / `POST_VERIFY_TESTS` overrides for Python, Rust, Go, static HTML, monorepos

## One-line summary

Parallel `codex exec` across git worktrees + an auto-commit wrapper + a rule-based monitor = you can dispatch 10 agents, go to lunch, come back, merge 10 branches.

That's the skill. Read `references/workflow-playbook.md` for the canonical recipe.
