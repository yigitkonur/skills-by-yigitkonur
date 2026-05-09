# audit-rhythm — Explore → Diagnose → Present → Optimize

The disciplined audit rhythm. Pattern-fitting before exploration generates worse advice than no advice — that's why this rhythm is non-negotiable for every Mode-A audit, on either surface. Read the user's actual code first, classify findings, present them one at a time with options, then optimize after the user picks. Don't dump 30 recommendations as a wall.

## The 4 phases

### Phase 1 — Explore (read the code, the help text, the call traces)

Before asking the user a single question, read what's already there. Generic questions waste the user's time; specific questions cite file paths and line numbers.

**For a CLI audit, read in this order:**

1. `bin/` entrypoint(s) — find the command parser (Cobra, Click, Yargs, Commander, plain argparse).
2. The flag and subcommand registry — find where `--json`, `--quiet`, `--yes`, `--dry-run` are (or aren't) declared.
3. Output formatters — find how stdout vs. stderr is split; whether there's a JSON envelope; whether errors print to stdout.
4. Error handlers — find the exit-code mapping (or absence thereof); whether there's a retry-safe / permanent classifier.
5. Auth code — find env-var lookups, TTY detection, sandbox boundaries; whether there's a non-interactive mode.
6. Help text — read every `--help` page as the agent will read it.

```bash
# CLI exploration commands — adapt to language
tree . -I 'node_modules|dist|target|build' --dirsfirst -L 3
rg -n "json\\.Marshal|json\\.dumps|JSON\\.stringify|fmt\\.Println" -g '!node_modules' -g '!dist'
rg -n "os\\.Exit|sys\\.exit|process\\.exit" -g '!node_modules'
rg -n "fmt\\.Fprintln\\(os\\.Stdout|console\\.log|print\\(" -g '!node_modules'
rg -n "os\\.Stdin\\.IsTerminal|isatty|process\\.stdin\\.isTTY"
```

**For an MCP audit, read in this order:**

1. Manifest (`package.json`, `pyproject.toml`) — find the SDK version (v1 or v2), entry point, transport.
2. Server entry — find `McpServer`, `FastMCP`, `Server()` instantiation; transport choice (stdio vs. Streamable HTTP).
3. Tool registrations — find every `server.tool` / `@tool` / `registerTool` call; count them.
4. Schemas — find the input schemas (Zod, Pydantic, JSONSchema); check depth and required fields.
5. Error handling — find whether errors use `isError: true` in result content vs. JSON-RPC protocol errors.
6. Auth code — find OAuth wiring, token verification, scope checks.

```bash
# MCP exploration commands
tree . -I node_modules --dirsfirst -L 3
rg -n -l "McpServer|FastMCP|server\\.tool|@tool|@mcp\\.tool|registerTool|Server\\(" . -g '!node_modules'
rg -n "server\\.tool|@tool|registerTool|def .*tool|tool\\(" . -g '!node_modules'
rg -n -l "z\\.|inputSchema|BaseModel|Field\\(|pydantic|jsonschema" . -g '!node_modules'
rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
rg -n "isError|JSONRPCError|McpError" . -g '!node_modules'
```

**Prerequisite check.** If nothing tool-shaped exists after searching repo root and the usual server/CLI directories, stop and report the missing prerequisite. Don't invent a tool just to keep going. If the user actually wants a new tool, switch to Mode B (`design-thinking.md` → architect-new files).

If multiple tools / servers / CLIs exist in one repo, stop and ask which is in scope. Don't blend findings across tools — the audit becomes incoherent.

**If call traces are available**, read them. The agent's actual call patterns reveal which tools it picks, which it avoids, which it loops on. Production logs beat hypotheticals.

### Phase 2 — Diagnose (list, classify, do not fix yet)

Produce a list of findings tied to specific files and lines. Classify each. Don't apply anything; just enumerate.

**Finding format:**

```
### Finding [N]: [Title]
Dimension: [description-quality | schema-quality | error-quality | output-noise |
            missing-iterative | tool-count | response-shape | auth-flakiness | ...]
Severity: Critical / High / Medium / Low
File(s): path/to/file.ts:line, path/to/other.ts:line

Current state: [the user's actual code snippet — short, exact, quoted]
Issue: [why it's suboptimal — reference the principle and the common/ file]
Evidence: [what you observed — call trace, --help output, schema dump, log line]
```

**Common dimensions across surfaces:**

| Dimension | What's wrong | Common/ reference |
|---|---|---|
| description-quality | Tool description / `--help` is human-doc, not LLM-prompt | `descriptions-as-prompts.md` |
| schema-quality | Deeply nested schema; unused params; ambiguous types | (CLI) `../cli/flags-and-discovery.md`, (MCP) `../mcp/patterns/schema-design.md` |
| error-quality | Errors not retry-safe; no `next_action`; protocol errors for business logic | `error-strategy.md` |
| output-noise | Raw API JSON dumped; stdout/stderr blended; no envelope | `output-contracts.md` |
| missing-iterative | Long-running workflow with no `phase` / `next_action` | `iterative-loops.md` |
| tool-count | 30+ tools in a flat namespace | (MCP) `agent-cognitive-load.md` + `../mcp/decision-trees/tool-count.md` |
| response-shape | No `schema_version`; field renames across releases | `output-contracts.md` |
| auth-flakiness | Manual token paste; no refresh; no headless mode | (CLI) `../cli/auth-headless.md`, (MCP) `../mcp/patterns/auth-identity.md` |

Severity rubric:

- **Critical** — agent cannot use the tool at all (broken parsing, infinite loop, hard crash on common input).
- **High** — agent succeeds sometimes but fails on retry, picks wrong tool, or wastes 5×+ tokens on noise.
- **Medium** — usability friction; agent works but takes more turns than needed.
- **Low** — nit; would polish the contract but doesn't change agent success rate.

Thresholds in reference docs (tool count, parameter count, latency, token budgets) are diagnostic cues, not verdicts. Cite them; don't weaponize them.

### Phase 3 — Present (one finding at a time, with options)

Surface findings one at a time, in severity order. Don't dump 30 at once — that's a wall the user can't act on. Each finding is presented as a question with a recommendation and explicit alternatives.

**Presentation format:**

```
### Finding [N]: [Title]
Dimension: [category]   Severity: [Critical / High / Medium / Low]
File(s): path/to/file.ts:line

Current state: [their actual code]
Issue: [why it's suboptimal]
Options:
  - A (recommended): [description + tradeoff]
  - B: [description + tradeoff]
  - C (minimal change): [description + tradeoff]
Should I apply this? (yes / no / show me option X first)
```

Wait for the user's decision before moving on. Don't queue up the next finding until this one is resolved.

**If the user is unavailable for follow-up**, switch to **draft mode**: surface the full prioritized finding set with explicit assumptions, but do not apply anything. Label every assumption. Mark draft mode explicitly so the user knows nothing has been changed.

### Phase 4 — Optimize (apply one fix, verify, repeat)

After the user picks a fix, apply it. Show the diff first, explain the change, make the edit, then suggest a verification step.

**Verification rungs (always claim the rung you actually reached, not the one you'd like to claim):**

| Rung | Claim |
|---|---|
| 1 | Read the code |
| 2 | Type-check / lint passes |
| 3 | Unit test passes (if a test exists or was added) |
| 4 | Integration test passes (CLI: subprocess wrapper test; MCP: `mcpc` against the live server) |
| 5 | Ran the program / hit the endpoint / observed the change |
| 6 | User confirmed the changed behavior |

For CLI fixes, common verification commands:

```bash
mycli command --json --dry-run               # exit code, schema_version, no side effects
mycli command --json 2>/dev/null | jq .ok    # exit code + JSON well-formed
echo "" | mycli interactive-cmd --yes        # non-interactive doesn't hang
mycli nonexistent-resource                   # exit code = 3 (not_found)
```

For MCP fixes, common verification commands:

```bash
npx -y @modelcontextprotocol/inspector       # local inspector, sanity-check tool/list output
mcpc list-tools <transport>                  # re-list tools
mcpc call-tool <transport> <tool> '<args>'   # exercise a single tool
```

Move to the next finding once the verification rung is reached and reported honestly.

## Worked example: CLI audit rhythm

User says: "Audit our `deploy` CLI for agent readiness."

**Phase 1 — Explore.**
Read `bin/deploy.go` (Cobra entrypoint). Read `cmd/deploy/apply.go` (the most-used subcommand). Note: `--json` flag exists but `apply.go` uses `fmt.Println("Deployed!")` mid-flow, blending stdout. Note: `os.Exit(1)` for every failure path. Note: `--help` lists 14 subcommands, no usage examples.

**Phase 2 — Diagnose.**

| # | Finding | Dimension | Severity |
|---|---|---|---|
| 1 | `apply.go:87` writes "Deployed!" to stdout, polluting JSON envelope | output-noise | Critical |
| 2 | All errors exit `1` regardless of class | error-quality | Critical |
| 3 | `--help` has no examples; agent has nothing to anchor on | description-quality | High |
| 4 | `--json` flag exists but `apply` doesn't honor it | output-noise | High |
| 5 | `auth login` blocks on prompt without `--yes` | auth-flakiness | High |
| 6 | No `schema_version` on the JSON envelope when it does emit | response-shape | Medium |

**Phase 3 — Present.**

```
### Finding 1: stdout/stderr pollution in apply.go
Dimension: output-noise   Severity: Critical
File: cmd/deploy/apply.go:87

Current state:
  fmt.Println("Deployed!")    // line 87, mid-flow

Issue: agents parsing --json output get "Deployed!" before the JSON envelope, breaking
JSON.parse. Per output-contracts.md: stdout = data only, progress = stderr.

Options:
  - A (recommended): replace with fmt.Fprintln(os.Stderr, "Deployed!")
  - B: gate behind a !jsonFlag check so non-JSON mode keeps the human message
  - C (minimal change): drop the line; leave success implicit in exit code

Should I apply Option A? (yes / no / show diff)
```

User picks A. Apply Option A. Verify: `mycli deploy apply --json | jq .ok` — exit 0, JSON parses. Move to finding 2.

## Worked example: MCP audit rhythm

User says: "Audit our customer-mcp server."

**Phase 1 — Explore.**
Repo has 14 tools registered in `packages/customer-mcp/tools/`. `search.ts` has a 14-param schema with nested `filters.dateRange.start` and `filters.dateRange.end`. `errors.ts` throws `JSONRPCError` for "user not found." Server uses stdio transport. No `instructions` field on the server.

**Phase 2 — Diagnose.**

| # | Finding | Dimension | Severity |
|---|---|---|---|
| 1 | `search.ts:42` 14-param schema with nested filters; LLM frequently misformats | schema-quality | Critical |
| 2 | `errors.ts:18` throws JSON-RPC protocol error for business "not found" — agent never sees the message | error-quality | Critical |
| 3 | No `instructions` field on the server | description-quality | High |
| 4 | 14 tools but `list_users` returns `avatarUrl`, `isAdmin`, `isGuest` (raw API noise) | output-noise | High |
| 5 | All response payloads stringify JSON in `content[].text`; no `structuredContent` | response-shape | Medium |

**Phase 3 — Present.** (One at a time, severity order. Stop after Finding 1 until the user picks.)

```
### Finding 1: 14-param nested schema in search.ts
Dimension: schema-quality   Severity: Critical
File: packages/customer-mcp/tools/search.ts:42

Current state:
  inputSchema: z.object({
    query: z.string(),
    filters: z.object({
      dateRange: z.object({ start: z.string(), end: z.string() }),
      tags: z.array(z.string()),
      ...
    }),
    ...
  })

Issue: LLMs reliably emit flat JSON; nested filter objects produce schema validation
failures across all major models. Per ../mcp/patterns/schema-design.md: flatten to
≤6 top-level params.

Options:
  - A (recommended): flatten to flat top-level (query, date_after, date_before, tag, ...)
  - B: keep filters wrapper but flatten dateRange (one level of nesting)
  - C (minimal change): leave schema; document failure pattern in description

Should I apply Option A? (yes / no / show diff)
```

User picks B. Apply B. Verify with `mcpc call-tool ./server search '{"query":"acme","date_after":"2026-01-01"}'` — should succeed without schema error. Move to finding 2.

## Anti-patterns that violate the rhythm

**Pattern-fitting before exploration.**
Looking at the user's repo for two minutes and concluding "the CLI should add `--json`" without checking whether they already have it (they often do; it's just broken). Read the code first.

**Batch-recommending.**
Listing 12 findings as bullet points without giving the user a way to engage with one at a time. The user's attention is the bottleneck, not the finding count.

**Fixing-without-asking.**
Editing the user's code as soon as you see a problem. Mode A is a discussion, not an autopilot. Apply only after explicit approval.

**Generic questions instead of specific ones.**
"What does the tool do?" is a generic question. "In `tools/search.ts:42`, the schema has 14 parameters including `filters.dateRange.start` — are all 14 used, or are most optional?" is a specific question. Spec specifically.

**Skipping the verification rung.**
Saying "Done, this is fixed" without running the binary or hitting the endpoint. Claim the rung you actually reached. Type-check passes is not the same as integration test passes is not the same as observed behavior.

**Blending findings across multiple servers / CLIs.**
If the repo has three CLIs and you find issues in two of them, stop and ask which one is in scope. Don't write a single audit document that mixes evidence from different tools.

**Assuming thresholds are verdicts.**
"Tool count is 22, that's too many" — no. Tool count is a diagnostic cue. Ask whether the count is justified by the workload (per `agent-cognitive-load.md`). Cloudflare ships 2 tools; GitHub ships 56+; both are correct for their workloads.

## Cross-references

- For Mode B (designing a new tool from scratch), use `design-thinking.md` instead.
- For surface-specific audit checklists, route to `../cli/audit-checklist.md` (the 5-check entry) or `../mcp/audit-existing.md`.
- For the principles each finding maps to, route to the named common/ file in the diagnose table.
- For verification commands beyond the basics, see `../cli/subprocess-harness.md` (CLI) or `../mcp/patterns/testing.md` (MCP).
