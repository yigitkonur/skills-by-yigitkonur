# Document and Client Providers

> `Document` is the shared server wrapper for the entire app, while `ClientProviders` is the shared client-only context stack mounted inside it. Use this reference when adding a global provider, debugging hydration order, or deciding whether logic belongs in the HTML shell, a server component, or a client provider.

## `Document` is the server-side root shell

`apps/web/modules/shared/components/Document.tsx` is an async server component. It owns the real `<html>` and `<body>` tags, sets `lang`, applies the font CSS variables, adds `suppressHydrationWarning`, and reads the `consent` cookie before any client provider is mounted.

```tsx
// apps/web/modules/shared/components/Document.tsx
<html
  lang={locale}
  suppressHydrationWarning
  className={cn(sansFont.variable, serifFont.variable)}
>
  <body className="min-h-screen bg-background text-foreground antialiased">
    <NuqsAdapter>
      <ConsentProvider initialConsent={consentCookie?.value === "true"}>
        <ClientProviders>{children}</ClientProviders>
      </ConsentProvider>
    </NuqsAdapter>
  </body>
</html>
```

Because `Document` runs on the server, it is the right place for request-bound inputs such as cookies and locale.

## `ClientProviders` is the client-only context stack

`apps/web/modules/shared/components/ClientProviders.tsx` is marked with `"use client"`. It composes the app's runtime client contexts and shared overlays:

```tsx
// apps/web/modules/shared/components/ClientProviders.tsx
<ApiClientProvider>
  <ProgressProvider ...>
    <ThemeProvider ...>
      <ApiClientProvider>
        {children}
        <Toaster position="top-right" />
        <ConsentBanner />
        <AnalyticsScript />
      </ApiClientProvider>
    </ThemeProvider>
  </ProgressProvider>
</ApiClientProvider>
```

The nesting order is important because route progress, theme class management, query context, and the shared UI overlays all depend on being mounted above page content.

## Responsibility split: server vs client

Use this rule when deciding where something belongs:

- **`Document`** for HTML/body tags, locale, cookies, server-known initial values, and wrapping the transition from server rendering to client contexts.
- **`ClientProviders`** for contexts that depend on browser APIs or client lifecycle, such as theme switching, progress bars, toast containers, analytics scripts, and query client usage.

## Where these providers sit in the app

Neither marketing nor SaaS defines its own HTML shell from scratch. Both top-level layouts call `Document`, which means both trees inherit the same `NuqsAdapter`, `ConsentProvider`, and `ClientProviders` chain before their route-specific providers are added.

---

**Related references:**
- `references/routing/layout-chain.md` — Where `Document` and `ClientProviders` sit relative to marketing and SaaS layouts
- `references/routing/routing-marketing.md` — Marketing-specific providers mounted above public pages
- `references/routing/routing-saas.md` — SaaS-specific providers mounted above dashboard and helper routes
