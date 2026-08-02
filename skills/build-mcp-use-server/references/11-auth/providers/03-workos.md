# OAuth Provider: WorkOS

*Read this when integrating WorkOS for enterprise SSO.*

## Import & Factory

```typescript
import { oauthWorkOSProvider } from "mcp-use/oauth/workos";

const oauth = oauthWorkOSProvider({
  subdomain: "example.authkit.app",
});
```

## Required Options

| Option | Type | Example |
|--------|------|---------|
| `subdomain` | `string` | `"example.authkit.app"` |

## User Type

```typescript
type WorkOSOAuthUser = {
  id: string;
  email?: string;
  emailVerified?: boolean;
  name?: string;
  firstName?: string;
  lastName?: string;
  picture?: string;
  roles: string[];
  organizationId?: string;
  sessionId?: string;
};
```

## Gotchas

1. Pass subdomain only (no scheme); `example.authkit.app`
2. No clientId/clientSecret needed
3. `organizationId` may be undefined; check before using
