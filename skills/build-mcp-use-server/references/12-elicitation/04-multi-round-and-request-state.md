# Multi-Round and Request State

*Read this when building flows across multiple elicitation rounds or needing state integrity across re-entry.*

Elicitation flows can span multiple rounds. Each round re-runs your handler from the top; `ctx.inputResponses` carries only the responses fulfilled **for that round** — not an accumulated history. Use `inputResponse()`/`acceptedContent()` to read this round's answer for a given key, and `requestState` when trusted data (not just form input) must survive to the next round.

A single round can request **more than one key at once** — `inputRequests` is a map, and the client fulfills every key in it before re-calling your tool. There is no requirement to ask one field per round; batch related fields into one `inputRequests` object when they belong together.

## Two-round flow pattern

```typescript
import { acceptedContent, inputRequired, inputResponse, MCPServer } from "mcp-use";
import { z } from "zod";

const confirmationSchema = z.object({ confirm: z.boolean() });

export const deploy = server.tool(
  {
    name: "deploy",
    inputSchema: z.object({ environment: z.string() }),
    outputSchema: z.object({ environment: z.string(), deployed: z.boolean() }),
  },
  async ({ environment }, ctx) => {
    // Every round starts over — inspect this round's response before deciding
    // whether to ask again.
    const response = inputResponse(ctx.inputResponses, "confirm");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { content: [{ type: "text", text: `Deployment ${response.action}` }], isError: true };
    }

    const confirmation = acceptedContent(ctx.inputResponses, "confirm", confirmationSchema);

    // Initial and schema-invalid rounds both return input_required.
    if (confirmation === undefined) {
      return inputRequired({
        inputRequests: {
          confirm: inputRequired.elicit({
            message: `Deploy to ${environment}?`,
            requestedSchema: confirmationSchema,
          }),
        },
      });
    }
    if (confirmation.confirm !== true) {
      return { content: [{ type: "text", text: "Deployment not confirmed" }], isError: true };
    }

    // Side effects only after accepted, validated input.
    const result = { environment, deployed: true };
    return { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result };
  }
);
```

## Batching multiple fields in one round

```typescript
const projectSchema = z.object({ project: z.string() });
const regionSchema = z.object({ region: z.string() });

server.tool(
  { name: "batch-profile", inputSchema: z.object({}) },
  async (_params, ctx) => {
    // inputResponses contains only the requests fulfilled for this round —
    // read every batched key before deciding whether the flow stopped.
    const projectResponse = inputResponse(ctx.inputResponses, "project");
    const regionResponse = inputResponse(ctx.inputResponses, "region");
    const stopped = [projectResponse, regionResponse].find(
      (r) => r.kind === "elicit" && r.action !== "accept"
    );
    if (stopped?.kind === "elicit" && stopped.action !== "accept") {
      return { content: [{ type: "text", text: `Batch ${stopped.action}` }], isError: true };
    }

    const project = acceptedContent(ctx.inputResponses, "project", projectSchema);
    const region = acceptedContent(ctx.inputResponses, "region", regionSchema);

    // If either value is missing or invalid, request the complete batch again —
    // accepted values from this round are not implicit state for the next one.
    if (project === undefined || region === undefined) {
      return inputRequired({
        inputRequests: {
          project: inputRequired.elicit({ message: "Project name?", requestedSchema: projectSchema }),
          region: inputRequired.elicit({ message: "Deployment region?", requestedSchema: regionSchema }),
        },
      });
    }

    return { content: [{ type: "text", text: `Provision ${project.project} in ${region.region}` }] };
  }
);
```

Do **not** store intermediate state in module-level variables — the module is shared across every request, not scoped to one flow. Keep state in:
- The handler closure (local variables, this call only)
- `requestState` codec for signed round-trip data (see below)
- Backend database keyed by user identity

## Request state for integrity

`ctx.inputResponses` carries only what the client typed into a form — it is untrusted user input. Use `createRequestStateCodec<T>({ key, ttlSeconds })` to mint and verify server-signed state that survives across rounds without round-tripping through the client's control:

```typescript
import { createRequestStateCodec, MCPServer } from "mcp-use";

type DeployRequestState = { phase: "awaiting-confirmation"; environment: string };

const requestStateCodec = createRequestStateCodec<DeployRequestState>({
  key: new Uint8Array(32).fill(7), // 32-byte signing key; load from env, never hardcode
  ttlSeconds: 60,
});

const server = new MCPServer({
  name: "secure-server",
  version: "1.0.0",
  requestState: { verify: requestStateCodec.verify }, // object wrapper, not the bare function
});
```

Without a `requestState.verify` configured, `ctx.requestState<T>()` returns the raw, attacker-controlled wire string instead of a verified object — only rely on it once a verifier is wired in.

Mint state alongside an `inputRequired()` result, and decode it with `ctx.requestState<T>()` (called as a generic function, not `.parse()`):

```typescript
export const statefulDeploy = server.tool(
  { name: "stateful-deploy", inputSchema: z.object({ environment: z.string() }) },
  async ({ environment }, ctx) => {
    // Both channels are per-invocation: inputResponses answers this round,
    // while verified requestState carries trusted workflow data across rounds.
    const response = inputResponse(ctx.inputResponses, "stateful-confirm");
    const state = ctx.requestState<DeployRequestState>();

    if (response.kind === "elicit" && response.action !== "accept") {
      return { content: [{ type: "text", text: `Stateful deployment ${response.action}` }], isError: true };
    }

    if (state !== undefined && (state.phase !== "awaiting-confirmation" || state.environment !== environment)) {
      return { content: [{ type: "text", text: "Confirmation does not match deployment" }], isError: true };
    }

    const confirmation = acceptedContent(ctx.inputResponses, "stateful-confirm", confirmationSchema);

    if (state === undefined || confirmation === undefined) {
      return inputRequired({
        inputRequests: {
          "stateful-confirm": inputRequired.elicit({
            message: `Statefully deploy to ${environment}?`,
            requestedSchema: confirmationSchema,
          }),
        },
        requestState: await requestStateCodec.mint({ phase: "awaiting-confirmation", environment }),
      });
    }

    if (confirmation.confirm !== true) {
      return { content: [{ type: "text", text: "Stateful deployment not approved" }], isError: true };
    }

    // Side effects only after verified state and validated consent.
    return { content: [{ type: "text", text: `Statefully deployed ${environment}` }] };
  }
);
```

A tampered or expired `requestState` string fails verification and throws — catch it at the boundary rather than letting an unhandled rejection surface to the client.

## Multi-round rules

1. **Guard re-entry with the response, not a boolean:** Call `inputResponse(ctx.inputResponses, key)` and branch on `.kind`/`.action` — do not gate on `if (!ctx.inputResponses)` alone, since a batch round can carry responses for some keys and not others.
2. **Batch related fields:** One `inputRequests` object with multiple keys is answered together in one round — prefer batching over serial single-field rounds when fields are logically related (see batching example above).
3. **Exit early on decline/cancel:** After each round, check `.action !== "accept"` and return early — treat `decline` as an explicit refusal, distinct from `cancel` (dismissal).
4. **Embed prior answers:** Reference earlier responses in prompts so context is clear.
5. **Validate with `acceptedContent()`:** It applies the schema and returns `undefined` on any mismatch — don't hand-roll a second Zod `.parse()` over `ctx.inputResponses`.
6. **Use requestState for trusted data:** Anything that affects authorization or policy must be signed/verified with `createRequestStateCodec`, not trusted from `ctx.inputResponses` alone.
7. **Cap rounds:** Keep flows to 2-3 rounds for good completion rates.

## Sequential onboarding example (carrying data across non-batched rounds)

`ctx.inputResponses` holds only the current round's answers. When a later round needs data collected in an earlier round (rather than batching everything into one `inputRequests` object), carry it forward with `requestState` — do not assume `ctx.inputResponses` accumulates history:

```typescript
type OnboardState = {
  phase: "awaiting-preferences";
  name: string;
  email: string;
};

const basicsSchema = z.object({
  name: z.string().min(2).describe("Full name"),
  email: z.string().email().describe("Email"),
});
const prefsSchema = z.object({
  role: z.enum(["dev", "designer", "manager"]).describe("Your role"),
  newsletter: z.boolean().default(true).describe("Weekly updates?"),
});

const onboardStateKey = process.env.REQUEST_STATE_SECRET;
if (!onboardStateKey) throw new Error("REQUEST_STATE_SECRET is required");

const onboardStateCodec = createRequestStateCodec<OnboardState>({
  key: onboardStateKey, // >= 32 bytes/chars
  ttlSeconds: 300,
});
const onboardServer = new MCPServer({
  name: "onboarding-server",
  version: "1.0.0",
  requestState: { verify: onboardStateCodec.verify },
});

export const onboard = onboardServer.tool(
  { name: "onboard", inputSchema: z.object({}) },
  async (_params, ctx) => {
    // Read and branch on signed workflow state before inspecting a round-specific
    // response. A preferences retry does not contain the earlier basics response.
    const state = ctx.requestState<OnboardState>();

    if (state !== undefined) {
      if (state.phase !== "awaiting-preferences") {
        return { content: [{ type: "text", text: "Invalid onboarding phase." }], isError: true };
      }

      const prefsResponse = inputResponse(ctx.inputResponses, "prefs");
      if (prefsResponse.kind === "elicit" && prefsResponse.action !== "accept") {
        return { content: [{ type: "text", text: `Onboarding ${prefsResponse.action}` }], isError: true };
      }
      if (prefsResponse.kind === "sampling") {
        return { content: [{ type: "text", text: "Unexpected sampling response." }], isError: true };
      }

      const prefs = acceptedContent(ctx.inputResponses, "prefs", prefsSchema);
      if (prefs === undefined) {
        return inputRequired({
          inputRequests: { prefs: inputRequired.elicit({ message: "Preferences", requestedSchema: prefsSchema }) },
          requestState: await onboardStateCodec.mint(state),
        });
      }

      await createUser({ name: state.name, email: state.email, role: prefs.role, newsletter: prefs.newsletter });
      return {
        content: [{ type: "text", text: `Welcome, ${state.name}!` }],
        structuredContent: { userId: state.email, role: prefs.role },
      };
    }

    // No workflow state means round 1. A preferences response without its signed
    // phase is not allowed to fall back to the basics prompt.
    const unexpectedPrefs = inputResponse(ctx.inputResponses, "prefs");
    if (unexpectedPrefs.kind !== "missing") {
      return { content: [{ type: "text", text: "Onboarding state missing or expired; restart." }], isError: true };
    }

    const basicsResponse = inputResponse(ctx.inputResponses, "basics");
    if (basicsResponse.kind === "elicit" && basicsResponse.action !== "accept") {
      return { content: [{ type: "text", text: `Onboarding ${basicsResponse.action}` }], isError: true };
    }
    if (basicsResponse.kind === "sampling") {
      return { content: [{ type: "text", text: "Unexpected sampling response." }], isError: true };
    }

    const basics = acceptedContent(ctx.inputResponses, "basics", basicsSchema);
    if (basics === undefined) {
      return inputRequired({
        inputRequests: { basics: inputRequired.elicit({ message: "Tell us about you", requestedSchema: basicsSchema }) },
      });
    }

    // Basics were accepted this round. Carry them in signed state while asking
    // for preferences; the next invocation branches on this phase first.
    return inputRequired({
      inputRequests: { prefs: inputRequired.elicit({ message: "Preferences", requestedSchema: prefsSchema }) },
      requestState: await onboardStateCodec.mint({
        phase: "awaiting-preferences",
        name: basics.name,
        email: basics.email,
      }),
    });
  }
);
```

## Related

- Form mode schema design: `02-form-mode.md`
- URL mode for browser flows: `03-url-mode.md`
- Anti-patterns: `05-anti-patterns.md`
- Production state patterns: `../10-sessions/03-state-patterns-without-sessions.md`
