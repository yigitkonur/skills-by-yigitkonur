# OAuth Provider: WorkOS

*Read this when integrating WorkOS AuthKit for enterprise SSO.*

## Import & Factory

```typescript
import { oauthWorkOSProvider } from "mcp-use/oauth/workos";

const oauth = oauthWorkOSProvider({
  subdomain: "example.authkit.app",
});
```

## Required Options

| Option | Type | Example | Notes |
|--------|------|---------|-------|
| `subdomain` | `string` | `"example.authkit.app"` | AuthKit hostname. A bare hostname (`"example.authkit.app"`) or a full `https://` origin both work; a value with a path, query, or fragment throws `TypeError`. |

There is no separate `audience` option and no `clientId`/`clientSecret` — this factory only builds a resource-server token verifier; WorkOS owns client registration and login.

## Optional Options

```typescript
oauthWorkOSProvider({
  subdomain: "...",
  resource?: string | URL,              // Full MCP endpoint URL (overrides host header inference)
  requiredScopes?: readonly string[],   // Scopes required by bearer gate (default: none enforced)
  scopesSupported?: readonly string[],  // Scopes advertised to clients (no factory default)
  resourceName?: string,                // Human-readable name for OAuth metadata
  serviceDocumentationUrl?: URL,        // Documentation link in OAuth metadata
})
```

## User Type

```typescript
type WorkOSOAuthUser = {
  id: string;                   // sub claim
  email?: string;
  emailVerified?: boolean;      // email_verified claim
  name?: string;
  preferredUsername?: string;   // preferred_username claim
  firstName?: string;           // first_name claim
  lastName?: string;            // last_name claim
  picture?: string;
  roles: string[];              // roles claim, normalized to a string array
  organizationId?: string;      // org_id claim
  sessionId?: string;           // sid claim
};
```

Token `permissions` claim maps separately to top-level `ctx.auth.permissions`, not to `user.roles`.

## Environment Variables

The provider does not read any environment variables itself — `subdomain` is a plain function argument:

```bash
WORKOS_SUBDOMAIN=your-company.authkit.app
```

```typescript
const subdomain = process.env.WORKOS_SUBDOMAIN;
if (!subdomain) throw new Error("WORKOS_SUBDOMAIN is required");

const oauth = oauthWorkOSProvider({ subdomain });
```

## Configure WorkOS

In the WorkOS Dashboard, before wiring the provider:

1. Enable Dynamic Client Registration.
2. Enable Client ID Metadata Document if your MCP clients use it.
3. Add the canonical MCP endpoint as a Resource Indicator (e.g. `https://mcp.example.com/mcp`).

## Typical Setup

```typescript
import { MCPServer } from "mcp-use";
import { oauthWorkOSProvider } from "mcp-use/oauth/workos";

interface DocumentRecord {
  id: string;
  title: string;
  organizationId: string;
}

// Application-owned database seam. Implement this with your ORM or SQL client.
interface DocumentsRepository {
  findManyByOrganizationId(organizationId: string): Promise<DocumentRecord[]>;
}

export function createWorkOSServer(documents: DocumentsRepository) {
  const subdomain = process.env.WORKOS_SUBDOMAIN;
  if (!subdomain) throw new Error("WORKOS_SUBDOMAIN is required");

  const server = new MCPServer({
    name: "workos-server",
    version: "1.0.0",
    oauth: oauthWorkOSProvider({ subdomain }),
  });

  server.tool(
    { name: "list_documents", description: "List documents for the WorkOS organization." },
    async (_args, ctx) => {
      const organizationId = ctx.auth.user.organizationId;
      if (!organizationId) {
        return { isError: true, content: [{ type: "text", text: "Organization context required" }] };
      }

      const records = await documents.findManyByOrganizationId(organizationId);
      return { content: [{ type: "text", text: JSON.stringify(records) }] };
    },
  );

  return server;
}
```

At the application composition root, pass the repository implementation and then call `listen()` or export `.fetch`:

```typescript
import { documentsRepository } from "./db.js";
import { createWorkOSServer } from "./workos-server.js";

await createWorkOSServer(documentsRepository).listen(3000);
```

## Gotchas

1. `subdomain` accepts a bare hostname or a full `https://` origin — no path, query, or fragment
2. No `clientId`/`clientSecret` needed — token verification only, WorkOS owns registration and login
3. `organizationId` may be undefined for users without an active organization; check before using
4. `roles` array is always present but may be empty; check `roles.includes(...)`, and use `ctx.auth.permissions` for verified permissions
