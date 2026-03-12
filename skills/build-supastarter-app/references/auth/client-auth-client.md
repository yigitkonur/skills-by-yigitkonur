# Client Auth Client

> Reference for the client-side Better Auth instance used by forms, settings pages, and organization flows. Consult this when a client component needs to sign in, sign up, switch organizations, or trigger passkey / 2FA actions.

> ⚠️ **Call `reloadSession()` after mutations.** Any mutation that changes user data (name, avatar, settings) requires `reloadSession()` to update the client cache.

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

## Common methods

| Method | Purpose | Used by |
|---|---|---|
| `authClient.signIn.email()` | Email/password login | Login page |
| `authClient.signUp.email()` | Email registration | Signup page |
| `authClient.signOut()` | End session | Nav menu |
| `authClient.updateUser()` | Update profile | Settings, onboarding |
| `authClient.organization.create()` | Create org | Org creation form |
| `authClient.organization.setActive()` | Switch active org | Org selector |
| `authClient.organization.inviteMember()` | Send invitation | Members page |
| `authClient.organization.removeMember()` | Remove member | Members page |
| `authClient.organization.updateMemberRole()` | Change role | Members page |
| `authClient.useSession()` | React hook for session | Any client component |

---

**Related references:**
- `references/auth/login-flow.md` — Primary consumer of `authClient.signIn.*`
- `references/auth/signup-invitations.md` — Primary consumer of `authClient.signUp.*` and invitation acceptance
- `references/auth/session-hook-provider.md` — Client-side session context that wraps auth consumers
