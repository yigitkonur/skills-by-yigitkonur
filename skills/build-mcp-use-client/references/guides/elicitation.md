# Elicitation

Complete reference for client-side elicitation — handling server requests for user input via form and URL modes.

---

## What Is Elicitation

Elicitation is a callback mechanism where an MCP server pauses tool execution to request input from the user through the client. Two modes:

- **Form mode** — Collect structured data (name, email, preferences) via a JSON Schema form
- **URL mode** — Direct the user to an external URL (OAuth, payment, third-party authorization)

The client renders the appropriate UI, collects the response, and returns it to the server.

---

## Type Definitions

### ElicitRequestFormParams

```typescript
import type { ElicitRequestFormParams } from "@modelcontextprotocol/sdk/types.js";

interface ElicitRequestFormParams {
  mode?: "form";                          // Optional — form is the default
  message: string;                        // Human-readable prompt
  requestedSchema: Record<string, any>;   // JSON Schema defining expected response
}
```

| Field | Type | Description |
|---|---|---|
| `mode` | `"form"` (optional) | Specifies form mode (default when omitted) |
| `message` | `string` | Human-readable prompt displayed to the user |
| `requestedSchema` | `Record<string, any>` | JSON Schema defining the expected fields and types |

### ElicitRequestURLParams

```typescript
import type { ElicitRequestURLParams } from "@modelcontextprotocol/sdk/types.js";

interface ElicitRequestURLParams {
  mode: "url";                // Required — distinguishes from form mode
  message: string;            // Human-readable explanation
  url: string;                // The URL to direct the user to
  elicitationId: string;      // Unique identifier for tracking
}
```

| Field | Type | Description |
|---|---|---|
| `mode` | `"url"` | Required, must be `"url"` |
| `message` | `string` | Human-readable explanation of why the URL is needed |
| `url` | `string` | The URL to direct the user to |
| `elicitationId` | `string` | Unique identifier for tracking this elicitation |

### ElicitResult

```typescript
interface ElicitResult {
  action: "accept" | "decline" | "cancel";
  content?: ElicitContent;    // Only for "accept" action in form mode
}
```

| Action | Meaning | `content` |
|---|---|---|
| `"accept"` | User submitted valid input | Present (form mode) or absent (URL mode) |
| `"decline"` | User explicitly refused | `undefined` |
| `"cancel"` | User dismissed the prompt | `undefined` |

### ElicitContent

```typescript
type ElicitContent = Record<string, string | number | boolean | string[]>;
```

Values must be primitives or arrays of strings — no nested objects.

---

## Client Helpers

All helpers are exported from `mcp-use` (or `mcp-use/client`). For a typed callback without importing the SDK directly, use `OnElicitationCallback` from `mcp-use`.

```typescript
import {
  accept,
  decline,
  cancel,
  reject,             // alias for decline
  validate,
  getDefaults,
  applyDefaults,
  acceptWithDefaults,
} from "mcp-use";
```

### Defaults

| Helper | Signature | Description |
|---|---|---|
| `getDefaults(params)` | `(params: ElicitParams) => ElicitContent` | Extract default values from the request schema |
| `applyDefaults(params, partial?)` | `(params: ElicitParams, partial?: ElicitContent) => ElicitContent` | Merge partial content with schema defaults |
| `acceptWithDefaults(params)` | `(params: ElicitParams) => ElicitResult` | Return an accept result built from schema defaults |

### Result Builders

| Helper | Signature | Description |
|---|---|---|
| `accept(content)` | `(content: ElicitContent) => ElicitResult` | Accept with the given content |
| `decline(reason?)` | `(reason?: string) => ElicitResult` | Decline the elicitation |
| `cancel()` | `() => ElicitResult` | Cancel the elicitation |
| `reject(reason?)` | `(reason?: string) => ElicitResult` | Alias for `decline` |

### Validation

```typescript
import { validate } from "mcp-use";

type ElicitValidationResult = {
  valid: boolean;
  errors?: string[];
};

const result: ElicitValidationResult = validate(params, formData);
```

Validation is Zod-based and uses `params.requestedSchema`. Client-side validation is optional but recommended for better UX — the server always validates as the final authority.

---

## Setting the Global Elicitation Callback

Pass `onElicitation` as the second argument to `MCPClient`:

```typescript
import { MCPClient, type OnElicitationCallback } from "mcp-use";
import type {
  ElicitRequestFormParams,
  ElicitRequestURLParams,
  ElicitResult,
} from "@modelcontextprotocol/sdk/types.js";

async function onElicitation(
  params: ElicitRequestFormParams | ElicitRequestURLParams
): Promise<ElicitResult> {
  if (params.mode === "url") {
    console.log(`Please visit: ${params.url}`);
    console.log(`Reason: ${params.message}`);
    const userConsent = await promptUser("Did you complete the authorization?");
    return { action: userConsent ? "accept" : "decline" };
  }

  // Form mode — collect structured data
  const schema = params.requestedSchema;
  const userData: Record<string, any> = {};
  if (schema.type === "object" && schema.properties) {
    for (const [fieldName, fieldSchema] of Object.entries(schema.properties)) {
      const value = await promptUser(
        `Enter ${fieldSchema.title || fieldName}:`,
        fieldSchema.default
      );
      userData[fieldName] = value;
    }
  }
  return { action: "accept", content: userData };
}

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  { onElicitation }
);
```

---

## Per-Server Elicitation Callbacks

Override the global callback for individual servers:

```typescript
import {
  acceptWithDefaults,
  MCPClient,
  type OnElicitationCallback,
} from "mcp-use";

const terminalElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    console.log(`Visit: ${params.url}`);
    return { action: "accept" };
  }
  const input = await promptTerminal(params.message, params.requestedSchema);
  return { action: "accept", content: input };
};

const webElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    window.open(params.url, "_blank");
    return { action: "accept" };
  }
  const formData = await showWebForm(params.message, params.requestedSchema);
  return formData ? { action: "accept", content: formData } : { action: "cancel" };
};

const client = new MCPClient(
  {
    mcpServers: {
      cliTool: { url: "https://cli.example.com/mcp", onElicitation: terminalElicitation },
      webService: { url: "https://web.example.com/mcp", onElicitation: webElicitation },
      internalService: { url: "https://internal.example.com/mcp" }, // uses global
    },
  },
  { onElicitation: async (params) => acceptWithDefaults(params) }
);
```

---

## Callback Precedence

| Priority | Source |
|---|---|
| 1 (highest) | Per-server `onElicitation` |
| 2 | Per-server `elicitationCallback` (deprecated — use `onElicitation`) |
| 3 | Global `onElicitation` (second MCPClient arg) |
| 4 (lowest) | Global `elicitationCallback` (deprecated — use `onElicitation`) |

---

## React Hook Elicitation

### useMcp with onElicitation

```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const { tools, callTool, state } = useMcp({
    url: "http://localhost:3000/mcp",
    onElicitation: async (params) => {
      if (params.mode === "url") {
        const confirmed = window.confirm(`${params.message}\n\nOpen ${params.url}?`);
        if (confirmed) {
          window.open(params.url, "_blank");
          const completed = window.confirm("Did you complete the action?");
          return { action: completed ? "accept" : "decline" };
        }
        return { action: "decline" };
      }
      // Form mode
      const formData = await showElicitationForm(params.message, params.requestedSchema);
      return {
        action: formData ? "accept" : "cancel",
        content: formData ?? undefined,
      };
    },
  });

  if (state !== "ready") return <div>Connecting...</div>;
  return <div>{tools.length} tools available</div>;
}
```

### McpClientProvider

`McpClientProvider` is a React context provider that supplies a configured `MCPClient` to descendant components. Import it from `mcp-use/react`. The global `onElicitation` callback is set on the underlying `MCPClient` instance passed to the provider. Consult per-component overrides via `useMcp`'s `onElicitation` option for per-hook control.

---

## Form-Mode Minimal Example

Accept using schema defaults — no user interaction needed:

```typescript
import { acceptWithDefaults, MCPClient, type OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  return acceptWithDefaults(params);
};

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  { onElicitation }
);
```

---

## URL-Mode Example

```typescript
import { MCPClient, acceptWithDefaults, type OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    console.log(`\nServer requests you visit:`);
    console.log(`   URL: ${params.url}`);
    console.log(`   Reason: ${params.message}`);
    console.log(`   Tracking ID: ${params.elicitationId}\n`);

    // In a browser context:
    // window.open(params.url, "_blank", "noopener,noreferrer");

    // In a terminal context, wait for user confirmation:
    const confirmed = await readline.question("Press Enter when done (or 'n' to decline): ");
    return { action: confirmed.toLowerCase() === "n" ? "decline" : "accept" };
  }

  // Form mode fallback — accept using schema defaults
  return acceptWithDefaults(params);
};
```

---

## Validation Example

Use `validate()` to check user input before accepting:

```typescript
import { accept, cancel, validate, type OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    return { action: "accept" };
  }

  // Collect form data from user
  const formData = await collectFormFromUser(params);

  // Validate against the schema
  const { valid, errors } = validate(params, formData);
  if (!valid) {
    await showErrors(errors ?? []);
    return cancel();
  }

  return accept(formData);
};
```

❌ **BAD** — Accepting without validation:

```typescript
const onElicitation: OnElicitationCallback = async (params) => {
  const raw = await collectFormFromUser(params);
  return { action: "accept", content: raw }; // May contain invalid data
};
```

✅ **GOOD** — Validate before accepting:

```typescript
import { accept, decline, validate, type OnElicitationCallback, MCPClient } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  const formData = await collectFormFromUser(params);
  const { valid, errors } = validate(params, formData);
  if (!valid) {
    await showErrors(errors);
    return decline(errors?.join("; "));
  }
  return accept(formData);
};

const client = new MCPClient(config, { onElicitation });
```

---

## SEP-1330 Enum Schema Variants

Servers may use different JSON Schema patterns for enum/select fields. Handle all variants:

| Variant | Schema Shape | Recommended UI |
|---|---|---|
| Untitled single-select | `type: "string"` + `enum` | Single-select dropdown |
| Titled single-select | `type: "string"` + `oneOf[{ const, title }]` | Dropdown with labels |
| Legacy titled enum | `type: "string"` + `enum` + `enumNames` | Dropdown using enumNames |
| Untitled multi-select | `type: "array"` + `items.enum` | Multi-select checkbox |
| Titled multi-select | `type: "array"` + `items.anyOf[{ const, title }]` | Checkbox with labels |

### getChoices() Helper

Parse any enum variant into a uniform `{ value, label }` array:

```typescript
function getChoices(field: Record<string, any>): Array<{ value: string; label: string }> {
  if (Array.isArray(field.oneOf)) {
    return field.oneOf
      .filter((x: any) => typeof x?.const === "string")
      .map((x: any) => ({ value: x.const, label: x.title ?? x.const }));
  }

  if (Array.isArray(field.enum)) {
    return field.enum.map((value: string, i: number) => ({
      value,
      label: field.enumNames?.[i] ?? value,
    }));
  }

  return [];
}
```

For multi-select fields (`type: "array"`), iterate `field.items.anyOf` or `field.items.enum` similarly to extract choices. When returning accepted values, single-select fields return a `string` and multi-select fields return `string[]`. Always use `const`/`enum` values as the submitted data, even when displaying a different label.

### Using getChoices in a Callback

```typescript
const onElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") return { action: "decline" };

  const schema = params.requestedSchema;
  const content: Record<string, any> = {};

  if (schema.type === "object" && schema.properties) {
    for (const [key, field] of Object.entries(schema.properties as Record<string, any>)) {
      const choices = getChoices(field);
      if (choices.length > 0) {
        // Render dropdown or checkbox list
        console.log(`${field.title ?? key}:`);
        choices.forEach((c, i) => console.log(`  ${i + 1}. ${c.label}`));
        const idx = parseInt(await readline.question("Select: ")) - 1;
        content[key] = choices[idx]?.value ?? choices[0].value;
      } else if (field.type === "boolean") {
        content[key] = (await readline.question(`${field.title ?? key} (y/n): `)) === "y";
      } else if (field.type === "number") {
        content[key] = Number(await readline.question(`${field.title ?? key}: `));
      } else {
        content[key] = await readline.question(`${field.title ?? key}: `);
      }
    }
  }

  return accept(content);
};
```

---

## Complete Example — Full Elicitation Handler

```typescript
import {
  MCPClient,
  accept,
  decline,
  cancel,
  validate,
  type OnElicitationCallback,
  type ElicitContent,
  type ElicitValidationResult,
} from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  // Handle URL mode
  if (params.mode === "url") {
    console.log(`\n🔗 Authorization required: ${params.message}`);
    console.log(`   Visit: ${params.url}`);
    const ok = await promptYesNo("Did you complete the authorization?");
    return ok ? { action: "accept" } : decline("User did not complete authorization");
  }

  // Form mode
  console.log(`\n📝 ${params.message}`);

  // Collect user input
  const userInput = await collectFormFromUser(params);
  if (!userInput) return cancel();

  // Validate before accepting
  const { valid, errors }: ElicitValidationResult = validate(params, userInput);
  if (!valid) {
    console.error("Invalid input:", errors);
    return decline(errors?.join("; "));
  }

  return accept(userInput);
};

const client = new MCPClient(
  {
    mcpServers: {
      myServer: { url: "http://localhost:3000/mcp" },
    },
  },
  { onElicitation }
);
```

---

## Error Handling

If no `onElicitation` (or deprecated `elicitationCallback`) is registered, any tool that triggers an elicitation request will cause the client call to reject with a runtime error:

```typescript
// Error thrown when no handler is configured
throw new Error("Elicitation not supported: client does not have an onElicitation handler");
```

This error propagates to the caller (e.g., `session.callTool`) and must be caught to avoid unhandled promise rejections.

```typescript
const onElicitation: OnElicitationCallback = async (params) => {
  try {
    if (params.mode === "url") {
      // URL handling...
      return { action: "accept" };
    }
    const formData = await collectFormFromUser(params);
    return formData ? accept(formData) : cancel();
  } catch (error) {
    console.error("Elicitation failed:", error);
    return decline(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
};
```

❌ **BAD** — Throwing from the callback:

```typescript
const onElicitation: OnElicitationCallback = async (params) => {
  const data = await collectFormFromUser(params);
  if (!data) throw new Error("No data"); // Crashes tool execution
  return accept(data);
};
```

✅ **GOOD** — Return decline/cancel instead of throwing:

```typescript
const onElicitation: OnElicitationCallback = async (params) => {
  try {
    const data = await collectFormFromUser(params);
    if (!data) return cancel();
    return accept(data);
  } catch (error) {
    return decline(`Failed: ${error instanceof Error ? error.message : String(error)}`);
  }
};
```

---

## Available Imports

```typescript
// Core types and helpers — importable from "mcp-use"
import {
  MCPClient,
  type OnElicitationCallback,
  type OnSamplingCallback,
  type OnNotificationCallback,
  type ElicitContent,
  type ElicitValidationResult,
  accept,
  decline,
  cancel,
  reject,             // alias for decline
  validate,
  getDefaults,
  applyDefaults,
  acceptWithDefaults,
} from "mcp-use";

// SDK types (for params and results)
import type {
  ElicitRequestFormParams,
  ElicitRequestURLParams,
  ElicitResult,
} from "@modelcontextprotocol/sdk/types.js";

// React hooks
import { useMcp, McpClientProvider, useMcpServer } from "mcp-use/react";
```
