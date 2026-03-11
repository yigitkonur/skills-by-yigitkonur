# User Input Handler Reference

## Type Signatures

```typescript
import type { UserInputHandler, UserInputRequest, UserInputResponse } from "@github/copilot-sdk";

type UserInputHandler = (
    request: UserInputRequest,
    invocation: { sessionId: string }
) => Promise<UserInputResponse> | UserInputResponse;
```

`onUserInputRequest` is **optional** in `SessionConfig`. When omitted, the `ask_user` tool is unavailable and any attempt by the agent to invoke it throws `"User input requested but no handler registered"`.

---

## UserInputRequest Structure

```typescript
interface UserInputRequest {
    question: string;         // The question the agent is asking the user
    choices?: string[];       // Optional predefined answer options
    allowFreeform?: boolean;  // Whether freeform text is accepted in addition to choices (default: true)
}
```

Field behavior:
- `question` is always present and non-empty. Display it verbatim to the user or process it programmatically.
- `choices` is optional. When present, it is an array of string options. When absent, only freeform input is expected.
- `allowFreeform` defaults to `true`. When `false` and `choices` is provided, the agent expects the answer to be one of the listed choices. Returning a freeform answer when `allowFreeform: false` may confuse the model — match a choice string exactly in that case.

---

## UserInputResponse Structure

```typescript
interface UserInputResponse {
    answer: string;        // The user's answer — either a choice string or freeform text
    wasFreeform: boolean;  // true if the answer was freeform (not from choices)
}
```

Set `wasFreeform: true` when the answer is not one of the provided `choices`. Set `wasFreeform: false` when returning a string that matches one of `request.choices`. The model uses `wasFreeform` to interpret confidence: choice selections signal stronger intent than freeform answers.

---

## Registering the Handler in SessionConfig

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";
import type { UserInputResponse } from "@github/copilot-sdk";

const client = new CopilotClient();

const session = await client.createSession({
    onPermissionRequest: approveAll,
    onUserInputRequest: async (request, invocation) => {
        console.log(`[${invocation.sessionId}] Agent asks: ${request.question}`);

        if (request.choices && request.choices.length > 0) {
            // Return the first choice as a default selection
            return { answer: request.choices[0], wasFreeform: false };
        }

        // Freeform response
        return { answer: "No preference", wasFreeform: true };
    },
});
```

Also include in `resumeSession` if the resumed session may invoke `ask_user`:

```typescript
const resumed = await client.resumeSession(sessionId, {
    onPermissionRequest: approveAll,
    onUserInputRequest: myInputHandler,
});
```

---

## Choice Selection Patterns

### Always Select First Choice (Testing / Automation)

```typescript
onUserInputRequest: (request) => {
    if (request.choices && request.choices.length > 0) {
        return { answer: request.choices[0], wasFreeform: false };
    }
    return { answer: "default", wasFreeform: true };
},
```

### Select Choice by Index

```typescript
function selectChoiceByIndex(request: UserInputRequest, index: number): UserInputResponse {
    if (request.choices && request.choices[index] !== undefined) {
        return { answer: request.choices[index], wasFreeform: false };
    }
    // Fall back to freeform if index out of range
    return { answer: request.question, wasFreeform: true };
}

onUserInputRequest: (request) => selectChoiceByIndex(request, 1),
```

### Match Choice by Substring

```typescript
onUserInputRequest: (request) => {
    if (request.choices) {
        const match = request.choices.find((c) => c.toLowerCase().includes("yes"));
        if (match) return { answer: match, wasFreeform: false };
    }
    return { answer: "yes", wasFreeform: true };
},
```

---

## Freeform Input Patterns

### Static Freeform Answer

```typescript
onUserInputRequest: (_request) => ({
    answer: "Please proceed with your best judgment.",
    wasFreeform: true,
}),
```

### Dynamic Freeform Based on Question Content

```typescript
const FREEFORM_RULES: Array<{ pattern: RegExp; answer: string }> = [
    { pattern: /preferred language/i, answer: "TypeScript" },
    { pattern: /test framework/i, answer: "vitest" },
    { pattern: /package manager/i, answer: "npm" },
];

onUserInputRequest: (request) => {
    for (const rule of FREEFORM_RULES) {
        if (rule.pattern.test(request.question)) {
            return { answer: rule.answer, wasFreeform: true };
        }
    }
    // Default: pick first choice or provide a generic answer
    if (request.choices?.length) {
        return { answer: request.choices[0], wasFreeform: false };
    }
    return { answer: "I have no preference.", wasFreeform: true };
},
```

---

## Interactive vs Automated Response Strategies

### Interactive Strategy (Human at the Keyboard)

Read from stdin or display a native prompt. Block until the user responds:

```typescript
import * as readline from "readline";

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

function promptUser(question: string, choices?: string[]): Promise<string> {
    return new Promise((resolve) => {
        const choiceText = choices ? `\nChoices: ${choices.join(", ")}\n` : "";
        rl.question(`${question}${choiceText}> `, resolve);
    });
}

onUserInputRequest: async (request) => {
    const raw = await promptUser(request.question, request.choices);

    if (request.choices) {
        const matched = request.choices.find((c) => c.toLowerCase() === raw.toLowerCase());
        if (matched) return { answer: matched, wasFreeform: false };
    }

    return { answer: raw, wasFreeform: true };
},
```

### Automated Strategy (Pipeline / CI)

Pre-configure answers for all expected questions. Fail fast on unexpected questions:

```typescript
type AnswerMap = Record<string, string>;

function buildAutomatedHandler(answers: AnswerMap): UserInputHandler {
    return (request) => {
        // Try exact question match
        if (answers[request.question]) {
            const answer = answers[request.question];
            const isChoice = request.choices?.includes(answer) ?? false;
            return { answer, wasFreeform: !isChoice };
        }

        // Try pattern matching
        for (const [pattern, answer] of Object.entries(answers)) {
            if (request.question.includes(pattern)) {
                const isChoice = request.choices?.includes(answer) ?? false;
                return { answer, wasFreeform: !isChoice };
            }
        }

        // Unexpected question in automated context — provide default
        console.warn(`Unhandled ask_user question: "${request.question}"`);
        if (request.choices?.length) {
            return { answer: request.choices[0], wasFreeform: false };
        }
        return { answer: "N/A", wasFreeform: true };
    };
}

const session = await client.createSession({
    onPermissionRequest: approveAll,
    onUserInputRequest: buildAutomatedHandler({
        "preferred language": "TypeScript",
        "overwrite existing files": "yes",
        "add tests": "yes",
    }),
});
```

---

## Elicitation (MCP Forms) — Structured Form Input

Elicitation is a separate protocol mechanism for MCP servers to request structured form input. It arrives as an `elicitation.requested` event, not via `onUserInputRequest`. Handle it by listening to session events:

```typescript
session.on("elicitation.requested", (event) => {
    const { requestId, message, requestedSchema, mode } = event.data;
    // mode is "form" (the only supported mode)
    // requestedSchema is a JSON Schema object describing form fields

    console.log(`Elicitation request: ${message}`);
    console.log(`Schema fields:`, requestedSchema.properties);

    // Respond by calling the elicitation RPC
    session.rpc.elicitation.respond({
        requestId,
        result: {
            action: "submit",
            content: {
                // Provide values for all required fields
                field_name: "field_value",
            },
        },
    });
});
```

### Elicitation Schema Structure

```typescript
// event.data.requestedSchema shape:
{
    type: "object";
    properties: {
        [fieldName: string]: {
            type: string;          // JSON Schema type: "string", "number", "boolean", etc.
            description?: string;  // Field label or description
            enum?: string[];       // Allowed values (for dropdown fields)
            default?: unknown;     // Default value
        };
    };
    required?: string[];  // Required field names
}
```

### Automated Elicitation Handler

```typescript
session.on("elicitation.requested", async (event) => {
    const { requestId, requestedSchema } = event.data;
    const content: Record<string, unknown> = {};

    // Auto-fill fields from defaults or enum first values
    for (const [name, field] of Object.entries(requestedSchema.properties)) {
        const schema = field as { type: string; enum?: string[]; default?: unknown };
        if (schema.default !== undefined) {
            content[name] = schema.default;
        } else if (schema.enum && schema.enum.length > 0) {
            content[name] = schema.enum[0];
        } else if (schema.type === "boolean") {
            content[name] = false;
        } else if (schema.type === "number") {
            content[name] = 0;
        } else {
            content[name] = "";
        }
    }

    await session.rpc.elicitation.respond({
        requestId,
        result: { action: "submit", content },
    });
});
```

Elicitation requests also emit `elicitation.completed` when resolved.

---

## Common askUser Scenarios and Responses

### Binary Yes/No Question

```typescript
// Agent asks: "Do you want to overwrite the existing file?"
// choices: ["Yes", "No"]

onUserInputRequest: (request) => {
    if (request.choices?.includes("Yes")) {
        return { answer: "Yes", wasFreeform: false };
    }
    return { answer: "yes", wasFreeform: true };
},
```

### Language / Framework Selection

```typescript
// Agent asks: "Which framework should I use?"
// choices: ["React", "Vue", "Angular", "Svelte"]

onUserInputRequest: (request) => {
    const preferred = "React";
    const match = request.choices?.find((c) => c === preferred);
    if (match) return { answer: match, wasFreeform: false };
    return { answer: preferred, wasFreeform: true };
},
```

### Open-Ended Requirement Clarification

```typescript
// Agent asks: "What should the API endpoint return?"
// No choices

onUserInputRequest: (request) => {
    if (!request.choices?.length) {
        return {
            answer: "Return a JSON object with id, name, and createdAt fields.",
            wasFreeform: true,
        };
    }
    return { answer: request.choices[0], wasFreeform: false };
},
```

### Confirmation Before Destructive Action

```typescript
// Agent asks: "This will delete all records in the users table. Are you sure?"
// choices: ["Proceed", "Cancel"]

onUserInputRequest: async (request) => {
    // In automated contexts, cancel by default for destructive confirmations
    const cancelChoice = request.choices?.find((c) => /cancel|no|abort/i.test(c));
    if (cancelChoice) {
        return { answer: cancelChoice, wasFreeform: false };
    }
    return { answer: "Cancel", wasFreeform: true };
},
```

---

## Error Behavior

- Handler throws → SDK re-throws the error. The agent's `ask_user` tool call fails, and the session may emit `session.error` depending on how the CLI handles the failure.
- Handler returns `undefined` or `null` → runtime error. Always return a valid `UserInputResponse`.
- No handler registered + agent calls `ask_user` → SDK throws `"User input requested but no handler registered"`. The CLI propagates this as a tool execution failure.

Unlike `onPermissionRequest`, there is no automatic fallback. Register `onUserInputRequest` whenever your session configuration or prompt might trigger the `ask_user` tool.

---

## Session Event Correlation

The `user_input.requested` and `user_input.completed` events appear in the session event stream (both are ephemeral). Subscribe to observe the full lifecycle:

```typescript
session.on("user_input.requested", (event) => {
    console.log(`[${event.data.requestId}] Question: ${event.data.question}`);
    console.log(`Choices: ${event.data.choices?.join(", ") ?? "freeform"}`);
});

session.on("user_input.completed", (event) => {
    console.log(`[${event.data.requestId}] Answered`);
});
```

These events are for observation only — the actual response flows through the `onUserInputRequest` handler registered at session creation, not through the event listener.
