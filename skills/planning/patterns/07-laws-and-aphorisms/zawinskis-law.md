# Zawinski's Law

## Origin

Jamie Zawinski (jwz), 1998, early Netscape/Mozilla developer: "Every program attempts to expand until it can read mail. Those programs which cannot so expand are replaced by ones which can."

Also known as the **Law of Software Envelopment** or the **Law of Feature Creep**.

## Explanation

Software has a natural tendency to accumulate features until it becomes a bloated, do-everything platform. The "reading mail" part is both literal (Emacs, browsers, and even games have acquired email functionality) and metaphorical — it represents the point where a tool tries to become an operating system.

This happens because:
1. **Users request adjacent features** — "Since I am already in this app, can it also do X?"
2. **Developers enjoy building** — new features are more exciting than maintaining existing ones.
3. **Market pressure** — competitors add features, and you feel compelled to match them.
4. **Revenue pressure** — more features justify higher prices or attract more users.
5. **Platform ambition** — every successful tool wants to become a platform.

## TypeScript Code Examples

### Bad: A Todo App That Became an Operating System

```typescript
// Version 1.0: Simple todo list (good)
interface Todo {
  id: string;
  title: string;
  done: boolean;
}

// Version 2.0: Added tags, priorities, due dates (reasonable)
// Version 3.0: Added collaboration, sharing, comments (stretching)
// Version 5.0: Full project management, Gantt charts, time tracking
// Version 8.0: The current state...

interface Todo {
  id: string;
  title: string;
  done: boolean;
  description: RichTextDocument;
  priority: "critical" | "high" | "medium" | "low" | "someday";
  tags: Tag[];
  dueDate: Date;
  recurrence: RecurrenceRule;
  assignees: User[];
  watchers: User[];
  comments: Comment[];
  attachments: Attachment[];
  subtasks: Todo[];
  dependencies: TodoDependency[];
  timeTracking: TimeEntry[];
  ganttPosition: { row: number; startCol: number; endCol: number };
  calendarSync: CalendarIntegration;
  emailNotifications: NotificationConfig;
  slackIntegration: SlackChannelConfig;
  aiSuggestions: AISuggestion[];
  customFields: Map<string, unknown>;
  workflow: WorkflowState;
  // It reads mail now.
  linkedEmails: Email[];
  emailForwardAddress: string;
}
```

### Good: Focused Tool with Clear Boundaries

```typescript
// Define what the product IS and what it IS NOT

// product-boundaries.ts
/**
 * This is a todo list. It manages tasks.
 *
 * IN SCOPE:
 * - Create, complete, delete tasks
 * - Organize with tags and priorities
 * - Due dates with reminders
 *
 * OUT OF SCOPE (use integrations instead):
 * - Project management → integrate with Jira/Linear
 * - Time tracking → integrate with Toggl/Harvest
 * - Email → that's what email is for
 * - Chat → that's what Slack is for
 */

interface Todo {
  readonly id: string;
  readonly title: string;
  readonly done: boolean;
  readonly priority: "high" | "medium" | "low";
  readonly tags: ReadonlyArray<string>;
  readonly dueDate?: Date;
}

// Extensibility through integrations, not feature bloat
interface Integration {
  readonly name: string;
  readonly type: "webhook" | "api";
  onTodoCreated?(todo: Todo): Promise<void>;
  onTodoCompleted?(todo: Todo): Promise<void>;
}
```

### Recognizing Feature Creep in Code

```typescript
// Warning sign: a single module that imports from everywhere

import { EmailClient } from "./email";
import { CalendarSync } from "./calendar";
import { SlackNotifier } from "./slack";
import { GanttRenderer } from "./gantt";
import { TimeTracker } from "./time-tracking";
import { AIEngine } from "./ai-suggestions";
import { VideoCall } from "./video-conferencing";   // wait, what?
import { SpreadsheetEngine } from "./spreadsheets"; // a todo app??

// If your imports read like a software catalog, you have Zawinski's Law.
```

## Feature Creep Warning Signs

| Signal | What It Means |
|---|---|
| "Since we're already doing X, let's also do Y" | Scope expansion disguised as efficiency |
| Feature matrix has more rows than competitors | Competing on breadth, not depth |
| New users are overwhelmed by settings | Product has lost its core identity |
| "It's basically a platform now" | Zawinski's Law has fully taken hold |
| Build time exceeds 10 minutes | Codebase has grown beyond its purpose |
| Onboarding takes more than a day | Feature surface area is unmanageable |

## Alternatives and Countermeasures

- **Unix philosophy:** Do one thing well. Compose tools via pipes and APIs.
- **Extension/plugin architecture:** Let others add features without bloating the core.
- **Product vision document:** Define what the product is NOT, not just what it is.
- **Feature budgets:** For every feature added, consider removing one.
- **Integration over incorporation:** Connect to specialized tools instead of rebuilding them.

## When NOT to Apply

- **Platforms that are supposed to be comprehensive:** Salesforce, SAP, and operating systems are meant to do everything. Zawinski's Law does not apply to intentional platforms.
- **Suites with synergy:** When features genuinely benefit from integration (e.g., a document editor with spreadsheets and presentations), expansion can be justified.
- **Survival:** Sometimes adding features is necessary to survive market competition, even if it is not elegant.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Stay focused, do one thing | Simple product, strong identity | May lose to feature-rich competitors |
| Add every requested feature | Captures more use cases | Product becomes bloated and confusing |
| Plugin/extension model | Core stays clean, ecosystem grows | Fragmented experience, plugin quality varies |
| Strategic feature expansion | Grows deliberately with market | Requires strong product discipline |

## Real-World Consequences

- **Emacs:** The canonical example. A text editor that has email, web browsing, a terminal, games, a psychiatrist, and a kitchen sink. (Users consider this a feature, not a bug.)
- **Slack:** Started as a chat app. Now has workflows, forms, canvases, huddles, clips, and channels that function as project management tools.
- **Jira:** Started as a bug tracker. Became project management. Then portfolio management. Then a platform. Now it requires consultants to configure.
- **Electron apps:** Each app bundles an entire browser, partly because web apps expanded to need desktop capabilities. The browser itself is a Zawinski's Law artifact.
- **Notion:** Notes, wikis, databases, project management, calendars — deliberately embracing Zawinski's Law as a product strategy.

## The Browser as Ultimate Example

Web browsers went from document viewers to:
- JavaScript runtime
- Application platform
- Video player
- PDF reader
- Payment processor
- Bluetooth controller
- File system accessor
- WebAssembly VM

The browser literally reads mail. Zawinski was prophetic.

## Further Reading

- Zawinski, J. — jwz.org (blog and writings)
- Raymond, E.S. (2003). *The Art of Unix Programming* — Unix philosophy as antidote
- Spolsky, J. (2001). "Strategy Letter IV: Bloatware and the 80/20 Myth"
- Krug, S. (2014). *Don't Make Me Think* — simplicity in product design
