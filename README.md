# skills-by-yigitkonur

51 skills for AI coding agents — code review, planning, research, browser automation, multi-agent orchestration, framework guides, SDK guides, design extraction, and more.

## Install

Add the marketplace to Claude Code (auto-updates on every launch):

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
```

Install a single skill:

```
/plugin install review-pr@yigitkonur-skills
```

Browse all available skills:

```
/plugin
```

<details>
<summary>Legacy npx install (still works)</summary>

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

</details>

## Skills

| Skill | Category | Description |
|---|---|---|
| [build-chrome-extension](skills/build-chrome-extension/) | development | Chrome extensions with Manifest V3 |
| [build-convex-clerk-swiftui](skills/build-convex-clerk-swiftui/) | development | Convex + Clerk backends for SwiftUI iOS/macOS apps |
| [build-copilot-sdk-app](skills/build-copilot-sdk-app/) | development | GitHub Copilot SDK apps in TypeScript |
| [build-daisyui-mcp](skills/build-daisyui-mcp/) | development | daisyUI components via MCP blueprint server |
| [build-hcom-systems](skills/build-hcom-systems/) | orchestration | Multi-agent systems on the hcom backbone |
| [build-langchain-ts-app](skills/build-langchain-ts-app/) | development | LangChain.js agents, RAG, and tool-calling |
| [build-mcp-use-agent](skills/build-mcp-use-agent/) | development | AI agents with mcp-use MCPAgent |
| [build-mcp-use-apps-widgets](skills/build-mcp-use-apps-widgets/) | development | MCP apps with React widget rendering |
| [build-mcp-use-client](skills/build-mcp-use-client/) | development | MCP clients with mcp-use SDK |
| [build-mcp-use-server](skills/build-mcp-use-server/) | development | MCP servers with mcp-use library |
| [build-openclaw-plugin](skills/build-openclaw-plugin/) | platform | OpenClaw plugins and tool registration |
| [build-openclaw-skill](skills/build-openclaw-skill/) | platform | OpenClaw skills with SKILL.md format |
| [build-openclaw-workflow](skills/build-openclaw-workflow/) | platform | OpenClaw automation and Lobster workflows |
| [build-raycast-script-command](skills/build-raycast-script-command/) | development | Raycast Script Commands in Python/Bash |
| [build-skills](skills/build-skills/) | productivity | Claude skill creation methodology |
| [build-supastarter-app](skills/build-supastarter-app/) | development | SupaStarter Next.js SaaS boilerplate |
| [convert-snapshot-nextjs](skills/convert-snapshot-nextjs/) | design | HTML snapshots to Next.js projects |
| [convert-vue-nextjs](skills/convert-vue-nextjs/) | development | Vue/Nuxt to Next.js App Router migration |
| [debug-tauri-devtools](skills/debug-tauri-devtools/) | development | Tauri debugging with CrabNebula DevTools |
| [develop-clean-architecture](skills/develop-clean-architecture/) | development | Clean Architecture and DDD in TypeScript |
| [develop-macos-liquid-glass](skills/develop-macos-liquid-glass/) | development | macOS Liquid Glass design system (Tahoe+) |
| [develop-typebox-fastify](skills/develop-typebox-fastify/) | development | Type-safe Fastify APIs with TypeBox |
| [develop-typescript](skills/develop-typescript/) | development | Strict TypeScript patterns and config |
| [enhance-prompt](skills/enhance-prompt/) | productivity | Turbocharge LLM prompts with steering, halt conditions, and failure pre-emption |
| [enhance-skill-by-derailment](skills/enhance-skill-by-derailment/) | productivity | Skill quality testing via subagent execution and trace analysis |
| [extract-saas-design](skills/extract-saas-design/) | design | SaaS dashboard visual system extraction |
| [init-agent-config](skills/init-agent-config/) | configuration | AGENTS.md and CLAUDE.md generation |
| [init-copilot-review](skills/init-copilot-review/) | productivity | GitHub Copilot review instruction files |
| [init-devin-review](skills/init-devin-review/) | productivity | Devin Bug Catcher review config |
| [init-greptile-review](skills/init-greptile-review/) | productivity | Greptile review config and scoped rules |
| [init-openclaw-agent](skills/init-openclaw-agent/) | platform | OpenClaw agent workspace configuration |
| [optimize-mcp-server](skills/optimize-mcp-server/) | development | MCP server audit and optimization |
| [optimize-swift-linter](skills/optimize-swift-linter/) | development | Swift code quality: SwiftLint, Airbnb rules, macOS/iOS patterns |
| [plan-issue-tree](skills/plan-issue-tree/) | productivity | GitHub Issues with sub-issues and waves |
| [plan-prd](skills/plan-prd/) | productivity | Product requirements documents |
| [plan-work](skills/plan-work/) | productivity | Structured planning and decision-making |
| [publish-npm-package](skills/publish-npm-package/) | development | npm publishing via GitHub Actions |
| [review-pr](skills/review-pr/) | productivity | Systematic pull request review |
| [run-agent-browser](skills/run-agent-browser/) | testing | Browser automation with agent-browser CLI |
| [run-comprehensive-research](skills/run-comprehensive-research/) | orchestration | Multi-domain research orchestrator with parallel agents and structured docs |
| [run-github-repo-evaluate](skills/run-github-repo-evaluate/) | productivity | Deep-evaluate GitHub repos for quality, maturity, and maintainer credibility |
| [run-github-repo-search](skills/run-github-repo-search/) | productivity | Discover GitHub repos via diverse search hypotheses and gh CLI |
| [run-github-scout](skills/run-github-scout/) | productivity | End-to-end GitHub repo discovery, evaluation, and ranking with subagent swarms |
| [run-hcom-agents](skills/run-hcom-agents/) | orchestration | Multi-agent orchestration via hcom |
| [run-issue-plan](skills/run-issue-plan/) | productivity | Execute GitHub Issue tree plans |
| [run-openclaw-agents](skills/run-openclaw-agents/) | platform | OpenClaw multi-agent orchestration |
| [run-openclaw-deploy](skills/run-openclaw-deploy/) | platform | OpenClaw production deployment |
| [run-playwright](skills/run-playwright/) | testing | Browser testing with Playwright CLI |
| [run-research](skills/run-research/) | productivity | Multi-source technical research with web search, Reddit practitioner mining, page scraping, and AI synthesis. Includes 3 reference docs: tool parameters, research workflows, synthesis methods. |
| [run-seo-analysis](skills/run-seo-analysis/) | marketing | SEO workflows with MCP Marketers |
| [test-by-mcpc-cli](skills/test-by-mcpc-cli/) | development | MCP server testing with mcpc CLI |
| [use-skill-dl-util](skills/use-skill-dl-util/) | productivity | Skill search and download via skill-dl |

## Notes

- Each installed skill adds to the context window. Install only what you need.
- Auto-updates run on Claude Code startup via `git pull`. Version bumps in `plugin.json` trigger updates.
- If you see duplicate skill triggers, that is a known Claude Code issue ([#27721](https://github.com/anthropics/claude-code/issues/27721)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
