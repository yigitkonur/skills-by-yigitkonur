# Resources and Prompts

## Resources

### What Are MCP Resources?

Resources are data sources that MCP servers expose to clients. Unlike tools (which perform actions), resources provide data that the LLM can read. Resources use URI-based addressing.

### Resource Types

| Type | Description | URI Example |
|---|---|---|
| Static | Fixed URI, unchanging content | `config://app`, `docs://readme` |
| Template | Parameterized URI, dynamic content | `users://{userId}/profile` |
| Subscription | Clients notified on changes | Any resource with subscriptions enabled |

### Official TS SDK — Static Resource

```typescript
server.registerResource('readme', 'docs://readme', {
    title: 'README Documentation',
    mimeType: 'text/markdown',
}, async (uri) => ({
    contents: [{
        uri: uri.href,
        text: '# My Server\nDocumentation content here.',
        mimeType: 'text/markdown',
    }]
}));
```

### Official TS SDK — Resource Template

```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
    'user-profile',
    new ResourceTemplate('users://{userId}/profile', {
        list: async () => ({
            resources: users.map(u => ({
                uri: `users://${u.id}/profile`,
                name: u.name,
                description: `Profile for ${u.name}`,
            }))
        })
    }),
    {
        title: 'User Profile',
        mimeType: 'application/json',
    },
    async (uri, { userId }) => ({
        contents: [{
            uri: uri.href,
            text: JSON.stringify(await getUser(userId)),
        }]
    })
);
```

### mcp-use TS — Static Resource

```typescript
import { markdown, text, object } from 'mcp-use/server'

server.resource({
    uri: 'docs://readme',
    name: 'README',
    title: 'README Documentation',
    mimeType: 'text/markdown',
}, async () => markdown('# My Server\nDocumentation content here.'))
```

### mcp-use TS — Resource Template

```typescript
server.resourceTemplate({
    uriTemplate: 'users://{userId}/profile',
    name: 'User Profile',
    mimeType: 'application/json',
}, async (uri, { userId }) => object(await getUser(userId)))
```

### mcp-use Python — Resources

```python
from mcp_use import MCPServer

server = MCPServer(name="my-server")

@server.resource(uri="docs://readme", name="readme", mime_type="text/markdown")
async def readme() -> str:
    return "# My Server\nDocumentation content here."

@server.resource(uri="users://{user_id}/profile", name="user_profile", mime_type="application/json")
async def user_profile(user_id: str) -> str:
    user = await get_user(user_id)
    return json.dumps(user)
```

### Reading Resources (Client Side)

```python
from mcp_use import MCPClient

client = MCPClient(config=config)
await client.create_all_sessions()
session = client.get_session("server-name")

# List available resources
resources = await session.list_resources()
for r in resources:
    print(f"{r.name}: {r.uri}")

# Read a specific resource
result = await session.read_resource("docs://readme")
print(result.contents[0].text)
```

### Resource Subscriptions

Servers can notify clients when resources change:

```typescript
// mcp-use TS server

// Notify specific resource updated (to subscribed clients)
await server.notifyResourceUpdated('users://123/profile')

// Notify all clients that the resource list changed (after adding/removing resources)
await server.sendResourcesListChanged()
```

```python
# mcp-use Python client — subscribe/read flow depends on the client implementation.
# For TypeScript mcp-use clients, the connector exposes subscribe/unsubscribe methods.
```

---

## Prompts

### What Are MCP Prompts?

Prompts are reusable prompt templates that servers expose. They allow servers to provide pre-built, parameterized prompts that clients can use to interact with LLMs more effectively.

### Official TS SDK — Prompt Definition

```typescript
server.registerPrompt('code-review', {
    title: 'Code Review',
    description: 'Generate a code review prompt for the given code',
    argsSchema: z.object({
        language: z.string().describe('Programming language'),
        code: z.string().describe('Code to review'),
        focus: z.enum(['bugs', 'performance', 'style', 'security']).default('bugs'),
    })
}, ({ language, code, focus }) => ({
    messages: [
        {
            role: 'user',
            content: {
                type: 'text',
                text: `Please review the following ${language} code for ${focus} issues:\n\n\`\`\`${language}\n${code}\n\`\`\``
            }
        }
    ]
}));
```

### mcp-use TS — Prompt Definition

```typescript
import { text } from 'mcp-use/server'

server.prompt({
    name: 'code-review',
    description: 'Generate a code review prompt',
    schema: z.object({
        language: z.string().describe('Programming language'),
        code: z.string().describe('Code to review'),
        focus: z.enum(['bugs', 'performance', 'style', 'security']).default('bugs'),
    }),
}, async ({ language, code, focus }) =>
    text(`Please review the following ${language} code for ${focus} issues:\n\n\`\`\`${language}\n${code}\n\`\`\``)
)
```

### mcp-use Python — Prompt Definition

```python
from typing import Annotated
from pydantic import Field

@server.prompt(name="code_review", title="Code Review")
def code_review(
    language: Annotated[str, Field(description="Programming language")],
    code: Annotated[str, Field(description="Code to review")],
    focus: Annotated[str, Field(default="bugs", description="Review focus")],
) -> str:
    return f"Review {language} code for {focus}:\n\n```{language}\n{code}\n```"
```

### Using Prompts (Client Side)

```python
from mcp_use import MCPClient

client = MCPClient(config=config)
await client.create_all_sessions()
session = client.get_session("server-name")

# List available prompts
prompts = await session.list_prompts()
for p in prompts:
    print(f"{p.name}: {p.description}")

# Get a prompt
result = await session.get_prompt("code-review", {
    "language": "python",
    "code": "def add(a, b): return a + b",
    "focus": "bugs"
})
for msg in result.messages:
    print(f"[{msg.role}]: {msg.content.text}")
```

### Prompt Response Format

The `GetPromptResult` contains an array of messages:

```typescript
interface GetPromptResult {
    description?: string;
    messages: PromptMessage[];
}

interface PromptMessage {
    role: 'user' | 'assistant';
    content: TextContent | ImageContent | AudioContent | EmbeddedResource;
}
```

### Multi-Message Prompts

```typescript
server.prompt({
    name: 'few-shot-classify',
    description: 'Classification with examples',
    schema: z.object({ text: z.string() }),
}, async ({ text: input }) => ({
    messages: [
        { role: 'user', content: { type: 'text', text: 'Classify: "Great product!" → positive' } },
        { role: 'assistant', content: { type: 'text', text: 'positive' } },
        { role: 'user', content: { type: 'text', text: 'Classify: "Terrible service" → negative' } },
        { role: 'assistant', content: { type: 'text', text: 'negative' } },
        { role: 'user', content: { type: 'text', text: `Classify: "${input}" →` } },
    ]
}))
```

## Comparison Table

| Aspect | Official TS SDK | mcp-use TS | mcp-use Python |
|---|---|---|---|
| Resource (static) | `registerResource(name, uri, meta, cb)` | `resource(config, cb)` | `@server.resource(uri=..., name=...)` |
| Resource (template) | `new ResourceTemplate(uri, {list})` + `registerResource(...)` | `resourceTemplate(config, cb)` | `@server.resource(uri=".../{param}")` |
| Prompt | `registerPrompt(name, config, cb)` | `prompt(config, cb)` | `@server.prompt(name=..., title=...)` |
| Schema key (prompt) | `argsSchema` | `schema` | Function signature |
| Response format | Manual `{ contents: [...] }` or `{ messages: [...] }` | Response helpers | Return strings |
| Subscriptions | Manual notification | `notifyResourceUpdated()` + `sendResourcesListChanged()` | Via session/client API |
