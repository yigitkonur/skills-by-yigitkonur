# Diagram Builder Example

*Read this when you need multiple related tools and multi-step workflows.*

## Overview

Diagram Builder is an **external template-gallery app** — a standalone repo outside the `mcp-use/mcp-use` monorepo, listed on the marketing site's Templates page. It is not one of the canonical in-repo examples under `libraries/typescript/packages/server/examples/`; see `references/31-canonical-examples/00-how-to-use-this-cluster.md` for that distinction. The metadata below (demo URL, GitHub repo, tool names) is verified against `docs/home/templates.mdx`. Its source is not part of the monorepo and was not available to verify line-for-line, so the code sample is illustrative of the pattern, not a quote from the repo — clone it and read the real source before copying anything from it.

**What it does:** Users create a diagram via `create-diagram`, then refine it via `edit-diagram`. Each tool returns structured output for an MCP App view.

## Live endpoints

| Resource | URL |
|----------|-----|
| **Demo endpoint** | `https://lucky-darkness-402ph.run.mcp-use.com/mcp` |
| **GitHub source** | [mcp-use/mcp-diagram-builder](https://github.com/mcp-use/mcp-diagram-builder) |
| **One-click deploy** | [Deploy on Manufact](https://mcp-use.com/deploy/start?repository-url=https%3A%2F%2Fgithub.com%2Fmcp-use%2Fmcp-diagram-builder&branch=main&project-name=mcp-diagram-builder&port=3000&runtime=node) |

## Connect in Inspector

1. Open [Inspector](/inspector/index).
2. Click **Direct transport**.
3. Paste: `https://lucky-darkness-402ph.run.mcp-use.com/mcp`
4. Open **Tools** → call `create-diagram` with a description (e.g., "flowchart for login flow")
5. Call `edit-diagram` to modify the result
6. View renders both operations in the diagram editor.

## Pattern this illustrates (verified against real v2 API surface, not this repo's source)

Two view-bound tools sharing one view name, matching the shape documented in `references/04-tools/canonical-anchor.md`:

```typescript
export const createDiagram = server.tool(
  {
    name: "create-diagram",
    description: "Create a new diagram from a natural language description",
    inputSchema: z.object({
      description: z.string().describe("Diagram description, e.g. 'flowchart of user signup'"),
    }),
    outputSchema: diagramSchema,
    view: { name: "diagram-editor" },
  },
  async ({ description }, ctx) => {
    const diagram = await generateDiagram(description);
    return {
      content: [{ type: "text", text: `Diagram created: ${diagram.title}` }],
      structuredContent: diagram,
    };
  }
);

export const editDiagram = server.tool(
  {
    name: "edit-diagram",
    description: "Edit an existing diagram",
    inputSchema: z.object({
      diagramId: z.string().describe("Diagram ID from create-diagram"),
      instructions: z.string().describe("What to change"),
    }),
    outputSchema: diagramSchema,
    view: { name: "diagram-editor" },
  },
  async ({ diagramId, instructions }, ctx) => {
    const diagram = await applyDiagramEdit(diagramId, instructions);
    return {
      content: [{ type: "text", text: "Diagram updated" }],
      structuredContent: diagram,
    };
  }
);
```

The view side reads tool output with the real hooks — `useToolContext` for the bound tool's own result, `useCallTool` to invoke a different tool from inside the view (`useWidget` is not exported by `mcp-use/react`; the shipped exports are enumerated in `references/18-mcp-apps/view-react/02-usetoolcontext.md` and `references/18-mcp-apps/view-react/03-usecalltool.md`):

```tsx
import { useCallTool, useToolContext } from "mcp-use/react";

export default function DiagramEditor() {
  const view = useToolContext<"create-diagram">();
  const editDiagram = useCallTool("edit-diagram"); // returns { callTool, data, error, isPending }

  const handleEdit = (instructions: string) => {
    if (view.status === "result") {
      editDiagram.callTool({ diagramId: view.toolOutput.id, instructions });
    }
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
# Prints a dashboard URL — copy the generated MCP endpoint from the
# dashboard rather than assuming a *.run.mcp-use.com slug.
```
