# Authentication and BYOK

## Authentication methods

| Method | Use Case | Copilot Subscription Required |
|--------|----------|-------------------------------|
| Signed-in user (default) | Interactive apps | Yes |
| GitHub OAuth | Apps on behalf of users | Yes |
| Environment variables | CI/CD, automation | Yes |
| BYOK (Bring Your Own Key) | Own API keys | No |

## Default: signed-in user

User signs in with the current Copilot CLI command. SDK uses stored credentials automatically.

```bash
copilot login
```

```typescript
const client = new CopilotClient(); // no config needed
```

For a machine-readable preflight, call `await client.getAuthStatus()` before `createSession()`.

## GitHub OAuth

Pass user access token from OAuth flow:

```typescript
const client = new CopilotClient({
  githubToken: userAccessToken, // gho_xxx or ghu_xxx
  useLoggedInUser: false,
});
```

### Supported token types

| Prefix | Type | Supported |
|--------|------|-----------|
| `gho_` | OAuth user access tokens | Yes |
| `ghu_` | GitHub App user access tokens | Yes |
| `github_pat_` | Fine-grained PATs | Yes |
| `ghp_` | Classic PATs (deprecated) | **No** |

### OAuth callback handler

```typescript
async function handleOAuthCallback(code: string): Promise<string> {
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
  return data.access_token; // gho_xxx
}
```

### Per-user client pattern

```typescript
const clients = new Map<string, CopilotClient>();

function getClientForUser(userId: string, token: string): CopilotClient {
  if (!clients.has(userId)) {
    clients.set(userId, new CopilotClient({
      githubToken: token,
      useLoggedInUser: false,
    }));
  }
  return clients.get(userId)!;
}
```

## Environment variables

Priority order (checked automatically):

1. `COPILOT_GITHUB_TOKEN` (recommended)
2. `GH_TOKEN` (GitHub CLI compatible)
3. `GITHUB_TOKEN` (GitHub Actions compatible)

No code changes needed — SDK auto-detects.

Set the environment variable before you start the Node.js process. This is the safest path for CI, containers, and other non-interactive runs.

### Practical auth order for app builders

1. Explicit `githubToken` in constructor
2. Env var tokens (`COPILOT_GITHUB_TOKEN` → `GH_TOKEN` → `GITHUB_TOKEN`)
3. Stored CLI credentials from `copilot login`

If you are writing app code, rely on the public flows above instead of undocumented internal auth environment variables.

## BYOK (Bring Your Own Key)

Use your own API keys. No Copilot subscription required.

### ProviderConfig

```typescript
interface ProviderConfig {
  type?: "openai" | "azure" | "anthropic";  // default "openai"
  wireApi?: "completions" | "responses";     // default "completions"
  baseUrl: string;                           // REQUIRED
  apiKey?: string;
  bearerToken?: string;                      // takes precedence over apiKey
  azure?: {
    apiVersion?: string;                     // default "2024-10-21"
  };
}
```

### Wire API formats

- `"completions"` (default) — Chat Completions API (`/chat/completions`). Use for most models.
- `"responses"` — Responses API. Use for GPT-5 series models.

### Provider examples

**OpenAI:**
```typescript
provider: {
  type: "openai",
  baseUrl: "https://api.openai.com/v1",
  apiKey: process.env.OPENAI_API_KEY,
}
```

**Azure OpenAI (native endpoint):**
```typescript
provider: {
  type: "azure",
  baseUrl: "https://my-resource.openai.azure.com", // just the host
  apiKey: process.env.AZURE_API_KEY,
}
```

**Azure AI Foundry (OpenAI-compatible):**
```typescript
provider: {
  type: "openai",
  baseUrl: "https://your-resource.openai.azure.com/openai/v1/",
  apiKey: process.env.AZURE_API_KEY,
}
```

**Anthropic:**
```typescript
provider: {
  type: "anthropic",
  baseUrl: "https://api.anthropic.com",
  apiKey: process.env.ANTHROPIC_API_KEY,
}
```

**Ollama (local, no key):**
```typescript
provider: {
  type: "openai",
  baseUrl: "http://localhost:11434/v1",
}
```

**vLLM / LiteLLM:**
```typescript
provider: {
  type: "openai",
  baseUrl: "http://localhost:8000/v1",
  apiKey: process.env.VLLM_API_KEY,
}
```

### BYOK requires `model`

```typescript
// WRONG — will error:
await client.createSession({
  provider: { type: "openai", baseUrl: "..." },
  onPermissionRequest: approveAll,
});

// CORRECT:
await client.createSession({
  model: "gpt-4",
  provider: { type: "openai", baseUrl: "..." },
  onPermissionRequest: approveAll,
});
```

### Custom model listing

Override `client.listModels()` for BYOK:

```typescript
const client = new CopilotClient({
  onListModels: () => [{
    id: "my-model",
    name: "My Custom Model",
    capabilities: {
      supports: { vision: false, reasoningEffort: false },
      limits: { max_context_window_tokens: 128000 },
    },
  }],
});
```

Results are cached after first call.

### BYOK limitations

- Static API keys or bearer tokens only (no Entra ID / Managed Identity auto-refresh)
- `bearerToken` is static — no automatic refresh for short-lived tokens
- Rate limits are provider-specific
- Usage tracked by your provider, not GitHub
- Premium request quotas are not consumed

## Auth status check

```typescript
const auth = await client.getAuthStatus();
// {
//   isAuthenticated: true,
//   authType: "user" | "env" | "gh-cli" | "hmac" | "api-key" | "token",
//   host: "github.com",
//   login: "username",
//   statusMessage: "Authenticated via user credentials"
// }
```

### Headless preflight

Use this pattern before your first `createSession()` in automation:

```typescript
const client = new CopilotClient();
const auth = await client.getAuthStatus();

if (!auth.isAuthenticated) {
  throw new Error(
    "Authenticate with `copilot login` or set COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN before starting the process."
  );
}
```

## Quota check

```typescript
const quota = await client.rpc.account.getQuota();
// { quotaSnapshots: { "chat": { entitlementRequests, usedRequests, remainingPercentage, ... } } }
```

## Steering notes

> Common mistakes agents make with authentication and BYOK.

- **Default auth (no config) works out of the box** if the user has the Copilot CLI installed and authenticated with `copilot login`. For a code-level preflight, call `await client.getAuthStatus()` before `createSession()`.
- **For non-interactive runs, prefer env-var auth** (`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`) over waiting for the CLI to prompt for login.
- **Use `client.getAuthStatus()` for automation checks**. The current public CLI auth surface is `copilot login` plus env-var tokens, so use the SDK call for a machine-readable preflight instead of shelling out to a separate auth-status command.
- **BYOK requires BOTH `provider` and `model`** in `createSession`. Omitting `model` creates the session successfully but `sendAndWait` will fail with an unhelpful error. Always pair them:
  ```typescript
  const session = await client.createSession({
    provider: { type: "openai", baseUrl: "...", apiKey: "..." },
    model: "gpt-4.1",  // REQUIRED with provider
    onPermissionRequest: approveAll,
  });
  ```
- **BYOK tokens are static** — the SDK doesn't refresh them. If your token expires mid-session, requests fail. For long-running apps, implement token rotation at the application level.
- **`GITHUB_TOKEN` env var** is checked automatically. You don't need to pass it in code. But if set, it takes priority over OAuth tokens.
- **GitHub App user tokens still go through `githubToken`**. If you mint a `ghu_` user access token outside the SDK, pass it as `githubToken`; the public SDK surface shown here does not expose a separate `authConfig.appAuth` object.
