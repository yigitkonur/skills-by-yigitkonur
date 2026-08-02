# OAuth Provider: Keycloak

*Read this when integrating self-hosted Keycloak for fine-grained auth.*

## Import & Factory

```typescript
import { oauthKeycloakProvider } from "mcp-use/oauth/keycloak";

const oauth = oauthKeycloakProvider({
  serverUrl: "https://keycloak.example.com",
  realm: "production",
});
```

## Required Options

| Option | Type | Example |
|--------|------|---------|
| `serverUrl` | `string \| URL` | `"https://keycloak.example.com"` |
| `realm` | `string` | `"production"` |

## User Type

```typescript
type KeycloakOAuthUser = {
  id: string;
  email?: string;
  name?: string;
  preferredUsername?: string;
  givenName?: string;
  familyName?: string;
  emailVerified?: boolean;
  roles: string[];
  realmAccess?: Record<string, unknown>;
  resourceAccess?: Record<string, unknown>;
};
```

## Environment Variables

```bash
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=production
```

## Gotchas

1. No trailing slash on serverUrl
2. Issuer auto-derived as `https://keycloak.example.com/realms/production`
3. `roles` contains realm roles only; check `resourceAccess` for app-specific roles
4. Default scopes: `["openid", "profile"]`
