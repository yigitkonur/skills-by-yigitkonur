# deploy-coolify-cloud

Deploying a docker-compose service to Coolify Cloud via the API — create/update services, wire project/environment/server, and verify the container actually came up.

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
