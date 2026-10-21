# skills-by-yigitkonur

30 skills for AI coding agents. They run only when you call them by name: `/skill-name` in Claude Code, `$skill-name` in Codex.

Pick from a list:

```
npx skills add yigitkonur/skills-by-yigitkonur
```

Or install one skill with a command from below. Add `-g` to install for every project, `-a claude-code` or `-a codex` to pick the agent.

Installed through the old plugin marketplace? Remove it (`claude plugin marketplace remove yigitkonur`, or `codex plugin marketplace remove yigitkonur`) and install again with the commands here.

## Skills

### audit-agentic-cli

Audit or design a CLI so agents can drive it: JSON output, exit codes, no prompts.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill audit-agentic-cli
```

### audit-agentic-mcp

Audit or design an MCP server for agents: framework, security, context cost.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill audit-agentic-mcp
```

### audit-completion

Check claimed-done work against evidence: session, plan or branch.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill audit-completion
```

### audit-skill-by-derailment

Test a skill by running an agent on it and reading where it got stuck.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill audit-skill-by-derailment
```

### audit-ui-ux

Audit web or mobile UI/UX from screenshots against design and usability heuristics.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill audit-ui-ux
```

### build-chrome-extension

Build or debug a Chrome MV3 extension.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-chrome-extension
```

### build-cloudflare-access-sso

Protect a subdomain with Cloudflare Access and Google SSO.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-cloudflare-access-sso
```

### build-cloudflare-email-sending

Send email through Cloudflare Email Service instead of Resend, SES or Postmark.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-cloudflare-email-sending
```

### build-kernel-ts-sdk

Build browser automation on the Kernel TypeScript SDK, CLI or MCP server.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-kernel-ts-sdk
```

### build-licenseseat-swift

Add LicenseSeat licensing to a macOS Swift app: activation, validation, seats.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-licenseseat-swift
```

### build-mcp-use-server

Build TypeScript MCP servers and ChatGPT Apps with mcp-use v2.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-mcp-use-server
```

### build-raycast-script-command

Write or fix a Raycast Script Command and its metadata header.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-raycast-script-command
```

### build-skill

Create, redesign or merge an agent skill, with research before writing.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill build-skill
```

### ci-cd-optimize

Speed up slow, flaky or queued CI/CD without weakening required checks.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill ci-cd-optimize
```

### convert-to-natural-writing

Rewrite robotic, AI-sounding text into natural copy, Turkish included.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill convert-to-natural-writing
```

### convert-url-to-nextjs

Rebuild a live URL or HTML snapshot as a pixel-faithful Next.js project.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill convert-url-to-nextjs
```

### init-agent-config

Create, audit or migrate CLAUDE.md, AGENTS.md and REVIEW.md.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill init-agent-config
```

### init-makefiles

Scaffold Makefile targets for dev, tunnels, deploys, R2, Supabase, Railway, Vercel.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill init-makefiles
```

### mobilerun-control

Control or test a connected Android phone with the mobilerun CLI.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill mobilerun-control
```

### optimize-nextjs-fluidity

Audit a Next.js App Router repo for performance and produce a task plan.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill optimize-nextjs-fluidity
```

### publish-npm-package

Publish to npm from GitHub Actions: trusted publishing, provenance.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill publish-npm-package
```

### run-astro-audit

Audit an Astro site and run multi-wave subagent remediation.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill run-astro-audit
```

### run-railway

Use the Railway CLI: deploys, logs, env vars, ssh, database shells.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill run-railway
```

### run-repo-cleanup

Review and merge every branch and worktree into main, then retire the rest.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill run-repo-cleanup
```

### run-ts-cleanup

Clean up a TypeScript codebase: dead code, unused deps, weak types.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill run-ts-cleanup
```

### test-by-maestro

Write, run and debug Maestro E2E flows on iOS, Android and web.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill test-by-maestro
```

### test-by-mcpc-cli

Smoke-test an MCP server with mcpc over stdio or Streamable HTTP.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill test-by-mcpc-cli
```

### update-agent-config

Find stale references and drift in AGENTS.md, CLAUDE.md and REVIEW.md.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill update-agent-config
```

### use-chatgpt-by-applescript

Drive the macOS ChatGPT app with AppleScript for research and extraction.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill use-chatgpt-by-applescript
```

### use-cloudflare-tunnel

Expose localhost through a Cloudflare Tunnel for public URLs and webhooks.

```
npx skills add yigitkonur/skills-by-yigitkonur --skill use-cloudflare-tunnel
```

## License

MIT
