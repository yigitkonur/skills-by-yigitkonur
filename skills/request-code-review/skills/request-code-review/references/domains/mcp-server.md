# MCP Server Review

Author-side checklist for PRs touching an MCP (Model Context Protocol) server — tool/resource/prompt registration, transport choice, Zod schemas, session handling, SKILL.md authoring for MCP-paired skills. Use when classifying the diff's domain as **mcp-server** in SKILL.md Step 4.

## What MCP reviewers care about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Tool contract stability** | Once an agent learns a tool's shape, breaking it breaks every downstream skill | Additive-only changes; version flag if breaking |
| **Schema precision** | Loose schemas give ambiguous errors back to the agent | Zod schemas tight; descriptions on every field |
| **Error surface** | The tool's error is what the agent sees — it has no other context | Clear error messages; no stack traces; actionable in agent's loop |
| **Context window cost** | Tool results that are too verbose poison every future turn | Output size budgeted; pagination / filtering on large returns |
| **Idempotency** | Agents retry. Non-idempotent tools double-fire. | Retry-safe or explicit "this is not idempotent" in description |
| **Auth / scope** | MCP tools run with the user's permissions. One tool should not expand scope. | No privilege elevation in the tool body |
| **Transport correctness** | stdio vs. HTTP vs. Streamable HTTP each have traps | Transport choice justified; session handling matches transport |

## Weaknesses the author should pre-empt

- **Tool name and description.** The description is what the agent's router reads. Is it specific enough to not fire for adjacent queries? Does it name the exact tool name the agent will call?
- **Zod schema gaps.** Did you add `z.any()` anywhere? Every `any` is a future ambiguity. Tighten to union + discriminator, or document why `any` is required.
- **Return shape.** What does the tool return on success? On "no results"? On partial failure? The agent treats each differently — make them distinct.
- **Output size.** If the tool can return 50kB of data, is there a way to paginate or trim? Tool outputs consume context on every downstream call.
- **Session bleed.** If the server is Streamable HTTP or HTTP, state must be per-session, not global. Did you accidentally cache in a module-level variable?
- **Resource vs. tool.** Is this action a mutation (tool) or a read (resource)? Resources should be read-only; tools can mutate.
- **Prompt injection via tool results.** If the tool returns user-supplied data, can an attacker smuggle instructions through it? Sanitize or mark as untrusted.

## Questions to ask the reviewer explicitly

- "The new `search_issues` tool returns up to 50 results by default. Is that right for the context-budget discipline this server follows, or should it be lower?"
- "Zod schema for the `filter` arg uses `z.record(z.string(), z.unknown())`. I want structured filters but can't fully enumerate. Is the looser schema acceptable?"
- "I chose a tool (mutation) over a resource (read-only) because the operation touches the DB. Is the line right?"
- "Server is stdio-transport for local use and Streamable HTTP for remote. Session handling is in `session/store.ts` — please verify the per-session state isolation."
- "Tool errors return `ApplicationError` with a `code` field. Is that shape what the agents in this ecosystem expect, or should it match a different convention?"

## What to verify before opening the PR

- [ ] MCP inspector (`@modelcontextprotocol/inspector`) connects to the server
- [ ] Every tool can be invoked via the inspector with a valid payload
- [ ] Every tool returns a well-formed error for a bad payload (missing required field, wrong type)
- [ ] Tool descriptions are copy-pasted into the inspector's tool-list — confirm they read correctly to a fresh reader
- [ ] If the server has sessions: open two inspector tabs, verify no state bleed
- [ ] If Streamable HTTP: verify CORS/auth gates if deployed remotely
- [ ] SKILL.md (if paired) references the actual current tool names, not stale ones

## Signals the review is off-track

- "I'll document the tool later." → The description IS the documentation for the agent. Write it now.
- "Zod schema is loose but it works." → Loose schemas become runtime bugs at the worst possible time.
- "The tool returns a lot of data but the agent can trim it." → Agents don't trim well. Trim at the tool boundary.
- "One tool both reads and writes for simplicity." → Two tools. Resources for reads, tools for writes.

## When to split the PR

- New tool + unrelated transport refactor → split
- New tool + schema-library migration (Zod v3 → v4) → split
- Multiple new tools that aren't related to one user intent → consider splitting

## MCP-specific follow-up skills

If the server uses a specific framework, route additionally:

| Framework | Skill |
|---|---|
| Bare `@modelcontextprotocol/sdk` v1.x | `build-mcp-sdk` |
| `@modelcontextprotocol/server` v2 | `build-mcp-sdk-v2` |
| `mcp-use` (server side) | `build-mcp-use-server` |
| `mcp-use` with React widgets | `build-mcp-use-apps-widgets` |
| Optimizing an existing server | `optimize-mcp-server` |

Name the specific framework in your PR body so the reviewer pulls the right context.
