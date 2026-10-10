# WebMCP: In-Browser Tool Discovery & Invocation

WebMCP is a W3C-standardized browser specification (developed under the Web Machine Learning Community Group) that allows websites and web applications to expose first-class tools and action models directly to AI agents.

Kernel browsers enable native WebMCP flags (`WebMCPTesting`, `DevToolsWebMCPSupport`) by default. As of `@onkernel/sdk@0.123.0` and `@onkernel/cli@0.47.0`, Kernel provides first-class discovery and invocation primitives for both native and polyfilled page tools.

---

## 1. How WebMCP Works in Kernel

When an agent navigates to a WebMCP-enabled web application:
1. The web page registers available tools either via the native browser `WebMCP` domain or via the `navigator.modelContext` polyfill.
2. Kernel's supervisor process intercepts the registrations via CDP and aggregates them into a structured tool manifest.
3. Your agent discovers available tools, inspects their JSON schemas, and invokes them through Kernel's SDK, CLI, or in-VM REPL without needing to write custom DOM scraping or brittle button click scripts.

### The Ephemeral Nature of `tool_ref`
Each discovered tool contains an opaque reference (`tool_ref`) bound to a specific document and window lifecycle. **`tool_ref` expires upon page navigation or full document replacement**. Agents must discover tools fresh after each page transition.

---

## 2. Discovery & Invocation API (`kernel.browsers.webmcp`)

### Discovering Page Tools
```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

// List all tools exposed by the active page
const { tools } = await kernel.browsers.webmcp.listTools(sessionId);

for (const tool of tools) {
  console.log(`Tool: ${tool.tool.name} — ${tool.tool.description}`);
  console.log('Schema:', JSON.stringify(tool.tool.inputSchema, null, 2));
}
```

### Invoking a Discovered Tool
```ts
// Discover and invoke tool by its opaque tool_ref
const tool = tools.find(t => t.tool.name === 'addToCart');
if (tool) {
  const response = await kernel.browsers.webmcp.invokeTool(sessionId, {
    tool_ref: tool.tool_ref,
    input: {
      sku: 'PROD-9871',
      quantity: 2,
    },
    timeout_sec: 10,
  });

  if (response.status === 'completed') {
    console.log('Cart updated:', response.output);
  } else if (response.status === 'awaiting_submission') {
    console.log('Form populated, awaiting submission confirmation');
  } else {
    console.error(`WebMCP invocation ${response.status}:`, response.error_text);
  }
}
```

### Invocation Result Schema
In `@onkernel/sdk`, `invokeTool` returns `InvocationResult`:
```ts
export interface InvocationResult {
  invocation_id: string;
  /**
   * awaiting_submission means a non-autosubmit declarative form was populated but
   * not submitted. Other statuses ('completed', 'canceled', 'error') are terminal results.
   */
  status: 'completed' | 'canceled' | 'error' | 'awaiting_submission';
  error_text?: string;
  /** Untrusted page-provided output. */
  output?: unknown;
}
```

---

## 3. Polyfill Support (`navigator.modelContext`)

As of October 2, 2026, Kernel browsers automatically recognize tools registered through the client-side `navigator.modelContext` polyfill:

```javascript
// Example: In-page polyfill executed by a web application or userscript
if ('modelContext' in navigator) {
  navigator.modelContext.registerTool({
    name: 'searchInventory',
    description: 'Search in-stock warehouse products',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string' }
      },
      required: ['query']
    },
    handler: async ({ query }) => {
      const data = await window.internalApp.search(query);
      return data;
    }
  });
}
```

Kernel detects this registration in the microVM and maps it directly to `kernel.browsers.webmcp.listTools()` with `source.registration_type: 'polyfill'`.

---

## 4. Hybrid WebMCP + REPL Automation Pattern

Best-practice agents attempt WebMCP tools first (which are deterministic and structured), falling back to DOM interaction or the Browser REPL when a website does not expose native tools:

```ts
// Inside an agent loop
const { tools } = await kernel.browsers.webmcp.listTools(sessionId);
const checkoutTool = tools.find(t => t.tool.name === 'initiateCheckout');

if (checkoutTool) {
  // Fast, deterministic path
  await kernel.browsers.webmcp.invokeTool(sessionId, {
    tool_ref: checkoutTool.tool_ref,
    input: { payment_method: 'saved_card' },
    timeout_sec: 15,
  });
} else {
  // Fallback to DOM interaction via REPL or Playwright
  await kernel.browsers.repl(sessionId, {
    code: `
      await click('button#checkout-button');
      await waitForElement('.payment-summary');
      repl.write('Checked out via DOM fallback');
    `,
  });
}
```

---

## 5. CLI Reference (`@onkernel/cli@0.47.0`)

```bash
# Discover WebMCP tools exposed by the active page
kernel browsers webmcp list <session-id>

# Filter out custom user-injected tools to see only site-native tools
kernel browsers webmcp list <session-id> --exclude-custom

# Invoke a WebMCP tool with JSON parameters
kernel browsers webmcp invoke <session-id> \
  --tool-ref <tool_ref> \
  --input '{"sku": "ABC-123", "quantity": 1}'
```
