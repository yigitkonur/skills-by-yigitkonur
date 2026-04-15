# run-codex-subagents research notes

## Classification

- Path: full research path
- Skill type: workflow automation
- Goal: rewrite an MCP-era orchestration skill into a CLI-native skill for `codex-worker`

## Workspace scan

- Target skill path: `skills/run-codex-subagents/skills/run-codex-subagents/`
- Existing `SKILL.md` had strong orchestration guidance but was built around MCP tool names, resource URIs, auto-answer assumptions, and `task:///...` state surfaces.
- Existing reference tree was broad and deeply MCP-shaped:
  - top-level MCP resources, tools, event/timeline docs
  - `guides/` focused on auto-answering, monitoring, labels, parallel dispatch, and fleet behavior
  - `scripts/` focused on MCP-era log locations
  - `templates/` mixed useful mission structure with stale MCP command names
- Best local structural reference was `skills/run-agent-browser`, which is already CLI-native and keeps `SKILL.md` lean while routing detail into a small reference set.

## Research summary

### Local evidence

- Current target skill:
  - path: `skills/run-codex-subagents/skills/run-codex-subagents/SKILL.md`
  - strengths: orchestration heuristics, recovery mindset, template-first prompt discipline
  - gaps: obsolete control plane and misleading runtime model
- CLI product evidence:
  - `/Users/yigitkonur/dev/mcp-codex-worker/src/cli.ts`
  - `/Users/yigitkonur/dev/mcp-codex-worker/README.md`
  - `/Users/yigitkonur/dev/mcp-codex-worker/features/00-cli-contract.feature`
  - `/Users/yigitkonur/dev/mcp-codex-worker/features/01-task-lifecycle.feature`
  - `/Users/yigitkonur/dev/mcp-codex-worker/features/03-request-handling.feature`
  - `/Users/yigitkonur/dev/mcp-codex-worker/features/04-prompt-bundles-and-delegation.feature`
  - `/Users/yigitkonur/dev/mcp-codex-worker/features/05-runtime-config-and-custom-provider.feature`
- Best local pattern reference:
  - `skills/run-agent-browser/skills/run-agent-browser/SKILL.md`

### Remote corpus

Downloaded with `skill-dl` into `/tmp/cli-skill-corpus.xyXWs2/corpus`:

- `upstash/context7/context7-cli`
- `aannoo/hcom/hcom-agent-messaging`
- `codervisor/lean-spec/agent-browser`
- `am-will/codex-skills/super-swarm-spark`

Dead links during search:

- `0xdarkmatter/claude-mods/cli-patterns`
- `first-fluke/fullstack-starter/orchestrator`

## Comparison table

| Source | Focus | Strengths | Gaps | Relevant paths or sections | Inherit / avoid |
|---|---|---|---|---|---|
| Local `run-codex-subagents` | Codex orchestration | strong prompt-writing and recovery instincts | stale MCP tool/resource worldview | old `SKILL.md`, `references/orchestration-patterns.md`, `references/templates/*.md` | Inherit orchestration heuristics and templates. Avoid MCP nouns, URIs, and auto-answer assumptions. |
| Local `run-agent-browser` | CLI-native orchestration | clear trigger boundary, non-negotiable rules, lean routing | browser-specific commands | `SKILL.md`, `references/commands.md`, `references/workflows.md` | Inherit structure and routing discipline. Avoid browser-specific content. |
| `upstash/context7-cli` | concise CLI command-family skill | clean CLI framing, quick-start emphasis, small surface | too thin for orchestration and recovery | `SKILL.md`, `references/docs.md`, `references/setup.md` | Inherit concise CLI framing. Avoid under-documenting decision loops. |
| `aannoo/hcom-agent-messaging` | shell-driven multi-agent orchestration | practical shell loops, explicit handoff and failure handling | too much inline detail and ecosystem-specific assumptions | `SKILL.md`, `references/patterns.md`, `references/gotchas.md` | Inherit event-wait loops and handoff/recovery patterns. Avoid bloated inline command catalogs. |
| `codervisor/lean-spec/agent-browser` | simple CLI automation | approachable examples and command loops | weaker trigger discipline and duplicate detail | `SKILL.md`, `references/commands.md` | Inherit simple workflow examples. Avoid duplicated reference content. |
| `super-swarm-spark` | specialized swarm workflow | explicit ownership and integration pass | overfit, monolithic, low portability | `SKILL.md` | Only keep the ownership idea. Avoid structure and scope. |

## Success criteria

- Trigger accuracy:
  - should trigger for CLI-based Codex delegation, prompt-bundle handoff, blocked-request handling, session reuse, and multi-wave task orchestration
  - should not trigger for MCP server testing, general Codex/OpenAI docs, or built-in `spawn_agent` delegation that does not use this CLI
- Execution quality:
  - first-pass workflow should guide an agent through prompt inspection, task start, monitoring, request answering, and recovery without user correction
- Token efficiency:
  - keep `SKILL.md` lean and route bulky detail to a small, explicit CLI-native reference set

## Synthesis strategy

- Keep the skill name and install path stable.
- Recast the skill as CLI-only and remove all MCP concepts from the operating model.
- Replace the large MCP-heavy reference tree with a smaller CLI-native set:
  - exact command/flag reference
  - orchestration patterns
  - request handling
  - prompt bundles and frontmatter
  - recovery and diagnostics
  - runtime config
  - composability and exit codes
  - prompt-writing guidance
  - four copy-ready templates
- Keep the strong parts of the old skill:
  - precise mission files
  - deliberate effort selection
  - recover-before-retry
  - multi-wave planning

## Generated artifacts

- `README.md` rewritten for `codex-worker`
- `SKILL.md` rewritten as CLI-native
- added:
  - `references/command-reference.md`
  - `references/request-handling.md`
  - `references/prompt-bundles.md`
  - `references/recovery-and-diagnostics.md`
  - `references/runtime-config.md`
  - `references/composability-and-exit-codes.md`
  - `references/prompt-writing.md`
- rewrote:
  - `references/orchestration-patterns.md`
  - `references/templates/coder-mission.md`
  - `references/templates/research-mission.md`
  - `references/templates/batch-wave.md`
  - `references/templates/test-runner.md`
- deleted obsolete MCP-era references and scripts

## Trigger tests

### Should trigger

- `delegate this repo fix to codex-worker and follow it live`
- `run this task.md with codex-worker and answer any blocked requests`
- `create a prompt for another coding agent using codex-worker`
- `reuse the same codex-worker session for a follow-up message`
- `run a wave of codex tasks from markdown files and inspect failures`

### Should not trigger

- `test this MCP server with mcpc`
- `explain Model Context Protocol resources`
- `use built-in spawn_agent to parallelize this coding task`
- `look up the latest OpenAI docs for Responses API`
- `drive a browser with agent-browser`

## Functional test plan

- verify `codex-worker run` on a simple temp task with `--follow`
- verify local artifacts and handoff paths through `task read --output json`
- verify no stale MCP command names remain in the final skill pack

## Functional test results

- `codex-worker run /tmp/task.md --follow --compact`
  - confirmed real-time event streaming and compact output format
- `codex-worker task read tsk_... --output json`
  - confirmed artifact paths and task status
- `npm run smoke`
  - passed
  - returned `output: "smoke-ok"` and a real `taskId` / `sessionId`
