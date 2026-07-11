# build-cloudflare-email-sending

Migrating transactional email to Cloudflare Email Service, replacing Resend/SES/Postmark/Supabase's built-in mailer, wiring a `send_email` Worker binding, or architecting email sending on Cloudflare from scratch.

**Category:** development

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install build-cloudflare-email-sending@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-cloudflare-email-sending
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
