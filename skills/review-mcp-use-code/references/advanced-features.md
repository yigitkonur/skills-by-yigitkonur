# Advanced Features

## Elicitation

Elicitation allows tools to request additional input from the user during execution.

### Two Modes

| Mode | Use Case | How |
|---|---|---|
| **Form** | Collect structured data (non-sensitive) | `ctx.elicit(message, zodSchema)` |
| **URL** | Sensitive data (credentials, OAuth) | `ctx.elicit(message, 'https://...')` |

### Form Mode

```typescript
server.tool({
    name: 'create-account',
    description: 'Create a new user account',
}, async (_, ctx) => {
    const result = await ctx.elicit(
        'Please provide your account details',
        z.object({
            name: z.string().describe('Full name'),
            email: z.string().email().describe('Email address'),
            role: z.enum(['admin', 'user', 'viewer']).default('user').describe('Account role'),
            notifications: z.boolean().default(true).describe('Email notifications'),
        })
    )

    if (result.action === 'accept') {
        // result.data is typed: { name: string, email: string, role: 'admin'|'user'|'viewer', ... }
        await createUser(result.data)
        return text(`Account created for ${result.data.name}`)
    } else if (result.action === 'decline') {
        return text('Account creation cancelled by user')
    } else {
        return text('Operation cancelled')
    }
})
```

### URL Mode

```typescript
server.tool({ name: 'connect-github' }, async (_, ctx) => {
    const result = await ctx.elicit(
        'Please authorize with GitHub',
        'https://github.com/login/oauth/authorize?client_id=xxx&scope=repo'
    )

    if (result.action === 'accept') return text('Authorization completed')
    if (result.action === 'decline') return error('Authorization declined')
    return text('Authorization cancelled')
})
```

### ElicitResult Interface

```typescript
interface ElicitResult<T = unknown> {
    action: 'accept' | 'decline' | 'cancel'
    data?: T   // Present for accept in form mode
}
```

### Server-Side Validation Flow

1. Zod schema → JSON Schema (sent to client)
2. Client collects user input
3. Client validates (optional)
4. Data sent back to server
5. **Server validates against original Zod schema** (mcp-use feature)
6. Typed data returned to tool handler

### Capability Check

```typescript
server.tool({ name: 'interactive-tool' }, async (_, ctx) => {
    if (!ctx.client?.can('elicitation')) {
        return error('This tool requires a client that supports elicitation')
    }
    const result = await ctx.elicit('...', z.object({...}))
})
```

---

## Sampling

Sampling allows tools to request LLM completions from the client.

### Basic Usage

```typescript
server.tool({
    name: 'smart-search',
    description: 'Search and summarize results',
    schema: z.object({ query: z.string() }),
}, async ({ query }, ctx) => {
    const results = await searchDatabase(query)
    const sampled = await ctx.sample(`Summarize these search results:\n${JSON.stringify(results)}`)

    return text(sampled.content[0].text)
})
```

### Extended Usage

```typescript
const response = await ctx.sample({
    messages: [
        { role: 'user', content: { type: 'text', text: 'Analyze this data...' } },
    ],
    modelPreferences: {
        intelligencePriority: 0.8,
        speedPriority: 0.5,
    },
    systemPrompt: 'You are an expert analyst.',
    maxTokens: 100,
})

console.log(response.content[0].text)
console.log(response.model)
console.log(response.stopReason)
```

### Progress Reporting During Sampling

```typescript
const response = await ctx.sample(
    {
        messages: [{ role: 'user', content: { type: 'text', text: '...' } }],
    },
    {
        timeout: 120000,
        progressIntervalMs: 2000,
        onProgress: ({ message }) => {
            console.log(`[Sampling progress] ${message}`)
        },
    }
)
```

### Capability Check

```typescript
if (ctx.client?.can('sampling')) {
    const result = await ctx.sample('...')
} else {
    // Fallback: use a direct API call
    const result = await callOpenAI('...')
}
```

---

## Subscriptions

Resource subscriptions allow clients to receive notifications when resource content changes.

### Server-Side

```typescript
// Notify subscribed clients that a specific resource changed
await server.notifyResourceUpdated('users://123/profile')

// Notify clients that the resources list changed (after dynamic add/remove)
await server.sendResourcesListChanged()
```

### Subscription Lifecycle

```
Client                                 Server
──────                                 ──────
resources/subscribe(uri)         →     Track subscription for session
                                       (auto-cleanup on disconnect)

[resource changes]               ←     notifications/resources/updated
                                       { uri: 'users://123/profile' }

resources/read(uri)              →     Return fresh content

resources/unsubscribe(uri)       →     Remove subscription tracking
```

### Per-Session Tracking

Subscriptions are tracked per session and automatically cleaned up when sessions disconnect:

```typescript
// Internal tracking (handled by mcp-use)
// Map<sessionId, Set<resourceUri>>
```

---

## Notifications

MCP supports bidirectional notifications (fire-and-forget, no response expected).

### Server → Client Notifications

```typescript
// Built-in list-change notifications
await server.sendToolsListChanged()      // After adding/removing tools
await server.sendResourcesListChanged()  // After adding/removing resources
await server.sendPromptsListChanged()    // After adding/removing prompts

// Custom notification to all connected sessions
await server.sendNotification('custom/event', { key: 'value' })

// Custom notification to a specific session
await server.sendNotificationToSession(sessionId, 'custom/event', { key: 'value' })

// From tool context (current client/session)
server.tool({ name: 'my-tool' }, async (_, ctx) => {
    await ctx.sendNotification('processing/started', {})
    // ... do work ...
    await ctx.sendNotification('processing/complete', { items: 42 })
    return text('Done')
})
```

### Progress Reporting

```typescript
server.tool({ name: 'long-task' }, async (_, ctx) => {
    if (ctx.reportProgress) {
        await ctx.reportProgress(0, 100, 'Starting...')
    }

    for (let i = 0; i < 100; i++) {
        await doWork(i)
        if (ctx.reportProgress) {
            await ctx.reportProgress(i + 1, 100)
        }
    }
    return text('Complete')
})
```

### Client → Server Notifications

```typescript
// Roots changed notification
server.onRootsChanged(async (roots) => {
    console.log('Client roots changed:', roots)
    // Re-index or update server state based on new roots
})
```

---

## Logging

### Server-Side Logging (mcp-use Logger)

```typescript
import { Logger } from 'mcp-use/server'

Logger.configure({
    level: 'info',      // error | warn | info | http | verbose | debug | silly
    format: 'minimal',  // minimal | detailed
})

// Numeric convenience mode
Logger.setDebug(0) // production
Logger.setDebug(1) // debug mode
Logger.setDebug(2) // verbose debug mode
```

### Tool-to-Client Logging

Tools can send log messages to the connected client:

```typescript
server.tool({ name: 'my-tool' }, async (_, ctx) => {
    await ctx.log('info', 'Starting processing')
    await ctx.log('debug', 'Detailed debug info', 'my-tool')
    await ctx.log('warning', 'Something unexpected')
    await ctx.log('error', 'Something failed')

    // MCP protocol log levels:
    // 'debug' | 'info' | 'notice' | 'warning' | 'error' | 'critical' | 'alert' | 'emergency'

    return text('Done')
})
```

### Log Levels

| Level | Numeric | Use Case |
|---|---|---|
| emergency | 0 | System unusable |
| alert | 1 | Immediate action needed |
| critical | 2 | Critical conditions |
| error | 3 | Error conditions |
| warning | 4 | Warning conditions |
| notice | 5 | Normal but significant |
| info | 6 | Informational |
| debug | 7 | Debug-level |

---

## Middleware

### Hono Middleware (mcp-use TS)

```typescript
import { MCPServer } from 'mcp-use/server'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

// Standard Hono middleware
server.app.use('*', cors())
server.app.use('*', logger())

// Custom middleware
server.app.use('*', async (c, next) => {
    const start = Date.now()
    await next()
    console.log(`${c.req.method} ${c.req.url} - ${Date.now() - start}ms`)
})

// Custom routes
server.app.get('/health', (c) => c.json({ status: 'ok' }))
server.app.post('/api/webhook', async (c) => {
    const body = await c.req.json()
    return c.json({ received: true, body })
})
```

### Custom HTTP Routes

```typescript
// MCP routes are registered internally: /mcp, /mcp-use/widgets/*, /inspector
// Add your own routes before calling listen() or getHandler().

server.app.get('/api/mango', (c) => c.json({ fruit: 'mango' }))
```

### Python Middleware

```python
from mcp_use.server.middleware import Middleware

class LoggingMiddleware(Middleware):
    async def process_request(self, request, context):
        print(f"Request: {request.method}")
        return request
    
    async def process_response(self, response, context):
        return response

server = MCPServer(
    name="my-server",
    middleware=[LoggingMiddleware()],
)
```

---

## UI Widgets (mcp-use / MCP Apps)

Widgets enable rich interactive UI in supported MCP clients.

### Tool + Widget Helper Pattern (Recommended)

```typescript
import { widget, text } from 'mcp-use/server'

server.tool({
    name: 'show-weather',
    description: 'Get weather and render widget',
    schema: z.object({ city: z.string() }),
    widget: {
        name: 'weather-display',
        invoking: 'Fetching weather...',
        invoked: 'Weather loaded',
    },
}, async ({ city }) => {
    const weatherData = await fetchWeather(city)

    return widget({
        props: weatherData,
        output: text(`Weather in ${city}: ${weatherData.temp}°C`),
    })
})
```

### UI Resources

```typescript
server.uiResource({
    type: 'externalUrl',
    name: 'weather_dashboard',
    widget: 'weather-dashboard',
    title: 'Weather Dashboard',
    description: 'Interactive weather visualization',
    schema: z.object({ city: z.string() }),
    size: ['800px', '600px'],
})
```

---

## Code Execution Mode (Python)

```python
from mcp_use import MCPClient

client = MCPClient(config=config, code_mode=True)
await client.create_all_sessions()

result = await client.execute_code('''
    tools = await search_tools("github")
    pr = await github.get_pull_request(owner="facebook", repo="react", number=12345)
    return {"title": pr["title"]}
''')
```

- Requires `code_mode=True` in MCPClient constructor
- Code has access to all discovered MCP tools as async functions
- Results returned as Python objects
- Raises `RuntimeError` if `code_mode=False`
