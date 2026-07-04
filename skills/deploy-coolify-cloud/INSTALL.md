# deploy-coolify-cloud

Deploying or updating a docker-compose service on Coolify Cloud via the API — wiring project/server, custom domains + TLS, cross-service networking, env-var secrets, and verifying the container actually came up.

**Category:** platform

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install deploy-coolify-cloud@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/deploy-coolify-cloud
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
