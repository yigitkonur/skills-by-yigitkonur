# OAuth Provider: Better Auth

*Read this when using Better Auth as your full OAuth and authorization server.*

## Import & Factory

```typescript
import { oauthBetterAuthProvider } from "mcp-use/oauth/better-auth";

const oauth = oauthBetterAuthProvider({
  authURL: "https://auth.example.com/api/auth",
});
```

## Required Options

| Option | Type | Example |
|--------|------|---------|
| `authURL` | `string \| URL` | `"https://auth.example.com/api/auth"` |

## User Type

```typescript
type BetterAuthOAuthUser = {
  id: string;
  email?: string;
  name?: string;
  picture?: string;
  emailVerified?: boolean;
  sessionId?: string;
  isAnonymous?: boolean;
  roles: string[];
};
```

## Environment Variables

```bash
BETTER_AUTH_URL=https://auth.example.com/api/auth
```

## Gotchas

1. Include full base path (`/api/auth`)
2. Better Auth owns registration, authorization, consent, and token issuance
3. Check `isAnonymous` before assuming authenticated session
4. `sessionId` provided but rarely needed in stateless MCP context
