# skills-by-yigitkonur

44 skills for AI coding agents -- code review, planning, research, browser automation, multi-agent orchestration, framework guides, SDK guides, design extraction, and more.

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
| [apply-clean-architecture](skills/apply-clean-architecture/) | development | Clean Architecture and DDD in TypeScript |
| [apply-liquid-glass](skills/apply-liquid-glass/) | development | macOS Liquid Glass design system (Tahoe+) |
| [apply-macos-hig](skills/apply-macos-hig/) | development | macOS HIG design system -- spacing, components, accessibility |
| [ask-review](skills/ask-review/) | productivity | Hand off work as a PR with domain-aware self-review, or produce a markdown review doc |
| [build-chrome-extension](skills/build-chrome-extension/) | development | Chrome extensions with Manifest V3 |
| [build-convex-clerk-swiftui](skills/build-convex-clerk-swiftui/) | development | Convex + Clerk backends for SwiftUI iOS/macOS apps |
| [build-copilot-sdk-app](skills/build-copilot-sdk-app/) | development | GitHub Copilot SDK apps in TypeScript |
| [build-langchain-ts-app](skills/build-langchain-ts-app/) | development | LangChain.js agents, RAG, and tool-calling |
| [build-mcp-server-sdk-v1](skills/build-mcp-server-sdk-v1/) | development | MCP servers with @modelcontextprotocol/sdk v1.x |
| [build-mcp-server-sdk-v2](skills/build-mcp-server-sdk-v2/) | development | MCP servers with @modelcontextprotocol/server v2 |
| [build-mcp-use-agent](skills/build-mcp-use-agent/) | development | AI agents with mcp-use MCPAgent |
| [build-mcp-use-apps-widgets](skills/build-mcp-use-apps-widgets/) | development | MCP apps with React widget rendering |
| [build-mcp-use-client](skills/build-mcp-use-client/) | development | MCP clients with mcp-use SDK |
| [build-mcp-use-server](skills/build-mcp-use-server/) | development | MCP servers with mcp-use library |
| [build-raycast-script-command](skills/build-raycast-script-command/) | development | Raycast Script Commands in Python/Bash |
| [build-skills](skills/build-skills/) | productivity | Claude skill creation and research methodology |
| [build-supastarter-app](skills/build-supastarter-app/) | development | SupaStarter Next.js SaaS boilerplate |
| [check-completion](skills/check-completion/) | productivity | Check what's done vs. claimed done via a 22-status taxonomy; remediate until every in-scope task reaches a terminal status |
| [convert-url-to-nextjs](skills/convert-url-to-nextjs/) | design | Live URLs or HTML snapshots to Next.js projects |
| [develop-typescript](skills/develop-typescript/) | development | Strict TypeScript patterns and config |
| [do-brainstorm](skills/do-brainstorm/) | productivity | Framework-aware, user-in-the-loop brainstorming; Cynefin-first classifier routes across 25 mental models |
| [do-debug](skills/do-debug/) | productivity | Language-agnostic systematic debugging; four phases + Iron Law + 3-fails handoff to do-brainstorm |
| [do-review](skills/do-review/) | productivity | Systematic pull request review |
| [do-think](skills/do-think/) | productivity | Generic deep-thinking framework for hard tasks |
| [enhance-prompt](skills/enhance-prompt/) | productivity | Turbocharge LLM prompts with steering, halt conditions, and failure pre-emption |
| [enhance-skill-by-derailment](skills/enhance-skill-by-derailment/) | productivity | Skill quality testing via subagent execution and trace analysis |
| [evaluate-code-review](skills/evaluate-code-review/) | productivity | Evaluate PR/session/markdown review feedback with verify-before-implement discipline and multi-agent consolidation |
| [extract-saas-design](skills/extract-saas-design/) | design | SaaS dashboard visual system extraction |
| [init-agent-config](skills/init-agent-config/) | configuration | AGENTS + REVIEW standardization hierarchies |
| [optimize-agentic-cli](skills/optimize-agentic-cli/) | development | Audit or design agent-ready CLIs with iterative feedback loops |
| [optimize-agentic-mcp](skills/optimize-agentic-mcp/) | development | Audit, optimize, or architect new MCP servers |
| [publish-npm-package](skills/publish-npm-package/) | development | npm publishing via GitHub Actions |
| [run-agent-browser](skills/run-agent-browser/) | testing | Browser automation with agent-browser CLI |
| [run-athena-flow](skills/run-athena-flow/) | orchestration | Athena Flow CLI for AI workflow orchestration |
| [run-codex-bridge](skills/run-codex-bridge/) | orchestration | Orchestrate Codex coding agents with codex-worker |
| [run-codex-exec](skills/run-codex-exec/) | orchestration | Parallel codex exec agents in git worktrees with auto-commit + live monitor |
| [run-github-scout](skills/run-github-scout/) | productivity | End-to-end GitHub repo discovery, evaluation, and ranking with subagent swarms |
| [run-issue-tree](skills/run-issue-tree/) | productivity | Plan and execute GitHub Issue trees with sub-issues and waves |
| [run-playwright](skills/run-playwright/) | testing | Browser testing with Playwright CLI |
| [run-research](skills/run-research/) | productivity | Technical research with web search, Reddit mining, and multi-agent orchestration |
| [swift-quality-hooks](skills/swift-quality-hooks/) | development | Swift pre-commit hook with SwiftLint + SwiftFormat for Apple platforms |
| [test-by-mcpc-cli](skills/test-by-mcpc-cli/) | development | MCP server testing with mcpc 0.2.x |
| [test-macos-snapshots](skills/test-macos-snapshots/) | testing | macOS app screenshot validation and drift checks |
| [use-railway](skills/use-railway/) | platform | Railway CLI commands, workflows, and version-drift routing |

## Notes

- Each installed skill adds to the context window. Install only what you need.
- If you see duplicate skill triggers, that is a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
