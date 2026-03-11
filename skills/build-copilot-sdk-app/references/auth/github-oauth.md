# GitHub OAuth Authentication Reference

## Token Types

Use these GitHub token types with `githubToken` in `CopilotClientOptions`:

| Prefix | Source | SDK Support |
|--------|--------|-------------|
| `gho_` | OAuth user access token | Supported |
| `ghu_` | GitHub App user access token | Supported |
| `github_pat_` | Fine-grained personal access token | Supported |
| `ghp_` | Classic personal access token | Not supported (deprecated) |

The SDK passes the `githubToken` value to the CLI process via environment variable. The CLI then exchanges it for a short-lived Copilot token internally. You never handle Copilot tokens directly — only GitHub tokens.

## Client Construction with OAuth Token

```typescript
import { CopilotClient } from "@github/copilot-sdk";

// Provide a GitHub token directly; disable fallback to stored CLI credentials
const client = new CopilotClient({
    githubToken: userAccessToken,   // gho_, ghu_, or github_pat_ prefix
    useLoggedInUser: false,         // Prevents falling back to CLI keychain
});
```

Set `useLoggedInUser: false` whenever you provide an explicit token. Without it, the SDK may silently fall back to the developer's own stored credentials in non-production environments, causing auth confusion.

## Device Flow (Interactive CLI Login)

The Copilot CLI handles GitHub OAuth device flow internally when a user runs `copilot` interactively. Your SDK code does not drive the device flow — you only consume credentials after they are stored.

When `useLoggedInUser: true` (the default), the CLI uses credentials stored in the system keychain from a previous `copilot` login. This is suitable for desktop tools and dev environments.

```typescript
// Uses system keychain credentials; appropriate only for single-user desktop tools
const client = new CopilotClient();
```

Do not use this pattern in server-side or multi-user code.

## Authentication Priority Order

When multiple auth sources are present, the CLI resolves them in this order:

1. `githubToken` passed to `CopilotClientOptions` constructor
2. `CAPI_HMAC_KEY` or `COPILOT_HMAC_KEY` environment variable (HMAC auth)
3. `GITHUB_COPILOT_API_TOKEN` with `COPILOT_API_URL` (direct API token)
4. `COPILOT_GITHUB_TOKEN` environment variable
5. `GH_TOKEN` environment variable (GitHub CLI compatible)
6. `GITHUB_TOKEN` environment variable (GitHub Actions compatible)
7. Stored OAuth credentials from previous `copilot` CLI login
8. `gh` CLI auth credentials (`gh auth login`)

The `githubToken` constructor option always wins. If you set it, set `useLoggedInUser: false` to prevent any ambiguity.

## Checking Authentication Status

Use `client.getAuthStatus()` to verify authentication before creating sessions:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import type { GetAuthStatusResponse } from "@github/copilot-sdk";

const client = new CopilotClient({ githubToken: token, useLoggedInUser: false });

const authStatus: GetAuthStatusResponse = await client.getAuthStatus();
// authStatus shape:
// {
//   isAuthenticated: boolean,
//   authType?: "user" | "env" | "gh-cli" | "hmac" | "api-key" | "token",
//   host?: string,      // GitHub host URL
//   login?: string,     // GitHub username
//   statusMessage?: string
// }

if (!authStatus.isAuthenticated) {
    throw new Error(`Auth failed: ${authStatus.statusMessage}`);
}
console.log(`Authenticated as ${authStatus.login} via ${authStatus.authType}`);
```

Call `getAuthStatus()` at application startup or before initiating a Copilot session in critical paths. Do not assume token validity from prior checks — check freshly after long idle periods.

## OAuth App Registration

Register a GitHub OAuth App when building multi-user flows where end users authenticate with their own GitHub accounts:

1. Go to GitHub Settings > Developer Settings > OAuth Apps > New OAuth App
2. Set Authorization callback URL to your redirect endpoint (e.g., `https://yourapp.com/auth/callback`)
3. Note your Client ID; generate a Client Secret
4. Request scope: `copilot` (required for Copilot API access)

Exchange the authorization code for a user token server-side:

```typescript
async function exchangeCodeForToken(code: string): Promise<string> {
    const response = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
            client_id: process.env.GITHUB_CLIENT_ID,
            client_secret: process.env.GITHUB_CLIENT_SECRET,
            code,
        }),
    });
    const data = await response.json();
    if (data.error) throw new Error(data.error_description);
    return data.access_token; // gho_xxx
}
```

## Token Refresh and Expiration

The SDK does not manage OAuth token lifecycle. Your application owns token storage, refresh, and expiration handling.

`gho_` tokens from standard OAuth Apps do not expire unless the user revokes them or the app is deauthorized. `ghu_` tokens from GitHub Apps with expiration enabled expire after 8 hours and come with a refresh token.

```typescript
async function getValidToken(userId: string): Promise<string> {
    const stored = await tokenStore.get(userId);

    if (!stored) throw new Error("User must authenticate");

    if (isExpired(stored.expiresAt)) {
        if (!stored.refreshToken) throw new Error("User must re-authenticate");

        // GitHub App token refresh
        const response = await fetch("https://github.com/login/oauth/access_token", {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify({
                client_id: process.env.GITHUB_CLIENT_ID,
                client_secret: process.env.GITHUB_CLIENT_SECRET,
                grant_type: "refresh_token",
                refresh_token: stored.refreshToken,
            }),
        });
        const refreshed = await response.json();
        await tokenStore.set(userId, {
            accessToken: refreshed.access_token,
            refreshToken: refreshed.refresh_token,
            expiresAt: Date.now() + refreshed.expires_in * 1000,
        });
        return refreshed.access_token;
    }

    return stored.accessToken;
}
```

Create a new `CopilotClient` instance whenever you refresh a token — the client binds the token at construction time and does not pick up changes.

## Authentication Error Handling

```typescript
import { CopilotClient } from "@github/copilot-sdk";

async function createAuthenticatedSession(token: string, userId: string) {
    const client = new CopilotClient({ githubToken: token, useLoggedInUser: false });

    const status = await client.getAuthStatus();
    if (!status.isAuthenticated) {
        // authType === undefined means no auth source found at all
        throw new AuthenticationError(
            `GitHub token rejected for user ${userId}: ${status.statusMessage}`
        );
    }

    const session = await client.createSession({
        sessionId: `user-${userId}`,
        model: "gpt-4.1",
        onPermissionRequest: () => ({ kind: "approved" }),
    });

    return { client, session };
}
```

Common error conditions:
- `isAuthenticated: false` with no `authType` — token is invalid or has no Copilot subscription
- Network errors reaching GitHub — handle with retry + exponential backoff
- 401 from Copilot API — token revoked; force user re-authentication

## Multi-User Auth Patterns for Backend Services

### One Client Per User (Recommended for Isolation)

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const userClients = new Map<string, CopilotClient>();

function getOrCreateClient(userId: string, githubToken: string): CopilotClient {
    if (!userClients.has(userId)) {
        userClients.set(userId, new CopilotClient({
            githubToken,
            useLoggedInUser: false,
        }));
    }
    return userClients.get(userId)!;
}

// Clean up clients when users log out
async function destroyClientForUser(userId: string) {
    const client = userClients.get(userId);
    if (client) {
        await client.stop();
        userClients.delete(userId);
    }
}
```

Each user's requests are billed against their own Copilot subscription. The CLI spawns a separate process per client by default, or all share a single headless CLI server via `cliUrl`.

### Shared CLI, Per-Request Token

For lower resource overhead, connect multiple SDK clients to a single headless CLI server and pass per-user tokens at client construction:

```typescript
// Start the CLI once: copilot --headless --port 4321
// Then in your API handler:
app.post("/chat", authMiddleware, async (req, res) => {
    const client = new CopilotClient({
        cliUrl: process.env.CLI_URL || "localhost:4321",
        githubToken: req.user.githubToken,
        useLoggedInUser: false,
    });

    const session = await client.createSession({
        sessionId: `user-${req.user.id}-${Date.now()}`,
        model: "gpt-4.1",
        onPermissionRequest: () => ({ kind: "approved" }),
    });

    const response = await session.sendAndWait({ prompt: req.body.message });
    await session.disconnect();
    res.json({ content: response?.data.content });
});
```

### Organization Membership Gating

Verify the user belongs to a required GitHub org before granting SDK access:

```typescript
async function verifyOrgMembership(token: string, requiredOrg: string): Promise<void> {
    const response = await fetch("https://api.github.com/user/orgs", {
        headers: { Authorization: `Bearer ${token}`, "User-Agent": "your-app/1.0" },
    });
    const orgs = await response.json();
    const isMember = orgs.some((org: { login: string }) => org.login === requiredOrg);
    if (!isMember) throw new Error(`User is not a member of ${requiredOrg}`);
}

// In your auth flow:
const token = await exchangeCodeForToken(code);
await verifyOrgMembership(token, "my-company");
const client = new CopilotClient({ githubToken: token, useLoggedInUser: false });
```

### Enterprise Managed Users (EMU)

No special SDK configuration is needed for EMU accounts. EMU users authenticate through the same GitHub OAuth flow. Enterprise IP restrictions and SAML SSO policies are enforced server-side by GitHub.

```typescript
// EMU token works identically to standard OAuth tokens
const client = new CopilotClient({
    githubToken: emuUserToken,  // gho_ prefix from EMU account
    useLoggedInUser: false,
});
```

## Session ID Strategy for Multi-User Apps

Use deterministic, user-scoped session IDs to enable session resumption across requests:

```typescript
const session = await client.createSession({
    sessionId: `user-${userId}-main`,    // Stable ID for resumption
    // or for request-scoped sessions:
    sessionId: `user-${userId}-${Date.now()}`,  // Unique per request
    model: "gpt-4.1",
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

To resume an existing session instead of creating a new one:

```typescript
try {
    session = await client.resumeSession(`user-${userId}-main`);
} catch {
    session = await client.createSession({
        sessionId: `user-${userId}-main`,
        model: "gpt-4.1",
        onPermissionRequest: () => ({ kind: "approved" }),
    });
}
```
