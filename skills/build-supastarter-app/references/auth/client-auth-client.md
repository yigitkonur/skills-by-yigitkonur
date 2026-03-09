# Client Auth Client

> Reference for the client-side Better Auth instance used by forms, settings pages, and organization flows. Consult this when a client component needs to sign in, sign up, switch organizations, or trigger passkey / 2FA actions.

## Key files

- `packages/auth/client.ts`

## Representative code

```ts
export const authClient = createAuthClient({
  plugins: [
    inferAdditionalFields<typeof auth>(),
    magicLinkClient(),
    organizationClient(),
    adminClient(),
    passkeyClient(),
    twoFactorClient(),
  ],
});

export type AuthClientErrorCodes = typeof authClient.$ERROR_CODES & {
  INVALID_INVITATION: string;
};
```

## Implementation notes

- The auth client mirrors the server plugin setup so typed methods exist for passkeys, organizations, admin actions, and 2FA.
- Most UI consumers call methods such as `signIn.email`, `signIn.magicLink`, `signUp.email`, and `organization.acceptInvitation`.
- `AuthClientErrorCodes` extends built-in Better Auth codes with invitation-only plugin errors.

---

**Related references:**
- `references/auth/login-flow.md` — Primary consumer of `authClient.signIn.*`
- `references/auth/signup-invitations.md` — Primary consumer of `authClient.signUp.*` and invitation acceptance
- `references/auth/session-hook-provider.md` — Client-side session context that wraps auth consumers
