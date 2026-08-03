# Workflow: Elicitation with InputRequired Re-Entry

*Read this for an end-to-end workflow: return input_required, accept host input, and finish on handler re-entry.*

> Documented but not shipped in 2.0.0-beta.66 — verify against your installed version.

`ctx.elicit()` appears in v2 documentation but is absent from the shipped beta.66 context type. The shipped model uses `inputRequired.elicit()` to return an `InputRequiredResult`; the host collects input and calls the tool again with `ctx.inputResponses`.

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 confirmation-server --template blank --npm --install
cd confirmation-server
```

**Verify:** `index.ts` exports a blank MCPServer.

### 2. Add a Request-State Verifier

When the state affects authorization or business logic, configure a request-state codec. Use the exact codec signature documented in `../12-elicitation/04-multi-round-and-request-state.md` for the installed v2 package.

```typescript
import { MCPServer, createRequestStateCodec, inputRequired } from "mcp-use";
import { z } from "zod";

const requestStateCodec = createRequestStateCodec({
  key: process.env.REQUEST_STATE_SECRET!, // string or Uint8Array, >= 32 bytes/chars
  ttlSeconds: 60,
});

const server = new MCPServer({
  name: "confirmation-server",
  version: "1.0.0",
  requestState: { verify: requestStateCodec.verify }, // object wrapper, not the bare function
});
```

**Verify:** `REQUEST_STATE_SECRET` is set and `npm run typecheck` accepts the codec for the installed version.

### 3. Return an Input-Required Result

Add a tool whose first invocation requests confirmation and whose second invocation reads `ctx.inputResponses`:

```typescript
import { acceptedContent, inputRequired, inputResponse } from "mcp-use";

const confirmSchema = z.object({ confirmed: z.boolean().describe("Confirm deletion") });

export const deleteRecord = server.tool(
  {
    name: "delete-record",
    description: "Delete a record after explicit confirmation",
    inputSchema: z.object({
      recordId: z.string().describe("Record identifier"),
    }),
  },
  async ({ recordId }, ctx) => {
    // Every round starts the handler over from the top — check this round's
    // response before deciding whether to ask again.
    const response = inputResponse(ctx.inputResponses, "confirmDelete");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { content: [{ type: "text", text: `Deletion of ${recordId} ${response.action}` }], isError: true };
    }

    const confirmed = acceptedContent(ctx.inputResponses, "confirmDelete", confirmSchema);

    // Initial and schema-invalid rounds both return input_required.
    if (confirmed === undefined) {
      return inputRequired({
        inputRequests: {
          confirmDelete: inputRequired.elicit({
            message: `Delete record ${recordId}?`,
            requestedSchema: confirmSchema,
          }),
        },
        requestState: await requestStateCodec.mint({ recordId }),
      });
    }

    if (!confirmed.confirmed) {
      return {
        content: [{ type: "text", text: `Deletion of ${recordId} cancelled` }],
      };
    }

    // Perform the irreversible operation only after validated confirmation.
    return {
      content: [{ type: "text", text: `Deleted ${recordId}` }],
    };
  }
);

export default server;
```

Never call `server.listen()` here — the CLI (`mcp-use dev`/`mcp-use start`) owns the listener.

**Verify:** `npm run typecheck` passes against an installed version that ships the helper signature shown by `../12-elicitation/01-overview.md`.

### 4. Run the First Round

```bash
REQUEST_STATE_SECRET=replace-with-a-long-random-secret npm run dev
```

In Inspector, call `delete-record` with `{"recordId":"record-123"}`.

**Verify:** The tool does not delete anything. It returns an `input_required` result asking for `confirmed`.

### 5. Complete the Host Form

Accept the prompt and submit `{"confirmed":true}`.

**Verify:** The host re-runs `delete-record` with the original tool arguments and a verified `requestState`; `inputResponse(ctx.inputResponses, "confirmDelete")` resolves to an accepted `{ confirmed: true }` response.

### 6. Verify Final Outcomes

Repeat the workflow twice:

1. submit `confirmed: true`
2. submit `confirmed: false`

**Verify:** The true path performs the operation once; the false path returns a cancellation result and performs no operation.

## Re-Entry Invariant

The handler starts from the top on every round. Never expect a suspended stack frame or in-memory continuation. Persist or encode only the minimum state needed to resume, validate `ctx.inputResponses`, and make the final side effect idempotent.

Read `../12-elicitation/01-overview.md` before adapting this recipe, then use `../12-elicitation/02-form-mode.md` for flat-schema constraints.
