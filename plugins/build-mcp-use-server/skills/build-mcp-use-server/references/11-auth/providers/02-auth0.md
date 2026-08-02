# OAuth Provider: Auth0

*Read this when integrating Auth0 for authentication.*

## Import & Factory

```typescript
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";

const oauth = oauthAuth0Provider({
  domain: "https://example.us.auth0.com",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `domain` | `string \| URL` | `"https://example.us.auth0.com"` | Auth0 tenant domain or issuer URL |

## Optional Options

```typescript
oauthAuth0Provider({
  domain: "...",
  resource?: string \| URL,
  requiredScopes?: readonly string[],
  scopesSupported?: readonly string[],
  resourceName?: string,
  serviceDocumentationUrl?: URL,
})
```

## User Type

```typescript
type Auth0OAuthUser = {
  id: string;
  email?: string;
  name?: string;
  nickname?: string;
  picture?: string;
  emailVerified?: boolean;
  updatedAt?: string;
  roles: string[];
};
```

## Environment Variables

```bash
AUTH0_DOMAIN=https://example.us.auth0.com
```

## Gotchas

1. Domain format includes `https://` scheme and region (`.us.auth0.com`, `.eu.auth0.com`)
2. Roles must be enabled in Auth0 Dashboard → Applications → Roles
3. `roles` array is always present; check `roles.includes(...)`
