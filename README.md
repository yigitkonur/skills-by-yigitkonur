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
| [build-copilot-sdk-app](skills/build-copilot-sdk-app/) | development | GitHub Copilot SDK apps in TypeScript |
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
| [build-tinacms-nextjs](skills/build-tinacms-nextjs/) | development | Next.js App Router sites with TinaCMS — git-backed MDX, schemas, visual editing, dynamic pages |
| [check-completion](skills/check-completion/) | productivity | Check what's done vs. claimed done via a 22-status taxonomy; remediate until every in-scope task reaches a terminal status |
| [convert-mcp-server-sdk-v1-to-v2](skills/convert-mcp-server-sdk-v1-to-v2/) | development | Port v1 MCP servers to the v2 split-package SDK |
| [convert-url-to-nextjs](skills/convert-url-to-nextjs/) | design | Live URLs or HTML snapshots to Next.js projects |
| [do-debug](skills/do-debug/) | productivity | Language-agnostic systematic debugging; four phases + Iron Law + 3-fails handoff to do-think Interactive |
| [do-review](skills/do-review/) | productivity | Systematic pull request review |
| [do-think](skills/do-think/) | productivity | Deep-thinking framework — Solo or user-in-the-loop Interactive modes; 4-phase loop with mandatory stress-test trio |
| [enhance-prompt](skills/enhance-prompt/) | productivity | Turbocharge LLM prompts with steering, halt conditions, and failure pre-emption |
| [enhance-skill-by-derailment](skills/enhance-skill-by-derailment/) | productivity | Skill quality testing via subagent execution and trace analysis |
| [evaluate-code-review](skills/evaluate-code-review/) | productivity | Evaluate PR/session/markdown review feedback with verify-before-implement discipline and multi-agent consolidation |
| [extract-saas-design](skills/extract-saas-design/) | design | SaaS dashboard visual system extraction |
| [init-agent-config](skills/init-agent-config/) | configuration | AGENTS + REVIEW standardization hierarchies |
| [make-local](skills/make-local/) | workflow | `make local` / `make tunnel` for Next.js/Node — Tailscale Serve, portless, LAN bind |
| [make-railway](skills/make-railway/) | workflow | `make prod` Railway deploy with parallel multi-service uploads + git-hook CI/CD |
| [make-vercel](skills/make-vercel/) | workflow | `make deploy` Vercel with find-or-create, env scoping, 50MB function limit |
| [optimize-agentic-cli](skills/optimize-agentic-cli/) | development | Audit or design agent-ready CLIs with iterative feedback loops |
| [optimize-agentic-mcp](skills/optimize-agentic-mcp/) | development | Audit, optimize, or architect new MCP servers |
| [publish-npm-package](skills/publish-npm-package/) | development | npm publishing via GitHub Actions |
| [run-agent-browser](skills/run-agent-browser/) | testing | Browser automation with agent-browser CLI |
| [run-batch-codex-research](skills/run-batch-codex-research/) | orchestration | Fan out codex (or another LLM CLI) over N inputs in parallel with idempotent retry |
| [run-codex-exec](skills/run-codex-exec/) | orchestration | Parallel codex exec agents in git worktrees with auto-commit + live monitor |
| [run-codex-review](skills/run-codex-review/) | orchestration | Per-branch /codex:review fix loops + /ask-review PR + codex rescue + multi-bot /do-review evaluation |
| [run-github-scout](skills/run-github-scout/) | productivity | Adaptive GitHub repo discovery and shortlisting for concrete needs |
| [run-industry-research](skills/run-industry-research/) | productivity | Industry research corpora with evidence packs and comparisons |
| [run-issue-tree](skills/run-issue-tree/) | productivity | Plan and execute GitHub Issue trees with sub-issues and waves |
| [run-playwright](skills/run-playwright/) | testing | Browser testing with Playwright CLI |
| [run-repo-cleanup](skills/run-repo-cleanup/) | productivity | Sweep dirty tree + unpushed commits + N worktrees into focused private-fork PRs with self-review bodies |
| [run-research](skills/run-research/) | productivity | Technical research with web search, Reddit mining, and multi-agent orchestration |
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
