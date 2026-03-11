# User Input Events

Events for user messages, askUser questions, and elicitation (form-based) input requests.

## Events

### `user.message`

Emitted when the user sends a message to the session.

```typescript
session.on("user.message", (event) => {
  console.log("User said:", event.data.content);
  if (event.data.attachments?.length) {
    console.log("Attachments:", event.data.attachments.length);
  }
});
```

**Data shape:**

```typescript
{
  content: string;                    // User's message text
  transformedContent?: string;        // Model-formatted version with XML wrapping
  attachments?: Array<
    | {
        type: "file";
        path: string;                 // Absolute file/directory path
        displayName: string;
        lineRange?: { start: number; end: number };
      }
    | {
        type: "selection";
        path: string;
        displayName: string;
        content: string;              // Selected text content
        lineRange?: { start: number; end: number };
      }
    | {
        type: "github";
        url: string;
        displayName: string;
        content: string;
      }
    | {
        type: "image";
        data: string;                 // Base64-encoded image
        mediaType: string;            // e.g., "image/png"
        displayName: string;
      }
  >;
}
```

### `user_input.requested`

Broadcast when the agent uses the `ask_user` tool to ask the user a question. In multi-client setups, all clients receive this.

```typescript
session.on("user_input.requested", (event) => {
  const { requestId, question, choices, allowFreeform } = event.data;
  console.log("Agent asks:", question);
  if (choices?.length) {
    choices.forEach((c, i) => console.log(`  ${i + 1}. ${c}`));
  }
});
```

**Data shape:**

```typescript
{
  requestId: string;           // UUID — use to respond
  question: string;            // The question text
  choices?: string[];          // Predefined answer choices
  allowFreeform?: boolean;     // Whether free-form text is allowed
}
```

**Programmatic handling via `onUserInputRequest`:**

The `onUserInputRequest` handler in SessionConfig receives these automatically. Use session events for UI rendering in multi-client setups.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  onUserInputRequest: async (request) => {
    // Auto-select first choice when available
    if (request.choices?.length) {
      return { answer: request.choices[0], wasFreeform: false };
    }
    return { answer: "Proceed with defaults", wasFreeform: true };
  },
});
```

### `user_input.completed`

Emitted when a user input request has been resolved. Use to dismiss UI.

```typescript
session.on("user_input.completed", (event) => {
  dismissInputUI(event.data.requestId);
});
```

**Data shape:**

```typescript
{
  requestId: string;    // Matches the original user_input.requested
}
```

### `elicitation.requested`

Broadcast when the agent needs structured form-based input. This is an ephemeral event (not persisted to disk).

```typescript
session.on("elicitation.requested", (event) => {
  const { requestId, message, requestedSchema } = event.data;
  console.log("Form requested:", message);
  console.log("Schema:", JSON.stringify(requestedSchema, null, 2));
});
```

**Data shape:**

```typescript
{
  requestId: string;          // UUID — use to respond via session.respondToElicitation()
  message: string;            // What information is needed
  mode?: "form";              // Currently only "form" is supported
  requestedSchema: {
    type: "object";
    properties: {             // JSON Schema field definitions
      [fieldName: string]: {
        type: string;
        description?: string;
        enum?: string[];
        default?: unknown;
      };
    };
    required?: string[];      // Required field names
  };
}
```

**Responding to elicitation:**

```typescript
session.on("elicitation.requested", async (event) => {
  const { requestId, requestedSchema } = event.data;

  // Build response matching the schema
  const response: Record<string, unknown> = {};
  for (const [field, schema] of Object.entries(requestedSchema.properties)) {
    response[field] = getDefaultValue(schema);
  }

  await session.rpc.session.respondToElicitation({
    requestId,
    response,
  });
});
```

### `elicitation.completed`

Emitted when an elicitation request is resolved. Ephemeral event.

```typescript
session.on("elicitation.completed", (event) => {
  dismissElicitationUI(event.data.requestId);
});
```

**Data shape:**

```typescript
{
  requestId: string;    // Matches the original elicitation.requested
}
```

## Event flow

```
User types message → user.message
Agent asks question → user_input.requested → user answers → user_input.completed
Agent needs form   → elicitation.requested → user submits → elicitation.completed
```

## Multi-client considerations

In protocol v3, `user_input.requested` and `elicitation.requested` are broadcast to all connected clients. Only one client should respond — implement first-responder logic or designate a primary UI client.
