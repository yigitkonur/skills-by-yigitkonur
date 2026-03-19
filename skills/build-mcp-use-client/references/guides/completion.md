# Completion

Request autocomplete suggestions for prompt and resource template arguments.

---

## Overview

Completions enable autocomplete suggestions for prompt arguments and resource template URIs. Servers can provide static lists or dynamic callbacks that suggest values based on partial user input, making it easier to discover valid argument values and improving the user experience.

The completion feature allows clients to request suggestions for:

- **Prompt arguments** — Arguments marked with `completable()` in the server's prompt schema
- **Resource template URI variables** — Variables in resource template URIs with completion support

Completions are requested via the `complete()` method, which sends a `completion/complete` request to the server and returns a list of suggested values.

### Method Signature

```typescript
complete(params: CompleteRequestParams): Promise<CompleteResult>
```

---

## Basic Usage with MCPClient

Request completions for a prompt argument:

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    completion: {
      url: 'http://localhost:3000/mcp',
      clientInfo: { name: 'completion-client', version: '1.0.0' },
    }
  }
})
await client.createAllSessions()

const session = client.getSession('completion')
const result = await session.complete({
  ref: { type: 'ref/prompt', name: 'code-review' },
  argument: { name: 'language', value: 'py' }
})

console.log('Suggestions:', result.completion.values)
// Output: ['python', 'pytorch', ...]

await client.closeAllSessions()
```

---

## Using with useMcp Hook

The `useMcp` hook exposes a `complete()` method for requesting completions in React applications:

```tsx
import { useMcp } from 'mcp-use/react'

function AutocompleteExample() {
  const mcp = useMcp({ url: 'http://localhost:3000/sse' })

  const handleInputChange = async (value: string) => {
    if (mcp.state === 'ready' && value.length > 0) {
      const result = await mcp.complete({
        ref: { type: 'ref/prompt', name: 'code-review' },
        argument: { name: 'language', value }
      })

      setSuggestions(result.completion.values)
    }
  }

  return (
    <input
      onChange={(e) => handleInputChange(e.target.value)}
      list="suggestions"
    />
  )
}
```

---

## Using with McpClientProvider

When using `McpClientProvider` with multiple servers, get completions via `useMcpServer`:

```tsx
import { useState } from 'react'
import { McpClientProvider, useMcpServer } from 'mcp-use/react'

function AutocompleteWithProvider() {
  const server = useMcpServer('my-server-id')
  const [suggestions, setSuggestions] = useState<string[]>([])

  const handleInputChange = async (value: string) => {
    if (server?.state === 'ready' && value.length > 0) {
      const result = await server.complete({
        ref: { type: 'ref/prompt', name: 'code-review' },
        argument: { name: 'language', value }
      })
      setSuggestions(result.completion.values)
    }
  }

  return (
    <input onChange={(e) => handleInputChange(e.target.value)} />
  )
}

function App() {
  return (
    <McpClientProvider
      mcpServers={{
        'my-server-id': { url: 'http://localhost:3000/sse' }
      }}
    >
      <AutocompleteWithProvider />
    </McpClientProvider>
  )
}
```

---

## Completion Request Parameters

The `complete()` method accepts a `CompleteRequestParams` object:

```typescript
type CompleteRequestParams = {
  // Reference to the prompt or resource template
  ref:
    | { type: 'ref/prompt'; name: string }
    | { type: 'ref/resource'; uri: string }

  // Argument to complete with current value
  argument: {
    name: string
    value: string
  }
}
```

| Field | Type | Description |
|---|---|---|
| `ref` | `object` | Reference to the prompt or resource template |
| `ref.type` | `"ref/prompt" \| "ref/resource"` | Whether completing a prompt arg or resource URI variable |
| `ref.name` | `string` | Prompt name (when `type` is `"ref/prompt"`) |
| `ref.uri` | `string` | Resource template URI (when `type` is `"ref/resource"`) |
| `argument.name` | `string` | The argument/variable name to complete |
| `argument.value` | `string` | The current partial value typed by the user |

### Completing Prompt Arguments

For prompt arguments, use `ref/prompt` and specify the prompt name:

```typescript
const result = await session.complete({
  ref: { type: 'ref/prompt', name: 'file-search' },
  argument: { name: 'extension', value: '.t' }
})

console.log(result.completion.values)
// Output: ['.ts', '.tsx', '.txt', ...]
```

### Completing Resource Template URIs

For resource template URI variables, use `ref/resource` with the template URI:

```typescript
const result = await session.complete({
  ref: { type: 'ref/resource', uri: 'file:///{path}' },
  argument: { name: 'path', value: '/home/user' }
})

console.log(result.completion.values)
// Output: ['/home/user/documents', '/home/user/downloads', ...]
```

---

## Completion Response

The completion result contains:

```typescript
type CompleteResult = {
  completion: {
    // Array of suggested values (max 100 per MCP spec)
    values: string[]

    // Total number of available completions
    total?: number

    // Whether more completions exist beyond the returned values
    hasMore?: boolean
  }
}
```

| Field | Type | Description |
|---|---|---|
| `completion.values` | `string[]` | Array of suggestions (max 100 per MCP spec) |
| `completion.total` | `number?` | Total matches available on the server |
| `completion.hasMore` | `boolean?` | `true` if more results exist beyond the returned batch |

---

## Contextual Completions

Some completions may depend on other argument values. Pass additional context in the request:

```typescript
// Complete 'city' — server may filter suggestions based on other already-selected arguments
// Pass only the target argument; server-side logic handles context from previously set values
const result = await session.complete({
  ref: { type: 'ref/prompt', name: 'weather' },
  argument: { name: 'city', value: 'San' }
})
```

---

## Autocomplete UI Example

A complete example of building an autocomplete dropdown:

```tsx
import { useMcp } from 'mcp-use/react'
import { useState, useCallback } from 'react'
import { debounce } from 'lodash'

function SmartAutocomplete({ promptName, argumentName }) {
  const mcp = useMcp({ url: process.env.MCP_SERVER_URL })
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const fetchCompletions = useCallback(
    debounce(async (value: string) => {
      if (mcp.state !== 'ready' || !value) {
        setSuggestions([])
        return
      }

      setLoading(true)
      try {
        const result = await mcp.complete({
          ref: { type: 'ref/prompt', name: promptName },
          argument: { name: argumentName, value }
        })
        setSuggestions(result.completion.values)
      } catch (error) {
        console.error('Completion failed:', error)
        setSuggestions([])
      } finally {
        setLoading(false)
      }
    }, 300), // Debounce requests by 300ms
    [mcp, promptName, argumentName]
  )

  return (
    <div>
      <input
        onChange={(e) => fetchCompletions(e.target.value)}
        placeholder="Start typing..."
      />
      {loading && <span>Loading...</span>}
      {suggestions.length > 0 && (
        <ul>
          {suggestions.map(suggestion => (
            <li key={suggestion}>{suggestion}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

---

## Server Implementation

Servers define completions using the `completable()` helper.

**Static list:**

```typescript
import { MCPServer, completable } from 'mcp-use/server'
import { z } from 'zod'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

server.prompt({
  name: 'code-review',
  schema: z.object({
    // Static list of completions
    language: completable(z.string(), [
      'python',
      'typescript',
      'javascript',
      'java',
      'go',
      'rust'
    ])
  })
}, async ({ language }) => ({
  messages: [
    { role: 'user', content: { type: 'text', text: `Review ${language} code` }}
  ]
}))
```

---

## Best Practices

### Debounce Requests

Always debounce completion requests to avoid overwhelming the server:

```typescript
import { debounce } from 'lodash'

const fetchCompletions = debounce(async (value) => {
  const result = await mcp.complete({
    ref: { type: 'ref/prompt', name: 'my-prompt' },
    argument: { name: 'arg', value }
  })
  setSuggestions(result.completion.values)
}, 300) // Wait 300ms after user stops typing
```

### Handle Errors Gracefully

Completion requests may fail if the server doesn't support completions for a specific argument:

```typescript
try {
  const result = await session.complete(params)
  setSuggestions(result.completion.values)
} catch (error) {
  // Server may not support completions for this argument
  // Gracefully degrade to no autocomplete
  console.warn('Completions not available:', error)
  setSuggestions([])
}
```

### Check Server Capabilities

Before requesting completions, verify the server supports the feature:

```typescript
const session = client.getSession('my-server')
const capabilities = session.connector.serverCapabilities

if (capabilities?.completions) {
  // Server supports completions
  const result = await session.complete(params)
}
```

### Limit UI Suggestions

The MCP spec enforces a maximum of 100 values per response, but you may want to show fewer in the UI:

```typescript
const result = await session.complete(params)
const topSuggestions = result.completion.values.slice(0, 10)
setSuggestions(topSuggestions)
```

---

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `Client not ready` | Calling `complete()` before connection is established | Wait for `state === "ready"` before calling |
| `Method not found (-32601)` | Server doesn't support completions | Check `serverCapabilities?.completions` first |
| `Invalid argument` | Argument name not defined in the prompt/resource schema | Verify the argument name matches the server schema |
| `Not completable` | Argument exists but doesn't have `completable()` | Only request completions for completable arguments |

---

## Run the Example

A full Node.js example is available in the mcp-use repository:

```bash
# From packages/mcp-use — starts server then client automatically:
pnpm run example:completion

# Or manually:
# 1. Start the completion server:
pnpm run example:server:completion

# 2. Run the client:
tsx examples/client/node/communication/completion-client.ts
```

This demonstrates prompt argument completions and resource template URI variable completions. See `examples/client/node/communication/completion-client.ts`.
