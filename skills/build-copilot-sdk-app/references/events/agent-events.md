# Agent, Subagent, Skill, and Command Events

Events for tracking agent hierarchy, skill invocations, and slash command execution.

## Subagent Events

### `subagent.started`

Emitted when a sub-agent is spawned (e.g., background agent, explore agent).

```typescript
session.on("subagent.started", (event) => {
  const { toolCallId, agentName, agentDisplayName, agentDescription } = event.data;
  console.log(`Subagent started: ${agentDisplayName} (${agentName})`);
  console.log(`Description: ${agentDescription}`);
  console.log(`Parent tool call: ${toolCallId}`);
});
```

**Data shape:**

```typescript
{
  toolCallId: string;         // Parent tool invocation that spawned this sub-agent
  agentName: string;          // Internal name (e.g., "explore", "task")
  agentDisplayName: string;   // Human-readable name
  agentDescription: string;   // What the sub-agent does
}
```

### `subagent.completed`

Emitted when a sub-agent finishes successfully.

```typescript
session.on("subagent.completed", (event) => {
  console.log(`Subagent done: ${event.data.agentDisplayName}`);
});
```

**Data shape:**

```typescript
{
  toolCallId: string;
  agentName: string;
  agentDisplayName: string;
}
```

### `subagent.failed`

Emitted when a sub-agent fails with an error.

```typescript
session.on("subagent.failed", (event) => {
  console.error(`Subagent failed: ${event.data.agentDisplayName}`);
  console.error(`Error: ${event.data.error}`);
});
```

**Data shape:**

```typescript
{
  toolCallId: string;
  agentName: string;
  agentDisplayName: string;
  error: string;              // Error message
}
```

### `subagent.selected`

Emitted when a custom agent is activated (selected).

```typescript
session.on("subagent.selected", (event) => {
  console.log(`Agent selected: ${event.data.agentDisplayName}`);
  console.log(`Available tools: ${event.data.tools?.join(", ") ?? "all"}`);
});
```

**Data shape:**

```typescript
{
  agentName: string;
  agentDisplayName: string;
  tools: string[] | null;     // null = all tools available
}
```

### `subagent.deselected`

Emitted when a custom agent is deactivated, returning to the default agent.

```typescript
session.on("subagent.deselected", () => {
  console.log("Returned to default agent");
});
```

**Data shape:** `{}` (empty)

## Skill Events

### `skill.invoked`

Emitted when a skill is loaded and injected into the conversation.

```typescript
session.on("skill.invoked", (event) => {
  const { name, path, allowedTools, pluginName } = event.data;
  console.log(`Skill loaded: ${name} from ${path}`);
  if (allowedTools?.length) {
    console.log(`Auto-approved tools: ${allowedTools.join(", ")}`);
  }
});
```

**Data shape:**

```typescript
{
  name: string;               // Skill name from SKILL.md frontmatter
  path: string;               // File path to SKILL.md
  content: string;            // Full skill content injected into conversation
  allowedTools?: string[];    // Tools auto-approved while skill is active
  pluginName?: string;        // Source plugin name, if applicable
  pluginVersion?: string;     // Source plugin version, if applicable
}
```

## Command Events

### `command.queued`

Emitted when a slash command is queued for execution. Ephemeral event.

```typescript
session.on("command.queued", (event) => {
  const { requestId, command } = event.data;
  console.log(`Command queued: ${command}`);
});
```

**Data shape:**

```typescript
{
  requestId: string;          // UUID — respond via session.respondToQueuedCommand()
  command: string;            // The slash command text (e.g., "/help", "/clear")
}
```

### `command.completed`

Emitted when a queued command has been resolved. Ephemeral event.

```typescript
session.on("command.completed", (event) => {
  dismissCommandUI(event.data.requestId);
});
```

**Data shape:**

```typescript
{
  requestId: string;
}
```

## Monitoring agent hierarchy

Track the full agent lifecycle:

```typescript
const activeSubagents = new Map<string, { name: string; startTime: number }>();

session.on("subagent.started", (event) => {
  activeSubagents.set(event.data.toolCallId, {
    name: event.data.agentDisplayName,
    startTime: Date.now(),
  });
});

session.on("subagent.completed", (event) => {
  const info = activeSubagents.get(event.data.toolCallId);
  if (info) {
    console.log(`${info.name} took ${Date.now() - info.startTime}ms`);
    activeSubagents.delete(event.data.toolCallId);
  }
});

session.on("subagent.failed", (event) => {
  const info = activeSubagents.get(event.data.toolCallId);
  console.error(`${info?.name ?? event.data.agentName} failed: ${event.data.error}`);
  activeSubagents.delete(event.data.toolCallId);
});
```
