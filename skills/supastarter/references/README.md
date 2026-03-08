# Reference Index (Read-If)

Load only the domains your current Supastarter task actually needs.

| Domain | Read when | Start with |
|---|---|---|
| `setup/`, `conventions/`, `cheatsheets/` | You need repo orientation, imports, config flags, commands, or file placement rules | `setup/monorepo-structure.md`, `setup/import-conventions.md`, `cheatsheets/file-locations.md` |
| `routing/` | You are changing layouts, route groups, middleware, guards, provider order, or dashboard shell behavior | `routing/routing-saas.md`, `routing/layout-chain.md`, `routing/middleware-proxy.md` |
| `api/` | You are adding/changing oRPC procedures, routers, handlers, or frontend API usage | `api/overview.md`, `api/procedure-tiers.md`, `api/root-router.md` |
| `auth/` | You are changing Better Auth config, login/signup behavior, session helpers, or invitation flows | `auth/overview.md`, `auth/better-auth-config.md`, `auth/login-flow.md` |
| `database/` | You are changing schema, Prisma client usage, generated exports, or shared query helpers | `database/schema-overview.md`, `database/prisma-client.md`, `database/query-patterns.md` |
| `payments/` | You are changing plans, checkout, Stripe provider logic, webhooks, or customer IDs | `payments/plans-config.md`, `payments/checkout-and-portal-flow.md`, `payments/stripe-provider.md` |
| `organizations/`, `onboarding/`, `settings/`, `hooks/` | You are working on org-scoped UI, onboarding, settings pages, or shared auth/org hooks | `organizations/active-organization-context.md`, `onboarding/onboarding-flow.md`, `settings/account-settings.md` |
| `ui/`, `patterns/`, `analytics/`, `ai/` | You are building interactive components, forms, client data flows, analytics consent, or AI features | `ui/forms.md`, `patterns/react-query-orpc.md`, `analytics/consent-flow.md`, `ai/models-and-exports.md` |
| `mail/`, `i18n/`, `storage/`, `marketing/` | You are working on email templates, localization, signed URLs, content collections, or public pages | `mail/send-email.md`, `i18n/setup.md`, `storage/signed-urls.md`, `marketing/pages.md` |
| `admin/`, `tasks/`, `deployment/`, root `logging.md` / `utils.md` | You need admin patterns, implementation recipes, deployment setup, or utility/logger behavior | `admin/users-admin.md`, `tasks/add-api-endpoint.md`, `deployment/vercel.md`, `utils.md` |

Rule of thumb: start with 2-4 files, not the whole tree.
