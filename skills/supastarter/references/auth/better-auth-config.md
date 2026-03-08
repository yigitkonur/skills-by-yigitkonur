# Better Auth Configuration

> High-level map of the server-side `betterAuth()` configuration: database adapter, sessions, account linking, lifecycle hooks, email flows, plugins, and OpenAPI. Consult this when changing the auth backend itself rather than a UI consumer.

## Key files

- `packages/auth/auth.ts`
- `packages/auth/config.ts`
- `packages/auth/lib/organization.ts`

## Representative code

```ts
export const auth = betterAuth({
  baseURL: appUrl,
  trustedOrigins: [appUrl],
  database: prismaAdapter(db, { provider: "postgresql" }),
  session: { expiresIn: config.sessionCookieMaxAge, freshAge: 0 },
  account: { accountLinking: { enabled: true, trustedProviders: ["google", "github"] } },
  hooks: {
    after: createAuthMiddleware(async (ctx) => { /* sync subscription seats */ }),
    before: createAuthMiddleware(async (ctx) => { /* cancel subscriptions before deletion */ }),
  },
  emailAndPassword: { enabled: true, autoSignIn: !config.enableSignup, requireEmailVerification: config.enableSignup },
  emailVerification: { sendOnSignUp: config.enableSignup, autoSignInAfterVerification: true },
  plugins: [username(), admin(), passkey(), magicLink({...}), organization({...}), openAPI(), invitationOnlyPlugin(), twoFactor()],
});
```

## What lives here

- **Database adapter** — Prisma + PostgreSQL
- **Sessions** — cookie-based with configurable max age and `freshAge: 0`
- **Lifecycle hooks** — seat synchronization and subscription cleanup around destructive actions
- **Transactional emails** — password reset, magic link, email verification, organization invitation
- **Plugins** — username, admin, passkey, magic link, organization, OpenAPI, invitation-only, two-factor

## Implementation notes

- Public signup behavior is controlled partly by config and partly by the invitation-only plugin.
- OpenAPI support for auth endpoints is enabled inside Better Auth, then merged into the API docs path.
- Multi-tenant organization behavior is an auth concern first, not a separate service.

---

**Related references:**
- `references/auth/overview.md` — System-level auth map
- `references/auth/feature-flags.md` — Flags that feed the auth instance
- `references/auth/signup-invitations.md` — Invitation, verification, and acceptance behavior
- `references/mail/email-templates.md` — Auth-triggered email templates
