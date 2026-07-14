# run-tailscale-funnel

Exposing a local HTTP server at a public `.ts.net` URL via Tailscale Funnel for agent-browser navigation, mobile testing, webhooks, or shared dev demos.

**Category:** platform

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-tailscale-funnel@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-tailscale-funnel
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
