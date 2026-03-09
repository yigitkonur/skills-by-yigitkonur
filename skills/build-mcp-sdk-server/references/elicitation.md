# Elicitation Reference

Elicitation lets servers request structured input from users at runtime. Two modes: **form** (in-band data collection) and **URL** (external secure flows).

## Form Mode — Non-Sensitive Data

Collect user preferences, search parameters, or configuration via a JSON Schema form:

```typescript
import { z } from 'zod/v4';

server.registerTool(
  'configure-search',
  {
    description: 'Configure search preferences before running',
    inputSchema: z.object({}),
  },
  async (_args, ctx) => {
    const result = await ctx.mcpReq.elicitInput({
      mode: 'form',
      message: 'Configure your search:',
      requestedSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', minLength: 1, title: 'Search Terms' },
          category: {
            type: 'string',
            enum: ['docs', 'code', 'issues'],
            default: 'docs',
            title: 'Category',
          },
          maxResults: {
            type: 'integer',
            minimum: 1,
            maximum: 50,
            default: 10,
            title: 'Max Results',
          },
        },
        required: ['query'],
      },
    });

    // Always handle all three actions
    if (result.action === 'accept') {
      return {
        content: [{ type: 'text', text: `Searching: ${JSON.stringify(result.content)}` }],
      };
    } else if (result.action === 'decline') {
      return { content: [{ type: 'text', text: 'Search cancelled by user.' }] };
    } else {
      // cancel
      return { content: [{ type: 'text', text: 'Search dismissed.' }] };
    }
  }
);
```

## URL Mode — Sensitive Data

For API keys, OAuth, payments, or any data that must not enter the LLM context:

```typescript
import { randomUUID } from 'node:crypto';

server.registerTool(
  'connect-service',
  {
    description: 'Authorize access to an external service',
    inputSchema: z.object({}),
  },
  async (_args, ctx) => {
    const elicitationId = randomUUID();

    const result = await ctx.mcpReq.elicitInput({
      mode: 'url',
      message: 'Please authorize access to your account.',
      elicitation_id: elicitationId,
      url: `https://myserver.example.com/connect?eid=${elicitationId}`,
    });

    if (result.action === 'accept') {
      // User consented to open URL — interaction happens out-of-band
      return { content: [{ type: 'text', text: 'Authorization started. Waiting for completion...' }] };
    } else if (result.action === 'decline') {
      return { content: [{ type: 'text', text: 'Authorization declined.' }] };
    } else {
      return { content: [{ type: 'text', text: 'Authorization dismissed.' }] };
    }
  }
);
```

## Schema Constraints

Form mode schemas must be **flat objects with primitive properties only**:

| Allowed | Not Allowed |
|---------|-------------|
| `string` | Nested `object` |
| `number` | `$ref` |
| `integer` | `array` |
| `boolean` | Complex types |
| `enum` | |

## Response Actions

| Action | Meaning | Handling |
|--------|---------|---------|
| `accept` | User provided data / consented to URL | Process `result.content` (form) or wait for URL completion |
| `decline` | User explicitly refused | Graceful fallback |
| `cancel` | User dismissed without deciding | Graceful fallback |

## Security Rules

1. **Never collect secrets via form mode** — passwords, API keys, tokens must use URL mode
2. Clients must show the full URL and get explicit consent before opening
3. Servers must verify the user who completes a URL flow matches the initiator
4. Check client capabilities before sending — clients may support only `form`, only `url`, or both

## Checking Client Capabilities

```typescript
// Client declares capabilities during construction
const client = new Client(
  { name: 'my-client', version: '1.0.0' },
  { capabilities: { elicitation: { form: {}, url: {} } } }
);
```

Server-side: check capabilities before requesting elicitation to avoid errors on clients that don't support it.
