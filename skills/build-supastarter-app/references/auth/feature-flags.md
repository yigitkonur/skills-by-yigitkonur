# Auth Feature Flags

> Documents the `packages/auth/config.ts` toggles that control signup, magic links, passkeys, onboarding, and organizations. Consult this when a UI branch or redirect path seems inconsistent with the auth setup.

## Key files

- `packages/auth/config.ts`

## Representative code

```ts
export const config = {
  enableSignup: true,
  enableMagicLink: true,
  enableSocialLogin: true,
  enablePasskeys: true,
  enablePasswordLogin: true,
  enableTwoFactor: true,
  sessionCookieMaxAge: 60 * 60 * 24 * 30,
  users: { enableOnboarding: true },
  organizations: {
    enable: true,
    hideOrganization: false,
    enableUsersToCreateOrganizations: true,
    requireOrganization: false,
    forbiddenOrganizationSlugs: ["new-organization", "admin", "settings", "ai-demo", "organization-invitation"],
  },
} as const;
```

## Downstream effects

- Login and signup UIs use these flags directly to decide which auth methods to render.
- The `/app` access-guard layout reads onboarding and organization requirements from this config.
- Session cookie lifetime comes from `sessionCookieMaxAge`, which is passed into Better Auth server config.
- Reserved organization slugs must stay aligned with hard-coded product routes.

---

**Related references:**
- `references/setup/config-feature-flags.md` — App-wide flags across auth, SaaS, and payments
- `references/routing/access-guards.md` — How onboarding and org requirements trigger redirects
- `references/auth/login-flow.md` — Conditional UI branches based on auth flags
