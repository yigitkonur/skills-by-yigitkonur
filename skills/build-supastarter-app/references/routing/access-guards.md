# Access Guards

> Access control is split between request-time middleware and server-side layout/page redirects. Use this reference when a user is bounced away from `/app`, `/onboarding`, `/new-organization`, or `/choose-plan` and you need to know whether the redirect happened before React rendered or inside the App Router tree.

> ⚠️ **Guard order.** Guards run top-down: auth check → onboarding check → org resolution. A missing guard causes silent redirect loops.

## Middleware-time checks in `apps/web/proxy.ts`

`apps/web/proxy.ts` runs before route rendering and handles broad routing decisions based on the path, session cookie, and feature flags from `apps/web/config.ts`.

```ts
// apps/web/proxy.ts
if (pathname.startsWith("/app")) {
  if (!appConfig.saas.enabled) {
    return NextResponse.redirect(new URL("/", origin));
  }

  if (!sessionCookie) {
    return NextResponse.redirect(
      new URL(withQuery("/auth/login", { redirectTo: pathname }), origin),
    );
  }
}
```

Middleware also lets `/onboarding`, `/new-organization`, `/choose-plan`, and `/organization-invitation` bypass locale middleware, and it redirects all non-SaaS requests to `/app` when `config.marketing.enabled` is `false`.

## `/app` layout guard order

Once a request reaches the App Router, `apps/web/app/(saas)/app/layout.tsx` performs the deeper SaaS checks. The layout is always re-evaluated because it exports `dynamic = "force-dynamic"` and `revalidate = 0`.

```ts
// apps/web/app/(saas)/app/layout.tsx
if (!session) {
  redirect("/auth/login");
}

if (authConfig.users.enableOnboarding && !session.user.onboardingComplete) {
  redirect("/onboarding");
}
```

After session and onboarding, it resolves the organization list. If organizations are enabled and required, users without an active org are sent to `/new-organization`. Finally, if billing applies and there is no free plan, it loads purchases with `orpcClient.payments.listPurchases(...)`, derives `activePlan` with `createPurchasesHelper(...)`, and redirects to `/choose-plan` when no active plan exists.

## Helper-page self-guards

The helper pages are not blindly accessible; each one validates that the user actually needs that step:

- `apps/web/app/(saas)/onboarding/page.tsx` redirects to `/auth/login` without a session and back to `/app` when onboarding is disabled or already complete.
- `apps/web/app/(saas)/new-organization/page.tsx` redirects to `/app` when organizations are disabled, or when the user is neither allowed nor required to create an organization.
- `apps/web/app/(saas)/choose-plan/page.tsx` redirects to `/auth/login` without a session, to `/new-organization` when org billing needs an organization but none exists, and to `/app` when an active plan already exists.

That makes the flow self-healing: `/app` sends users to the next missing prerequisite, and the helper page sends them back once that prerequisite is no longer missing.

## Config values that influence guard behavior

`apps/web/config.ts` contributes the request-time feature flags:

- `config.saas.enabled`
- `config.marketing.enabled`
- `config.saas.redirectAfterSignIn = "/app"`
- `config.saas.redirectAfterLogout = "/auth/login"`

The deeper onboarding, organization, and billing decisions come from the auth and payments configs imported directly inside the layout and helper pages.

---

**Related references:**
- `references/routing/routing-saas.md` — Where `/app` and helper pages sit in the route tree
- `references/routing/layout-chain.md` — Which layout layer owns each guard
- `references/payments/checkout-and-portal-flow.md` — How active billing state is derived from purchases
