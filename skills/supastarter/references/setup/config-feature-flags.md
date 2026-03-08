# Configuration & Feature Flags

> Documents the three main config files that control application behavior. Consult this when enabling/disabling features, changing app behavior, or understanding what config options are available.

## 1. App Config (`apps/web/config.ts`)

Controls UI behavior, feature toggles, and routing:

```typescript
// apps/web/config.ts
export const config = {
  appName: "supastarter for Next.js Demo",
  docsLink: process.env.NEXT_PUBLIC_DOCS_URL as string | undefined,
  enabledThemes: ["light", "dark"],
  defaultTheme: "light",
  saas: {
    enabled: true,              // Enable the entire SaaS application
    useSidebarLayout: true,     // true = sidebar nav, false = top nav
    redirectAfterSignIn: "/app",
    redirectAfterLogout: "/auth/login",
  },
  marketing: {
    enabled: true,              // Enable marketing pages
  },
} as const;
```

**Key flags:**
- `saas.enabled` — When `false`, middleware blocks all `/app` routes
- `marketing.enabled` — When `false`, middleware blocks marketing pages
- `saas.useSidebarLayout` — Switches between sidebar and top-bar dashboard layout
- `enabledThemes` — Array of available themes; empty array disables theme switching

## 2. Auth Config (`packages/auth/config.ts`)

Controls authentication features and organization behavior:

```typescript
// packages/auth/config.ts
export const config = {
  enableSignup: true,           // Allow new user registration
  enableMagicLink: true,        // Magic link authentication
  enableSocialLogin: true,      // OAuth providers (Google, GitHub)
  enablePasskeys: true,         // WebAuthn passkey authentication
  enablePasswordLogin: true,    // Email/password authentication
  enableTwoFactor: true,        // TOTP two-factor authentication
  sessionCookieMaxAge: 60 * 60 * 24 * 30,  // 30 days

  users: {
    enableOnboarding: true,     // Show onboarding flow for new users
  },

  organizations: {
    enable: true,               // Enable multi-tenancy
    hideOrganization: false,    // Hide org UI (still functional)
    enableUsersToCreateOrganizations: true,
    requireOrganization: false, // Force users into an organization
    forbiddenOrganizationSlugs: [
      "new-organization", "admin", "settings",
      "ai-demo", "organization-invitation",
    ],
  },
} as const;
```

**Key flags:**
- `enableSignup` — When `false`, the signup form is hidden and registration is disabled
- `organizations.enable` — Master toggle for multi-tenancy features
- `organizations.requireOrganization` — When `true`, users must be in an org to use the app
- `users.enableOnboarding` — When `true`, new users go through the onboarding wizard

## 3. Payments Config (`packages/payments/config.ts`)

Controls billing plans and provider behavior:

```typescript
// packages/payments/config.ts
export const config = {
  billingAttachedTo: "user" as "user" | "organization",
  plans: {
    free: { isFree: true },
    pro: {
      recommended: true,
      prices: [
        { type: "recurring", productId: process.env.NEXT_PUBLIC_PRICE_ID_PRO_MONTHLY,
          interval: "month", amount: 29, currency: "USD", seatBased: true, trialPeriodDays: 7 },
        { type: "recurring", productId: process.env.NEXT_PUBLIC_PRICE_ID_PRO_YEARLY,
          interval: "year", amount: 290, currency: "USD", seatBased: true, trialPeriodDays: 7 },
      ],
    },
    lifetime: {
      prices: [
        { type: "one-time", productId: process.env.NEXT_PUBLIC_PRICE_ID_LIFETIME,
          amount: 799, currency: "USD" },
      ],
    },
    enterprise: { isEnterprise: true },
  },
} as const;
```

**Key flags:**
- `billingAttachedTo` — `"user"` for per-user billing, `"organization"` for org billing
- `seatBased: true` — Price multiplied by organization member count
- `isFree: true` — Plan auto-assigned when no purchase exists
- `isEnterprise: true` — Shows "Contact us" CTA instead of checkout

## How Config Is Used

### Middleware (`apps/web/proxy.ts`)

```typescript
// Checks config.saas.enabled for /app routes
if (request.nextUrl.pathname.startsWith("/app")) {
  if (!config.saas.enabled) { /* block */ }
}

// Checks config.marketing.enabled for marketing routes
if (!config.saas.enabled && !config.marketing.enabled) { /* block */ }
```

### Auth forms check feature flags

```typescript
// LoginForm conditionally renders based on auth config
{authConfig.enablePasswordLogin && <PasswordForm />}
{authConfig.enableMagicLink && <MagicLinkForm />}
{authConfig.enableSocialLogin && <OAuthButtons />}
{authConfig.enablePasskeys && <PasskeyButton />}
```

### Payment plans drive the pricing UI

Plan keys (`"free"`, `"pro"`, `"lifetime"`, `"enterprise"`) become the `PlanId` type used throughout the billing system.

---

**Related references:**
- `references/auth/feature-flags.md` — Deep dive into auth feature flags
- `references/payments/plans-config.md` — Full plans config documentation
- `references/routing/access-guards.md` — How guards use config
