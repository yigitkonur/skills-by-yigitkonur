# skills-by-yigitkonur

Skills for AI coding agents — code review, planning, research, browser automation, multi-agent orchestration, framework guides, SDK guides, design extraction, and more. **46 skills** organized under the 12-verb naming registry (see [NAMING.md](NAMING.md)).

## Install

Install **the full pack**:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

Install **a single skill** — substitute `<skill-name>`:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

Per-skill one-liners are listed under each row below.

---

## 🏗️ Build apps & code

Write application code with a framework or SDK.

- **[build-chrome-extension](skills/build-chrome-extension/)** — Chrome extensions with Manifest V3.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-chrome-extension`

- **[build-clean-mcp-architecture](skills/build-clean-mcp-architecture/)** — Clean Architecture standard for TypeScript MCP servers — folder layout, layer boundaries, mcp-use placement, TS quality.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-clean-mcp-architecture`

- **[build-effect-ts-v3](skills/build-effect-ts-v3/)** — Effect-TS v3 apps — typed errors, services, layers, Schema, Stream, HTTP, SQL.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-effect-ts-v3`

- **[build-kernel-ts-sdk](skills/build-kernel-ts-sdk/)** — Browser-automation agents and apps with the Kernel TypeScript SDK.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-kernel-ts-sdk`

- **[build-langchain-ts-app](skills/build-langchain-ts-app/)** — LangChain.js agents, RAG, and tool-calling.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-langchain-ts-app`

- **[build-macos-app](skills/build-macos-app/)** — Production-grade macOS SwiftUI/AppKit — HIG, Liquid Glass, snapshots, hooks, Convex+Clerk.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-macos-app`

- **[build-mcp-server-sdk-v1](skills/build-mcp-server-sdk-v1/)** — MCP servers with @modelcontextprotocol/sdk v1.x.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-server-sdk-v1`

- **[build-mcp-server-sdk-v2](skills/build-mcp-server-sdk-v2/)** — MCP servers with @modelcontextprotocol/server v2.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-server-sdk-v2`

- **[build-mcp-use-agent](skills/build-mcp-use-agent/)** — AI agents with mcp-use MCPAgent.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-agent`

- **[build-mcp-use-client](skills/build-mcp-use-client/)** — MCP clients with mcp-use SDK.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-client`

- **[build-mcp-use-server](skills/build-mcp-use-server/)** — MCP servers with mcp-use — tools, schemas, responses, auth, sessions, transports, MCP Apps widgets, ChatGPT Apps, Inspector, deploy.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-server`

- **[build-raycast-script-command](skills/build-raycast-script-command/)** — Raycast Script Commands in Python/Bash.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-raycast-script-command`

- **[build-skill](skills/build-skill/)** — Claude skill creation and research methodology.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skill`

- **[build-tinacms-nextjs](skills/build-tinacms-nextjs/)** — TinaCMS-backed App Router sites with MDX, schemas, visual editing.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-tinacms-nextjs`

---

## ⚙️ Config & instruction files

Generate or refresh config / instruction files that another tool consumes.

- **[init-agent-config](skills/init-agent-config/)** — AGENTS.md / CLAUDE.md / REVIEW.md hierarchies; folder-scoped guidance; native review adapters.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-agent-config`

- **[init-makefiles](skills/init-makefiles/)** — Scaffold safe scenario Makefiles (Vercel default; Cloudflare Pages opt-in), R2 bulk upload via rclone, AGENTS sync, optional deploy CI.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-makefiles`

- **[update-agent-config](skills/update-agent-config/)** — Audit AGENTS.md / CLAUDE.md / REVIEW.md for drift after refactors; refresh refs, recount frequency tables, fill gap folders.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/update-agent-config`

---

## 🔍 Audit (read-only inspection)

Inspect an artifact; produce findings, no fixes.

- **[audit-agentic-cli](skills/audit-agentic-cli/)** — Audit and design agent-ready CLI contracts.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-agentic-cli`

- **[audit-agentic-mcp](skills/audit-agentic-mcp/)** — Audit MCP servers for agent-readiness; design framework, security, context posture.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-agentic-mcp`

- **[audit-completion](skills/audit-completion/)** — Audit task / session / plan / branch completion claims; remediate to terminal status.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-completion`

- **[audit-skill-by-derailment](skills/audit-skill-by-derailment/)** — Skill quality testing via subagent execution and trace analysis.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-skill-by-derailment`

- **[audit-ui](skills/audit-ui/)** — Visual UI audit across pages and viewports with browser screenshots.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/audit-ui`

---

## 📝 Review (PR / diff / feedback)

Evaluate a code change for merge-readiness; produce reviewer feedback.

- **[review-feedback](skills/review-feedback/)** — Triage received human, bot, markdown, or multi-reviewer feedback.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/review-feedback`

- **[review-pr](skills/review-pr/)** — Review PRs and branch diffs for merge readiness.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/review-pr`

- **[review-self](skills/review-self/)** — Hand off work as a PR with domain-aware self-review, or produce a markdown review doc.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/review-self`

---

## ✅ Test (pass / fail)

Binary verification.

- **[test-by-mcpc-cli](skills/test-by-mcpc-cli/)** — MCP server testing with mcpc 0.2.x.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/test-by-mcpc-cli`

---

## 🐛 Debug & plan

Investigate runtime bugs; frame decisions without writing code.

- **[debug-runtime](skills/debug-runtime/)** — Language-agnostic systematic debugging; four phases + Iron Law + 3-fails handoff to plan-tradeoff.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/debug-runtime`

- **[plan-tradeoff](skills/plan-tradeoff/)** — Deep thinking for ambiguous plans, architecture, refactors, or choices.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/plan-tradeoff`

---

## 🔄 Convert & extract

Transform an artifact A → B, or pull data / design out of existing artifacts.

- **[convert-mcp-sdk-v1-to-v2](skills/convert-mcp-sdk-v1-to-v2/)** — Port v1 MCP servers to the v2 split-package SDK.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/convert-mcp-sdk-v1-to-v2`

- **[convert-url-to-nextjs](skills/convert-url-to-nextjs/)** — Live URLs or HTML snapshots to Next.js projects.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/convert-url-to-nextjs`

- **[extract-saas-design](skills/extract-saas-design/)** — SaaS dashboard visual system extraction.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/extract-saas-design`

---

## 🛠️ Run external tools

Drive a CLI, API, browser, or other live tool during the session.

- **[run-agent-browser](skills/run-agent-browser/)** — Browser automation with agent-browser CLI.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-agent-browser`

- **[run-batch-codex-research](skills/run-batch-codex-research/)** — Fan out codex (or another LLM CLI) over inputs in parallel with retry.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-batch-codex-research`

- **[run-codex-1](skills/run-codex-1/)** — Drive codex CLI fleets, batches, review loops, and rescue (alias of run-codex-2 during A/B period).
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-1`

- **[run-codex-2](skills/run-codex-2/)** — Drive codex CLI fleets, batches, review loops, and rescue.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-2`

- **[run-codex-exec](skills/run-codex-exec/)** — Deprecated install-path stub for parallel codex exec agents.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-exec`

- **[run-codex-review](skills/run-codex-review/)** — Per-branch codex review fix loops with multi-bot feedback handling.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-review`

- **[run-corpus-research](skills/run-corpus-research/)** — Multi-entity evidence-corpus research with per-entity packs.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-corpus-research`

- **[run-github-scout](skills/run-github-scout/)** — Adaptive GitHub repo discovery and shortlisting for concrete needs.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-github-scout`

- **[run-industry-research](skills/run-industry-research/)** — Industry research corpora with evidence packs and comparisons.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-industry-research`

- **[run-issue-tree](skills/run-issue-tree/)** — Plan and execute GitHub-only issue trees with runtime dispatch.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-issue-tree`

- **[run-linear-cli](skills/run-linear-cli/)** — linear-cli for Linear issue lifecycle, bulk creation, and git / PR loops.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-linear-cli`

- **[run-railway](skills/run-railway/)** — Railway CLI commands, workflows, and version-drift routing.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-railway`

- **[run-repo-cleanup](skills/run-repo-cleanup/)** — Sweep dirty tree + unpushed commits + N worktrees into focused private-fork PRs with self-review bodies.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-repo-cleanup`

- **[run-research](skills/run-research/)** — Single-question technical research with source-backed synthesis.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research`

---

## 📦 Publish

Release to a registry.

- **[publish-npm-package](skills/publish-npm-package/)** — npm package releases via GitHub Actions with trusted publishing, provenance, semantic-release, changesets, release-please.
  `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/publish-npm-package`

---

## Notes

- Each installed skill adds to the context window. Install only what you need.
- For the verb taxonomy and naming conventions, read [NAMING.md](NAMING.md).
- For the canonical skill structure and contribution checklist, read [CONTRIBUTING.md](CONTRIBUTING.md).
- The spec this pack follows: [agentskills.io/specification](https://agentskills.io/specification). Discovery paths per Anthropic: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).
- If you see duplicate skill triggers, that's a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills must use a verb from the [12-verb registry](NAMING.md) and pass `python3 scripts/validate-skills.py`.

## License

MIT
