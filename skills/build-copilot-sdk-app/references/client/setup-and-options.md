# CopilotClient: Setup and Options

## Import Pattern

The SDK is ESM-only. Use named import only:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
```

Never use `require()`. Never use default import. If your project uses CommonJS, configure a bundler or set `"type": "module"` in `package.json`.

## Constructor Signature

```typescript
new CopilotClient(options?: CopilotClientOptions): CopilotClient
```

Throws synchronously if mutually exclusive options are combined:
- `cliUrl` + `useStdio: true` → throws
- `cliUrl` + `cliPath` → throws
- `cliUrl` + `githubToken` → throws
- `cliUrl` + `useLoggedInUser` → throws
- `isChildProcess: true` + `cliUrl` → throws
- `isChildProcess: true` + `useStdio: false` → throws

## All ClientConfig Fields

```typescript
interface CopilotClientOptions {
  // TRANSPORT
  useStdio?: boolean;           // Default: true. false uses TCP.
  cliUrl?: string;              // External server URL. Mutually exclusive with useStdio/cliPath.
  port?: number;                // Default: 0 (random). TCP mode only, when spawning local CLI.

  // CLI PROCESS
  cliPath?: string;             // Default: bundled CLI from @github/copilot package.
  cliArgs?: string[];           // Extra args inserted before SDK-managed args.
  cwd?: string;                 // Default: process.cwd().
  isChildProcess?: boolean;     // Default: false. True when SDK runs as child of CLI server.

  // LOGGING
  logLevel?: "none" | "error" | "warning" | "info" | "debug" | "all";  // Default: "debug"

  // LIFECYCLE
  autoStart?: boolean;          // Default: true. Auto-start on first createSession().
  autoRestart?: boolean;        // Default: true. Auto-restart CLI if it crashes.

  // AUTHENTICATION
  env?: Record<string, string | undefined>;  // Default: process.env
  githubToken?: string;         // Explicit GitHub token. Sets useLoggedInUser=false by default.
  useLoggedInUser?: boolean;    // Default: true (false when githubToken provided).

  // MODELS
  onListModels?: () => Promise<ModelInfo[]> | ModelInfo[];  // BYOK custom model list override.
}
```

## Default Values Table

| Field | Default | Notes |
|-------|---------|-------|
| `useStdio` | `true` | Overridden to `false` when `cliUrl` provided |
| `cliPath` | bundled CLI | Resolved via `@github/copilot/sdk` export |
| `cliArgs` | `[]` | |
| `cwd` | `process.cwd()` | |
| `port` | `0` | Random port; TCP mode only |
| `logLevel` | `"debug"` | |
| `autoStart` | `true` | |
| `autoRestart` | `true` | |
| `env` | `process.env` | |
| `useLoggedInUser` | `true` | `false` when `githubToken` provided |

## Environment Variables

The SDK reads auth tokens from CLI process environment (not from SDK process directly). Pass them via `env` option or rely on inherited `process.env`.

Priority order for token resolution (highest to lowest):

```
COPILOT_GITHUB_TOKEN   → Recommended, Copilot-specific
GH_TOKEN               → GitHub CLI compatible
GITHUB_TOKEN           → GitHub Actions compatible
```

When `githubToken` option is set programmatically, it is injected as `COPILOT_SDK_AUTH_TOKEN` in the subprocess environment and passed to CLI via `--auth-token-env COPILOT_SDK_AUTH_TOKEN`.

Set token via option (preferred for dynamic tokens):

```typescript
const client = new CopilotClient({
  githubToken: await getUserToken(),  // Takes priority over env vars
  useLoggedInUser: false,             // Disable keychain lookup
});
```

Set token via environment (preferred for server deployments):

```bash
export COPILOT_GITHUB_TOKEN="gho_xxxx"
# No code changes needed — SDK inherits process.env
```

Pass custom env to subprocess (isolates subprocess env from parent):

```typescript
const client = new CopilotClient({
  env: {
    ...process.env,
    COPILOT_GITHUB_TOKEN: process.env.MY_COPILOT_TOKEN,
  },
});
```

Never pass `NODE_DEBUG` to the subprocess env — the SDK strips it automatically to prevent stdout pollution in stdio mode.

## Complete Constructor Examples

### Minimal (local dev, bundled CLI, stdio):

```typescript
const client = new CopilotClient();
// Equivalent to:
const client = new CopilotClient({
  useStdio: true,
  autoStart: true,
  autoRestart: true,
  logLevel: "debug",
});
```

### All options (annotation of every field):

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

const client = new CopilotClient({
  // Transport: spawn local CLI via stdio (default)
  useStdio: true,

  // CLI location: custom binary (e.g., bundled in your app)
  cliPath: join(__dirname, "../vendor/copilot"),

  // Extra CLI flags passed before SDK-managed args
  cliArgs: ["--disable-telemetry"],

  // Working directory for the CLI process
  cwd: "/path/to/project",

  // Port only matters in TCP mode (useStdio: false, no cliUrl)
  port: 0,  // 0 = random available port

  // Log verbosity for the CLI subprocess
  logLevel: "info",

  // Lifecycle: auto-start on first createSession (default true)
  autoStart: true,

  // Lifecycle: auto-restart if CLI crashes (default true)
  autoRestart: true,

  // Auth: inject token into CLI subprocess
  githubToken: process.env.MY_GITHUB_TOKEN,

  // Auth: skip keychain/gh-cli auth since token is explicit
  useLoggedInUser: false,

  // Env: pass custom env to CLI subprocess (strips NODE_DEBUG automatically)
  env: { ...process.env, MY_VAR: "value" },

  // Models: custom BYOK model list
  onListModels: async () => [
    {
      id: "gpt-4o",
      name: "GPT-4o",
      capabilities: {
        supports: { vision: true, reasoningEffort: false },
        limits: { max_context_window_tokens: 128000 },
      },
    },
  ],
});
```

### External server (TCP, no subprocess):

```typescript
const client = new CopilotClient({
  cliUrl: "localhost:4321",
  // cliPath, useStdio, githubToken, useLoggedInUser are ALL forbidden with cliUrl
});
```

Accepted `cliUrl` formats:
- `"4321"` → `localhost:4321`
- `"localhost:4321"` → `localhost:4321`
- `"http://127.0.0.1:4321"` → `127.0.0.1:4321`
- `"https://cli.internal:4321"` → `cli.internal:4321`

### Child process mode (SDK running inside CLI):

```typescript
const client = new CopilotClient({
  isChildProcess: true,
  useStdio: true,  // Required with isChildProcess
  // Uses process.stdin/process.stdout to communicate with parent CLI
});
```

## Node.js and CLI Version Requirements

- Node.js minimum: check `engines` in `package.json` of `@github/copilot-sdk`
- The SDK uses `import.meta.resolve` — requires Node.js 20.6+ or 18.19+
- Bun runtime: supported (SDK detects Bun and forces `node` executable path)
- CLI binary: must match SDK protocol version range (MIN=2, MAX from `sdkProtocolVersion.js`)
- Protocol mismatch throws: `"SDK protocol version mismatch: SDK supports versions 2-N, but server reports version M"`

## Bundled CLI Resolution

When `cliPath` is not set and `cliUrl` is not set, the SDK resolves the bundled CLI automatically:

```typescript
// Internal logic (do not replicate — use cliPath only if overriding):
const sdkUrl = import.meta.resolve("@github/copilot/sdk");
// Traverses to @github/copilot package root, finds index.js
```

Install the bundled CLI package:

```bash
npm install @github/copilot-sdk @github/copilot
```

For bundled app distribution (Electron, CLI tools), resolve platform-specific binary:

```typescript
import os from "os";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function getCLIPath(): string {
  const platform = process.platform;   // "darwin" | "linux" | "win32"
  const arch = os.arch();              // "arm64" | "x64"
  const ext = platform === "win32" ? ".exe" : "";
  return join(__dirname, "../vendor", `copilot-${platform}-${arch}${ext}`);
}

const client = new CopilotClient({ cliPath: getCLIPath() });
```

Supported platforms: `darwin-arm64`, `darwin-x64`, `linux-x64`, `win32-x64`.

## The `onListModels` Override

Use this for BYOK deployments where model list comes from your own provider, not CLI:

```typescript
const client = new CopilotClient({
  onListModels: async () => {
    const res = await fetch("https://api.openai.com/v1/models", {
      headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
    });
    const data = await res.json();
    return data.data.map((m: { id: string }) => ({
      id: m.id,
      name: m.id,
      capabilities: {
        supports: { vision: false, reasoningEffort: false },
        limits: { max_context_window_tokens: 128000 },
      },
    }));
  },
});
```

`listModels()` returns cached results after the first call. Cache clears on client disconnect.

## `autoStart` vs Manual `start()`

Use `autoStart: true` (default) for most applications — the client starts on first `createSession()`.

Use `autoStart: false` when you need to control startup timing explicitly:

```typescript
const client = new CopilotClient({ autoStart: false });

// Warm up connection before accepting requests
await client.start();

// Now createSession() does not need to wait for startup
const session = await client.createSession({ onPermissionRequest: approveAll });
```

Use `autoRestart: false` when you want crash failures to propagate as errors rather than silently reconnecting.
