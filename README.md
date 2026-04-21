# skills-by-yigitkonur

54 skills for AI coding agents -- code review, planning, research, browser automation, multi-agent orchestration, framework guides, SDK guides, design extraction, and more.

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
| [check-completion](skills/check-completion/) | productivity | Check what's done vs. claimed done via a 22-status taxonomy; remediate until every in-scope task reaches a terminal status |
| [do-brainstorm](skills/do-brainstorm/) | productivity | Framework-aware, user-in-the-loop brainstorming; Cynefin-first classifier routes across 25 mental models |
| [optimize-cli-for-agents](skills/optimize-cli-for-agents/) | development | Audit or design agent-ready CLIs with iterative feedback loops |
| [build-chrome-extension](skills/build-chrome-extension/) | development | Chrome extensions with Manifest V3 |
| [build-convex-clerk-swiftui](skills/build-convex-clerk-swiftui/) | development | Convex + Clerk backends for SwiftUI iOS/macOS apps |
| [build-copilot-sdk-app](skills/build-copilot-sdk-app/) | development | GitHub Copilot SDK apps in TypeScript |
| [build-daisyui-mcp](skills/build-daisyui-mcp/) | development | daisyUI components via MCP blueprint server |
| [build-hcom-systems](skills/build-hcom-systems/) | orchestration | Multi-agent systems on the hcom backbone |
| [build-langchain-ts-app](skills/build-langchain-ts-app/) | development | LangChain.js agents, RAG, and tool-calling |
| [build-mcp-sdk](skills/build-mcp-sdk/) | development | MCP servers with @modelcontextprotocol/sdk v1.x |
| [build-mcp-sdk-v2](skills/build-mcp-sdk-v2/) | development | MCP servers with @modelcontextprotocol/server v2 |
| [build-mcp-use-agent](skills/build-mcp-use-agent/) | development | AI agents with mcp-use MCPAgent |
| [build-mcp-use-apps-widgets](skills/build-mcp-use-apps-widgets/) | development | MCP apps with React widget rendering |
| [build-mcp-use-client](skills/build-mcp-use-client/) | development | MCP clients with mcp-use SDK |
| [build-mcp-use-server](skills/build-mcp-use-server/) | development | MCP servers with mcp-use library |
| [build-openclaw-plugin](skills/build-openclaw-plugin/) | platform | OpenClaw plugins and tool registration |
| [build-openclaw-skill](skills/build-openclaw-skill/) | platform | OpenClaw skills with SKILL.md format |
| [build-openclaw-workflow](skills/build-openclaw-workflow/) | platform | OpenClaw automation and Lobster workflows |
| [build-raycast-script-command](skills/build-raycast-script-command/) | development | Raycast Script Commands in Python/Bash |
| [build-skills](skills/build-skills/) | productivity | Claude skill creation and research methodology |
| [build-supastarter-app](skills/build-supastarter-app/) | development | SupaStarter Next.js SaaS boilerplate |
| [convert-snapshot-nextjs](skills/convert-snapshot-nextjs/) | design | HTML snapshots to Next.js projects |
| [convert-vue-nextjs](skills/convert-vue-nextjs/) | development | Vue/Nuxt to Next.js App Router migration |
| [debug-tauri-devtools](skills/debug-tauri-devtools/) | development | Tauri debugging with CrabNebula DevTools |
| [develop-clean-architecture](skills/develop-clean-architecture/) | development | Clean Architecture and DDD in TypeScript |
| [develop-macos-hig](skills/develop-macos-hig/) | development | macOS HIG design system -- spacing, components, accessibility |
| [develop-macos-liquid-glass](skills/develop-macos-liquid-glass/) | development | macOS Liquid Glass design system (Tahoe+) |
| [develop-typescript](skills/develop-typescript/) | development | Strict TypeScript patterns and config |
| [enhance-prompt](skills/enhance-prompt/) | productivity | Turbocharge LLM prompts with steering, halt conditions, and failure pre-emption |
| [enhance-skill-by-derailment](skills/enhance-skill-by-derailment/) | productivity | Skill quality testing via subagent execution and trace analysis |
| [evaluate-code-review](skills/evaluate-code-review/) | productivity | Evaluate PR/session/markdown review feedback with verify-before-implement discipline and multi-agent consolidation |
| [extract-saas-design](skills/extract-saas-design/) | design | SaaS dashboard visual system extraction |
| [init-agent-config](skills/init-agent-config/) | configuration | AGENTS + REVIEW standardization hierarchies |
| [init-openclaw-agent](skills/init-openclaw-agent/) | platform | OpenClaw agent workspace configuration |
| [optimize-mcp-server](skills/optimize-mcp-server/) | development | Audit, optimize, or architect new MCP servers |
| [publish-npm-package](skills/publish-npm-package/) | development | npm publishing via GitHub Actions |
| [request-code-review](skills/request-code-review/) | productivity | Hand off work as a PR with domain-aware self-review, or produce a markdown review doc |
| [review-pr](skills/review-pr/) | productivity | Systematic pull request review |
| [run-agent-browser](skills/run-agent-browser/) | testing | Browser automation with agent-browser CLI |
| [run-athena-flow](skills/run-athena-flow/) | orchestration | Athena Flow CLI for AI workflow orchestration |
| [run-codex-exec](skills/run-codex-exec/) | orchestration | Parallel codex exec agents in git worktrees with auto-commit + live monitor |
| [run-codex-subagents](skills/run-codex-subagents/) | orchestration | Orchestrate Codex coding agents with codex-worker |
| [run-github-scout](skills/run-github-scout/) | productivity | End-to-end GitHub repo discovery, evaluation, and ranking with subagent swarms |
| [run-hcom-agents](skills/run-hcom-agents/) | orchestration | Multi-agent orchestration via hcom |
| [run-issue-tree](skills/run-issue-tree/) | productivity | Plan and execute GitHub Issue trees with sub-issues and waves |
| [run-openclaw-agents](skills/run-openclaw-agents/) | platform | OpenClaw multi-agent orchestration |
| [run-openclaw-deploy](skills/run-openclaw-deploy/) | platform | OpenClaw production deployment |
| [run-playwright](skills/run-playwright/) | testing | Browser testing with Playwright CLI |
| [run-research](skills/run-research/) | productivity | Technical research with web search, Reddit mining, and multi-agent orchestration |
| [swift-quality-hooks](skills/swift-quality-hooks/) | development | Swift pre-commit hook with SwiftLint + SwiftFormat for Apple platforms |
| [test-by-mcpc-cli](skills/test-by-mcpc-cli/) | development | MCP server testing with mcpc 0.2.x |
| [test-macos-snapshots](skills/test-macos-snapshots/) | testing | macOS app screenshot validation and drift checks |
| [think-deeper](skills/think-deeper/) | productivity | Generic deep-thinking framework for hard tasks |
| [use-railway](skills/use-railway/) | platform | Railway CLI commands, workflows, and version-drift routing |

## Notes

- Each installed skill adds to the context window. Install only what you need.
- If you see duplicate skill triggers, that is a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
