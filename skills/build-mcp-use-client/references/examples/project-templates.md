# MCP Client Project Templates

Starter project structures for building MCP client applications with mcp-use.

---

## Template 1: Minimal Node.js Client

```
minimal-mcp-client/
├── package.json
├── tsconfig.json
├── src/client.ts
└── README.md
```

### `package.json`
```json
{
  "name": "minimal-mcp-client",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "tsx src/client.ts",
    "build": "tsc",
    "start:built": "node dist/client.js"
  },
  "dependencies": {
    "mcp-use": "^1.21.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "typescript": "^5.5.0"
  }
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src"]
}
```

### `src/client.ts`
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    "my-server": {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
    },
  },
});

try {
  await client.createAllSessions();
  const session = client.getSession("my-server");

  // List tools
  const tools = await session.listTools();
  console.log("Available tools:");
  for (const tool of tools) {
    console.log(`  ${tool.name}: ${tool.description}`);
  }

  // Call a tool
  if (tools.length > 0) {
    const result = await session.callTool(tools[0].name, {});
    if (result.isError) {
      console.error("Tool error:", result.content);
    } else {
      console.log("Result:", result.content);
    }
  }

  // List resources
  const resources = await session.listResources();
  console.log(`\n${resources.length} resources available`);

  // List prompts
  const prompts = await session.listPrompts();
  console.log(`${prompts.length} prompts available`);
} finally {
  await client.closeAllSessions();
  console.log("Done.");
}
```

### `README.md`
````markdown
# Minimal MCP Client

```bash
npm install
npm start
```

Connect to an HTTP server instead:
```bash
# Edit src/client.ts mcpServers to:
# "my-server": { url: "http://localhost:3000/mcp" }
```
````

---

## Template 2: Production HTTP Client

```
production-mcp-client/
├── package.json
├── tsconfig.json
├── .env.example
├── src/
│   ├── client.ts
│   ├── config.ts
│   └── sampling.ts
└── README.md
```

### `package.json`
```json
{
  "name": "production-mcp-client",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "tsx src/client.ts",
    "build": "tsc",
    "start:built": "node dist/client.js"
  },
  "dependencies": {
    "mcp-use": "^1.21.0",
    "dotenv": "^16.4.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "typescript": "^5.5.0",
    "@types/node": "^22.0.0"
  }
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src"]
}
```

### `.env.example`
```env
MCP_SERVER_URL=http://localhost:3000/mcp
MCP_AUTH_TOKEN=sk-your-api-key
OPENAI_API_KEY=sk-your-openai-key
REQUEST_TIMEOUT=60000
MAX_RETRIES=3
```

### `src/config.ts`
```typescript
import "dotenv/config";

export const config = {
  server: {
    url: process.env.MCP_SERVER_URL || "http://localhost:3000/mcp",
    authToken: process.env.MCP_AUTH_TOKEN,
  },
  timeouts: {
    request: parseInt(process.env.REQUEST_TIMEOUT || "60000", 10),
    maxTotal: parseInt(process.env.MAX_TOTAL_TIMEOUT || "300000", 10),
  },
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    model: process.env.OPENAI_MODEL || "gpt-4o",
  },
  retries: parseInt(process.env.MAX_RETRIES || "3", 10),
};
```

### `src/sampling.ts`
```typescript
import {
  type OnSamplingCallback,
  type CreateMessageRequestParams,
  type CreateMessageResult,
} from "mcp-use";
import { config } from "./config.js";

export const onSampling: OnSamplingCallback = async (
  params: CreateMessageRequestParams
): Promise<CreateMessageResult> => {
  if (!config.openai.apiKey) {
    return {
      role: "assistant",
      content: { type: "text", text: "LLM not configured. Set OPENAI_API_KEY." },
      model: "none",
      stopReason: "endTurn",
    };
  }

  let model = config.openai.model;
  if (params.modelPreferences?.hints?.[0]?.name) {
    model = params.modelPreferences.hints[0].name;
  } else if ((params.modelPreferences?.intelligencePriority ?? 0) > 0.8) {
    model = "gpt-4o";
  } else if ((params.modelPreferences?.speedPriority ?? 0) > 0.8) {
    model = "gpt-4o-mini";
  }

  const messages = params.messages.map((m) => ({
    role: m.role as "user" | "assistant",
    content: typeof m.content === "object" && "text" in m.content ? m.content.text! : "",
  }));

  if (params.systemPrompt) {
    messages.unshift({ role: "user" as any, content: params.systemPrompt });
  }

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${config.openai.apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      max_tokens: params.maxTokens ?? 1024,
      temperature: params.temperature ?? 0.7,
      stop: params.stopSequences,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    return {
      role: "assistant",
      content: { type: "text", text: `LLM error ${res.status}: ${errText}` },
      model,
      stopReason: "endTurn",
    };
  }

  const data = await res.json();
  return {
    role: "assistant",
    content: { type: "text", text: data.choices[0].message.content },
    model: data.model,
    stopReason: data.choices[0].finish_reason === "stop" ? "endTurn" : "maxTokens",
  };
};
```

### `src/client.ts`
```typescript
import { MCPClient, acceptWithDefaults, types, type OnNotificationCallback } from "mcp-use";
import { config } from "./config.js";
import { onSampling } from "./sampling.js";

const headers: Record<string, string> = {};
if (config.server.authToken) {
  headers["Authorization"] = `Bearer ${config.server.authToken}`;
}

const onNotification: OnNotificationCallback = (notification) => {
  console.log(`[notification] ${notification.method}`, notification.params ?? "");
};

const client = new MCPClient(
  {
    clientInfo: { name: "production-mcp-client", version: "1.0.0" },
    mcpServers: {
      main: {
        url: config.server.url,
        headers,
      },
    },
  },
  {
    onSampling,
    onElicitation: async (params) => acceptWithDefaults(params),
    onNotification,
    loggingCallback: (logParams: types.LoggingMessageNotificationParams) => {
      console.log(`[server-log:${logParams.level}] ${logParams.message}`);
    },
  }
);

// Graceful shutdown
let shuttingDown = false;
async function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log("\nShutting down...");
  await client.closeAllSessions();
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

// Retry wrapper
async function callWithRetry(
  session: ReturnType<typeof client.getSession>,
  tool: string,
  args: Record<string, unknown>,
  retries = config.retries
): Promise<any> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const result = await session.callTool(tool, args, {
        timeout: config.timeouts.request,
        maxTotalTimeout: config.timeouts.maxTotal,
        resetTimeoutOnProgress: true,
      });
      if (result.isError) throw new Error(`Tool error: ${JSON.stringify(result.content)}`);
      return result;
    } catch (err) {
      console.error(`Attempt ${attempt}/${retries} failed:`, (err as Error).message);
      if (attempt === retries) throw err;
      await new Promise((r) => setTimeout(r, 1000 * attempt)); // exponential-ish backoff
    }
  }
}

try {
  await client.createAllSessions();
  const session = client.getSession("main");
  console.log(`Connected to ${config.server.url}`);

  // Auto-refresh tools on notification
  session.on("notification", async (notification) => {
    if (notification.method === "notifications/tools/list_changed") {
      const tools = await session.listTools();
      console.log(`Tools refreshed: ${tools.length} available`);
    }
  });

  const tools = await session.listTools();
  console.log(`${tools.length} tools available:`);
  for (const t of tools) console.log(`  ${t.name}: ${t.description}`);

  // Example call with retry
  if (tools.length > 0) {
    const result = await callWithRetry(session, tools[0].name, {});
    console.log("Result:", result.content);
  }

  // Keep running for notifications (remove if one-shot)
  console.log("\nListening for notifications... (Ctrl+C to stop)");
  await new Promise(() => {}); // block forever
} catch (err) {
  console.error("Fatal:", err);
  await client.closeAllSessions();
  process.exit(1);
}
```

### `README.md`
````markdown
# Production MCP Client

```bash
cp .env.example .env   # edit with real values
npm install
npm start
```

Features:
- Bearer token auth
- Named `clientInfo` for server-side identification
- LLM sampling callback (OpenAI)
- Auto-accept elicitation with defaults
- Notification logging via `OnNotificationCallback`
- Server log forwarding via `loggingCallback`
- Retry with backoff
- Graceful shutdown (SIGINT/SIGTERM)
````

---

## Template 3: React MCP Dashboard

```
react-mcp-dashboard/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── ServerCard.tsx
│   │   └── OAuthCallback.tsx
│   └── vite-env.d.ts
└── README.md
```

### `package.json`
```json
{
  "name": "react-mcp-dashboard",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "mcp-use": "^1.21.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^6.0.0"
  }
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

### `vite.config.ts`
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
```

### `index.html`
```html
<!DOCTYPE html>
<html lang="en">
  <head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>MCP Dashboard</title></head>
  <body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>
</html>
```

### `src/vite-env.d.ts`
```typescript
/// <reference types="vite/client" />
```

### `src/main.tsx`
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

### `src/App.tsx`
```tsx
import { useCallback, useEffect, useState } from "react";
import {
  McpClientProvider,
  useMcpClient,
  LocalStorageProvider,
} from "mcp-use/react";
import ServerCard from "./components/ServerCard";

function Dashboard() {
  const { addServer, removeServer, servers, storageLoaded } = useMcpClient();
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");

  const handleAdd = useCallback(() => {
    if (!url) return;
    const id = name || `server-${Date.now()}`;
    addServer(id, {
      url,
      name: id,
      autoReconnect: { enabled: true, initialDelay: 3000, healthCheckInterval: 10000 },
    });
    setUrl("");
    setName("");
  }, [url, name, addServer]);

  if (!storageLoaded) return <p>Loading saved servers...</p>;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
      <h1>MCP Dashboard</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <input placeholder="Server name" value={name} onChange={(e) => setName(e.target.value)} />
        <input placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} style={{ flex: 1 }} />
        <button onClick={handleAdd} disabled={!url}>Add Server</button>
      </div>

      {servers.length === 0 && <p>No servers connected. Add one above.</p>}
      {servers.map((s) => (
        <ServerCard key={s.id} serverId={s.id} onRemove={() => removeServer(s.id)} />
      ))}
    </div>
  );
}

export default function App() {
  return (
    <McpClientProvider
      defaultAutoProxyFallback={true}
      storageProvider={new LocalStorageProvider("mcp-dashboard-servers")}
      onSamplingRequest={(req, serverId, serverName, approve, reject) => {
        if (window.confirm(`[${serverName}] Allow LLM sampling?`)) {
          approve({
            role: "assistant",
            content: { type: "text", text: "Approved" },
            model: "user-approved",
          });
        } else {
          reject();
        }
      }}
    >
      <Dashboard />
    </McpClientProvider>
  );
}
```

### `src/components/ServerCard.tsx`
```tsx
import { useState } from "react";
import { useMcpServer } from "mcp-use/react";

interface Props {
  serverId: string;
  onRemove: () => void;
}

export default function ServerCard({ serverId, onRemove }: Props) {
  const server = useMcpServer(serverId);
  const [result, setResult] = useState<string>("");
  const [args, setArgs] = useState<string>("{}");

  if (!server) return null;

  // Auth required
  if (server.state === "pending_auth") {
    return (
      <div style={{ border: "1px solid orange", padding: 16, marginBottom: 12, borderRadius: 8 }}>
        <h3>{server.name} — Authentication Required</h3>
        <button onClick={() => server.authenticate()}>Authenticate with OAuth</button>
        <button onClick={onRemove} style={{ marginLeft: 8 }}>Remove</button>
      </div>
    );
  }

  // Not ready
  if (server.state !== "ready") {
    return (
      <div style={{ border: "1px solid #ccc", padding: 16, marginBottom: 12, borderRadius: 8 }}>
        <h3>{server.name} — {server.state}</h3>
        {server.error && <p style={{ color: "red" }}>{server.error}</p>}
        {server.state === "failed" && <button onClick={() => server.retry()}>Retry</button>}
        <button onClick={onRemove} style={{ marginLeft: 8 }}>Remove</button>
      </div>
    );
  }

  const handleCall = async (toolName: string) => {
    try {
      const parsed = JSON.parse(args);
      const res = await server.callTool(toolName, parsed, { timeout: 30000 });
      setResult(JSON.stringify(res, null, 2));
    } catch (err) {
      setResult(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div style={{ border: "1px solid #4caf50", padding: 16, marginBottom: 12, borderRadius: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>{server.serverInfo?.name || server.name}</h3>
        <div>
          {server.unreadNotificationCount > 0 && (
            <span style={{ marginRight: 8 }}>
              🔔 {server.unreadNotificationCount}
              <button onClick={() => server.markAllNotificationsRead()} style={{ marginLeft: 4 }}>✓</button>
            </span>
          )}
          <button onClick={() => server.disconnect()}>Disconnect</button>
          <button onClick={onRemove} style={{ marginLeft: 4 }}>Remove</button>
        </div>
      </div>

      <p>
        Tools: {server.tools.length} · Resources: {server.resources.length} · Prompts: {server.prompts.length}
      </p>

      <div style={{ marginBottom: 8 }}>
        <input
          value={args}
          onChange={(e) => setArgs(e.target.value)}
          placeholder='{"key": "value"}'
          style={{ width: "100%", fontFamily: "monospace" }}
        />
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {server.tools.map((t) => (
          <button key={t.name} onClick={() => handleCall(t.name)} title={t.description}>
            {t.name}
          </button>
        ))}
      </div>

      {result && (
        <pre style={{ background: "#f5f5f5", padding: 8, marginTop: 8, overflow: "auto", maxHeight: 300 }}>
          {result}
        </pre>
      )}
    </div>
  );
}
```

### `src/components/OAuthCallback.tsx`
```tsx
import { useEffect, useState } from "react";
import { onMcpAuthorization } from "mcp-use/auth";

export default function OAuthCallback() {
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    onMcpAuthorization()
      .then(() => {
        setStatus("success");
        setTimeout(() => (window.location.href = "/"), 1500);
      })
      .catch((err) => {
        setStatus("error");
        setErrorMsg((err as Error).message);
        console.error("OAuth callback failed:", err);
      });
  }, []);

  return (
    <div style={{ textAlign: "center", padding: 48 }}>
      {status === "processing" && <p>Completing authentication...</p>}
      {status === "success" && <p>✅ Success! Redirecting...</p>}
      {status === "error" && (
        <div>
          <p>❌ Authentication failed</p>
          <p style={{ color: "red" }}>{errorMsg}</p>
          <button onClick={() => (window.location.href = "/")}>Back to Dashboard</button>
        </div>
      )}
    </div>
  );
}
```

### `README.md`
````markdown
# React MCP Dashboard

```bash
npm install
npm run dev          # http://localhost:5173
```

Features:
- Multi-server management (add/remove dynamically)
- Auto proxy fallback for CORS issues
- OAuth flow with callback page
- Notification badges
- Tool calling with JSON args editor
- Server persistence via localStorage
- Reconnection with health checks

For OAuth callback, add a route at `/oauth/callback` rendering `OAuthCallback`.
````

---

## Template 4: Browser Extension Client

```
browser-extension-client/
├── package.json
├── tsconfig.json
├── src/
│   ├── client.ts
│   └── types.ts
└── README.md
```

### `package.json`
```json
{
  "name": "browser-extension-mcp-client",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "dependencies": {
    "mcp-use": "^1.21.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0"
  }
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"]
  },
  "include": ["src"]
}
```

### `src/types.ts`
```typescript
export interface McpConfig {
  serverUrl: string;
  authToken?: string;
  oauthClientId?: string;
  oauthAuthorizationUrl?: string;
  oauthTokenUrl?: string;
}

export interface ToolCallResult {
  toolName: string;
  content: unknown;
  isError: boolean;
  timestamp: number;
}
```

### `src/client.ts`
```typescript
import { MCPClient, BrowserOAuthClientProvider } from "mcp-use/browser";
import type { McpConfig, ToolCallResult } from "./types.js";

/**
 * Browser extension MCP client.
 *
 * Limitations (browser environment):
 *  - No STDIO connections (cannot spawn child processes)
 *  - No file system operations
 *  - No code mode (sandboxed execution unavailable)
 *  - HTTP connections only
 *  - Subject to CORS restrictions (use proxy fallback if needed)
 */
export class ExtensionMcpClient {
  private client: MCPClient | null = null;
  private config: McpConfig;

  constructor(config: McpConfig) {
    this.config = config;
  }

  async connect(): Promise<void> {
    const headers: Record<string, string> = {};
    if (this.config.authToken) {
      headers["Authorization"] = `Bearer ${this.config.authToken}`;
    }

    const serverConfig: Record<string, any> = {
      url: this.config.serverUrl,
      headers,
    };

    // Add OAuth provider if configured
    if (this.config.oauthClientId && this.config.oauthAuthorizationUrl && this.config.oauthTokenUrl) {
      serverConfig.authProvider = new BrowserOAuthClientProvider({
        clientId: this.config.oauthClientId,
        authorizationUrl: this.config.oauthAuthorizationUrl,
        tokenUrl: this.config.oauthTokenUrl,
        callbackUrl: chrome?.identity
          ? chrome.identity.getRedirectURL("oauth")
          : window.location.origin + "/oauth/callback",
      });
    }

    this.client = new MCPClient({
      mcpServers: { extension: serverConfig },
    });

    await this.client.createAllSessions();
  }

  async listTools(): Promise<Array<{ name: string; description?: string }>> {
    this.ensureConnected();
    const session = this.client!.getSession("extension");
    const tools = await session.listTools();
    return tools.map((t) => ({ name: t.name, description: t.description }));
  }

  async callTool(name: string, args: Record<string, unknown> = {}): Promise<ToolCallResult> {
    this.ensureConnected();
    const session = this.client!.getSession("extension");
    const result = await session.callTool(name, args, { timeout: 30000 });
    return {
      toolName: name,
      content: result.content,
      isError: result.isError ?? false,
      timestamp: Date.now(),
    };
  }

  async listResources(): Promise<Array<{ uri: string; name: string }>> {
    this.ensureConnected();
    const session = this.client!.getSession("extension");
    const resources = await session.listResources();
    return resources.map((r) => ({ uri: r.uri, name: r.name }));
  }

  async readResource(uri: string): Promise<unknown> {
    this.ensureConnected();
    const session = this.client!.getSession("extension");
    return session.readResource(uri);
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.closeAllSessions();
      this.client = null;
    }
  }

  private ensureConnected(): void {
    if (!this.client) throw new Error("Not connected. Call connect() first.");
  }
}

// Usage example
async function main() {
  const client = new ExtensionMcpClient({
    serverUrl: "https://api.example.com/mcp",
    authToken: "your-token-here",
  });

  try {
    await client.connect();
    const tools = await client.listTools();
    console.log("Available tools:", tools);

    if (tools.length > 0) {
      const result = await client.callTool(tools[0].name, {});
      console.log("Result:", result);
    }
  } catch (err) {
    console.error("MCP client error:", err);
  } finally {
    await client.disconnect();
  }
}

// Auto-run if loaded directly
main().catch(console.error);
```

### `README.md`
````markdown
# Browser Extension MCP Client

```bash
npm install
npm run build
```

## Browser Limitations

| Feature | Supported |
|---|---|
| HTTP connections | ✅ |
| OAuth authentication | ✅ |
| STDIO connections | ❌ (cannot spawn processes) |
| File system operations | ❌ |
| Code mode | ❌ |

## Usage

```typescript
import { ExtensionMcpClient } from "./client.js";

const client = new ExtensionMcpClient({
  serverUrl: "https://api.example.com/mcp",
  authToken: "your-token",
});
await client.connect();
const tools = await client.listTools();
const result = await client.callTool("my-tool", { arg: "value" });
await client.disconnect();
```

## CORS

If the MCP server doesn't set CORS headers, use a proxy:
- Self-hosted: deploy the mcp-use inspector proxy
- Public: `https://inspector.mcp-use.com/inspector/api/proxy`

## OAuth in Extensions

For Chrome extensions, use `chrome.identity.getRedirectURL("oauth")` as the callback URL.
For other browsers, use a custom callback page in the extension.
````
