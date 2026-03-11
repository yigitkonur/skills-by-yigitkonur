# Layout Chain

> The app has two top-level layout chains: a locale-aware marketing chain and a SaaS chain that adds hydration, session, organization, and confirmation contexts before any dashboard shell appears. Use this reference when inserting a new provider or when debugging which layout layer owns a redirect, context, or visual wrapper.

> ⚠️ **Provider order matters.** Layouts nest Document → ClientProviders → (marketing OR saas). Moving a provider out of order breaks context for all child routes.

## Marketing layout chain

Marketing routes inherit a single layout from `apps/web/app/(marketing)/[locale]/layout.tsx`:

```text
Document
  → NextIntlClientProvider
    → SessionProvider
      → NavBar
      → main.min-h-screen
      → Footer
```

The `Document` wrapper comes from `apps/web/modules/shared/components/Document.tsx`, so the marketing chain also includes the shared HTML/body wrapper, consent setup, theme provider, query client, toasts, analytics script, and route progress bar indirectly through `ClientProviders`.

## SaaS layout chain before `/app`

Every route inside `apps/web/app/(saas)` first passes through the SaaS root layout at `apps/web/app/(saas)/layout.tsx`:

```text
Document
  → NextIntlClientProvider
    → HydrationBoundary
      → SessionProvider
        → ActiveOrganizationProvider
          → ConfirmationAlertProvider
            → children
```

This is where server-fetched session, organization, and purchase data is dehydrated for client reuse. Helper pages like `/onboarding`, `/new-organization`, and `/choose-plan` stop here and render their own page content under this shared provider stack.

## Additional nesting under `/app`

The protected application subtree adds the `/app` guard layout and then branches into account-scoped and organization-scoped layouts:

```text
SaaS root layout
  → /app guard layout (apps/web/app/(saas)/app/layout.tsx)
    → /(account) layout
      → AppWrapper
        → page
    → /(organizations)/[organizationSlug] layout
      → AppWrapper
        → page
```

The `/app` layout does not add UI chrome; it performs redirects for auth, onboarding, organization, and billing requirements. The visible dashboard shell begins in the account and organization branch layouts when they mount `AppWrapper`.

## What the organization branch adds

The organization layout does one extra server-side step before rendering the shell:

```tsx
// apps/web/app/(saas)/app/(organizations)/[organizationSlug]/layout.tsx
const organization = await getActiveOrganization(organizationSlug);
if (!organization) {
  return notFound();
}
```

It also prefetches the active organization query and, when organization billing is enabled, prefetches purchases for that organization. That is why organization pages can read the current org immediately on the client.

## Practical rule of thumb

- **Need global HTML/body, theme, analytics, consent, or query context?** That belongs at `Document` / `ClientProviders` level.
- **Need SaaS-wide session or organization context?** That belongs in `apps/web/app/(saas)/layout.tsx`.
- **Need a redirect before any dashboard page renders?** That belongs in `apps/web/app/(saas)/app/layout.tsx`.
- **Need dashboard chrome such as navigation and sidebar spacing?** That belongs in `AppWrapper`, which is mounted by both `/app/(account)` and `/app/(organizations)/[organizationSlug]` layouts.

## Full layout tree

```text
Document (app/layout.tsx)
└── ClientProviders (providers + session)
    ├── (marketing) ← public pages, locale routing
    │   └── [locale]/page.tsx
    └── (saas) ← auth guard + onboarding check
        └── app/
            ├── (account) ← personal settings
            │   └── settings/page.tsx
            └── (organizations) ← ActiveOrganizationProvider
                └── [organizationSlug]/
                    └── AppWrapper.tsx (nav + shell)
                        └── <page>/page.tsx
```

---

**Related references:**
- `references/routing/providers-document.md` — The shared root document and client provider stack
- `references/routing/routing-saas.md` — SaaS route split between `/app` branches and helper pages
- `references/routing/routing-marketing.md` — Locale-scoped marketing shell
