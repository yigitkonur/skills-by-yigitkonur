# Environment Variables Reference

## Token Environment Variables (Authentication)

These variables are read by the CLI process, not the Node.js SDK layer. Set them in the environment where the CLI spawns, or pass them via `CopilotClientOptions.env`.

### Priority Order (Highest to Lowest)

1. `COPILOT_GITHUB_TOKEN` — Explicit Copilot-scoped token; use this in all automation
2. `GH_TOKEN` — GitHub CLI compatible; used if `COPILOT_GITHUB_TOKEN` is absent
3. `GITHUB_TOKEN` — GitHub Actions compatible; used if neither above is present

```bash
# Preferred for server automation and CI
export COPILOT_GITHUB_TOKEN="gho_xxxx"

# GitHub Actions — GITHUB_TOKEN is auto-provisioned; no export needed
# GITHUB_TOKEN="{{ secrets.GITHUB_TOKEN }}" in workflow YAML
```

The SDK also accepts `CAPI_HMAC_KEY` / `COPILOT_HMAC_KEY` for HMAC auth, and `GITHUB_COPILOT_API_TOKEN` + `COPILOT_API_URL` for direct API token auth. These are internal/enterprise patterns — prefer `COPILOT_GITHUB_TOKEN` for standard deployments.

Pass environment variables programmatically to override or isolate the CLI's environment:

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient({
    env: {
        ...process.env,
        COPILOT_GITHUB_TOKEN: userSpecificToken,
    },
});
```

When `env` is set, the CLI inherits only what you explicitly include. Omitting `...process.env` strips all inherited variables — useful for sandboxed environments, but ensure `PATH` is preserved if needed.

## CLI Path

### `COPILOT_CLI_PATH`

Overrides the path to the Copilot CLI binary or JavaScript entry point. The SDK ships a bundled CLI from `@github/copilot`; set this only when you need a specific version, a custom build, or when the bundled CLI is not accessible.

```bash
export COPILOT_CLI_PATH="/usr/local/bin/copilot"
# or a JS entry point:
export COPILOT_CLI_PATH="/opt/copilot-cli/dist/index.js"
```

Equivalent in code via `CopilotClientOptions.cliPath`:

```typescript
const client = new CopilotClient({
    cliPath: process.env.COPILOT_CLI_PATH ?? "/usr/local/bin/copilot",
});
```

`cliPath` takes precedence over `COPILOT_CLI_PATH`. Do not set both — use one or the other.

## Logging

### `COPILOT_SDK_LOG_LEVEL`

Controls the CLI server's log verbosity. Valid values: `none`, `error`, `warning`, `info`, `debug`, `all`.

```bash
export COPILOT_SDK_LOG_LEVEL="debug"   # Verbose: all RPC messages + internal CLI state
export COPILOT_SDK_LOG_LEVEL="info"    # Default-level operational events
export COPILOT_SDK_LOG_LEVEL="error"   # Errors only
export COPILOT_SDK_LOG_LEVEL="none"    # Silence all CLI output
```

Equivalent in code via `CopilotClientOptions.logLevel`:

```typescript
const client = new CopilotClient({
    logLevel: (process.env.COPILOT_SDK_LOG_LEVEL as any) ?? "error",
});
```

Use `"debug"` or `"all"` only during development. In production, use `"error"` or `"warning"` to avoid log volume from streaming RPC messages.

## Azure BYOK Variables

When using Azure AI Foundry in BYOK mode, these variables are consumed by your application code (not the CLI directly):

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_AI_FOUNDRY_RESOURCE_URL` | Your Azure AI Foundry resource base URL | `https://myresource.openai.azure.com` |
| `FOUNDRY_API_KEY` | Static API key for Azure AI Foundry | `abc123...` |
| `OPENAI_API_KEY` | OpenAI API key for direct OpenAI BYOK | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude BYOK | `sk-ant-...` |

Read them in your session config:

```typescript
const session = await client.createSession({
    model: "gpt-4.1",
    provider: {
        type: "openai",
        baseUrl: `${process.env.AZURE_AI_FOUNDRY_RESOURCE_URL}/openai/v1/`,
        apiKey: process.env.FOUNDRY_API_KEY,
        wireApi: "responses",
    },
    onPermissionRequest: () => ({ kind: "approved" }),
});
```

For Azure Managed Identity (no static key), use `DefaultAzureCredential` and pass the resulting bearer token to `provider.bearerToken`. These Azure SDK variables are consumed by `DefaultAzureCredential` automatically:

| Variable | Purpose |
|----------|---------|
| `AZURE_CLIENT_ID` | Service principal or user-assigned managed identity client ID |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_CLIENT_SECRET` | Service principal client secret |

## Environment Variable Precedence Rules

Variables set in `CopilotClientOptions.env` override inherited process environment:

```typescript
// Explicit token beats any env var
const client = new CopilotClient({
    githubToken: explicitToken,        // Priority 1: always wins
    useLoggedInUser: false,
});

// Environment variable approach
const client2 = new CopilotClient({
    env: {
        COPILOT_GITHUB_TOKEN: automationToken,  // Priority 2: beats GH_TOKEN/GITHUB_TOKEN
        PATH: process.env.PATH!,                // Always preserve PATH
    },
    useLoggedInUser: false,
});
```

The resolution order for auth is enforced by the CLI process, not the Node.js SDK. The Node.js `githubToken` option is translated into `COPILOT_GITHUB_TOKEN` before being passed to the CLI, so it wins over other env vars.

## Docker and Container Environments

Pass environment variables at container runtime via `--env` or `--env-file`:

```bash
# Single container: CLI spawned by SDK inside the container
docker run \
  -e COPILOT_GITHUB_TOKEN="${COPILOT_GITHUB_TOKEN}" \
  -e COPILOT_SDK_LOG_LEVEL="warning" \
  your-app:latest

# Headless CLI as separate container
docker run -d \
  --name copilot-cli \
  -p 4321:4321 \
  -e COPILOT_GITHUB_TOKEN="${COPILOT_GITHUB_TOKEN}" \
  ghcr.io/github/copilot-cli:latest \
  --headless --port 4321
```

Docker Compose with env file:

```yaml
# docker-compose.yml
services:
  copilot-cli:
    image: ghcr.io/github/copilot-cli:latest
    command: ["--headless", "--port", "4321"]
    env_file: .env.copilot       # Contains COPILOT_GITHUB_TOKEN
    ports:
      - "4321:4321"
    restart: always

  api:
    build: .
    environment:
      - CLI_URL=copilot-cli:4321
      - COPILOT_SDK_LOG_LEVEL=warning
    depends_on:
      - copilot-cli
```

```bash
# .env.copilot (never commit to git)
COPILOT_GITHUB_TOKEN=gho_xxxx
```

When running as a headless CLI container, the SDK connects via `cliUrl` and does not need auth env vars on the API container:

```typescript
const client = new CopilotClient({
    cliUrl: process.env.CLI_URL!,   // "copilot-cli:4321" from Docker Compose
    // No githubToken here — auth is on the CLI container
});
```

## CI/CD Environment Configuration

### GitHub Actions

```yaml
# .github/workflows/copilot-task.yml
jobs:
  run-copilot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - name: Run Copilot task
        env:
          COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_GITHUB_TOKEN }}
          COPILOT_SDK_LOG_LEVEL: warning
        run: node scripts/copilot-task.js
```

Use `secrets.COPILOT_GITHUB_TOKEN` (a service account token) rather than `secrets.GITHUB_TOKEN` (ephemeral Actions token) unless the repository owner has an active Copilot subscription tied to that token.

### Jenkins / Generic CI

```bash
# Set in Jenkins credentials store, reference as environment injection
COPILOT_GITHUB_TOKEN="${COPILOT_GITHUB_TOKEN}"
COPILOT_SDK_LOG_LEVEL="error"
node scripts/copilot-task.js
```

### Kubernetes

```yaml
# k8s/copilot-deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: copilot-cli
          image: ghcr.io/github/copilot-cli:latest
          args: ["--headless", "--port", "4321"]
          env:
            - name: COPILOT_GITHUB_TOKEN
              valueFrom:
                secretKeyRef:
                  name: copilot-secrets
                  key: github-token
            - name: COPILOT_SDK_LOG_LEVEL
              value: "warning"
```

```bash
kubectl create secret generic copilot-secrets \
  --from-literal=github-token="gho_xxxx"
```

## Security Considerations

**Never hardcode tokens in source code.** Always read from environment at runtime.

**Rotate tokens regularly.** GitHub OAuth tokens for service accounts should be rotated on a schedule (monthly or per security policy). `gho_` tokens do not expire by default — treat them like passwords.

**Limit token scope.** When registering an OAuth App for automation, request only the `copilot` scope. Do not request broader scopes (repo, org) unless your application requires them.

**Protect the CLI network port.** When running the CLI in headless mode, bind to `127.0.0.1` or restrict with firewall rules. There is no built-in authentication between the SDK and CLI server:

```bash
# Bind to localhost only (not 0.0.0.0)
copilot --headless --port 4321 --host 127.0.0.1
```

**Use secrets management.** In production, use a secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) rather than plain environment variables in deployment configs. Inject secrets at runtime via the manager's agent sidecar or init container.

**Audit env var exposure.** When `CopilotClientOptions.env` is set, only the explicitly included variables are passed to the CLI. Do not spread `process.env` blindly in security-sensitive deployments — it may expose unrelated secrets present in the parent process environment.

```typescript
// Minimal safe env for CLI — only what it needs
const client = new CopilotClient({
    env: {
        PATH: process.env.PATH!,
        HOME: process.env.HOME!,
        COPILOT_GITHUB_TOKEN: process.env.COPILOT_GITHUB_TOKEN!,
        // Do NOT spread all of process.env here if it contains unrelated secrets
    },
});
```
