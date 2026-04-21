# Subagent Dispatch for Multi-Domain Diffs

Fan out to per-domain specialists when one PR crosses 2+ domains (e.g., backend + UI, or MCP server + CLI). One body-writing subagent per domain cluster, combined into a single coherent review body by the parent agent.

## When to fan out

| Situation | Action |
|---|---|
| Diff touches 1 domain | Skip fan-out. Parent agent reads the one domain reference and writes the body. |
| Diff touches 2+ domains, each with ≥5% of changed lines | **Fan out.** One subagent per domain. |
| Diff touches 2+ domains but one is trivial (<5% of lines, or just a version bump) | Mention the trivial cluster inline in the main body. Do not fan out for it. |
| Diff is huge (>1500 lines or >30 files) even in a single domain | Consider splitting the PR before reviewing; don't paper over size with fan-out. |

## Per-subagent prompt template

Pass each subagent **only** the context it needs for its cluster. Do not forward session history. Borrowed from obra/superpowers/requesting-code-review: "the reviewer gets precisely crafted context — never your session's history."

```
You are reviewing the <DOMAIN> portion of a pull request. Your output will be combined with sibling reviews for other domains into one PR body.

## Scope
BASE_SHA: <sha>
HEAD_SHA: <sha>
Paths in your cluster (you do not review anything outside this list):
  <path/a.ts>
  <path/b.ts>
  <dir/**/*.sql>

## What to produce
A markdown block with these three sections, nothing else:

### <Domain> — what changed
<One paragraph on what this cluster of changes does, reading the diff as a proposal.>

### Weaknesses in this cluster
<List 1-3 weaknesses you would flag if you were the reviewer. Include file:line.>

### Questions for the reviewer
<List 1-2 questions the author should ask a reviewer with <domain> expertise.>

## Context you have
- Run `git diff BASE_SHA..HEAD_SHA -- <path list>` to read the cluster.
- Read `skills/request-code-review/skills/request-code-review/references/domains/<domain>.md` for the checklist.
- Do NOT read the full repo. Do NOT speculate on changes outside your cluster.
- Your output is one of N — do NOT write the overall summary, the Files touched table, the Follow-ups section, or the Verification section. The parent agent handles those.

## Constraints
- Output max 1500 characters. Heavily prefer evidence over prose.
- Cite file:line for every weakness.
- If you find nothing worth flagging, say so explicitly rather than padding.
```

## Combining subagent outputs

The parent agent receives N subagent outputs (one per domain). Combine them into the final review body as follows:

1. Write the **Summary** yourself, from the full diff — 2-4 sentences covering the overall intent. Do not let a subagent write this; they only see one cluster.
2. Write **Context / Why now** yourself from the user's prompt and any linked issue.
3. Under **The N items**, one subsection per domain with the subagent's "what changed" as the body of that subsection.
4. Under **Weaknesses and open questions**, merge the subagent weakness lists. Deduplicate. If two subagents flag the same concern from different angles, merge them into one item with cross-domain references.
5. Under **Request to the reviewer**, surface the subagent questions. Weave them into one or two paragraphs, not a bullet list per subagent.
6. Write **Follow-ups** yourself from the user's stated scope boundaries.
7. Run a final pass: the body must read as one voice, not N. Rewrite any phrasing that breaks consistency.

## Subagent type choice

- Use the Claude Code `Task` tool with `subagent_type: "general-purpose"` for most cases.
- Use `subagent_type: "Explore"` if the subagent also needs to search the wider repo to find context (e.g., call sites of a changed function).
- Do **not** use `Task` with `subagent_type: "code-reviewer"` or similar if available — this skill is author-side (preparing the handoff), not reviewer-side.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| One subagent reviews all domains | Defeats the point. One per cluster. |
| Subagent gets the full session history | Violates precise-context principle. Pass only BASE_SHA/HEAD_SHA/path-list/domain reference. |
| Combined body has one section per subagent with zero editing | Parent agent's job is to synthesize, not concatenate. Rewrite to one voice. |
| Fan out for 2-line cross-cutting changes | Overhead > value. Mention inline. |
| Subagents write the Summary or Verification sections | Those cover the full diff; subagents only see one slice. Parent writes them. |

## Edge cases

**Subagent returns empty weaknesses list.** Fine. Include the empty result — absence of findings is a real signal. Say "no weaknesses flagged for <domain>" in the body.

**Subagents contradict each other.** E.g., backend subagent says "the API shape matches the UI contract" and frontend subagent says "the UI call expects a different shape". Surface the contradiction explicitly in "Weaknesses and open questions" as a cross-cutting concern. Do not silently pick one.

**One subagent times out or errors.** Do not write the body without its section. Retry once with a tighter scope (fewer paths, shorter prompt). If it keeps failing, hand that domain off to the user and write the others — transparency beats fabrication.
