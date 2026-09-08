# build-cloudflare-access-sso

Putting Cloudflare Access with Google SSO in front of a subdomain, restricting an internal tool or dashboard to one email domain, configuring the Google OAuth client and consent screen for it, or locking an origin so Access cannot be bypassed by IP.

**Category:** development

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install build-cloudflare-access-sso@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-cloudflare-access-sso
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
