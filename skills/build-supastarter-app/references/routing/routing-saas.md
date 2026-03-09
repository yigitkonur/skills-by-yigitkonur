# SaaS Route Structure

> The SaaS surface is split between a root `/(saas)` layout, an inner `/app` guard layout, and a few helper pages that live outside `/app` but still inside the SaaS route group. Use this reference when deciding where a new SaaS page belongs or when tracing why a user lands on onboarding, organization creation, or plan selection before reaching the dashboard.

## Route group layers

`apps/web/app/(saas)` contains two different kinds of routes:

- **Protected application routes** under `apps/web/app/(saas)/app/...`
- **Helper routes** such as `apps/web/app/(saas)/onboarding/page.tsx`, `new-organization/page.tsx`, and `choose-plan/page.tsx`

Inside the protected `/app` subtree, Supastarter splits pages again into two layout branches:

- **Non-organization pages** in `apps/web/app/(saas)/app/(account)/...`
- **Organization-scoped pages** in `apps/web/app/(saas)/app/(organizations)/[organizationSlug]/...`

That split matters because only `/app/*` passes through the inner guard layout at `apps/web/app/(saas)/app/layout.tsx`, while only org-scoped routes resolve an `organizationSlug` and prefetch active organization data before rendering the shell.

## Root SaaS layout at `apps/web/app/(saas)/layout.tsx`

The outer layout sets up the provider and hydration chain shared by every SaaS-scoped route, including `/app`, `/onboarding`, `/new-organization`, and `/choose-plan`:

```tsx
// apps/web/app/(saas)/layout.tsx
return (
  <Document locale={locale}>
    <NextIntlClientProvider messages={messages}>
      <HydrationBoundary state={dehydrate(queryClient)}>
        <SessionProvider>
          <ActiveOrganizationProvider>
            <ConfirmationAlertProvider>{children}</ConfirmationAlertProvider>
          </ActiveOrganizationProvider>
        </SessionProvider>
      </HydrationBoundary>
    </NextIntlClientProvider>
  </Document>
);
```

Before rendering, it fetches `locale`, translation messages, and the session, then prefetches React Query state for the session, the organization list when organizations are enabled, and user purchases when billing is attached to the user.

## Inner `/app` layout at `apps/web/app/(saas)/app/layout.tsx`

The `/app` subtree adds a second layer whose only job is gatekeeping. It is explicitly dynamic on every request:

```tsx
// apps/web/app/(saas)/app/layout.tsx
export const dynamic = "force-dynamic";
export const revalidate = 0;
```

Its checks run in order:

1. redirect to `/auth/login` if there is no session
2. redirect to `/onboarding` if onboarding is enabled and incomplete
3. redirect to `/new-organization` if organizations are required and the user has none
4. redirect to `/choose-plan` if billing applies, there is no free plan, and no active purchase exists

That means `/app/*` is the fully gated dashboard surface, while the helper pages are the places users are sent to satisfy missing prerequisites.

## Non-org vs org-scoped `/app` branches

Account-level pages go through `apps/web/app/(saas)/app/(account)/layout.tsx` and immediately mount the dashboard shell:

```tsx
// apps/web/app/(saas)/app/(account)/layout.tsx
export default function UserLayout({ children }: PropsWithChildren) {
  return <AppWrapper>{children}</AppWrapper>;
}
```

Organization-scoped pages take a different route through `apps/web/app/(saas)/app/(organizations)/[organizationSlug]/layout.tsx`:

```tsx
// apps/web/app/(saas)/app/(organizations)/[organizationSlug]/layout.tsx
const organization = await getActiveOrganization(organizationSlug);

if (!organization) {
  return notFound();
}

await queryClient.prefetchQuery({
  queryKey: activeOrganizationQueryKey(organizationSlug),
  queryFn: () => organization,
});

return <AppWrapper>{children}</AppWrapper>;
```

So both branches end up inside `AppWrapper`, but only the organization branch validates the slug, prefetches the active organization query, and optionally prefetches organization purchases when billing is attached to the organization.

## Helper pages outside `/app`

The helper pages exist outside `apps/web/app/(saas)/app` so they can be reached during the prerequisite flow:

- `apps/web/app/(saas)/onboarding/page.tsx` requires a session, then redirects back to `/app` if onboarding is disabled or already complete.
- `apps/web/app/(saas)/new-organization/page.tsx` renders the org creation form only when orgs are enabled and the user is allowed or required to create one.
- `apps/web/app/(saas)/choose-plan/page.tsx` requires a session, may redirect to `/new-organization` for org-level billing, and redirects to `/app` if an active plan already exists.

These pages are still inside `/(saas)`, so they inherit the SaaS provider stack, but they intentionally avoid the `/app` redirect chain.

---

**Related references:**
- `references/routing/access-guards.md` — Request-time and layout-time redirect logic for SaaS routes
- `references/routing/layout-chain.md` — Full nesting order from `Document` down to account and organization pages
- `references/routing/middleware-proxy.md` — `AppWrapper`, `NavBar`, and sidebar shell inside the `/app` branches
