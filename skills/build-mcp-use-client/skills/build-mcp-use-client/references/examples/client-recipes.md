# MCP Client Recipes

Complete, copy-pasteable client examples using the mcp-use TypeScript library (v1.21.5).

---

## Recipe 1: Multi-Server CLI Client

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  {
    clientInfo: { name: "my-client", version: "1.0.0" },
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
      },
      github: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! },
      },
      database: {
        command: "npx",
        args: ["-y", "mcp-server-sqlite", "--db", "./app.db"],
      },
    },
  }
);

try {
  await client.createAllSessions();

  // List tools from every server
  for (const name of ["filesystem", "github", "database"]) {
    const session = client.getSession(name);
    const tools = await session.listTools();
    console.log(`[${name}] ${tools.length} tools:`, tools.map((t) => t.name));
  }

  // Call tools on different servers
  const fsSession = client.getSession("filesystem");
  const files = await fsSession.callTool("list_directory", { path: "." });
  console.log("Files:", files.content);

  const ghSession = client.getSession("github");
  const repos = await ghSession.callTool("search_repositories", { query: "mcp-use" });
  console.log("Repos:", repos.content);

  const dbSession = client.getSession("database");
  const tables = await dbSession.callTool("list-tables", {});
  console.log("Tables:", tables.content);
} finally {
  await client.closeAllSessions();
}
```

## Recipe 2: HTTP Client with Auth

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    "api-server": {
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: `Bearer ${process.env.API_TOKEN}`,
        "X-API-Version": "2024-01-01",
        "X-Request-Source": "cli-client",
      },
    },
  },
});

try {
  await client.createAllSessions();
  const session = client.getSession("api-server");

  // Verify connection
  const tools = await session.listTools();
  console.log(`Connected. ${tools.length} tools available.`);

  // Call an authenticated tool
  const result = await session.callTool("list-users", { page: 1, limit: 10 });
  if (result.isError) {
    console.error("Tool error:", result.content);
  } else {
    console.log("Users:", result.content);
  }

  // Call with timeout for slow operations
  const report = await session.callTool("generate-report", { type: "monthly" }, {
    timeout: 120000,
    maxTotalTimeout: 300000,
    resetTimeoutOnProgress: true,
  });
  console.log("Report:", report.content);
} finally {
  await client.closeAllSessions();
}
```

## Recipe 3: Browser Client with Proxy Fallback

```typescript
import { MCPClient, BrowserOAuthClientProvider } from "mcp-use/browser";

const authProvider = new BrowserOAuthClientProvider({
  clientId: "your-client-id",
  authorizationUrl: "https://api.example.com/oauth/authorize",
  tokenUrl: "https://api.example.com/oauth/token",
  callbackUrl: window.location.origin + "/oauth/callback",
});

const client = new MCPClient({
  mcpServers: {
    main: {
      url: "https://api.example.com/mcp",
      authProvider,
    },
    public: {
      url: "https://public.example.com/mcp",
      headers: { Authorization: "Bearer public-key" },
    },
  },
});

async function connectWithFallback(serverName: string, proxyUrl: string) {
  try {
    await client.createAllSessions();
    console.log(`[${serverName}] Direct connection succeeded`);
  } catch (err) {
    const msg = (err as Error).message;
    if (msg.includes("CORS") || msg.includes("FastMCP") || msg.includes("Failed to fetch")) {
      console.warn(`[${serverName}] Direct failed, trying proxy...`);
      // Recreate with proxy — browser clients only support HTTP
      const proxyClient = new MCPClient({
        mcpServers: {
          [serverName]: {
            url: proxyUrl,
            headers: {
              "X-Target-URL": "https://api.example.com/mcp",
              Authorization: "Bearer public-key",
            },
          },
        },
      });
      await proxyClient.createAllSessions();
      console.log(`[${serverName}] Proxy connection succeeded`);
      return proxyClient;
    }
    throw err;
  }
  return client;
}

try {
  const activeClient = await connectWithFallback(
    "public",
    "https://inspector.mcp-use.com/inspector/api/proxy"
  );
  const session = activeClient.getSession("public");
  const tools = await session.listTools();
  console.log("Tools:", tools.map((t) => t.name));
} catch (err) {
  console.error("All connection methods failed:", err);
}
```

## Recipe 4: React Multi-Server Dashboard

```tsx
import { useEffect, useState, useCallback } from "react";
import {
  McpClientProvider,
  useMcpClient,
  useMcpServer,
  LocalStorageProvider,
} from "mcp-use/react";
import { onMcpAuthorization } from "mcp-use/auth";
import type { CreateMessageResult, ElicitResult } from "mcp-use";

// — App root with provider —
export default function App() {
  return (
    <McpClientProvider
      defaultAutoProxyFallback={true}
      storageProvider={new LocalStorageProvider("mcp-dashboard")}
      onSamplingRequest={(request, serverId, serverName, approve, reject) => {
        const ok = window.confirm(`[${serverName}] Allow LLM sampling?`);
        if (ok) {
          approve({
            role: "assistant",
            content: { type: "text", text: "Approved by user" },
            model: "user-approved",
          });
        } else {
          reject();
        }
      }}
      onElicitationRequest={(request, serverId, serverName, approve, reject) => {
        if (request.mode === "url") {
          window.open(request.url, "_blank");
          approve({ action: "accept" });
        } else {
          const data: Record<string, string> = {};
          if (request.requestedSchema?.properties) {
            for (const [key, schema] of Object.entries(request.requestedSchema.properties)) {
              const val = window.prompt(`${(schema as any).title || key}:`, (schema as any).default ?? "");
              if (val !== null) data[key] = val;
            }
          }
          approve({ action: "accept", content: data });
        }
      }}
    >
      <Dashboard />
    </McpClientProvider>
  );
}

// — Dashboard manages servers —
function Dashboard() {
  const { addServer, removeServer, servers } = useMcpClient();
  const [newUrl, setNewUrl] = useState("");

  const handleAdd = useCallback(() => {
    if (!newUrl) return;
    const id = `server-${Date.now()}`;
    addServer(id, {
      url: newUrl,
      name: id,
      autoReconnect: { enabled: true, initialDelay: 3000, healthCheckInterval: 10000 },
    });
    setNewUrl("");
  }, [newUrl, addServer]);

  return (
    <div>
      <h1>MCP Dashboard ({servers.length} servers)</h1>
      <div>
        <input value={newUrl} onChange={(e) => setNewUrl(e.target.value)} placeholder="https://..." />
        <button onClick={handleAdd}>Add Server</button>
      </div>
      {servers.map((s) => (
        <ServerCard key={s.id} serverId={s.id} onRemove={() => removeServer(s.id)} />
      ))}
    </div>
  );
}

// — Per-server card —
function ServerCard({ serverId, onRemove }: { serverId: string; onRemove: () => void }) {
  const server = useMcpServer(serverId);
  const [result, setResult] = useState<string>("");

  if (!server) return null;

  if (server.state === "pending_auth") {
    return (
      <div>
        <h3>{server.name} — Awaiting Auth</h3>
        <button onClick={() => server.authenticate()}>Authenticate</button>
      </div>
    );
  }

  if (server.state !== "ready") {
    return (
      <div>
        <h3>{server.name} — {server.state}</h3>
        {server.error && <p style={{ color: "red" }}>{server.error}</p>}
        {server.state === "failed" && <button onClick={() => server.retry()}>Retry</button>}
      </div>
    );
  }

  const handleCall = async (toolName: string) => {
    try {
      const res = await server.callTool(toolName, {}, { timeout: 30000 });
      setResult(JSON.stringify(res, null, 2));
    } catch (err) {
      setResult(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div style={{ border: "1px solid #ccc", padding: 16, margin: 8 }}>
      <h3>{server.serverInfo?.name || server.name}</h3>
      <p>Tools: {server.tools.length} | Resources: {server.resources.length}</p>
      {server.unreadNotificationCount > 0 && (
        <span>
          🔔 {server.unreadNotificationCount} new
          <button onClick={() => server.markAllNotificationsRead()}>Mark read</button>
        </span>
      )}
      <ul>
        {server.tools.map((t) => (
          <li key={t.name}>
            <button onClick={() => handleCall(t.name)}>{t.name}</button>
            <span> — {t.description}</span>
          </li>
        ))}
      </ul>
      {result && <pre>{result}</pre>}
      <button onClick={onRemove}>Remove</button>
      <button onClick={() => server.disconnect()}>Disconnect</button>
    </div>
  );
}

// — OAuth callback page (mount at /oauth/callback) —
export function OAuthCallback() {
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");

  useEffect(() => {
    onMcpAuthorization()
      .then(() => {
        setStatus("success");
        setTimeout(() => (window.location.href = "/"), 1000);
      })
      .catch((err) => {
        setStatus("error");
        console.error("OAuth failed:", err);
      });
  }, []);

  if (status === "processing") return <div>Completing authentication...</div>;
  if (status === "success") return <div>Success! Redirecting...</div>;
  return <div>Authentication failed. Please try again.</div>;
}
```

## Recipe 5: Sampling Integration (Connect Client to LLM)

```typescript
import {
  MCPClient,
  type OnSamplingCallback,
  type OnNotificationCallback,
  type CreateMessageRequestParams,
  type CreateMessageResult,
} from "mcp-use";

// — OpenAI sampling callback —
const openaiSampling: OnSamplingCallback = async (
  params: CreateMessageRequestParams
): Promise<CreateMessageResult> => {
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
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: "gpt-4o",
      messages,
      max_tokens: params.maxTokens ?? 1024,
      temperature: params.temperature ?? 0.7,
      stop: params.stopSequences,
    }),
  });

  const data = await res.json();
  return {
    role: "assistant",
    content: { type: "text", text: data.choices[0].message.content },
    model: data.model,
    stopReason: data.choices[0].finish_reason === "stop" ? "endTurn" : "maxTokens",
  };
};

// — Anthropic sampling callback —
const anthropicSampling: OnSamplingCallback = async (
  params: CreateMessageRequestParams
): Promise<CreateMessageResult> => {
  const messages = params.messages.map((m) => ({
    role: m.role,
    content: typeof m.content === "object" && "text" in m.content ? m.content.text! : "",
  }));

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": process.env.ANTHROPIC_API_KEY!,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: params.maxTokens ?? 1024,
      system: params.systemPrompt,
      messages,
    }),
  });

  const data = await res.json();
  return {
    role: "assistant",
    content: { type: "text", text: data.content[0].text },
    model: data.model,
    stopReason: data.stop_reason === "end_turn" ? "endTurn" : "maxTokens",
  };
};

// — Model preference routing —
function routeSampling(params: CreateMessageRequestParams): OnSamplingCallback {
  const hints = params.modelPreferences?.hints;
  if (hints?.[0]?.name?.includes("claude")) return anthropicSampling;
  if (hints?.[0]?.name?.includes("gpt")) return openaiSampling;
  if ((params.modelPreferences?.intelligencePriority ?? 0) > 0.8) return anthropicSampling;
  if ((params.modelPreferences?.speedPriority ?? 0) > 0.8) return openaiSampling;
  return openaiSampling; // default
}

// — Multi-server with different LLM backends —
const client = new MCPClient(
  {
    mcpServers: {
      codeServer: {
        url: "https://code.example.com/mcp",
        onSampling: anthropicSampling, // code tasks → Claude
      },
      creativeServer: {
        url: "https://creative.example.com/mcp",
        onSampling: openaiSampling, // creative tasks → GPT
      },
      autoServer: {
        url: "https://auto.example.com/mcp",
        // falls through to root-level with routing
      },
    },
  },
  {
    onSampling: async (params) => {
      const handler = routeSampling(params);
      return handler(params);
    },
  }
);

try {
  await client.createAllSessions();
  const session = client.getSession("codeServer");
  const result = await session.callTool("analyze-code", { file: "main.ts" });
  console.log("Analysis:", result.content);
} finally {
  await client.closeAllSessions();
}
```

## Recipe 6: Elicitation Handler

```typescript
import {
  MCPClient,
  accept,
  acceptWithDefaults,
  decline,
  validate,
  type OnElicitationCallback,
} from "mcp-use";
import type {
  ElicitRequestFormParams,
  ElicitRequestURLParams,
  ElicitResult,
} from "@modelcontextprotocol/sdk/types.js";
import readline from "readline";

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = (q: string): Promise<string> => new Promise((r) => rl.question(q, r));

// — Form mode: collect structured data with validation —
const formElicitation: OnElicitationCallback = async (params): Promise<ElicitResult> => {
  if (params.mode === "url") return { action: "decline" };

  console.log(`\n📋 Server requests: ${params.message}`);
  const schema = params.requestedSchema;
  const data: Record<string, any> = {};

  if (schema?.type === "object" && schema.properties) {
    for (const [key, fieldSchema] of Object.entries(schema.properties) as [string, any][]) {
      const required = schema.required?.includes(key);
      const label = fieldSchema.title || key;
      const defaultVal = fieldSchema.default;
      const hint = defaultVal !== undefined ? ` [default: ${defaultVal}]` : "";
      const reqTag = required ? " (required)" : "";

      const raw = await ask(`  ${label}${reqTag}${hint}: `);
      const value = raw || defaultVal;

      if (required && !value) {
        console.log(`  ⚠ Skipping required field ${key}`);
        return decline(`Missing required field: ${key}`);
      }
      if (value !== undefined) data[key] = value;
    }
  }

  const { valid, errors } = validate(params, data);
  if (!valid) {
    console.log("  ❌ Validation failed:", errors);
    return decline(errors?.join("; "));
  }

  return accept(data);
};

// — URL mode: open external URLs —
const urlElicitation: OnElicitationCallback = async (params): Promise<ElicitResult> => {
  if (params.mode !== "url") return { action: "decline" };

  console.log(`\n🔗 Please visit: ${(params as ElicitRequestURLParams).url}`);
  console.log(`   Reason: ${params.message}`);
  const answer = await ask("   Did you complete the action? (y/n): ");
  return { action: answer.toLowerCase() === "y" ? "accept" : "decline" };
};

// — Combined handler —
const combinedElicitation: OnElicitationCallback = async (params): Promise<ElicitResult> => {
  if (params.mode === "url") return urlElicitation(params);
  return formElicitation(params);
};

const client = new MCPClient(
  {
    mcpServers: {
      main: { url: "http://localhost:3000/mcp" },
      autoAccept: {
        url: "http://localhost:3001/mcp",
        onElicitation: async (params) => acceptWithDefaults(params),
      },
    },
  },
  { onElicitation: combinedElicitation }
);

try {
  await client.createAllSessions();
  const session = client.getSession("main");
  const result = await session.callTool("configure-settings", {});
  console.log("Result:", result.content);
} finally {
  rl.close();
  await client.closeAllSessions();
}
```

### React Elicitation with UI Forms

```tsx
import { useMcp } from "mcp-use/react";
import { useState } from "react";

function ElicitationApp() {
  const [formFields, setFormFields] = useState<Record<string, any> | null>(null);
  const [pendingResolve, setPendingResolve] = useState<((v: any) => void) | null>(null);

  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    onElicitation: async (params) => {
      if (params.mode === "url") {
        const confirmed = window.confirm(`Open ${(params as any).url}?`);
        if (confirmed) window.open((params as any).url, "_blank");
        return { action: confirmed ? "accept" : "decline" };
      }
      // Show form UI and wait for user input
      return new Promise((resolve) => {
        setFormFields(params.requestedSchema?.properties || {});
        setPendingResolve(() => resolve);
      });
    },
  });

  const handleSubmit = (data: Record<string, string>) => {
    pendingResolve?.({ action: "accept", content: data });
    setFormFields(null);
    setPendingResolve(null);
  };

  if (formFields) {
    return (
      <form onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        handleSubmit(Object.fromEntries(fd) as Record<string, string>);
      }}>
        {Object.entries(formFields).map(([key, schema]: [string, any]) => (
          <label key={key}>
            {schema.title || key}
            <input name={key} defaultValue={schema.default ?? ""} required={schema.required} />
          </label>
        ))}
        <button type="submit">Submit</button>
        <button type="button" onClick={() => {
          pendingResolve?.({ action: "cancel" });
          setFormFields(null);
        }}>Cancel</button>
      </form>
    );
  }

  if (mcp.state !== "ready") return <div>Connecting... ({mcp.state})</div>;

  return (
    <div>
      <h2>Tools ({mcp.tools.length})</h2>
      {mcp.tools.map((t) => (
        <button key={t.name} onClick={() => mcp.callTool(t.name, {})}>{t.name}</button>
      ))}
    </div>
  );
}
```

## Recipe 7: Resource Monitor

```typescript
import { MCPClient, type Notification } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    dataServer: { url: "http://localhost:3000/mcp" },
  },
});

try {
  await client.createAllSessions();
  const session = client.getSession("dataServer");

  // List all resources
  const resources = await session.listResources();
  console.log("Resources:");
  for (const r of resources) {
    console.log(`  ${r.uri} — ${r.name}`);
  }

  // Read a specific resource
  const configResult = await session.readResource("config://app");
  for (const content of configResult.contents) {
    if ("text" in content) {
      console.log("Config (text):", content.text);
    } else if ("blob" in content) {
      console.log("Config (binary), length:", content.blob.length);
    }
  }

  // Read a templated resource (fill in variables to form the concrete URI)
  const userProfileResult = await session.readResource("users://profile/42");
  for (const content of userProfileResult.contents) {
    if ("text" in content) {
      console.log("User profile:", content.text);
    }
  }

  // Subscribe to resource changes
  const handler = async (notification: Notification) => {
    switch (notification.method) {
      case "notifications/resources/list_changed": {
        console.log("Resource list changed — refreshing...");
        const updated = await session.listResources();
        console.log(`  Now ${updated.length} resources`);
        break;
      }
      case "notifications/resources/updated": {
        const uri = notification.params?.uri as string;
        console.log(`Resource updated: ${uri}`);
        const fresh = await session.readResource(uri);
        for (const content of fresh.contents) {
          if ("text" in content) console.log("  New content:", content.text);
        }
        break;
      }
      default:
        console.log(`Notification: ${notification.method}`, notification.params);
    }
  };

  session.on("notification", handler);

  // Keep alive to receive notifications
  console.log("\nMonitoring resources... (Ctrl+C to stop)");
  await new Promise<void>((resolve) => {
    process.on("SIGINT", () => {
      console.log("\nShutting down...");
      resolve();
    });
  });
} finally {
  await client.closeAllSessions();
}
```

## Recipe 8: Code Mode Client

```typescript
import { MCPClient, BaseCodeExecutor } from "mcp-use";

// — VM executor (local, zero-latency) —
const vmClient = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
      },
      github: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! },
      },
    },
  },
  {
    codeMode: {
      enabled: true,
      executor: "vm",
      executorOptions: { timeoutMs: 60000, memoryLimitMb: 512 },
    },
  }
);

try {
  await vmClient.createAllSessions();

  // Direct code execution with tool namespaces
  const result = await vmClient.executeCode(`
    // Tools are accessed as serverName.toolName(args)
    const files = await filesystem.list_directory({ path: "." });
    const prs = await github.list_pull_requests({ owner: "facebook", repo: "react" });
    return { fileCount: files.length, prCount: prs.length };
  `);
  console.log("VM result:", result.result);
  console.log("Logs:", result.logs);
  console.log("Time:", result.execution_time, "s");

  // search_tools() discovery
  const allTools = await vmClient.searchTools();
  console.log(`Total tools: ${allTools.meta.total_tools}`);
  console.log(`Namespaces: ${allTools.meta.namespaces.join(", ")}`);

  const fsTools = await vmClient.searchTools("file", "descriptions");
  for (const t of fsTools.results) {
    console.log(`  ${t.server}.${t.name}: ${t.description}`);
  }
} finally {
  await vmClient.close(); // close() cleans up both sessions and the code executor
}

// — E2B executor (cloud sandbox, true isolation) —
const e2bClient = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
      },
    },
  },
  {
    codeMode: {
      enabled: true,
      executor: "e2b",
      executorOptions: {
        apiKey: process.env.E2B_API_KEY!,
        timeoutMs: 300000,
      },
    },
  }
);

try {
  await e2bClient.createAllSessions();

  const sandboxResult = await e2bClient.executeCode(`
    const files = await filesystem.list_directory({ path: "." });
    return files;
  `);
  console.log("E2B result:", sandboxResult.result);
  if (sandboxResult.error) console.error("E2B error:", sandboxResult.error);
} finally {
  await e2bClient.close();
}

// — Custom executor —
const customClient = new MCPClient(
  {
    mcpServers: {
      myServer: { url: "http://localhost:3000/mcp" },
    },
  },
  {
    codeMode: {
      enabled: true,
      executor: async (code: string, timeout?: number) => {
        const start = Date.now();
        const logs: string[] = [];
        try {
          const fn = new Function("console", `return (async () => { ${code} })()`);
          const fakeConsole = { log: (...args: any[]) => logs.push(args.join(" ")) };
          const result = await fn(fakeConsole);
          return { result, logs, error: null, execution_time: (Date.now() - start) / 1000 };
        } catch (e) {
          return { result: null, logs, error: (e as Error).message, execution_time: (Date.now() - start) / 1000 };
        }
      },
    },
  }
);
```

## Recipe 9: CLI Scripting

```bash
#!/bin/bash
set -euo pipefail

# — Connect to servers —
npx mcp-use client connect http://localhost:3000/mcp --name api-server
npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-filesystem /tmp" --name fs

# — Connect with bearer token auth —
npx mcp-use client connect https://api.example.com/mcp --name auth-server --auth sk-my-token

# — List sessions —
npx mcp-use client sessions list

# — List tools (JSON for scripting) —
TOOLS=$(npx mcp-use client tools list --session api-server --json)
echo "Available tools:"
echo "$TOOLS" | jq -r '.[].name'

# — Inspect a tool's input schema before calling it —
npx mcp-use client tools describe get_data --session api-server

# — Call a tool and parse output —
DATA=$(npx mcp-use client tools call get_data '{"query": "active users"}' --session api-server --json)
COUNT=$(echo "$DATA" | jq '.content[0].text | fromjson | .count')
echo "Active users: $COUNT"

# — Call a tool with explicit timeout (ms) —
RESULT=$(npx mcp-use client tools call generate_report '{"year": 2024}' --session api-server --json --timeout 120000)

# — Multi-step workflow: read → process → write —
# Step 1: Read config from one server
CONFIG=$(npx mcp-use client tools call read_file '{"path": "/tmp/config.json"}' --session fs --json)
CONFIG_TEXT=$(echo "$CONFIG" | jq -r '.content[0].text')

# Step 2: Process with API server
RESULT=$(npx mcp-use client tools call process_config "{\"config\": $CONFIG_TEXT}" --session api-server --json)
PROCESSED=$(echo "$RESULT" | jq -r '.content[0].text')

# Step 3: Write result back
npx mcp-use client tools call write_file "{\"path\": \"/tmp/result.json\", \"content\": \"$PROCESSED\"}" --session fs

echo "Workflow complete."

# — Resource operations —
npx mcp-use client resources list --session api-server --json | jq -r '.[].uri'
npx mcp-use client resources read "config://app" --session api-server

# — Subscribe to resource updates (process stays running) —
npx mcp-use client resources subscribe "data://live-feed" --session api-server

# — Prompt retrieval —
PROMPT=$(npx mcp-use client prompts get analyze_data '{"dataset": "users"}' --session api-server --json)
echo "$PROMPT" | jq -r '.messages[0].content.text'

# — Cleanup —
npx mcp-use client disconnect --all
```

### Session Persistence Across Scripts

```bash
#!/bin/bash
# script-a.sh — Setup (sessions persist at ~/.mcp-use/cli-sessions.json)
npx mcp-use client connect http://localhost:3000/mcp --name shared-session
npx mcp-use client tools call initialize '{"project": "demo"}' --session shared-session --json > /dev/null
echo "Session created."
```

```bash
#!/bin/bash
# script-b.sh — Uses existing session from script-a.sh
npx mcp-use client sessions list  # shows shared-session
RESULT=$(npx mcp-use client tools call get_status '{}' --session shared-session --json)
echo "Status: $(echo "$RESULT" | jq -r '.content[0].text')"
```

```bash
#!/bin/bash
# script-c.sh — Cleanup
npx mcp-use client disconnect shared-session
```

## Recipe 10: Logging Callback

The `loggingCallback` option receives structured log messages emitted by the server. Use `OnNotificationCallback` for the notification handler type.

```typescript
import { MCPClient, types, type OnNotificationCallback } from "mcp-use";

async function handleLogs(
  logParams: types.LoggingMessageNotificationParams
): Promise<void> {
  // logParams.level: "debug" | "info" | "warning" | "error"
  // logParams.message: string
  console.log(`[${logParams.level.toUpperCase()}] ${logParams.message}`);
}

const onNotification: OnNotificationCallback = (notification) => {
  console.log(`[notification] ${notification.method}`, notification.params ?? "");
};

const client = new MCPClient(
  {
    mcpServers: {
      myServer: { url: "http://localhost:3000/mcp" },
    },
  },
  {
    loggingCallback: handleLogs,
    onNotification,
  }
);

try {
  await client.createAllSessions();
  const session = client.getSession("myServer");
  const result = await session.callTool("logging_tool", {});
  console.log("Result:", result.content);
} finally {
  await client.closeAllSessions();
}
```

---

## Key Patterns

**Error handling** — check `isError` on tool results:
```typescript
const result = await session.callTool("my-tool", { arg: "value" });
if (result.isError) {
  console.error("Tool failed:", result.content);
} else {
  console.log("Success:", result.content);
}
```

**Timeout with abort** — cancel long-running tools:
```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 60000);

const result = await session.callTool("slow-tool", {}, {
  timeout: 120000,
  maxTotalTimeout: 300000,
  resetTimeoutOnProgress: true,
  signal: controller.signal,
});
```

**Session lifecycle** — always clean up:
```typescript
const client = new MCPClient(config);
try {
  await client.createAllSessions();
  // ... work ...
} finally {
  await client.closeAllSessions();
}
```

**Config from file** — load JSON config:
```typescript
import { MCPClient, loadConfigFile } from "mcp-use";

const config = loadConfigFile("./mcp-config.json");
const client = new MCPClient(config);
await client.createAllSessions();
```

**Completions** — autocomplete prompt arguments and resource template variables (requires server capability):
```typescript
await client.createAllSessions();
const session = client.getSession("myServer");

// Complete a prompt argument
const result = await session.complete({
  ref: { type: "ref/prompt", name: "code-review" },
  argument: { name: "language", value: "py" },
});
console.log("Suggestions:", result.completion.values);

// Complete a resource template URI variable
const resourceResult = await session.complete({
  ref: { type: "ref/resource", uri: "file:///{path}" },
  argument: { name: "path", value: "/home/user" },
});
console.log("Path suggestions:", resourceResult.completion.values);
```

**Low-level session access** — `HttpConnector` + `MCPSession` for advanced notification handling:
```typescript
import { HttpConnector, MCPSession, type Notification, type Root } from "mcp-use";

const connector = new HttpConnector("http://localhost:3000/mcp", {
  clientInfo: { name: "my-client", version: "1.0.0" },
  roots: [{ uri: "file:///workspace", name: "Workspace" }],
});

const session = new MCPSession(connector, false);
session.on("notification", async (notification: Notification) => {
  console.log(`Notification: ${notification.method}`);
});

await session.connect();
await session.initialize();
// Later: update roots
await session.setRoots([{ uri: "file:///workspace", name: "Workspace" }]);
```
