# Convex Components Ecosystem

## Use This When
- Evaluating whether a Convex component solves a backend need (aggregation, rate limiting, retries, workflows).
- Understanding how components relate to your Swift client code.
- Installing and wiring up a component in the Convex backend.

## What Are Components

Convex components are npm packages that contain self-contained backend logic with their own tables, functions, and indexes. Each component runs in an **isolated sandbox** — it has its own database namespace and cannot access your app's tables directly (and vice versa).

From the Swift client's perspective, components are **invisible**. You interact with them through wrapper functions you write in your own Convex backend.

## Architecture

```
Swift App
  → client.mutation("myFunctions:doThing")
    → Your Convex Function
      → Component API (internal call)
        → Component's isolated tables & logic
```

The Swift client never calls component functions directly.

## Key Components

### persistent-text-streaming

Streams text from AI models to clients in real-time using Convex's reactive subscriptions instead of HTTP streaming.

```typescript
// convex/convex.config.ts
import { defineApp } from "convex/server";
import textStreaming from "@anthropic-ai/persistent-text-streaming";

const app = defineApp();
app.use(textStreaming);
export default app;
```

### aggregate

Maintains running aggregates (count, sum, average) efficiently. Avoids the `.collect().length` antipattern for counting documents.

```typescript
import { defineApp } from "convex/server";
import aggregate from "@convex-dev/aggregate";

const app = defineApp();
app.use(aggregate);
export default app;
```

### action-retrier

Automatically retries failed actions with configurable backoff:

```typescript
import { defineApp } from "convex/server";
import actionRetrier from "@convex-dev/action-retrier";

const app = defineApp();
app.use(actionRetrier);
export default app;
```

### rate-limiter

Rate limits function calls per user or globally:

```typescript
import { defineApp } from "convex/server";
import rateLimiter from "@convex-dev/rate-limiter";

const app = defineApp();
app.use(rateLimiter);
export default app;
```

### workflow

Durable workflow engine with steps, retries, and compensation:

```typescript
import { defineApp } from "convex/server";
import workflow from "@convex-dev/workflow";

const app = defineApp();
app.use(workflow);
export default app;
```

### agent

AI agent framework that integrates with Convex's data layer:

```typescript
import { defineApp } from "convex/server";
import agent from "@convex-dev/agent";

const app = defineApp();
app.use(agent);
export default app;
```

## Installation Pattern

Every component follows the same three-step installation:

```bash
# 1. Install the npm package
npm install @convex-dev/aggregate

# 2. Register in convex/convex.config.ts (see examples above)

# 3. Deploy
npx convex dev
```

## Using Components From Your Functions

Components expose APIs that your functions call internally. Example with action-retrier:

```typescript
// convex/myFunctions.ts
import { components } from "./_generated/api";
import { ActionRetrier } from "@convex-dev/action-retrier";
import { userMutation } from "./functions";
import { v } from "convex/values";

const retrier = new ActionRetrier(components.actionRetrier);

export const sendEmailReliably = userMutation({
  args: { to: v.string(), subject: v.string(), body: v.string() },
  handler: async (ctx, args) => {
    const emailId = await ctx.db.insert("emails", {
      ...args,
      status: "pending",
    });

    await retrier.run(ctx, internal.emails.actuallySend, { emailId });
    return emailId;
  },
});
```

## Swift Client: Transparent Interaction

The Swift client calls your wrapper functions. It never knows about components:

```swift
// Swift doesn't know about action-retrier, aggregate, etc.
// It just calls your functions as normal

// Send email (retried automatically by action-retrier on server)
try await client.mutation(
    "myFunctions:sendEmailReliably",
    with: [
        "to": "user@example.com",
        "subject": "Hello",
        "body": "World"
    ]
)
```

## Component Isolation Rules

Each component has its own database tables (namespaced), functions (internal), indexes, and schema.

Components **cannot**:
- Read your app's tables directly.
- Be called from the Swift client directly.
- Share tables with other components.
- Access `ctx.auth` from your app (must be passed explicitly if needed).

## Available Components Registry

| Component | Purpose | Package |
|-----------|---------|---------|
| persistent-text-streaming | Real-time AI text streaming | `@anthropic-ai/persistent-text-streaming` |
| aggregate | Running counts/sums/averages | `@convex-dev/aggregate` |
| action-retrier | Retry failed actions | `@convex-dev/action-retrier` |
| rate-limiter | Rate limit function calls | `@convex-dev/rate-limiter` |
| workflow | Durable workflows with steps | `@convex-dev/workflow` |
| agent | AI agent framework | `@convex-dev/agent` |
| crons | Enhanced cron scheduling | `@convex-dev/crons` |
| migrations | Schema migration helpers | `@convex-dev/migrations` |

## Avoid
- Calling component functions directly from the Swift client — always go through your own wrapper functions.
- Assuming components can read your app's tables — they run in an isolated sandbox.
- Installing components without registering them in `convex.config.ts` — they will not be deployed.
- Treating components as optional server-side sugar — some (like aggregate) solve real performance problems that cannot be solved client-side.

## Read Next
- [02-file-storage-upload-download-and-document-ids.md](02-file-storage-upload-download-and-document-ids.md)
- [04-streaming-workloads-and-transcription.md](04-streaming-workloads-and-transcription.md)
- [06-full-text-search-reactive.md](06-full-text-search-reactive.md)
