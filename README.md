# skills-by-yigitkonur

53 skills for AI coding agents. Every skill is **manual-only**: it never shows up in the always-loaded skill list and runs only when you name it (`/skill-name` in Claude Code, `$skill-name` in Codex).

## Install

**Claude Code plugins**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install <skill>@yigitkonur          # one skill
/plugin install yk-everything@yigitkonur    # all of them
```

**Codex plugins**

```bash
codex plugin marketplace add yigitkonur/skills-by-yigitkonur
```

Then install `<skill>@yigitkonur`, or `skills-by-yigitkonur@yigitkonur` for the full pack, from `/plugins`.

**`skills` CLI** (installs to `.agents/skills`, read by Codex, Gemini CLI and Antigravity)

```bash
npx -y skills add yigitkonur/skills-by-yigitkonur -y                      # project, full pack
npx -y skills add yigitkonur/skills-by-yigitkonur/skills/<skill> -y       # project, one skill
npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal      # global, full pack
```

## Skills

| skill | what it does |
|---|---|
| [audit-agentic-cli](skills/audit-agentic-cli/) | auditing or designing a CLI for agent/LLM use — JSON output, exit codes, non-interactive. |
| [audit-agentic-mcp](skills/audit-agentic-mcp/) | auditing or designing an MCP server for agent-readiness — framework, security, context. |
| [audit-completion](skills/audit-completion/) | verifying claimed-done work or auditing session/plan/branch completion with evidence. |
| [audit-skill-by-derailment](skills/audit-skill-by-derailment/) | testing a skill with an agent execution trace; never for ordinary code, PR, or workflow review. |
| [audit-ui-and-save-files](skills/audit-ui-and-save-files/) | auditing a running web app UI across pages/viewports, saving per-bug findings to a tree. |
| [audit-ux-and-save-files](skills/audit-ux-and-save-files/) | auditing a running app's usability via persona journeys, saving per-issue findings to a tree. |
| [audit-ux-laws](skills/audit-ux-laws/) | building or auditing UI against the 30 Laws of UX (Fitts, Hick, Gestalt, cognitive load). |
| [build-chrome-extension](skills/build-chrome-extension/) | building or debugging a Chrome MV3 extension — manifest v3, service_worker, content_scripts. |
| [build-cloudflare-access-sso](skills/build-cloudflare-access-sso/) | protecting a subdomain with Cloudflare Access + Google SSO, or locking an origin against Access bypass. |
| [build-cloudflare-email-sending](skills/build-cloudflare-email-sending/) | sending email via Cloudflare Email Service, replacing Resend/SES/Postmark or send_email. |
| [build-effect-ts-v3](skills/build-effect-ts-v3/) | building TypeScript with Effect-TS v3 — Effect.gen, Layer, Schema, typed errors, Stream. |
| [build-kernel-ts-sdk](skills/build-kernel-ts-sdk/) | building browser-automation apps on the Kernel TS SDK (@onkernel/sdk) — browsers, pools. |
| [build-langchain-ts-app](skills/build-langchain-ts-app/) | building TypeScript apps with langchain/@langchain — agents, RAG, structured output. |
| [build-licenseseat-swift](skills/build-licenseseat-swift/) | integrating the LicenseSeat Swift SDK into a macOS/Swift app — activation, validation, seats. |
| [build-mcp-server-sdk-v1](skills/build-mcp-server-sdk-v1/) | building a TypeScript MCP server on @modelcontextprotocol/sdk v1.x — single-package, Zod. |
| [build-mcp-server-sdk-v2](skills/build-mcp-server-sdk-v2/) | building MCP servers on @modelcontextprotocol/server v2 alpha — split packages, registerTool. |
| [build-mcp-use-agent](skills/build-mcp-use-agent/) | building TypeScript mcp-use MCPAgent code where an LLM orchestrates MCP tools (run/stream). |
| [build-mcp-use-client](skills/build-mcp-use-client/) | writing TypeScript mcp-use MCP client code — MCPClient, MCPSession, useMcp, mcp-use/react. |
| [build-mcp-use-server](skills/build-mcp-use-server/) | you are building TypeScript MCP servers with mcp-use v2 — MCPServer tools, views (MCP Apps), oauth providers, streamable HTTP, deploys, or… |
| [build-raycast-script-command](skills/build-raycast-script-command/) | authoring or fixing a Raycast Script Command (@raycast.* metadata header) — fields, modes. |
| [build-sentry-macos-swift](skills/build-sentry-macos-swift/) | adding or auditing Sentry crash reporting in a macOS/Swift app — dSYM, breadcrumbs, tracing. |
| [build-skill](skills/build-skill/) | creating, redesigning, or merging a Claude skill, with research before writing SKILL.md. |
| [build-tinacms-nextjs](skills/build-tinacms-nextjs/) | building a TinaCMS + Next.js App Router site — tina/config.ts, MDX content, useTina editing. |
| [ci-cd-optimize](skills/ci-cd-optimize/) | you are diagnosing or optimizing slow, flaky, queued, expensive, or cache-inefficient CI/CD pipelines, or waiting on remote runs, while preserving… |
| [convert-mcp-sdk-v1-to-v2](skills/convert-mcp-sdk-v1-to-v2/) | porting an MCP TypeScript server from @modelcontextprotocol/sdk v1.x to the v2 SDK. |
| [convert-to-natural-writing](skills/convert-to-natural-writing/) | you are humanizing or rewriting AI-sounding, robotic, or generic text, Markdown, MDX, or HTML into natural multilingual copy; not… |
| [convert-url-to-nextjs](skills/convert-url-to-nextjs/) | rebuilding a live URL or .html snapshot as a pixel-faithful AS-IS Next.js project. |
| [deploy-coolify-cloud](skills/deploy-coolify-cloud/) | deploying/updating a docker-compose service on Coolify Cloud via its API — domains, env. |
| [herdr](skills/herdr/) | controlling interactive coding agents, tabs, worktrees, or session lifecycle through Herdr CLI. |
| [init-agent-config](skills/init-agent-config/) | creating, auditing, or migrating CLAUDE.md/AGENTS.md/REVIEW.md instruction files. |
| [init-jean-json](skills/init-jean-json/) | onboarding a repo to Jean — jean.json and .worktreeinclude setup, run, teardown, ports. |
| [init-makefiles](skills/init-makefiles/) | scaffolding Makefile targets for dev, tunnels, deploys, R2, Supabase, Railway, Vercel. |
| [mobilerun-control](skills/mobilerun-control/) | controlling or testing a connected Android phone via the mobilerun CLI — tap, type, swipe. |
| [optimize-nextjs-fluidity](skills/optimize-nextjs-fluidity/) | auditing and optimizing a Next.js App Router repo for performance and fluidity, producing a version-gated task plan the agent then executes. |
| [publish-npm-package](skills/publish-npm-package/) | publishing to npm via GitHub Actions — trusted publishing, provenance, semantic-release. |
| [run-agent-browser](skills/run-agent-browser/) | driving agent-browser for webpage interaction, screenshots, @ref snapshots, tabs, UI verification, CDP attach, Steel Browser, or cloud providers… |
| [run-agent-device](skills/run-agent-device/) | testing or debugging an iOS app via agent-device CLI — simulator flows, evidence, bug triage. |
| [run-agentic-tests](skills/run-agentic-tests/) | orchestrating multi-agent E2E campaigns with independent evidence review, isolated runtimes, and defect fix/retest loops. |
| [run-astro-audit](skills/run-astro-audit/) | conducting comprehensive Astro audits, running multi-wave subagent remediation, validating AST rules with Astro Sentinel, or managing serial merge… |
| [run-deep-research](skills/run-deep-research/) | running deep multi-file research over 5+ entities or a market — wave-dispatched corpus. |
| [run-railway](skills/run-railway/) | running railway CLI — deploys, logs, env vars, link, ssh, db shells, scaling. |
| [run-repo-cleanup](skills/run-repo-cleanup/) | finishing a project — review and merge every branch/worktree into main, retire dead branches. |
| [run-research](skills/run-research/) | you are researching one current technical question with source-grounded web evidence. Do not use for five-plus-entity corpora, GitHub-repository… |
| [run-testsprite-backend](skills/run-testsprite-backend/) | you are creating, debugging, running, or managing credentials for TestSprite backend API tests against deployed services; not frontend, load,… |
| [run-testsprite-frontend](skills/run-testsprite-frontend/) | you are creating, running, debugging, or release-gating TestSprite frontend browser tests, including public-target CLI or localhost MCP routing;… |
| [run-ts-cleanup](skills/run-ts-cleanup/) | cleaning up a TypeScript codebase — dead code, unused deps, AI slop, weak types. |
| [test-by-maestro](skills/test-by-maestro/) | writing, running, or debugging Maestro mobile E2E tests on iOS Simulators or Android. |
| [test-by-mcpc-cli](skills/test-by-mcpc-cli/) | you are driving mcpc 0.7.x to test or smoke-check an MCP server over stdio or Streamable HTTP. |
| [update-agent-config](skills/update-agent-config/) | auditing AGENTS.md/CLAUDE.md/REVIEW.md for drift after refactors — stale refs, rules. |
| [upgrade-typescript-go](skills/upgrade-typescript-go/) | upgrading a TypeScript project to the native Go compiler (TypeScript 7.0+ / tsgo) — preflight audit, tsconfig modernization, Compiler API… |
| [use-chatgpt-by-applescript](skills/use-chatgpt-by-applescript/) | driving macOS ChatGPT desktop app via AppleScript or SSH to run web research, computer actions, status checks, or markdown extraction. |
| [use-cloudflare-tunnel](skills/use-cloudflare-tunnel/) | exposing localhost ports or multi-service apps via Cloudflare Tunnel for public URLs, remote testing, webhooks, or previewing without port forwarding. |
| [use-sentry](skills/use-sentry/) | initializing Sentry from scratch, auditing an existing setup across 4 pillars, or triaging production errors with token-efficient CLI recipes. |

## Notes

- Metadata (`.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/`, `plugins/`) is generated from `skills/` by `python3 scripts/gen-marketplace.py`; do not hand-edit it.
- Every skill ships `disable-model-invocation: true` in `SKILL.md` and `agents/openai.yaml` with `policy.allow_implicit_invocation: false` (Codex ignores the frontmatter key).
- Naming rules: [NAMING.md](NAMING.md). Structure and checklist: [CONTRIBUTING.md](CONTRIBUTING.md). Spec: [agentskills.io](https://agentskills.io/specification).

## License

MIT
