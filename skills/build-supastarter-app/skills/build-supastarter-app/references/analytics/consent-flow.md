# Consent Flow

> Documents the cookie-consent state and banner that sit next to analytics in the shared client-provider layer. Consult this when changing consent persistence or controlling when analytics scripts should activate.
>
> The flow is split between `ConsentProvider` for state and cookie writes, and `ConsentBanner` for the fixed-position UI.

## Consent Provider

```tsx
// apps/web/modules/shared/components/ConsentProvider.tsx
export const ConsentContext = createContext({
  userHasConsented: false,
  allowCookies: () => {},
  declineCookies: () => {},
});

Cookies.set("consent", "true", { expires: 30 });
Cookies.set("consent", "false", { expires: 30 });
```

## Consent Banner

```tsx
// apps/web/modules/shared/components/ConsentBanner.tsx
if (!mounted) return null;
if (userHasConsented) return null;

return (
  <div className="fixed left-4 bottom-4 max-w-md z-50">
    ...
    <Button onClick={() => declineCookies()}>Decline</Button>
    <Button onClick={() => allowCookies()}>Allow</Button>
  </div>
);
```

## Where It Mounts

`ClientProviders.tsx` renders both `ConsentBanner` and `AnalyticsScript`, which keeps consent/analytics concerns in the same global client layer.

---

**Related references:**
- `references/routing/providers-document.md` — Global client-provider stack
- `references/analytics/provider-overview.md` — Analytics provider entry-point selection
- `references/routing/layout-chain.md` — Where consent state enters the route tree
- `references/hooks/consent-hooks.md` — Consent hooks
