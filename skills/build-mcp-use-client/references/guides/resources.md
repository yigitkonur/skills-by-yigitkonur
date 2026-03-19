# Resources

Complete reference for accessing MCP resources — listing, reading, templates, subscriptions, and content types.

---

## Understanding Resources

Resources provide URI-based access to content and data exposed by MCP servers. Use resources to read configuration, files, database records, and any other data a server chooses to expose.

Key characteristics:

- **Unique URI** — Every resource is identified by a unique URI string (e.g., `config://settings`, `file:///data.json`).
- **Content types** — Resources return text, JSON, binary (base64-encoded), or any other MIME type.
- **Static or dynamic** — Resources are either fixed (always return the same data) or generated on demand by the server.
- **Template support** — Servers expose parameterized URI templates that accept variables, enabling dynamic content access.

Resources are read-only from the client perspective. The client lists available resources, reads their content, and optionally subscribes to change notifications. The server controls what resources exist and how they behave.

---

## Types of Resources

MCP defines two categories of resources:

| Category | URI Style | Behavior | Example |
|---|---|---|---|
| **Direct Resources** | Fixed, concrete URI | Always resolve to the same endpoint | `config://settings` |
| **Resource Templates** | URI with `{variable}` placeholders | Accept parameters to resolve dynamically | `file:///{path}` |

### Direct Resources

Direct resources have static URIs. The server registers them at startup and they remain available for the lifetime of the session. Use `listResources()` to discover them.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

// Direct resources appear in listResources() — result.resources is the array
const result = await session.listAllResources();
for (const resource of result.resources) {
  console.log(`URI: ${resource.uri}`);
  console.log(`Name: ${resource.name}`);
  console.log(`MIME: ${resource.mimeType ?? "not specified"}`);
  console.log(`Description: ${resource.description ?? "none"}`);
  console.log("---");
}
```

### Resource Templates

Resource templates define URI patterns with placeholders. The client fills in the placeholders to construct a concrete URI, then reads it like any other resource.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    fileServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("fileServer");

// Server defines template: file:///{path}
// Client fills the variable to form a concrete URI:
const result = await session.readResource("file:///home/user/data.json");
for (const content of result.contents) {
  console.log("File content:", content.text);
}
```

---

## Listing Resources

Always list available resources before attempting to read. This avoids hardcoding URIs that may not exist on a given server.

`listResources()` supports pagination via a `cursor` argument and returns an object with a `resources` array and an optional `nextCursor`. For most use cases, `listAllResources()` is more convenient — it handles pagination automatically and returns the full list.

### List All Direct Resources

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

// listAllResources() handles pagination and returns all resources at once
const result = await session.listAllResources();

// Each resource has: uri, name, mimeType?, description?
for (const resource of result.resources) {
  console.log(`${resource.uri}: ${resource.name}`);
}
```

### Paginated Listing

```typescript
// First page
const page1 = await session.listResources();
for (const resource of page1.resources) {
  console.log(resource.uri);
}

// Next page (if there are more)
if (page1.nextCursor) {
  const page2 = await session.listResources(page1.nextCursor);
  for (const resource of page2.resources) {
    console.log(resource.uri);
  }
}
```

### Listing Resource Templates

Servers may also expose resource templates (URI patterns with variables). List them separately:

```typescript
const templates = await session.listResourceTemplates();
for (const template of templates.resourceTemplates) {
  console.log(`Template: ${template.uriTemplate} — ${template.name}`);
}
```

### Discover Then Read Pattern

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    backend: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("backend");

// Step 1: discover what is available (all pages)
const result = await session.listAllResources();

// Step 2: find the resource you need
const configResource = result.resources.find((r) => r.uri === "config://settings");
if (!configResource) {
  throw new Error("config://settings not available on this server");
}

// Step 3: read it
const readResult = await session.readResource(configResource.uri);
for (const content of readResult.contents) {
  console.log("Config:", content.text);
}
```

> ❌ **BAD** — Hardcoding a resource URI without checking availability:
>
> ```typescript
> // Fails silently or throws if the server does not expose this URI
> const readResult = await session.readResource("config://settings");
> ```

> ✅ **GOOD** — List first, then read:
>
> ```typescript
> const result = await session.listAllResources();
> const target = result.resources.find((r) => r.uri === "config://settings");
> if (target) {
>   const readResult = await session.readResource(target.uri);
>   for (const content of readResult.contents) {
>     console.log(content.text);
>   }
> }
> ```

---

## Reading Resources

Read a resource by passing its URI to `readResource()`. The method returns an object with a `contents` array. Each entry in `contents` has a `uri`, optional `mimeType`, and either a `text` field (for text content) or a `blob` field (`string` — base64-encoded binary, per the MCP spec) for binary content. The `blob` value should be decoded with `Buffer.from(content.blob, "base64")` before writing to disk.

### Basic Read

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

const result = await session.readResource("config://settings");

for (const content of result.contents) {
  if (content.mimeType === "application/json") {
    console.log("JSON content:", content.text);
  } else if (content.mimeType === "text/plain") {
    console.log("Text content:", content.text);
  } else {
    console.log("Binary content length:", content.blob?.length);
  }
}
```

### Reading Multiple Resources

When you need data from several resources, read them sequentially:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

const uris = [
  "config://settings",
  "config://feature-flags",
  "db://users/count"
];

for (const uri of uris) {
  const result = await session.readResource(uri);
  for (const content of result.contents) {
    console.log(`${uri}:`, content.text ?? content.blob);
  }
}
```

---

## Resource Content Types

Resources return content in one of two forms depending on the MIME type. The `readResource()` return value always has a `contents` array; each element has a `uri`, optional `mimeType`, and either a `text` field or a `blob` field.

### Content Type Reference

| Content Form | MIME Types | Field Present | Notes |
|---|---|---|---|
| **Text** | `text/plain`, `application/json`, `text/yaml`, `text/csv`, `text/html` | `content.text` | String value, parse as needed |
| **Binary** | `image/png`, `application/pdf`, `application/octet-stream` | `content.blob` | `Uint8Array \| number[]`; wrap in `Buffer.from(content.blob)` to write |

### Text Content

Text-based resources (JSON, XML, plain text) are available via `content.text`:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

const result = await session.readResource("file:///config.json");

for (const content of result.contents) {
  if ("text" in content) {
    console.log("Text content:", content.text);
    console.log("MIME type:", content.mimeType);
  }
}
```

### Binary Content

Binary resources (images, files) are available via `content.blob`. Wrap the value in `Buffer.from()` before writing to disk:

```typescript
import { MCPClient } from "mcp-use";
import { writeFileSync } from "fs";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

const result = await session.readResource("file:///image.png");

for (const content of result.contents) {
  if ("blob" in content && content.blob) {
    console.log(`Binary data size: ${content.blob.length} bytes`);
    writeFileSync("downloaded_image.png", Buffer.from(content.blob));
  }
}
```

> ❌ **BAD** — Treating the return value as a plain string:
>
> ```typescript
> const result = await session.readResource("file:///image.png");
> console.log(result); // Logs the whole result object, not the content
> ```

> ✅ **GOOD** — Iterate `result.contents` and check for `text` or `blob`:
>
> ```typescript
> const result = await session.readResource("file:///image.png");
> for (const content of result.contents) {
>   if ("blob" in content && content.blob) {
>     writeFileSync("image.png", Buffer.from(content.blob));
>   } else if ("text" in content) {
>     console.log(content.text);
>   }
> }
> ```

---

## Working with Resource Templates

Resource templates are dynamic resources that accept parameters to generate different content based on input. The server publishes a URI pattern with `{variable}` placeholders (e.g., `db://users/{user_id}/profile`). The client fills in the variables to form a concrete URI, then calls `readResource()` with the fully resolved URI.

### Using Templates to Read Resources

Construct the concrete URI by substituting the template variables, then call `readResource()`. Iterate `result.contents` to access the data:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    database_server: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("database_server");

// Template URI might be: "db://users/{user_id}/profile"
// Fill in the variable to form a concrete URI:
const result = await session.readResource("db://users/12345/profile");
for (const content of result.contents) {
  console.log("User profile:", content.text);
}
```

### Template Variable Patterns

| Template | Variable | Example Concrete URI |
|---|---|---|
| `file:///{path}` | `path` | `file:///home/user/data.json` |
| `db://users/{userId}` | `userId` | `db://users/42` |
| `log://app/{date}` | `date` | `log://app/2025-01-15` |
| `cache://{namespace}/{key}` | `namespace`, `key` | `cache://sessions/abc123` |

---

## Resource Subscriptions

Some MCP servers support resource subscriptions, allowing the client to receive notifications when a resource changes.

### Subscribing and Unsubscribing Programmatically

Use `session.subscribeToResource(uri)` and `session.unsubscribeFromResource(uri)` to manage subscriptions:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({ mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } });
await client.createAllSessions();
const session = client.requireSession("myServer");

// Subscribe to a specific resource
await session.subscribeToResource("file:///tmp/data.json");

// Unsubscribe when no longer needed
await session.unsubscribeFromResource("file:///tmp/data.json");
```

### CLI-Based Subscriptions

Use the `mcp-use` CLI to subscribe and unsubscribe from resource changes interactively:

```bash
# Subscribe to changes on a specific resource
npx mcp-use client resources subscribe "file:///tmp/data.json"

# Unsubscribe when you no longer need updates
npx mcp-use client resources unsubscribe "file:///tmp/data.json"

# List current subscriptions
npx mcp-use client resources list
```

### Programmatic Subscription via Notifications

Listen for resource change notifications on the session:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

// Listen for resource list changes
session.on("notification", async (notification) => {
  if (notification.method === "notifications/resources/list_changed") {
    console.log("Resource list changed — refreshing...");
    const result = await session.listAllResources();
    console.log("Updated resource count:", result.resources.length);
  }
});

// Listen for individual resource updates
session.on("notification", async (notification) => {
  if (notification.method === "notifications/resources/updated") {
    const uri = notification.params?.uri;
    console.log(`Resource updated: ${uri}`);
    const freshResult = await session.readResource(uri);
    for (const content of freshResult.contents) {
      console.log("New content:", content.text ?? content.blob);
    }
  }
});
```

> ❌ **BAD** — Not handling resource change notifications:
>
> ```typescript
> // Read once and assume the data never changes
> const data = await session.readResource("config://settings");
> // Stale data used for the rest of the session
> ```

> ✅ **GOOD** — Subscribe to changes and re-read when notified:
>
> ```typescript
> let cachedConfig = await session.readResource("config://settings");
>
> session.on("notification", async (notification) => {
>   if (notification.method === "notifications/resources/updated") {
>     if (notification.params?.uri === "config://settings") {
>       cachedConfig = await session.readResource("config://settings");
>       for (const content of cachedConfig.contents) {
>         console.log("Config refreshed:", content.text);
>       }
>     }
>   }
> });
> ```

---

## React Hook Usage

The `mcp-use/react` package provides hooks for accessing resources in React components.

### Using `useMcp`

```typescript
import { useMcp } from "mcp-use/react";

function ResourceViewer() {
  const mcp = useMcp({ url: "http://localhost:3000/mcp" });

  if (mcp.state !== "ready") {
    return <div>Connecting...</div>;
  }

  const handleRead = async () => {
    const result = await mcp.readResource("config://settings");
    for (const content of result.contents) {
      console.log(content.text);
    }
  };

  const handleList = async () => {
    // In the useMcp hook context, listResources returns a paginated result
    const result = await mcp.listResources();
    for (const r of result.resources) {
      console.log(`${r.uri}: ${r.name}`);
    }
  };

  return (
    <div>
      <button onClick={handleRead}>Read Config</button>
      <button onClick={handleList}>List Resources</button>
    </div>
  );
}
```

### Using `useMcpServer`

The `useMcpServer` hook provides direct access to a named server's resources.

```typescript
import { useMcpServer } from "mcp-use/react";

function ServerResources() {
  const server = useMcpServer("my-server");

  // Access cached resource list
  const resources = server.resources; // Resource[]

  const handleRead = async () => {
    const result = await server.readResource("config://settings");
    for (const content of result.contents) {
      console.log("Config:", content.text);
    }
  };

  const handleRefresh = async () => {
    await server.listResources();
    console.log("Refreshed");
  };

  return (
    <div>
      <h2>Resources ({resources.length})</h2>
      <ul>
        {resources.map((r) => (
          <li key={r.uri}>
            {r.name} — <code>{r.uri}</code>
          </li>
        ))}
      </ul>

      <button onClick={handleRead}>Read Config</button>
      <button onClick={handleRefresh}>Refresh</button>
    </div>
  );
}
```

---

## URI Patterns and Conventions

MCP does not mandate specific URI schemes. Servers define their own. These are common conventions:

| Scheme | Example URI | Typical Use |
|---|---|---|
| `file://` | `file:///home/user/data.json` | File system access |
| `config://` | `config://settings` | Application configuration |
| `db://` | `db://users/123` | Database records |
| `log://` | `log://app/2025-01-15` | Log entries by date |
| `cache://` | `cache://sessions/abc123` | Cached data |
| `env://` | `env://NODE_ENV` | Environment variables |
| `secret://` | `secret://api-key` | Secrets (server-controlled access) |
| Custom | `weather://london` | Application-specific data |

### URI Best Practices

- Use hierarchical paths for nested data: `db://users/42/orders/7`
- Keep URIs human-readable and predictable
- Document URI schemes in your server's description
- Use templates for any URI that accepts variable input

---

## Error Handling

Resource operations can fail for several reasons. Always wrap reads in try/catch blocks.

### Common Error Scenarios

| Error | Cause | Recovery |
|---|---|---|
| Resource not found | URI does not match any server resource | List resources first, verify URI exists |
| Invalid URI | Malformed URI string | Validate URI format before calling |
| Server unavailable | Connection lost or server crashed | Reconnect the session |
| Permission denied | Server rejects access to the resource | Check server access controls |
| Template variable invalid | Provided value not accepted by server | Use `complete()` to get valid values |

### Try/Catch Pattern

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

type ReadResult = Awaited<ReturnType<typeof session.readResource>>;

async function safeReadResource(uri: string): Promise<ReadResult | null> {
  try {
    return await session.readResource(uri);
  } catch (error) {
    console.error(`Failed to read resource ${uri}:`, error);
    return null;
  }
}

// Use the safe wrapper
const config = await safeReadResource("config://settings");
if (config) {
  for (const content of config.contents) {
    console.log("Got config:", content.text);
  }
} else {
  console.log("Using default configuration");
}
```

### Validating Before Reading

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

async function readIfAvailable(uri: string): Promise<unknown | null> {
  const result = await session.listAllResources();
  const exists = result.resources.some((r) => r.uri === uri);

  if (!exists) {
    console.warn(`Resource ${uri} is not available on this server`);
    return null;
  }

  return session.readResource(uri);
}

const data = await readIfAvailable("config://settings");
```

---

## Caching Strategies

Resource reads involve network round-trips. Cache results when appropriate.

### When to Cache

| Scenario | Cache? | Reason |
|---|---|---|
| Configuration that rarely changes | ✅ Yes | Avoid repeated reads for stable data |
| Database records that update frequently | ❌ No | Stale data causes bugs |
| Static file content | ✅ Yes | File content does not change during session |
| Real-time metrics | ❌ No | Must always reflect current state |
| Templates list | ✅ Yes | Templates rarely change after server startup |

### Simple In-Memory Cache

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

type ReadResult = Awaited<ReturnType<typeof session.readResource>>;
const resourceCache = new Map<string, { data: ReadResult; timestamp: number }>();
const CACHE_TTL_MS = 60_000; // 1 minute

async function cachedRead(uri: string): Promise<ReadResult> {
  const cached = resourceCache.get(uri);
  const now = Date.now();

  if (cached && now - cached.timestamp < CACHE_TTL_MS) {
    return cached.data;
  }

  const data = await session.readResource(uri);
  resourceCache.set(uri, { data, timestamp: now });
  return data;
}

// First call hits the server
const config1 = await cachedRead("config://settings");

// Second call within TTL returns cached data
const config2 = await cachedRead("config://settings");
```

### Cache Invalidation with Notifications

Combine caching with subscription notifications for the best of both worlds:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

type ReadResult = Awaited<ReturnType<typeof session.readResource>>;
const cache = new Map<string, ReadResult>();

// Invalidate cache on resource update
session.on("notification", async (notification) => {
  if (notification.method === "notifications/resources/updated") {
    const uri = notification.params?.uri;
    if (typeof uri === "string") {
      cache.delete(uri);
      console.log(`Cache invalidated for ${uri}`);
    }
  }

  if (notification.method === "notifications/resources/list_changed") {
    cache.clear();
    console.log("Full cache cleared — resource list changed");
  }
});

async function smartRead(uri: string): Promise<ReadResult> {
  const cached = cache.get(uri);
  if (cached) {
    return cached;
  }
  const data = await session.readResource(uri);
  cache.set(uri, data);
  return data;
}
```

---

## Browser Usage

Use the browser-specific import for browser environments:

```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});
await client.createAllSessions();
const session = client.requireSession("myServer");

const listResult = await session.listAllResources();
console.log("Available resources:", listResult.resources);

const readResult = await session.readResource("config://settings");
for (const content of readResult.contents) {
  console.log("Config:", content.text);
}
```

The browser build excludes Node-specific dependencies (filesystem, child process) and works in any modern browser environment.

---

## Complete Workflow Example

End-to-end example combining discovery, reading, templates, and notifications:

```typescript
import { MCPClient } from "mcp-use";

async function main() {
  // 1. Initialize client
  const client = new MCPClient({
    mcpServers: {
      backend: { url: "http://localhost:3000/mcp" }
    }
  });
  await client.createAllSessions();
  const session = client.requireSession("backend");

  // 2. Discover available resources (listAllResources handles pagination)
  const listResult = await session.listAllResources();
  console.log(`Found ${listResult.resources.length} resources:`);
  for (const r of listResult.resources) {
    console.log(`  ${r.uri} — ${r.name} (${r.mimeType ?? "unknown type"})`);
  }

  // 3. Read a direct resource
  const configResult = await session.readResource("config://settings");
  for (const content of configResult.contents) {
    console.log("Config:", content.text);
  }

  // 4. Use a template URI (fill in the variable manually)
  const userResult = await session.readResource("db://users/1");
  for (const content of userResult.contents) {
    console.log("User:", content.text);
  }

  // 5. Subscribe to changes
  session.on("notification", async (notification) => {
    if (notification.method === "notifications/resources/list_changed") {
      const updated = await session.listAllResources();
      console.log("Resources changed. New count:", updated.resources.length);
    }
    if (notification.method === "notifications/resources/updated") {
      console.log("Resource updated:", notification.params?.uri);
    }
  });

  console.log("Listening for resource changes...");
}

main().catch(console.error);
```

---

## Quick Reference

### Session Resource Methods

| Method | Signature | Returns |
|---|---|---|
| `session.listResources(cursor?, options?)` | Paginated list | `Promise<{ resources: Resource[]; nextCursor?: string }>` |
| `session.listAllResources(options?)` | All resources (handles pagination) | `Promise<{ resources: Resource[] }>` |
| `session.listResourceTemplates(options?)` | List URI templates | `Promise<{ resourceTemplates: ResourceTemplate[] }>` |
| `session.readResource(uri, options?)` | Read content of a resource | `Promise<{ contents: ResourceContent[] }>` |
| `session.subscribeToResource(uri, options?)` | Subscribe to resource changes | `Promise<void>` |
| `session.unsubscribeFromResource(uri, options?)` | Unsubscribe from resource changes | `Promise<void>` |

### ResourceContent Shape

Each element of `result.contents` from `readResource()`:

| Field | Type | Present When |
|---|---|---|
| `uri` | `string` | Always |
| `mimeType` | `string \| undefined` | When server specifies content type |
| `text` | `string \| undefined` | Text content (`text/plain`, `application/json`, etc.) |
| `blob` | `Uint8Array \| number[]` \| undefined | Binary content (`image/png`, `application/pdf`, etc.) |

### Resource Object Shape

| Field | Type | Required | Description |
|---|---|---|---|
| `uri` | `string` | ✅ | Unique resource identifier |
| `name` | `string` | ✅ | Human-readable display name |
| `description` | `string` | ❌ | What this resource contains |
| `mimeType` | `string` | ❌ | Content MIME type hint |

### Notification Types

| Method | Trigger |
|---|---|
| `notifications/resources/list_changed` | Server adds or removes resources |
| `notifications/resources/updated` | Content of a specific resource changed |
