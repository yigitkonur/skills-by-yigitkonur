# Runtime: ctx.auth and User Context

*Read this when you need to access authenticated user info inside tools, resources, or prompts.*

Every authenticated tool, resource, or prompt callback's second argument (`ctx`, a `RequestContext<TUser, true>`) carries an `auth: OAuthAuth<TUser>` field populated by the bearer gate. This is distinct from `ctx.client` (`RequestClientContext`), which holds unverified client-reported hints (locale, user agent, coarse location) and is never a source of authentication.

## Full ctx.auth Shape

```typescript
type OAuthAuth<TUser> = {
  /** Authenticated application user mapped by the OAuth provider. */
  user: TUser;
  
  /** Verified access-token claims. */
  payload: Record<string, unknown>;
  
  /** Raw bearer token for authenticated downstream requests. */
  accessToken: string;
  
  /** OAuth scopes granted to the access token. */
  scopes: string[];
  
  /** Provider-normalized permissions. */
  permissions: string[];
  
  /** OAuth client identifier from token's client_id or azp claim. */
  clientId?: string;
  
  /** Access-token expiration as Unix time (seconds). */
  expiresAt: number;
  
  /** Resource audience the token authorizes, when supplied. */
  resource?: URL;
}
```

## User Type (Provider-Specific)

Every provider returns its own `TUser` interface. For Clerk:

```typescript
type ClerkOAuthUser = {
  id: string;                         // ← Always present; stable user ID
  email?: string;
  name?: string;
  username?: string;
  picture?: string;
  emailVerified?: boolean;
  organizationId?: string;
  organizationRole?: string;
  organizationSlug?: string;
  roles: string[];                    // ← Always present; may be empty
};
```

**Key fact:** Use `ctx.auth.user.id`, not `userId`. Every provider has an `id` field; it is the stable user identifier.

## Usage in Tools

```typescript
server.tool(
  {
    name: "my-tool",
    description: "Example tool",
    inputSchema: z.object({ query: z.string() }),
  },
  async (params, ctx) => {
    // Access the user
    const userId = ctx.auth.user.id;
    const email = ctx.auth.user.email;

    // Check scopes or permissions
    if (!ctx.auth.scopes.includes("email")) {
      return {
        isError: true,
        content: [{ type: "text", text: "email scope required" }],
      };
    }

    // Check roles (if provider includes them)
    if (ctx.auth.user.roles && !ctx.auth.user.roles.includes("admin")) {
      return {
        isError: true,
        content: [{ type: "text", text: "admin role required" }],
      };
    }

    // Token expires in how long?
    const expiresIn = ctx.auth.expiresAt - Math.floor(Date.now() / 1000);

    return {
      content: [
        {
          type: "text",
          text: `User ${userId} (${email}) — token expires in ${expiresIn}s`,
        },
      ],
    };
  },
);
```

## Scopes vs Permissions

- **Scopes** (`ctx.auth.scopes`): The OAuth scope list from the verified token (e.g., `["openid", "profile", "email"]`)
- **Permissions** (`ctx.auth.permissions`): Provider-normalized permissions. Set by the provider's `mapAuthInfo()` function or extracted from a `permissions` claim in the token. Often mirrors scopes but may be mapped differently per provider.

See `references/11-auth/04-permission-guards.md` for guard patterns.

## Accessing the Raw Token

If you need to forward the access token to downstream services:

```typescript
async (params, ctx) => {
  const response = await fetch("https://api.example.com/me", {
    headers: {
      Authorization: `Bearer ${ctx.auth.accessToken}`,
    },
  });
  // ...
}
```

The token is valid until `ctx.auth.expiresAt` (Unix seconds).

## Provider-Specific Fields

Each provider includes additional user fields. See the provider's file (`providers/01-clerk.md`, etc.) for what fields are available for that service.

Example (Keycloak roles):
```typescript
// if provider is Keycloak
const user = ctx.auth.user as KeycloakOAuthUser;
const realmAccess = user.realmAccess;      // Raw realm_access claim
const resourceAccess = user.resourceAccess; // Raw resource_access claim
```
