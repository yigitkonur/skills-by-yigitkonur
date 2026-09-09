# use-cloudflare-tunnel

Expose localhost ports and multi-service apps (frontend SPA + backend APIs) to the internet via Cloudflare Tunnel. Use when you need public URLs for local development, remote browser testing (ego-browser), mobile viewport testing, external webhooks (Stripe/GitHub), or sharing live previews without port forwarding.

**Category:** development

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install use-cloudflare-tunnel@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/use-cloudflare-tunnel
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
