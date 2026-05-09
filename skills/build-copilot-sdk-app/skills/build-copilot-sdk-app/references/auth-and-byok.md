# Authentication and BYOK

Check the installed package before copying auth code. As of the 2026-05-08 audit baseline, the npm `latest` package is `0.3.0`, `prerelease` is `1.0.0-beta.3`, and the TypeScript option is `gitHubToken` with a capital `H`. Some GitHub Docs pages still show `githubToken`; code must follow the installed `dist/types.d.ts`.

## Supported auth paths

| Method | Use case | Copilot subscription |
|---|---|---|
| Signed-in GitHub user | Local apps and development | Required |
| OAuth GitHub App user token | Apps acting for users | Required |
| Environment GitHub token | CI, containers, automation | Required |
| BYOK provider credentials | Own OpenAI-compatible, Azure, Anthropic, or local model provider | Not required |

Official docs also describe direct API token environment variables (`GITHUB_COPILOT_API_TOKEN` with `COPILOT_API_URL`) in the auth priority list. The current stable package exposes no constructor option for that path; do not build undocumented internal guidance around it unless the current package and docs for the chosen deployment path explicitly require it.

## Default signed-in user

The SDK uses stored Copilot CLI credentials when no explicit token or provider is configured:

```typescript
const client = new CopilotClient();
```

For interactive setup, authenticate with the Copilot CLI available to the project or globally:

```bash
npx copilot login
# or, when installed globally:
copilot login
```

The package includes bundled CLI support through `@github/copilot`, so a global `copilot` command is not automatically required for every app. External server and local interactive workflows still need a CLI process that is authenticated.

Preflight with the SDK, not by parsing CLI output:

```typescript
const auth = await client.getAuthStatus();
if (!auth.isAuthenticated) {
  throw new Error("Authenticate with Copilot CLI or set COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN.");
}
```

## OAuth GitHub App token

Use `gitHubToken`, not `githubToken`, in current TypeScript:

```typescript
const client = new CopilotClient({
  gitHubToken: userAccessToken,
  useLoggedInUser: false,
});
```

Supported token prefixes from GitHub Docs:

| Prefix | Token |
|---|---|
| `gho_` | OAuth user access token |
| `ghu_` | GitHub App user access token |
| `github_pat_` | Fine-grained personal access token |

Classic `ghp_` PATs are not a supported path in the current GitHub Docs.

### Per-user client pattern

```typescript
const clients = new Map<string, CopilotClient>();

function getClientForUser(userId: string, token: string): CopilotClient {
  let client = clients.get(userId);
  if (!client) {
    client = new CopilotClient({ gitHubToken: token, useLoggedInUser: false });
    clients.set(userId, client);
  }
  return client;
}
```

Session-level `gitHubToken` also exists in current types. Use it for multi-tenant sessions when the CLI process has one auth context but each session should use a different GitHub identity:

```typescript
await client.createSession({
  gitHubToken: userAccessToken,
  model: "gpt-5",
  onPermissionRequest: approveAll,
});
```

## Environment variables

GitHub Docs list this priority for environment tokens:

1. `COPILOT_GITHUB_TOKEN`
2. `GH_TOKEN`
3. `GITHUB_TOKEN`

Set the variable before starting Node. Do not log token values.

## Practical auth order

For implementation work, resolve auth in this order:

1. BYOK `provider` plus `model`, when the app intentionally bypasses GitHub Copilot auth.
2. Explicit `gitHubToken` in `CopilotClientOptions` or `SessionConfig`, when acting for a user.
3. Environment token (`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`).
4. Stored CLI credentials from `copilot login` or equivalent project/global CLI auth.

## BYOK requirements

BYOK uses your provider credentials and does not require a GitHub Copilot subscription. Provider billing, quotas, model availability, and rate limits apply.

Every BYOK session needs both:

- `provider`: endpoint and credentials
- `model`: the provider model or deployment name

Current package README says the SDK throws if `provider` is set without `model`. Verify this against the selected runtime, but never omit `model`.

```typescript
const session = await client.createSession({
  model: process.env.COPILOT_MODEL ?? "gpt-4.1",
  provider: {
    type: "openai",
    baseUrl: "https://api.openai.com/v1",
    apiKey: process.env.OPENAI_API_KEY,
  },
  onPermissionRequest: approveAll,
});
```

## ProviderConfig fields

Stable `0.3.0` fields from `dist/types.d.ts`:

```typescript
interface ProviderConfig {
  type?: "openai" | "azure" | "anthropic";
  wireApi?: "completions" | "responses";
  baseUrl: string;
  apiKey?: string;
  bearerToken?: string;
  azure?: { apiVersion?: string };
  headers?: Record<string, string>;
}
```

Prerelease `1.0.0-beta.3` also adds provider-level model mapping and token budget fields:

```typescript
interface ProviderConfig {
  modelId?: string;
  wireModel?: string;
  maxInputTokens?: number;
}
```

Only use prerelease-only fields when the selected package version includes them.

## Provider env vars

| Provider path | Required env vars | Session `model` |
|---|---|---|
| OpenAI direct | `OPENAI_API_KEY` | OpenAI model ID, for example `gpt-4.1` |
| Azure OpenAI native | `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, optional `AZURE_OPENAI_API_VERSION` | Azure deployment name |
| Azure AI Foundry OpenAI-compatible | `FOUNDRY_API_KEY`, `FOUNDRY_BASE_URL` | Foundry deployment/model name |
| Anthropic | `ANTHROPIC_API_KEY` | Claude model ID |
| Ollama | optional `OLLAMA_BASE_URL` | Local Ollama model name |
| vLLM/LiteLLM/OpenAI-compatible | provider-specific key, `OPENAI_COMPAT_BASE_URL` | Provider model name |

## Provider examples

### OpenAI direct

```typescript
provider: {
  type: "openai",
  baseUrl: "https://api.openai.com/v1",
  apiKey: process.env.OPENAI_API_KEY,
}
```

### Azure OpenAI native endpoint

Use the GitHub Docs native Azure path when the endpoint is only the Azure resource host:

```typescript
provider: {
  type: "azure",
  baseUrl: process.env.AZURE_OPENAI_ENDPOINT!, // https://RESOURCE.openai.azure.com
  apiKey: process.env.AZURE_OPENAI_KEY,
  azure: {
    apiVersion: process.env.AZURE_OPENAI_API_VERSION ?? "2024-10-21",
  },
}
```

For this path, do not append `/openai/v1`; the SDK handles native Azure paths.

### Azure AI Foundry OpenAI-compatible endpoint

Use the GitHub Docs OpenAI-compatible path when Azure gives an `/openai/v1/` endpoint:

```typescript
provider: {
  type: "openai",
  baseUrl: process.env.FOUNDRY_BASE_URL!, // https://RESOURCE.openai.azure.com/openai/v1/
  apiKey: process.env.FOUNDRY_API_KEY,
  wireApi: "responses",
}
```

This is intentionally `type: "openai"` because the endpoint speaks the OpenAI-compatible API.

### Anthropic

```typescript
provider: {
  type: "anthropic",
  baseUrl: "https://api.anthropic.com",
  apiKey: process.env.ANTHROPIC_API_KEY,
}
```

### Ollama

```typescript
provider: {
  type: "openai",
  baseUrl: process.env.OLLAMA_BASE_URL ?? "http://localhost:11434/v1",
}
```

### Static bearer token or custom headers

```typescript
provider: {
  type: "openai",
  baseUrl: process.env.OPENAI_COMPAT_BASE_URL!,
  bearerToken: process.env.PROVIDER_BEARER_TOKEN,
  headers: { "X-Provider-Feature": "enabled" },
}
```

`bearerToken` takes precedence over `apiKey`.

## Custom model listing

For BYOK, provide `onListModels` when the CLI cannot discover your provider's models:

```typescript
const client = new CopilotClient({
  onListModels: () => [{
    id: "my-model",
    name: "My Model",
    capabilities: {
      supports: { vision: false, reasoningEffort: false },
      limits: { max_context_window_tokens: 128000 },
    },
  }],
});
```

Results are cached after the first call.

## BYOK limitations

- Static API key or static bearer token only.
- No automatic Managed Identity, Entra ID, OIDC, SAML, or service-principal refresh unless current docs and package types add a refresh mechanism.
- Short-lived bearer tokens can expire mid-session; rotate in application code by creating new sessions with fresh credentials.
- Provider billing, rate limits, model availability, and regional constraints apply.
- BYOK usage is tracked by the provider, not GitHub, and does not consume Copilot premium request quotas.
- Copilot SDK is public preview; do not claim production readiness beyond current GitHub statements.

## Steering notes

- Always spell current TypeScript token options as `gitHubToken`.
- Use `client.getAuthStatus()` for GitHub-auth preflight; BYOK provider credentials are validated by provider calls.
- For BYOK, fail fast if the required provider env var or `model` is missing.
- Prefer `type: "azure"` only for native Azure OpenAI host endpoints; use `type: "openai"` for `/openai/v1/` OpenAI-compatible endpoints.
