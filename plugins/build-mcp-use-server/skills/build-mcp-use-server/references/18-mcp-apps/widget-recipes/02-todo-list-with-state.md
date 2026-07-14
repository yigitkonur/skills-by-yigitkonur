# Recipe 02 — Todo List With Persistent State

**What it demonstrates:** persistent state via `setState`, local CRUD without round-tripping the server, follow-up message after a meaningful change.

Synthesized from the kanban-board recipe pattern; adapted to the simpler todo shape so the persistence loop is the focus.

## File layout

```
resources/todo-list/
└── widget.tsx
src/tools/todos.ts
```

## Server tool — `src/tools/todos.ts`

```typescript
import { widget, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerTodoTools(server: MCPServer) {
  server.tool(
    {
      name: "show-todos",
      description: "Display a todo list for a project",
      schema: z.object({
        project: z.string().describe("Project name"),
      }),
      widget: {
        name: "todo-list",
        invoking: "Loading todos...",
        invoked: "Todos ready",
      },
    },
    async ({ project }) => {
      const todos = [
        { id: "1", title: "Write spec", done: true },
        { id: "2", title: "Review PR feedback", done: false },
        { id: "3", title: "Ship release", done: false },
      ];
      return widget({
        props: { project, todos },
        message: `Loaded ${todos.length} todos for ${project}`,
      });
    }
  );

  server.tool(
    {
      name: "persist-todos",
      description: "Persist a todo list to the backing store",
      schema: z.object({
        project: z.string(),
        todos: z.array(z.object({
          id: z.string(),
          title: z.string(),
          done: z.boolean(),
        })),
      }),
    },
    async ({ project, todos }) => {
      // Replace with real DB write
      return object({ project, count: todos.length, persisted: true });
    }
  );
}
```

## Widget — `resources/todo-list/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Editable todo list with persistent widget state and follow-up messages",
  props: z.object({
    project: z.string(),
    todos: z.array(z.object({
      id: z.string(),
      title: z.string(),
      done: z.boolean(),
    })),
  }),
  metadata: { prefersBorder: true },
};

interface Todo {
  id: string;
  title: string;
  done: boolean;
}

interface TodoProps {
  project: string;
  todos: Todo[];
}

interface TodoState {
  todos: Todo[];
}

function TodoContent() {
  const { props, isPending, theme, state, setState, sendFollowUpMessage } =
    useWidget<TodoProps, TodoState>();
  const { callTool: persist } = useCallTool("persist-todos");

  const [draft, setDraft] = useState("");
  const isDark = theme === "dark";
  const todos = state?.todos ?? props.todos ?? [];

  if (isPending) {
    return (
      <div className="p-6 animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className={`h-10 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
        ))}
      </div>
    );
  }

  const updateTodos = async (next: Todo[]) => {
    await setState({ todos: next });
    persist({ project: props.project, todos: next });
  };

  const addTodo = () => {
    if (!draft.trim()) return;
    const newTodo: Todo = { id: crypto.randomUUID(), title: draft.trim(), done: false };
    updateTodos([...todos, newTodo]);
    setDraft("");
  };

  const toggleTodo = (id: string) => {
    updateTodos(todos.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));
  };

  const removeTodo = (id: string) => {
    updateTodos(todos.filter((t) => t.id !== id));
  };

  const completed = todos.filter((t) => t.done).length;
  const allDone = completed === todos.length && todos.length > 0;

  return (
    <div className={`p-6 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">{props.project}</h2>
        <span className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>
          {completed}/{todos.length} done
        </span>
      </div>

      <div className="flex gap-2 mb-4">
        <input
          className={`flex-1 px-3 py-2 rounded border text-sm ${isDark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-300"}`}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addTodo()}
          placeholder="Add a todo..."
        />
        <button onClick={addTodo} className="px-3 py-2 bg-blue-500 text-white rounded text-sm">
          Add
        </button>
      </div>

      <ul className="space-y-2">
        {todos.map((todo) => (
          <li
            key={todo.id}
            className={`flex items-center gap-3 p-2 rounded ${isDark ? "hover:bg-gray-800" : "hover:bg-gray-50"}`}
          >
            <input
              type="checkbox"
              checked={todo.done}
              onChange={() => toggleTodo(todo.id)}
              className="w-4 h-4"
            />
            <span className={`flex-1 text-sm ${todo.done ? "line-through opacity-50" : ""}`}>
              {todo.title}
            </span>
            <button
              onClick={() => removeTodo(todo.id)}
              className={`text-xs ${isDark ? "text-gray-500 hover:text-red-400" : "text-gray-400 hover:text-red-500"}`}
            >
              ✕
            </button>
          </li>
        ))}
      </ul>

      {allDone && (
        <button
          onClick={() => sendFollowUpMessage(`All todos for ${props.project} are done. What should I work on next?`)}
          className="mt-4 w-full py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
        >
          All done — ask for the next thing →
        </button>
      )}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <TodoContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Persistent state | `useWidget<TodoProps, TodoState>()` plus `setState({ todos })` — survives re-renders and re-hydrations |
| Local CRUD without server round-trip | `updateTodos` calls `setState` first, then a fire-and-forget `persist` tool |
| `state ?? props` fallback | First render reads from `props`, subsequent renders read from `state` |
| Follow-up message | `sendFollowUpMessage` after a meaningful state change (all done) |
| Local-only UI state | `useState(draft)` — input value never leaves the widget |
