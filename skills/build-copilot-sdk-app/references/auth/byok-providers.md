# BYOK (Bring Your Own Key) Provider Reference

## Overview

BYOK bypasses GitHub Copilot authentication entirely. No Copilot subscription is required. You supply credentials for a model provider directly via `SessionConfig.provider` (typed as `ProviderConfig`). The `model` field in `SessionConfig` is **required** when `provider` is set — omitting it causes a runtime error.

## `ProviderConfig` Type

```typescript
// From @github/copilot-sdk types.ts
interface ProviderConfig {
    type?: "openai" | "azure" | "anthropic";  // Default: "openai"
    wireApi?: "completions" | "responses";      // Default: "completions"
    baseUrl: string;                            // Required. Full endpoint URL.
    apiKey?: string;                            // Optional for local providers (Ollama, Foundry Local)
    bearerToken?: string;                       // Takes precedence over apiKey when both set
    azure?: {
        apiVersion?: string;                    // Default: "2024-10-21"
    };
}
```

Pass `ProviderConfig` inside `SessionConfig.provider`:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import type { ProviderConfig } from "@github/copilot-sdk";

const provider: ProviderConfig = {
    type: "openai",
    baseUrl: "https://api.openai.com/v1",
    apiKey: process.env.OPENAI_API_KEY,
};

const client = new CopilotClient();
const session = await client.createSession({
    model: "gpt-4.1",   // Required with provider
    provider,
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

## `wireApi` Option

Controls which HTTP API format the CLI uses when calling your provider endpoint.

| Value | Endpoint Called | Use When |
|-------|----------------|----------|
| `"completions"` (default) | `POST /chat/completions` | Most models; GPT-4 series; Anthropic; Ollama |
| `"responses"` | `POST /responses` | GPT-5 series models on Azure AI Foundry or OpenAI |

```typescript
// Use "responses" for GPT-5 series
provider: {
    type: "openai",
    baseUrl: "https://your-resource.openai.azure.com/openai/v1/",
    apiKey: process.env.FOUNDRY_API_KEY,
    wireApi: "responses",  // Required for gpt-5.2-codex, gpt-5.4, etc.
}

// Use "completions" (or omit) for everything else
provider: {
    type: "openai",
    baseUrl: "https://api.openai.com/v1",
    apiKey: process.env.OPENAI_API_KEY,
    // wireApi defaults to "completions"
}
```

## OpenAI Provider

```typescript
// Direct OpenAI API
const session = await client.createSession({
    model: "gpt-4.1",
    provider: {
        type: "openai",
        baseUrl: "https://api.openai.com/v1",   // Full path including /v1
        apiKey: process.env.OPENAI_API_KEY,      // sk-...
        // wireApi: "completions"               // Default; omit unless using GPT-5
    },
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

`baseUrl` must include the `/v1` path segment for OpenAI. The SDK appends `/chat/completions` or `/responses` to this base — do not include those path segments.

```typescript
// OpenAI-compatible endpoints (vLLM, LiteLLM, etc.)
provider: {
    type: "openai",
    baseUrl: "http://your-vllm-server:8000/v1",
    apiKey: process.env.VLLM_API_KEY,    // May be arbitrary string or empty for local
}
```

## Azure OpenAI Provider

Two distinct endpoint patterns exist for Azure. Use the correct `type` for each:

### Native Azure OpenAI Endpoint (`*.openai.azure.com` without `/openai/v1/`)

```typescript
// type: "azure" — SDK constructs Azure-specific paths internally
provider: {
    type: "azure",
    baseUrl: "https://my-resource.openai.azure.com",  // Host ONLY — no path suffix
    apiKey: process.env.AZURE_OPENAI_KEY,
    azure: {
        apiVersion: "2024-10-21",  // Default; override if your deployment requires different
    },
}
```

Do not append `/openai/v1/` to `baseUrl` when using `type: "azure"`. The SDK handles Azure path construction. Appending the path causes double-path errors.

### Azure AI Foundry OpenAI-Compatible Endpoint (with `/openai/v1/`)

```typescript
// type: "openai" — endpoint already includes /openai/v1/ path
provider: {
    type: "openai",
    baseUrl: "https://your-resource.openai.azure.com/openai/v1/",  // Full path required
    apiKey: process.env.FOUNDRY_API_KEY,
    wireApi: "responses",  // Use for GPT-5 series deployments
}
```

Decision rule: if your `baseUrl` ends with `/openai/v1/`, use `type: "openai"`. If it is just the host, use `type: "azure"`.

### Azure Managed Identity (Bearer Token)

When using `DefaultAzureCredential` instead of a static API key:

```typescript
import { DefaultAzureCredential } from "@azure/identity";
import { CopilotClient } from "@github/copilot-sdk";

const credential = new DefaultAzureCredential();
const tokenResponse = await credential.getToken(
    "https://cognitiveservices.azure.com/.default"
);

const client = new CopilotClient();
const session = await client.createSession({
    model: "gpt-4.1",
    provider: {
        type: "openai",
        baseUrl: `${process.env.AZURE_AI_FOUNDRY_RESOURCE_URL}/openai/v1/`,
        bearerToken: tokenResponse.token,  // Static string; expires in ~1 hour
        wireApi: "responses",
    },
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

Bearer tokens from Entra ID expire (~1 hour). Refresh before each session creation for long-running applications:

```typescript
async function createSessionWithFreshToken(client: CopilotClient, model: string) {
    const credential = new DefaultAzureCredential();
    const { token } = await credential.getToken(
        "https://cognitiveservices.azure.com/.default"
    );
    return client.createSession({
        model,
        provider: {
            type: "openai",
            baseUrl: `${process.env.AZURE_AI_FOUNDRY_RESOURCE_URL}/openai/v1/`,
            bearerToken: token,
            wireApi: "responses",
        },
        onPermissionRequest: () => ({ kind: "approved" }),
    });
}
```

`bearerToken` takes precedence over `apiKey` when both are set. The SDK does not automatically refresh bearer tokens — this is your responsibility.

## Anthropic Provider

```typescript
const session = await client.createSession({
    model: "claude-opus-4",    // Anthropic model name — must match provider's supported models
    provider: {
        type: "anthropic",
        baseUrl: "https://api.anthropic.com",   // Base URL only; no path suffix
        apiKey: process.env.ANTHROPIC_API_KEY,   // sk-ant-...
        // wireApi not applicable for anthropic type
    },
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

`wireApi` is only applicable for `type: "openai"` and `type: "azure"`. Do not set it for `type: "anthropic"`.

## Local Providers

### Ollama

```typescript
provider: {
    type: "openai",
    baseUrl: "http://localhost:11434/v1",
    // No apiKey required for local Ollama
}

// Model must match a pulled Ollama model name
const session = await client.createSession({
    model: "llama3.2",   // Must match: ollama list
    provider: { type: "openai", baseUrl: "http://localhost:11434/v1" },
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

Verify Ollama is running: `curl http://localhost:11434/v1/models`

### Microsoft Foundry Local

```typescript
// Port is dynamic — check with: foundry service status
provider: {
    type: "openai",
    baseUrl: "http://localhost:5272/v1",  // Replace port from `foundry service status`
    // No apiKey required
}
```

## Bearer Token Authentication

Use `bearerToken` for providers requiring `Authorization: Bearer <token>` instead of an API key:

```typescript
provider: {
    type: "openai",
    baseUrl: "https://custom-llm-gateway.example.com/v1",
    bearerToken: process.env.MY_BEARER_TOKEN,  // Sets Authorization header directly
    // Do NOT set apiKey when using bearerToken — bearerToken wins anyway
}
```

`bearerToken` is a static string. The SDK never refreshes it. If the token expires, requests fail with a 401. Create a new session with a fresh token.

## `onListModels` Callback

When using BYOK, `client.listModels()` does not query the CLI's default model list (which reflects GitHub Copilot's available models). Supply `onListModels` at client construction to return your provider's model list in the standard `ModelInfo` format:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import type { ModelInfo } from "@github/copilot-sdk";

const client = new CopilotClient({
    onListModels: (): ModelInfo[] => [
        {
            id: "gpt-4.1",
            name: "GPT-4.1",
            capabilities: {
                supports: { vision: true, reasoningEffort: false },
                limits: { max_context_window_tokens: 128000 },
            },
        },
        {
            id: "gpt-5.4",
            name: "GPT-5.4",
            capabilities: {
                supports: { vision: true, reasoningEffort: true },
                limits: { max_context_window_tokens: 200000 },
            },
            supportedReasoningEfforts: ["low", "medium", "high", "xhigh"],
            defaultReasoningEffort: "medium",
        },
    ],
});

// client.listModels() now returns your custom list; no CLI RPC call occurs
const models = await client.listModels();
```

The result is cached after the first call, same as default behavior. `onListModels` completely replaces the CLI's `models.list` RPC — no fallback occurs.

For async model discovery (fetching from provider's `/models` endpoint):

```typescript
const client = new CopilotClient({
    onListModels: async (): Promise<ModelInfo[]> => {
        const response = await fetch("https://api.openai.com/v1/models", {
            headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
        });
        const data = await response.json();
        return data.data.map((m: any) => ({
            id: m.id,
            name: m.id,
            capabilities: {
                supports: { vision: m.id.includes("vision"), reasoningEffort: false },
                limits: { max_context_window_tokens: 128000 },
            },
        }));
    },
});
```

## Model Selection with BYOK

`model` in `SessionConfig` must match the exact model identifier your provider expects — not GitHub Copilot model IDs. The SDK passes this string verbatim to the provider endpoint.

```typescript
// OpenAI — use OpenAI model IDs
await client.createSession({ model: "gpt-4.1", provider: openaiProvider, ... });

// Azure AI Foundry — use your deployment name
await client.createSession({ model: "my-gpt4-deployment", provider: azureProvider, ... });

// Anthropic — use Anthropic model IDs
await client.createSession({ model: "claude-opus-4-5", provider: anthropicProvider, ... });

// Ollama — use the pulled model name
await client.createSession({ model: "llama3.2:8b", provider: ollamaProvider, ... });
```

Omitting `model` when `provider` is set causes this error: `"Model not specified"`. Always provide `model` with BYOK.

## Provider in Full SessionConfig

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient({
    onListModels: () => [/* your models */],
});

const session = await client.createSession({
    sessionId: "byok-session-001",
    model: "gpt-4.1",             // Required with provider
    provider: {
        type: "openai",
        baseUrl: "https://api.openai.com/v1",
        apiKey: process.env.OPENAI_API_KEY,
        wireApi: "completions",   // Explicit; matches default
    },
    onPermissionRequest: approveAll,  // From @github/copilot-sdk; approves all tool calls
    streaming: false,
});
```

`approveAll` is a convenience export that returns `{ kind: "approved" }` for all permission requests. Use it in BYOK automation where interactive permission prompts are not needed.

## Cost and Rate Limit Considerations

With BYOK:
- Billing goes directly to your provider account, not GitHub Copilot
- Usage does not count against Copilot premium request quotas
- Rate limits are governed by your provider's plan (OpenAI tier, Azure quota, etc.)
- The SDK does not implement retry-after logic for provider rate limits — add it in your application layer

```typescript
// Basic retry wrapper for provider rate limits
async function createSessionWithRetry(client: CopilotClient, config: SessionConfig) {
    for (let attempt = 0; attempt < 3; attempt++) {
        try {
            return await client.createSession(config);
        } catch (err: any) {
            if (err.message?.includes("429") && attempt < 2) {
                await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
                continue;
            }
            throw err;
        }
    }
}
```

## Testing BYOK Configurations

Validate a provider config before integrating into production:

```typescript
async function testProviderConfig(provider: ProviderConfig, model: string): Promise<void> {
    const client = new CopilotClient({
        logLevel: "debug",
        useLoggedInUser: false,
    });

    const session = await client.createSession({
        model,
        provider,
        onPermissionRequest: () => ({ kind: "approved" }),
    });

    const response = await session.sendAndWait({ prompt: "Reply with just: OK" });
    console.log("Provider test response:", response?.data.content);

    await session.disconnect();
    await client.stop();
}

// Usage
await testProviderConfig(
    { type: "openai", baseUrl: "https://api.openai.com/v1", apiKey: process.env.OPENAI_API_KEY! },
    "gpt-4.1"
);
```

Check these when a BYOK config fails:
1. `baseUrl` format: `type: "azure"` takes host only; `type: "openai"` needs `/v1` path
2. `model` string matches provider's exact model or deployment name
3. API key is valid and not expired
4. `wireApi` matches the model generation (`"responses"` for GPT-5, `"completions"` for everything else)
5. For bearer tokens: token is not expired (check `expires_on` from token response)

## Supported Providers Summary

| Provider | `type` | `baseUrl` Format | `wireApi` | Key Field |
|----------|--------|-----------------|-----------|-----------|
| OpenAI | `"openai"` | `https://api.openai.com/v1` | `"completions"` / `"responses"` | `apiKey` |
| Azure OpenAI (native) | `"azure"` | `https://resource.openai.azure.com` (host only) | `"completions"` / `"responses"` | `apiKey` |
| Azure AI Foundry (OpenAI-compat) | `"openai"` | `https://resource.openai.azure.com/openai/v1/` | `"completions"` / `"responses"` | `apiKey` or `bearerToken` |
| Azure Managed Identity | `"openai"` | `https://resource.openai.azure.com/openai/v1/` | `"responses"` | `bearerToken` (from DefaultAzureCredential) |
| Anthropic | `"anthropic"` | `https://api.anthropic.com` | n/a | `apiKey` |
| Ollama (local) | `"openai"` | `http://localhost:11434/v1` | `"completions"` | none |
| Foundry Local (local) | `"openai"` | `http://localhost:<PORT>/v1` | `"completions"` | none |
| vLLM / LiteLLM | `"openai"` | Your server URL + `/v1` | `"completions"` | `apiKey` |
