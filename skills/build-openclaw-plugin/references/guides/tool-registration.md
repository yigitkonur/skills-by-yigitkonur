# Tool Registration

Tools are typed function definitions that OpenClaw sends to the model API. When the model decides to call a tool, OpenClaw routes the call to the plugin's handler function.

## What a tool is

A tool consists of:

1. **Name** — unique identifier the model uses to call it (snake_case)
2. **Description** — prompt engineering text that tells the model when and how to use the tool
3. **Parameters** — JSON Schema defining the input the model must provide
4. **Group** — optional logical grouping for bulk access control
5. **Handler** — the function that executes when the tool is called

## Defining tools in the manifest

Tools can be declared statically in `openclaw.plugin.json`:

```json
{
  "tools": [
    {
      "name": "search_documents",
      "description": "Search the document index by keyword or semantic query. Use when the user asks to find documents, look up information, or search for content. Returns a list of matching documents with titles, snippets, and relevance scores.",
      "group": "group:memory",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The search query — can be keywords or a natural language question"
          },
          "limit": {
            "type": "number",
            "description": "Maximum results to return (default: 10, max: 50)"
          },
          "filter": {
            "type": "string",
            "enum": ["all", "recent", "starred"],
            "description": "Filter scope: 'all' searches everything, 'recent' limits to last 7 days, 'starred' only starred docs"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

## Defining tools in code

Tools can also be registered programmatically in the plugin entry point:

Verify the real SDK import path in the target runtime before copying the example below. The package name shown here is illustrative; some OpenClaw deployments ship the plugin base classes from a monorepo package or private runtime path instead of a public npm package.

```typescript
// src/index.ts
import { Plugin, ToolDefinition } from '@openclaw/sdk';

const searchTool: ToolDefinition = {
  name: 'search_documents',
  description: 'Search the document index by keyword or semantic query...',
  group: 'group:memory',
  parameters: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'The search query' },
      limit: { type: 'number', description: 'Max results (default: 10)' },
    },
    required: ['query'],
  },
  handler: async (params: { query: string; limit?: number }) => {
    const results = await performSearch(params.query, params.limit ?? 10);
    return {
      content: [
        {
          type: 'text',
          text: formatSearchResults(results),
        },
      ],
    };
  },
};

export default class MyPlugin extends Plugin {
  tools = [searchTool];
}
```

## Tool naming conventions

| Rule | Example | Why |
|---|---|---|
| Use snake_case | `search_documents` | Consistent with OpenClaw core tools |
| Start with a verb | `get_user`, `create_ticket` | Tells the model what action occurs |
| Be specific | `search_jira_tickets` not `search` | Avoids ambiguity when multiple plugins provide tools |
| No plugin prefix needed | `search_documents` not `myplugin_search_documents` | OpenClaw handles namespacing |

## Writing effective descriptions

Tool descriptions are **prompt engineering**. The model reads them to decide which tool to call and how to fill parameters.

**Good description anatomy:**

```
[What the tool does]. [When to use it]. [What it returns].
[Important constraints or behavior notes].
```

**Example:**

```
Search the document index by keyword or semantic query.
Use when the user asks to find documents, look up information, or search for content.
Returns a list of matching documents with titles, snippets, and relevance scores.
Results are ordered by relevance. Empty queries return recent documents.
```

**Avoid:**

- Single-word descriptions ("Searches")
- Implementation details ("Calls the Elasticsearch API")
- Ambiguous scope ("Does search stuff")

## Parameter schema best practices

1. **Keep schemas flat** — avoid nesting deeper than one level
2. **Limit to 6 parameters or fewer** — models generate better output with fewer params
3. **Mark only truly required fields as required** — let the model skip optional params
4. **Write parameter descriptions** — every property needs a description
5. **Use enums for constrained choices** — gives the model a finite set of valid values
6. **Provide defaults in descriptions** — e.g., "Maximum results (default: 10)"

## Schema guidance vs runtime validation

The schema helps the model form valid tool calls, but it is not a security boundary.

- Treat `parameters` as guidance for tool selection and argument shape
- Re-validate and authorize inside the handler before side effects
- Return an actionable `isError: true` response when input is invalid instead of crashing

## Tool response format

Tool handlers return a response object with a `content` array:

```typescript
// Text response
return {
  content: [{ type: 'text', text: 'Result text here' }],
};

// Error response (model can reason about it)
return {
  content: [{ type: 'text', text: 'Error: API rate limit exceeded. Try again in 30 seconds.' }],
  isError: true,
};

// Mixed content
return {
  content: [
    { type: 'text', text: 'Found 3 results:' },
    { type: 'text', text: JSON.stringify(results, null, 2) },
  ],
};
```

**Rules for responses:**

- Use `isError: true` for business logic failures (not protocol errors)
- Include actionable information in error messages so the model can recover
- Summarize large results instead of dumping raw data
- Keep response text under the context budget — truncate with a note if needed

## Assigning tool groups

Every tool should belong to a group for access control:

```json
{
  "name": "my_tool",
  "group": "group:web"
}
```

Available groups: `group:fs`, `group:runtime`, `group:web`, `group:ui`, `group:memory`, `group:sessions`, `group:messaging`, `group:nodes`, `group:automation`, `group:agents`, `group:media`.

If no built-in group fits, you can define custom groups. Custom groups are not included in any predefined profile, so they must be explicitly allowed.

## Checklist

Before shipping a tool:

- [ ] Name is snake_case and starts with a verb
- [ ] Description explains what, when, and what-it-returns
- [ ] Parameters schema is flat (max 1 level nesting), 6 or fewer params
- [ ] Every parameter has a description
- [ ] Required array only lists truly required params
- [ ] Handler returns `{ content: [...] }` format
- [ ] Error responses use `isError: true` with actionable messages
- [ ] Tool is assigned to an appropriate group
- [ ] Tool works correctly when called with only required params
- [ ] Tool handles invalid input gracefully (returns error, does not crash)
- [ ] Local build resolves the actual OpenClaw SDK imports used by this runtime
