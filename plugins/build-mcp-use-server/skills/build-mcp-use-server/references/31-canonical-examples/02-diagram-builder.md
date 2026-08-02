# Diagram Builder Example

*Read this when you need multiple related tools and multi-step workflows.*

## Overview

The Diagram Builder example shows how to implement related tools (`create-diagram`, `edit-diagram`) that work together to create and modify diagrams interactively.

**What it does:** Users create a diagram via `create-diagram`, then refine it via `edit-diagram`. Each tool returns structured output for an MCP App view.

**Key files:**
- `index.ts` — Server with `create-diagram` and `edit-diagram` tools
- `views/diagram-editor/view.tsx` — React view with state management for live editing
- `.mcp-use/build/` — Compiled output

## Live endpoints

| Resource | URL |
|----------|-----|
| **Demo endpoint** | `https://lucky-darkness-402ph.run.mcp-use.com/mcp` |
| **GitHub source** | [mcp-use/mcp-diagram-builder](https://github.com/mcp-use/mcp-diagram-builder) |

## Connect in Inspector

1. Open [Inspector](/inspector/index).
2. Click **Direct transport**.
3. Paste: `https://lucky-darkness-402ph.run.mcp-use.com/mcp`
4. Open **Tools** → call `create-diagram` with a description (e.g., "flowchart for login flow")
5. Call `edit-diagram` to modify the result
6. View renders both operations in the diagram editor.

## Key patterns

**Multi-tool registration:**
```typescript
export const createDiagram = server.tool(
  {
    name: "create-diagram",
    description: "Create a new diagram from natural language description",
    inputSchema: z.object({
      description: z.string().describe("Diagram description, e.g. 'flowchart of user signup'")
    }),
    outputSchema: diagramSchema,
    view: { name: "diagram-editor" }
  },
  async ({ description }, ctx) => {
    const diagram = await generateDiagram(description);
    return {
      content: [{ type: "text", text: `Diagram created: ${diagram.title}` }],
      structuredContent: diagram
    };
  }
);

export const editDiagram = server.tool(
  {
    name: "edit-diagram",
    description: "Edit an existing diagram",
    inputSchema: z.object({
      diagramId: z.string().describe("Diagram ID from create-diagram"),
      instructions: z.string().describe("What to change")
    }),
    outputSchema: diagramSchema,
    view: { name: "diagram-editor" }
  },
  async ({ diagramId, instructions }, ctx) => {
    const diagram = await editDiagram(diagramId, instructions);
    return {
      content: [{ type: "text", text: `Diagram updated` }],
      structuredContent: diagram
    };
  }
);
```

**React view with state:**
```tsx
import { useWidget, useCallTool } from "mcp-use/react";

export default function DiagramEditor() {
  const { props } = useWidget<DiagramData>();
  const { callTool } = useCallTool("edit-diagram");

  const handleEdit = (instructions: string) => {
    callTool({ diagramId: props.id, instructions });
  };

  return (
    <div>
      {/* SVG or canvas diagram rendering */}
      <button onClick={() => handleEdit("add new node")}>Edit</button>
    </div>
  );
}
```

## Clone and customize

```bash
git clone https://github.com/mcp-use/mcp-diagram-builder
cd mcp-diagram-builder
npm install
npm run dev
```

## Deploy

```bash
npm run deploy
```
