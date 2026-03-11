# Session Lifecycle Events — Reference

Session lifecycle events track the state of the Copilot session itself — idle/active state, context changes, compaction, handoffs, and shutdown. Subscribe to these to build session-aware UI, orchestrate multi-turn flows, and detect context window pressure.

## `session.idle` — Turn Complete Signal

**Ephemeral.** Emitted when the agent finishes all processing and is ready for the next message. This is the terminal event of every turn. `sendAndWait()` resolves only after this event.

```typescript
type SessionIdleEvent = {
  id: string; timestamp: string; parentId: string | null;
  ephemeral: true;
  type: "session.idle";
  data: {
    backgroundTasks?: {
      agents: { agentId: string; agentType: string; description?: string }[];
      shells: { shellId: string; description?: string }[];
    };
  };
};
```

`backgroundTasks` is populated when the agent went idle but background agents or shell commands are still running. Check this field when building UIs that need to show "still working in background" state.

```typescript
session.on("session.idle", (event) => {
  const bg = event.data.backgroundTasks;
  if (bg && (bg.agents.length > 0 || bg.shells.length > 0)) {
    console.log(`Idle with ${bg.agents.length} background agents, ${bg.shells.length} shells`);
  } else {
    console.log("Fully idle");
  }
});
```

## `session.error` — Error During Processing

**Persisted.** Emitted when an unrecoverable error occurs. `sendAndWait()` rejects its internal promise when it receives this event, so the returned `Promise` from `sendAndWait()` will throw.

```typescript
type SessionErrorEvent = {
  id: string; timestamp: string; parentId: string | null; ephemeral?: boolean;
  type: "session.error";
  data: {
    errorType: string;   // "authentication" | "authorization" | "quota" | "rate_limit" | "query"
    message: string;
    stack?: string;
    statusCode?: number;
    providerCallId?: string; // x-github-request-id for server-side log correlation
  };
};
```

Handle `session.error` explicitly when using `session.on()` + `session.send()` (not `sendAndWait`):

```typescript
session.on("session.error", (event) => {
  const { errorType, message, statusCode, providerCallId } = event.data;
  if (errorType === "rate_limit") {
    scheduleRetry();
  } else if (errorType === "quota") {
    notifyUserQuotaExhausted();
  }
  console.error(`Session error [${errorType}] HTTP ${statusCode}: ${message}`);
  if (providerCallId) {
    console.error(`Provider call ID: ${providerCallId}`); // use for GitHub support
  }
});
```

## `session.compaction_start` — Context Compaction Began

**Persisted.** Data payload is empty `{}`. Emitted when the agent starts LLM-powered conversation compaction to free context window space.

```typescript
session.on("session.compaction_start", (_event) => {
  updateUI({ status: "Compacting context..." });
});
```

## `session.compaction_complete` — Context Compaction Finished

**Persisted.** Contains detailed metrics about the compaction operation.

```typescript
type SessionCompactionCompleteEvent = {
  type: "session.compaction_complete";
  data: {
    success: boolean;
    error?: string;
    preCompactionTokens?: number;
    postCompactionTokens?: number;
    preCompactionMessagesLength?: number;
    messagesRemoved?: number;
    tokensRemoved?: number;
    summaryContent?: string;          // LLM-generated summary of compacted history
    checkpointNumber?: number;
    checkpointPath?: string;
    compactionTokensUsed?: {
      input: number;
      output: number;
      cachedInput: number;
    };
    requestId?: string;
  };
};
```

```typescript
session.on("session.compaction_complete", (event) => {
  if (!event.data.success) {
    console.error("Compaction failed:", event.data.error);
    return;
  }
  const freed = event.data.tokensRemoved ?? 0;
  const before = event.data.preCompactionTokens ?? 0;
  const after = event.data.postCompactionTokens ?? 0;
  console.log(`Compacted: ${before} → ${after} tokens (freed ${freed})`);
  if (event.data.summaryContent) {
    console.log("Summary:", event.data.summaryContent.slice(0, 200));
  }
});
```

## `session.handoff` — Repository Handoff

**Persisted.** Emitted when a session is handed off between remote and local contexts. Contains the repository context being transferred.

```typescript
type SessionHandoffEvent = {
  type: "session.handoff";
  data: {
    handoffTime: string;              // ISO 8601
    sourceType: "remote" | "local";
    repository?: {
      owner: string;                  // e.g., "github"
      name: string;                   // e.g., "copilot"
      branch?: string;
    };
    context?: string;
    summary?: string;                 // summary of work done in source session
    remoteSessionId?: string;
  };
};
```

```typescript
session.on("session.handoff", (event) => {
  const repo = event.data.repository;
  if (repo) {
    console.log(`Handoff from ${event.data.sourceType}: ${repo.owner}/${repo.name}@${repo.branch ?? "default"}`);
  }
  if (event.data.summary) {
    console.log("Prior work:", event.data.summary);
  }
});
```

## `session.context_changed` — Working Directory Changed

**Persisted.** Emitted when the session's working directory or git context changes.

```typescript
type SessionContextChangedEvent = {
  type: "session.context_changed";
  data: {
    cwd: string;          // absolute path
    gitRoot?: string;     // git repo root
    repository?: string;  // "owner/name" format
    branch?: string;
  };
};
```

## `session.start` — Session Initialized

**Persisted.** First event in any new session. Contains session metadata and initial context.

```typescript
type SessionStartEvent = {
  type: "session.start";
  data: {
    sessionId: string;
    version: number;
    producer: string;           // e.g., "copilot-agent"
    copilotVersion: string;
    startTime: string;          // ISO 8601
    selectedModel?: string;
    context?: {
      cwd: string;
      gitRoot?: string;
      repository?: string;
      branch?: string;
    };
    alreadyInUse?: boolean;
  };
};
```

## `session.resume` — Session Resumed

**Persisted.** First event after `client.resumeSession()`. Contains the total persisted event count at resume time.

```typescript
type SessionResumeEvent = {
  type: "session.resume";
  data: {
    resumeTime: string;      // ISO 8601
    eventCount: number;      // total persisted events in session at resume
    context?: { cwd: string; gitRoot?: string; repository?: string; branch?: string };
    alreadyInUse?: boolean;
  };
};
```

## `session.shutdown` — Session Ended

**Persisted.** Final event before the session process exits. Contains aggregate metrics for the entire session.

```typescript
type SessionShutdownEvent = {
  type: "session.shutdown";
  data: {
    shutdownType: "routine" | "error";
    errorReason?: string;
    totalPremiumRequests: number;
    totalApiDurationMs: number;
    sessionStartTime: number;    // Unix ms
    codeChanges: {
      linesAdded: number;
      linesRemoved: number;
      filesModified: string[];
    };
    modelMetrics: {
      [modelId: string]: {
        requests: { count: number; cost: number };
        usage: {
          inputTokens: number;
          outputTokens: number;
          cacheReadTokens: number;
          cacheWriteTokens: number;
        };
      };
    };
    currentModel?: string;
  };
};
```

## `session.usage_info` — Context Window Snapshot

**Ephemeral.** Periodic snapshot of context window utilization. Use to drive compaction warnings or progress bars.

```typescript
session.on("session.usage_info", (event) => {
  const { tokenLimit, currentTokens, messagesLength } = event.data;
  const pct = Math.round((currentTokens / tokenLimit) * 100);
  if (pct > 80) console.warn(`Context window ${pct}% full (${currentTokens}/${tokenLimit})`);
});
```

## `session.task_complete` — Agent Finished Task

**Persisted.** Emitted when the agent signals it has completed its assigned task.

```typescript
session.on("session.task_complete", (event) => {
  console.log("Task complete:", event.data.summary ?? "(no summary)");
});
```

## `session.title_changed` — Auto-Generated Title Updated

**Ephemeral.** The session's display title was updated by the agent.

```typescript
session.on("session.title_changed", (event) => {
  document.title = event.data.title;
});
```

## `session.model_change` — Model Switched

**Persisted.** Emitted when the active model changes, including on session start.

```typescript
session.on("session.model_change", (event) => {
  console.log(`Model: ${event.data.previousModel ?? "none"} → ${event.data.newModel}`);
});
```

## `session.mode_changed` — Agent Mode Changed

**Persisted.** Emitted when the agent switches between `"interactive"`, `"plan"`, `"autopilot"`, or `"shell"` modes.

```typescript
session.on("session.mode_changed", (event) => {
  console.log(`Mode: ${event.data.previousMode} → ${event.data.newMode}`);
});
```

## `pending_messages.modified` — Message Queue Changed

**Ephemeral.** Data payload is empty `{}`. Signals that the queue of pending messages changed (e.g., a queued message was added or processed). Use to refresh pending message display in a UI.

## `session.truncation` — Context Truncated

**Persisted.** Emitted when the conversation was truncated (non-LLM truncation, different from compaction).

```typescript
type SessionTruncationEvent = {
  type: "session.truncation";
  data: {
    tokenLimit: number;
    preTruncationTokensInMessages: number;
    preTruncationMessagesLength: number;
    postTruncationTokensInMessages: number;
    postTruncationMessagesLength: number;
    tokensRemovedDuringTruncation: number;
    messagesRemovedDuringTruncation: number;
    performedBy: string;   // e.g., "BasicTruncator"
  };
};
```

## `session.snapshot_rewind` — Session Rewound

**Ephemeral.** Emitted after a session checkpoint rewind operation.

```typescript
type SessionSnapshotRewindEvent = {
  type: "session.snapshot_rewind";
  ephemeral: true;
  data: {
    upToEventId: string;    // event ID that was rewound to
    eventsRemoved: number;
  };
};
```

## `session.plan_changed` — Plan File Modified

**Persisted.** Emitted when the session's `plan.md` file is created, updated, or deleted (infinite sessions only).

```typescript
session.on("session.plan_changed", (event) => {
  console.log(`Plan ${event.data.operation}d`); // "create" | "update" | "delete"
});
```

## `session.workspace_file_changed` — Workspace File Modified

**Persisted.** Emitted when a file in the session workspace `files/` directory is created or updated.

```typescript
session.on("session.workspace_file_changed", (event) => {
  console.log(`Workspace file ${event.data.operation}: ${event.data.path}`);
});
```
