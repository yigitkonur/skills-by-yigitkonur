# Connecting Clerk to Convex: auth.config.ts

## Use This When
- Wiring Clerk JWTs to the Convex backend for the first time.
- Debugging why `ctx.auth.getUserIdentity()` returns `null`.
- Setting up the backend environment variable for the Clerk issuer domain.

## Create the Auth Config

One file tells Convex which JWTs to trust:

```typescript
// convex/auth.config.ts
export default {
  providers: [
    {
      domain: process.env.CLERK_JWT_ISSUER_DOMAIN!,
      applicationID: "convex",
    },
  ],
};
```

## Set the Environment Variable

1. [dashboard.convex.dev](https://dashboard.convex.dev) -> your project -> **Settings** -> **Environment Variables**.
2. Add: `CLERK_JWT_ISSUER_DOMAIN` = `https://verb-noun-00.clerk.accounts.dev` (the issuer URL from your Clerk JWT Template).

## How It Works

When the Swift app sends a Clerk-issued JWT over the WebSocket:

1. Convex fetches public keys from `https://verb-noun-00.clerk.accounts.dev/.well-known/jwks.json`.
2. Validates the JWT signature.
3. Checks the audience claim matches `"convex"`.
4. Makes the identity available via `ctx.auth.getUserIdentity()`.

## Verify Auth Works

Backend test query:

```typescript
// convex/test.ts
import { query } from "./_generated/server";

export const whoAmI = query({
  args: {},
  handler: async (ctx) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return "Not logged in";
    return `Logged in as: ${identity.name} (${identity.tokenIdentifier})`;
  },
});
```

Subscribe from Swift after Clerk sign-in:

```swift
import ConvexMobile

for await result in client.subscribe(to: "test:whoAmI", yielding: String.self).values {
  print(result) // "Logged in as: ..."
}
```

If your name appears, auth is working end-to-end.

## The tokenIdentifier Field

`ctx.auth.getUserIdentity()` returns an object with many fields. The most important is `tokenIdentifier` -- a stable, globally unique identifier for this user.

**Always use `tokenIdentifier` as the ownership key:**

```typescript
// convex/schema.ts
users: defineTable({
  tokenIdentifier: v.string(),
  name: v.string(),
}).index("by_token", ["tokenIdentifier"])
```

Use `convex-helpers` `userQuery`/`userMutation` as the primary backend auth pattern for ownership-guarded functions. Use raw `ctx.auth.getUserIdentity()` with manual `requireUser()` checks only as an alternative.

**Never accept userId as a function argument for authorization.** Derive it from `ctx.auth.getUserIdentity()` server-side.

## Avoid
- Omitting `auth.config.ts` -- without it, `getUserIdentity()` always returns `null`.
- Hardcoding the issuer domain instead of using an environment variable.
- Accepting client-passed user IDs for authorization decisions.
- Using `.replaceError(with:)` in the verify subscription -- it terminates the stream after the first error.
- Calling `loginFromCache()` manually -- the `ClerkConvexAuthProvider` bound via `bind(client:)` handles session restore automatically.

## Read Next
- [05-first-run-npx-convex-dev.md](05-first-run-npx-convex-dev.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
