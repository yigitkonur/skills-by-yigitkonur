# skills-by-yigitkonur

Skills for AI coding agents -- code review, planning, research, browser automation, multi-agent orchestration, framework guides, SDK guides, design extraction, and more.

## Install

Install all skills at once:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

Install a single skill:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

## Skills

| Skill | Category | Description |
|---|---|---|
| [apply-clean-mcp-architecture](skills/apply-clean-mcp-architecture/) | development | Clean Architecture standard for TypeScript MCP servers — folder layout, layer boundaries, mcp-use placement, TS quality |
| [ask-review](skills/ask-review/) | productivity | Hand off work as a PR with domain-aware self-review, or produce a markdown review doc |
| [build-chrome-extension](skills/build-chrome-extension/) | development | Chrome extensions with Manifest V3 |
| [build-effect-ts-v3](skills/build-effect-ts-v3/) | development | Effect-TS v3 apps — typed errors, services, layers, Schema, Stream, HTTP, SQL |
| [build-kernel-ts-sdk](skills/build-kernel-ts-sdk/) | development | Build browser-automation agents and apps with the Kernel TypeScript SDK |
| [build-langchain-ts-app](skills/build-langchain-ts-app/) | development | LangChain.js agents, RAG, and tool-calling |
| [build-macos-app](skills/build-macos-app/) | development | Production-grade macOS SwiftUI/AppKit — HIG, Liquid Glass, snapshots, hooks, Convex+Clerk |
| [build-mcp-server-sdk-v1](skills/build-mcp-server-sdk-v1/) | development | MCP servers with @modelcontextprotocol/sdk v1.x |
| [build-mcp-server-sdk-v2](skills/build-mcp-server-sdk-v2/) | development | MCP servers with @modelcontextprotocol/server v2 |
| [build-mcp-use-agent](skills/build-mcp-use-agent/) | development | AI agents with mcp-use MCPAgent |
| [build-mcp-use-client](skills/build-mcp-use-client/) | development | MCP clients with mcp-use SDK |
| [build-mcp-use-server](skills/build-mcp-use-server/) | development | MCP servers with mcp-use — tools, schemas, responses, auth, sessions, transports, MCP Apps widgets, ChatGPT Apps, Inspector, deploy |
| [build-raycast-script-command](skills/build-raycast-script-command/) | development | Raycast Script Commands in Python/Bash |
| [build-tinacms-nextjs](skills/build-tinacms-nextjs/) | development | TinaCMS-backed App Router sites with MDX, schemas, visual editing |
| [check-completion](skills/check-completion/) | productivity | Audit task/session/plan/branch completion claims; remediate to terminal status |
| [convert-mcp-server-sdk-v1-to-v2](skills/convert-mcp-server-sdk-v1-to-v2/) | development | Port v1 MCP servers to the v2 split-package SDK |
| [convert-url-to-nextjs](skills/convert-url-to-nextjs/) | design | Live URLs or HTML snapshots to Next.js projects |
| [do-debug](skills/do-debug/) | productivity | Language-agnostic systematic debugging; four phases + Iron Law + 3-fails handoff to do-think Interactive |
| [do-review](skills/do-review/) | productivity | Review PRs and branch diffs for merge readiness |
| [do-think](skills/do-think/) | productivity | Deep thinking for ambiguous plans, architecture, refactors, or choices |
| [do-ui-audit](skills/do-ui-audit/) | productivity | Visual UI audit across pages and viewports with browser screenshots |
| [enhance-skill-by-derailment](skills/enhance-skill-by-derailment/) | productivity | Skill quality testing via subagent execution and trace analysis |
| [evaluate-code-review](skills/evaluate-code-review/) | productivity | Triage received human, bot, markdown, or multi-reviewer feedback |
| [extract-saas-design](skills/extract-saas-design/) | design | SaaS dashboard visual system extraction |
| [init-agent-config](skills/init-agent-config/) | configuration | AGENTS-first instruction and review-context hierarchies |
| [init-makefiles](skills/init-makefiles/) | workflow | Scaffold safe scenario Makefiles (Vercel default; Cloudflare Pages opt-in), R2 bulk upload via rclone, AGENTS sync, optional deploy CI |
| [optimize-agentic-cli](skills/optimize-agentic-cli/) | development | Audit and design agent-ready CLI contracts |
| [optimize-agentic-mcp](skills/optimize-agentic-mcp/) | development | Audit, optimize, and architect MCP servers for agent-readiness |
| [orchestrate-codex](skills/orchestrate-codex/) | orchestration | Drive codex CLI fleets, batches, review loops, and rescue |
| [publish-npm-package](skills/publish-npm-package/) | development | npm package releases via GitHub Actions |
| [run-agent-browser](skills/run-agent-browser/) | testing | Browser automation with agent-browser CLI |
| [run-github-scout](skills/run-github-scout/) | productivity | Adaptive GitHub repo discovery and shortlisting for concrete needs |
| [run-industry-research](skills/run-industry-research/) | productivity | Industry research corpora with evidence packs and comparisons |
| [run-issue-tree](skills/run-issue-tree/) | productivity | Plan and execute GitHub-only issue trees with runtime dispatch |
| [run-repo-cleanup](skills/run-repo-cleanup/) | productivity | Sweep dirty tree + unpushed commits + N worktrees into focused private-fork PRs with self-review bodies |
| [run-research](skills/run-research/) | productivity | Single-question technical research with source-backed synthesis |
| [synthesize-skills](skills/synthesize-skills/) | productivity | Claude skill creation and research methodology |
| [test-by-mcpc-cli](skills/test-by-mcpc-cli/) | development | MCP server testing with mcpc 0.2.x |
| [use-linear-cli](skills/use-linear-cli/) | platform | linear-cli for Linear issue lifecycle, bulk creation, and git/PR loops |
| [use-railway](skills/use-railway/) | platform | Railway CLI commands, workflows, and version-drift routing |

## Notes

- Each installed skill adds to the context window. Install only what you need.
- If you see duplicate skill triggers, that is a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
