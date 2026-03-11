---
name: build-supastarter-app
description: Use skill if you are building or extending a Supastarter app and need project-grounded patterns for routing, auth, API, billing, UI, storage, or deployment.
---

# Build Supastarter App

Use this skill when you need to change or extend a Supastarter-based Next.js SaaS app and you want the implementation to match the real codebase instead of generic boilerplate patterns.

## What this skill gives you

- the **actual monorepo structure** used by this project
- the **real App Router layout and provider chain**
- the **exact oRPC + Better Auth + Prisma/Drizzle patterns** used in production code
- grounded references for **payments (Stripe, Polar, Creem, Dodo Payments), organizations, settings, onboarding, marketing, mail, storage, analytics, and deployment**
- task-specific guides for **adding endpoints, pages, models, and billing flows**

## How to use this skill

Keep this file lean and use the reference docs on demand.

### Default workflow

1. Read the brief and classify the change:
   - setup/config
   - routing/layout
   - API/backend
   - auth/organizations
   - database/payments
   - UI/forms
   - marketing/content
   - deployment
2. Open the matching reference files from the lists below.
3. Copy the **existing pattern** instead of inventing a new one.
4. Prefer the task guides in `references/tasks/` when the request is implementation-oriented.
5. Use the cheatsheets for commands, imports, file locations, and env vars.

## Start here first

If you are new to the codebase, read these in order:

1. `references/setup/monorepo-structure.md`
2. `references/setup/import-conventions.md`
3. `references/setup/config-feature-flags.md`
4. `references/conventions/typescript-patterns.md`
5. `references/conventions/component-patterns.md`
6. `references/cheatsheets/file-locations.md`

That gives you the repo shape, imports, config switches, TS/component conventions, and where new files belong.

## Quick architecture map

### App structure

- `apps/web` — Next.js App Router app
- `packages/api` — Hono + oRPC API surface
- `packages/auth` — Better Auth setup
- `packages/database` — Prisma schema, client, queries, generated artifacts
- `packages/payments` — billing config, provider abstraction (Stripe, Polar, Creem, Dodo Payments)
- `packages/mail` — email rendering and delivery
- `packages/storage` — S3-compatible signed URLs
- `packages/ui` — reusable UI components

### Route groups

- marketing pages live under `apps/web/app/(marketing)/[locale]`
- protected product routes live under `apps/web/app/(saas)`
- `/app/**` gets the full SaaS provider + guard chain

For the actual nesting and providers, read:

- `references/routing/routing-marketing.md`
- `references/routing/routing-saas.md`
- `references/routing/layout-chain.md`
- `references/routing/access-guards.md`
- `references/routing/providers-document.md`
- `references/routing/middleware-proxy.md`

## Reference map by task

### Setup, repo shape, and conventions

Read these when you need global orientation or project-wide rules:

- `references/setup/environment-setup.md`
- `references/setup/monorepo-structure.md`
- `references/setup/import-conventions.md`
- `references/setup/config-feature-flags.md`
- `references/setup/next-config.md`
- `references/setup/tooling-biome.md`
- `references/conventions/naming.md`
- `references/conventions/typescript-patterns.md`
- `references/conventions/component-patterns.md`
- `references/conventions/code-review-checklist.md`

Use the cheatsheets when you need a fast answer:

- `references/cheatsheets/commands.md`
- `references/cheatsheets/imports.md`
- `references/cheatsheets/file-locations.md`
- `references/cheatsheets/env-vars.md`

### Routing, layouts, guards, and shell

Read these when the task involves pages, providers, redirects, auth gates, or dashboard chrome:

- `references/routing/routing-marketing.md`
- `references/routing/routing-saas.md`
- `references/routing/layout-chain.md`
- `references/routing/access-guards.md`
- `references/routing/providers-document.md`
- `references/routing/middleware-proxy.md`

### API work

Read these when adding or changing backend procedures or client integrations:

- `references/api/overview.md`
- `references/api/procedure-tiers.md`
- `references/api/root-router.md`
- `references/api/transport-handlers.md`
- `references/api/next-route-bridge.md`
- `references/api/client-integration.md`
- `references/api/contact-module.md`
- `references/api/payments-organizations-modules.md`

### Authentication and session behavior

Read these when changing login, signup, session access, org invitations, or auth feature flags:

- `references/auth/overview.md`
- `references/auth/better-auth-config.md`
- `references/auth/feature-flags.md`
- `references/auth/client-auth-client.md`
- `references/auth/server-session-helpers.md`
- `references/auth/session-hook-provider.md`
- `references/auth/login-flow.md`
- `references/auth/signup-invitations.md`

### Database and query layer

Read these before touching schema, ORM client usage, or shared queries. Supastarter defaults to Prisma but also supports Drizzle as an alternative ORM:

- `references/database/schema-overview.md`
- `references/database/prisma-client.md`
- `references/database/query-patterns.md`
- `references/database/users-organizations-purchases.md`
- `references/database/generation-exports.md`

### Payments and billing

Read these when changing plans, checkout flows, customer IDs, payment provider logic, or purchase resolution. The provider abstraction supports Stripe, Polar, Creem, and Dodo Payments:

- `references/payments/plans-config.md`
- `references/payments/provider-abstraction.md`
- `references/payments/stripe-provider.md`
- `references/payments/customer-ids.md`
- `references/payments/checkout-and-portal-flow.md`
- `references/payments/webhook-flow.md`

### Organizations, onboarding, settings, and admin

Read these for multi-tenant UX, post-signup flows, and admin management:

- `references/organizations/active-organization-context.md`
- `references/organizations/organization-select.md`
- `references/organizations/create-organization-form.md`
- `references/organizations/members-and-invitations.md`
- `references/onboarding/onboarding-flow.md`
- `references/onboarding/onboarding-step-one.md`
- `references/settings/account-settings.md`
- `references/settings/billing-security-and-avatar.md`
- `references/hooks/auth-hooks.md`
- `references/hooks/organization-hooks.md`
- `references/hooks/consent-hooks.md`
- `references/admin/users-admin.md`
- `references/admin/organizations-admin.md`

### UI, forms, analytics, and client patterns

Read these when building interactive client components:

- `references/ui/components.md`
- `references/ui/forms.md`
- `references/ui/theme-tokens.md`
- `references/ui/styling-patterns.md`
- `references/ui/feedback-overlays.md`
- `references/patterns/form-with-zod.md`
- `references/patterns/react-query-orpc.md`
- `references/patterns/server-prefetch.md`
- `references/patterns/organization-scoped-page.md`
- `references/patterns/direct-upload-s3.md`
- `references/analytics/provider-overview.md`
- `references/analytics/consent-flow.md`
- `references/ai/models-and-exports.md`
- `references/ai/prompt-helpers.md`

### Mail, i18n, storage, marketing, and deployment

Read these when the feature crosses user communication, localization, content, assets, or infra:

- `references/mail/send-email.md`
- `references/mail/template-rendering.md`
- `references/mail/email-templates.md`
- `references/mail/providers.md`
- `references/i18n/setup.md`
- `references/i18n/messages-loading.md`
- `references/i18n/locale-routing.md`
- `references/storage/bucket-config.md`
- `references/storage/s3-provider.md`
- `references/storage/signed-urls.md`
- `references/marketing/home-page-components.md`
- `references/marketing/content-collections.md`
- `references/marketing/pages.md`
- `references/deployment/environment-checklist.md`
- `references/deployment/local-services.md`
- `references/deployment/vercel.md`
- `references/logging.md`
- `references/utils.md`

## Use the task guides for implementation requests

If the user asks you to add something concrete, start here:

- **Add an API endpoint:** `references/tasks/add-api-endpoint.md`
- **Add a SaaS page:** `references/tasks/add-saas-page.md`
- **Add a marketing page:** `references/tasks/add-marketing-page.md`
- **Add a database model:** `references/tasks/add-database-model.md`
- **Integrate billing:** `references/tasks/integrate-payments.md`

These task guides point back to the underlying references and actual file locations.

## Common decision rules

### When changing UI

- default to server components
- add `"use client"` only when hooks/browser APIs are required
- use the existing form stack: `react-hook-form` + `zod` + shared form components
- use deep UI imports such as `@repo/ui/components/button`

Read:

- `references/conventions/component-patterns.md`
- `references/ui/forms.md`
- `references/ui/components.md`
- `references/ui/styling-patterns.md`

### When changing backend/API

- procedures live in `packages/api/modules/*`
- route them through the module router and then the root router
- validate inputs with Zod
- use `publicProcedure`, `protectedProcedure`, or `adminProcedure` deliberately

Read:

- `references/api/procedure-tiers.md`
- `references/api/root-router.md`
- `references/api/transport-handlers.md`
- `references/tasks/add-api-endpoint.md`

### When changing auth or organizations

- check auth feature flags first
- match Better Auth plugin usage already in the repo
- treat org-aware and account-aware routes differently
- reuse session and active-organization helpers before inventing new hooks

Read:

- `references/auth/feature-flags.md`
- `references/auth/server-session-helpers.md`
- `references/organizations/active-organization-context.md`
- `references/routing/access-guards.md`

### When changing data or billing

- schema changes start in `schema.prisma` (or your Drizzle schema if using Drizzle)
- query helpers belong in `packages/database/prisma/queries`
- billing behavior flows through payments config, provider abstraction (Stripe/Polar/Creem/Dodo), and API procedures

Read:

- `references/database/schema-overview.md`
- `references/database/query-patterns.md`
- `references/payments/plans-config.md`
- `references/payments/stripe-provider.md`
- `references/tasks/add-database-model.md`
- `references/tasks/integrate-payments.md`

## High-signal pitfalls

- Do **not** import shared packages through deep relative paths; use aliases from `references/setup/import-conventions.md`.
- Do **not** invent a new form approach; match `references/ui/forms.md` and `references/patterns/form-with-zod.md`.
- Do **not** bypass the oRPC layer with ad hoc handlers unless the task explicitly requires it.
- Do **not** put Prisma calls directly into app components if a shared query helper pattern already exists.
- Do **not** guess where files belong; check `references/cheatsheets/file-locations.md` first.
- Do **not** hardcode env assumptions; check `references/setup/environment-setup.md` and `references/cheatsheets/env-vars.md`.

## Minimal reading sets

Use these smaller bundles when you need speed:

### “I need to add one protected API procedure”

Read:

- `references/tasks/add-api-endpoint.md`
- `references/api/procedure-tiers.md`
- `references/api/root-router.md`
- `references/auth/server-session-helpers.md`
- `references/database/query-patterns.md`

### “I need to add one new dashboard page”

Read:

- `references/tasks/add-saas-page.md`
- `references/routing/routing-saas.md`
- `references/routing/access-guards.md`
- `references/routing/middleware-proxy.md`
- `references/organizations/active-organization-context.md`

### “I need to add one new marketing page or content page”

Read:

- `references/tasks/add-marketing-page.md`
- `references/routing/routing-marketing.md`
- `references/marketing/pages.md`
- `references/marketing/content-collections.md`

### “I need to change auth UI or signup/login behavior”

Read:

- `references/auth/overview.md`
- `references/auth/login-flow.md`
- `references/auth/signup-invitations.md`
- `references/auth/feature-flags.md`
- `references/mail/email-templates.md`

### “I need to touch billing or subscriptions”

Read:

- `references/payments/plans-config.md`
- `references/payments/provider-abstraction.md`
- `references/payments/customer-ids.md`
- `references/payments/stripe-provider.md`
- `references/payments/webhook-flow.md`
- `references/settings/billing-security-and-avatar.md`

### "I need to manage users or organizations as admin"

Read:

- `references/admin/users-admin.md`
- `references/admin/organizations-admin.md`
- `references/auth/better-auth-config.md`
- `references/organizations/members-and-invitations.md`

## Final reminder

This skill is intentionally split into many small reference files. Do not load everything blindly. Start with the smallest relevant bundle above, then expand into neighboring references only when the task actually needs them.
