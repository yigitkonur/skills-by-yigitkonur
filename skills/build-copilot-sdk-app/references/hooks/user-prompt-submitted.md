# onUserPromptSubmitted Hook Reference

Intercept every user message before the model processes it. Use this hook to augment prompts with context, enforce content policies, apply shorthand expansion, inject per-user preferences, or implement rate limiting. The hook fires synchronously in the message dispatch path — return promptly.

## Type Signatures

```typescript
import type {
  UserPromptSubmittedHookInput,
  UserPromptSubmittedHookOutput,
  SessionHooks,
} from "@github/copilot-sdk";

// Handler signature
type UserPromptSubmittedHandler = (
  input: UserPromptSubmittedHookInput,
  invocation: { sessionId: string }
) => Promise<UserPromptSubmittedHookOutput | void> | UserPromptSubmittedHookOutput | void;

// Register via SessionConfig.hooks
const hooks: SessionHooks = {
  onUserPromptSubmitted: async (input, invocation) => { /* ... */ },
};
```

## Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `string` | The full text of the user's submitted message |
| `timestamp` | `number` | Unix epoch milliseconds when the hook fired |
| `cwd` | `string` | Working directory of the session at submission time |

Access `invocation.sessionId` for the session identifier. Confirmed by e2e tests: `input.prompt` contains the exact string passed to `session.sendAndWait()`.

## Output Fields

Return `void` or `undefined` to forward the prompt unchanged. Return an object to modify behavior:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `modifiedPrompt` | `string` | — | Replacement prompt forwarded to the model instead of the original |
| `additionalContext` | `string` | — | Text injected into the conversation context alongside the prompt |
| `suppressOutput` | `boolean` | `false` | When `true`, suppresses the assistant's response from the conversation |

Prefer `additionalContext` over `modifiedPrompt` when augmenting rather than replacing — it preserves the user's original message in the conversation history.

## Pattern: Prompt Augmentation with Project Context

Append dynamically loaded context so every message benefits from environment-aware information.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input) => {
      const projectMeta = await detectProject(input.cwd);
      return {
        additionalContext: [
          `Project: ${projectMeta.name} (${projectMeta.type})`,
          `Language: ${projectMeta.language}`,
          `Package manager: ${projectMeta.packageManager}`,
          `Git branch: ${projectMeta.branch ?? "unknown"}`,
        ].join("\n"),
      };
    },
  },
});
```

Keep `detectProject` fast — cache results keyed by `cwd` rather than re-running filesystem detection on every message.

## Pattern: Inject System Instructions into Every Prompt

Prepend mandatory instructions that must apply to all turns without relying solely on the system message.

```typescript
const MANDATORY_PREFIX =
  "You are operating within a production environment. " +
  "Never suggest dropping database tables. " +
  "Always use transactions for multi-step operations.";

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input) => {
      return {
        additionalContext: MANDATORY_PREFIX,
      };
    },
  },
});
```

## Pattern: Shorthand Expansion

Expand command-style shortcuts into full, structured prompts.

```typescript
const SHORTCUTS: Record<string, (rest: string) => string> = {
  "/fix": (r) =>
    `Fix the following issue in the codebase: ${r}\n\nProvide the corrected code and a brief explanation of the root cause.`,
  "/test": (r) =>
    `Write comprehensive unit tests for: ${r}\n\nCover happy paths, edge cases, and error conditions.`,
  "/explain": (r) =>
    `Explain in detail: ${r}\n\nAssume intermediate-level familiarity with the language but not the specific API.`,
  "/refactor": (r) =>
    `Refactor the following for clarity and maintainability: ${r}\n\nDo not change external behavior.`,
};

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input) => {
      for (const [shortcut, expand] of Object.entries(SHORTCUTS)) {
        if (input.prompt.startsWith(shortcut)) {
          const rest = input.prompt.slice(shortcut.length).trim();
          return { modifiedPrompt: expand(rest) };
        }
      }
    },
  },
});
```

## Pattern: Input Validation and Content Filtering

Detect and block prompts containing credential patterns or policy-violating content.

```typescript
const BLOCKED_PATTERNS: Array<{ pattern: RegExp; reason: string }> = [
  {
    pattern: /(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S+/i,
    reason: "Prompt appears to contain credentials. Use environment variables instead.",
  },
  {
    pattern: /DROP\s+TABLE|DELETE\s+FROM\s+\w+\s+(?:WHERE\s+1=1|;)/i,
    reason: "Prompt contains potentially destructive SQL. Rephrase your request.",
  },
];

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input) => {
      for (const { pattern, reason } of BLOCKED_PATTERNS) {
        if (pattern.test(input.prompt)) {
          return {
            modifiedPrompt: `[Blocked] ${reason}`,
            suppressOutput: true,
          };
        }
      }
    },
  },
});
```

Setting `suppressOutput: true` alongside `modifiedPrompt` sends the replacement to the model but hides the response. Use this when you want to log the blocked event without surfacing model output to the user.

## Pattern: Adding Per-User Preferences

Load user preferences and embed them as context so the model tailors all responses.

```typescript
interface UserPrefs {
  language: string;
  verbosity: "concise" | "detailed";
  experienceLevel: "beginner" | "intermediate" | "expert";
  preferTypeScript: boolean;
}

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input, invocation) => {
      const prefs: UserPrefs = await loadPrefs(invocation.sessionId);

      const lines: string[] = [
        `User language preference: ${prefs.language}`,
        `Response style: ${prefs.verbosity}`,
        `Experience level: ${prefs.experienceLevel}`,
      ];
      if (prefs.preferTypeScript) {
        lines.push("Prefer TypeScript over JavaScript for all code examples.");
      }
      if (prefs.experienceLevel === "beginner") {
        lines.push("Explain concepts step-by-step without assuming prior knowledge.");
      }

      return { additionalContext: lines.join("\n") };
    },
  },
});
```

Cache `loadPrefs` by `sessionId` — preferences rarely change within a session.

## Pattern: Rate Limiting and Abuse Prevention

Track submission frequency per session and reject prompts that exceed the allowed rate.

```typescript
interface RateWindow {
  timestamps: number[];
}

const rateLimitMap = new Map<string, RateWindow>();
const LIMIT = 10;           // max prompts
const WINDOW_MS = 60_000;   // per minute

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input, invocation) => {
      const sid = invocation.sessionId;
      const now = input.timestamp;
      const window = rateLimitMap.get(sid) ?? { timestamps: [] };

      // Evict entries outside the rolling window
      window.timestamps = window.timestamps.filter((t) => t > now - WINDOW_MS);

      if (window.timestamps.length >= LIMIT) {
        const retryAfterMs = WINDOW_MS - (now - window.timestamps[0]);
        return {
          modifiedPrompt: `[Rate limited] Too many messages. Retry in ${Math.ceil(retryAfterMs / 1000)}s.`,
          suppressOutput: true,
        };
      }

      window.timestamps.push(now);
      rateLimitMap.set(sid, window);
    },
  },
});
```

Clean up `rateLimitMap` entries in the `onSessionEnd` hook to avoid memory leaks in long-running processes.

## Pattern: Enforce Prompt Length Limits

Truncate oversized prompts and inform the model about the truncation.

```typescript
const MAX_PROMPT_CHARS = 12_000;

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input) => {
      if (input.prompt.length <= MAX_PROMPT_CHARS) return;

      const truncated = input.prompt.slice(0, MAX_PROMPT_CHARS);
      const omitted = input.prompt.length - MAX_PROMPT_CHARS;
      return {
        modifiedPrompt: truncated,
        additionalContext:
          `The user's prompt was truncated. ${omitted} characters were omitted from the end.`,
      };
    },
  },
});
```

## Common Mistakes

- Replacing the entire prompt with `modifiedPrompt` discards the user's original message from the conversation history. Use `additionalContext` when the goal is augmentation, not replacement.
- Performing blocking I/O (database queries, HTTP calls) without caching adds latency to every turn. Cache aggressively keyed by `sessionId` or `cwd`.
- Setting `suppressOutput: true` without also setting `modifiedPrompt` sends the original prompt to the model but hides the response — this is usually unintentional.
- Matching patterns case-sensitively against user text misses variants. Use the `i` flag on regular expressions for credential and content detection.
- Rate limit state held in process memory is lost on restart. For production deployments, use an external store (Redis, database) as the rate limit backing.
