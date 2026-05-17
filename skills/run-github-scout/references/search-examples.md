# Adaptive Search Examples

Each example shows a small first pass, what the results revealed, and
one refinement (or a recovery, if the first pass derailed). The
three-phase shape is intentional: real sessions almost never
land cleanly on the first pass.

## Example 1: Self-hosted Notion alternative

**Need:** collaborative self-hosted docs or knowledge base.

**First pass (4 angles)**

```bash
gh search repos 'notion alternative fork:false archived:false' --limit 20 --sort=stars
gh search repos 'self-hosted wiki fork:false archived:false' --limit 20 --sort=stars
gh search repos 'outline OR affine fork:false archived:false' --limit 20 --sort=stars
gh search repos 'block editor collaborative docs fork:false archived:false' --limit 20 --sort=stars
```

**Observed shape**

- Repo wording in the relevant set: `knowledge base`, `wiki`,
  `collaborative docs`, `workspace`.
- Likely category leaders dominate: AppFlowy, Outline, Affine, Anytype.
- Two of the four angles surface adjacent (notes-only) repos that are
  not collaborative — useful as Maybes.

**Refinement (2 angles, harvested vocabulary)**

```bash
gh search repos 'knowledge base self-hosted fork:false archived:false' --limit 20 --sort=stars
gh search repos 'collaborative wiki self-hosted fork:false archived:false' --limit 20 --sort=stars
```

The new vocabulary tightens the relevant set; the Maybe set becomes
clearer. Stop at refinement; classify; deepen 3-5.

## Example 2: AI code review bot

**Need:** repos that review pull requests with AI assistance.

**First pass (4 angles)**

```bash
gh search repos 'ai code review fork:false archived:false' --limit 20 --sort=stars
gh search repos 'pull request review bot fork:false archived:false' --limit 20 --sort=stars
gh search repos 'coderabbit OR greptile fork:false archived:false' --limit 20 --sort=stars
gh search repos 'llm pr review fork:false archived:false' --limit 20 --sort=stars
```

**Observed shape**

- The category uses multiple labels: `code review bot`, `PR review`,
  `review agent`, `GitHub App`.
- Some relevant repos position themselves as **agents** rather than
  bots — the wording matters.
- Star spread is wide; the niche is young enough that high-quality
  candidates appear at 200-2000⭐.

**Refinement (2 angles, agent framing)**

```bash
gh search repos 'review agent github app fork:false archived:false' --limit 20 --sort=stars
gh search repos 'ai pull request bot fork:false archived:false' --limit 20 --sort=stars
```

Star threshold note: this is a young niche. The skill's discipline
matrix says **no threshold** here. Adding `stars:>500` would have
silently dropped the strongest candidates.

## Example 3: TypeScript MCP server framework

**Need:** frameworks or starter repos for building MCP servers in
TypeScript.

**First pass (4 angles)**

```bash
gh search repos 'mcp server typescript fork:false archived:false' --limit 20 --sort=stars
gh search repos 'model context protocol typescript fork:false archived:false' --limit 20 --sort=stars
gh search repos 'mcp framework typescript fork:false archived:false' --limit 20 --sort=stars
gh search repos 'mcp sdk typescript fork:false archived:false' --limit 20 --sort=stars
```

**Observed shape**

- Repos vary in self-description: `sdk`, `framework`, `starter`,
  `boilerplate`, `template`.
- Some relevant repos are libraries; others are example packs or full
  applications. Distinguishing matters.
- This is a very young niche (MCP is 2024+). No star threshold.

**Refinement (2 angles, harvested wording)**

```bash
gh search repos 'mcp starter typescript fork:false archived:false' --limit 20 --sort=stars
gh search repos 'mcp boilerplate typescript fork:false archived:false' --limit 20 --sort=stars
```

## Example 4: Fuzzy-naming category — browser agents

**Need:** repos for "browser agents" where projects may use other
labels (`automation`, `operator`, `assistant`, `copilot`).

**First pass (4 angles)**

```bash
gh search repos 'browser agent fork:false archived:false' --limit 20 --sort=stars
gh search repos 'web automation agent fork:false archived:false' --limit 20 --sort=stars
gh search repos 'browser copilots fork:false archived:false' --limit 20 --sort=stars
gh search repos 'playwright ai agent fork:false archived:false' --limit 20 --sort=stars
```

**Observed shape**

- Repo names in the relevant set use `automation`, `operator`,
  `assistant`, `copilot` instead of `agent`.
- The user's wording differs from the community's wording — naming
  cluster pivot needed.

**Refinement (pivot to discovered cluster + optional augment)**

```bash
gh search repos 'browser automation operator OR assistant fork:false archived:false' --limit 20 --sort=stars
```

If GitHub-only first-pass remains noisy, optionally invoke
`run-research` per `web-augment.md` to learn community vocabulary on
Reddit/HN, then return to GitHub with new names. The augmentation is a
detour back to GitHub, not a parallel research track.

## Example 5: Verify-first when the user names a known thing

**Need:** "find alternatives to `clink` for managing AI CLIs."

This is the canonical derailment-recovery example. Read it before
running any search where the user named a specific repo, project, or
tool by name.

**Wrong path (the derailment)**

The skill assumes `clink` is a multi-CLI manager and searches the
broader category directly:

```bash
gh search repos 'agent bridge cli fork:false archived:false' --limit 15 --sort=stars
gh search repos 'claude code codex orchestrat fork:false archived:false' --limit 15 --sort=stars
gh search repos 'clink claude codex agent fork:false archived:false' --limit 15 --sort=stars
# ... several more searches
```

Three or four queries in, a verify call surfaces the truth: `clink`
is **not** a multi-CLI manager. The top result for `clink` is
`chrisant996/clink` (5.2k⭐) — a cmd.exe shell editor, completely
unrelated to AI agents. Cost so far: 3-4 wasted searches plus
interpretive drift in the agent's mental model.

**Correct path**

```bash
# Step 1 — Verify-first (the FIRST call when the user named a thing)
gh search repos 'clink' --limit 5 --sort=stars \
  --json fullName,description,stargazersCount,updatedAt \
  --jq '.[] | [.fullName, (.stargazersCount|tostring), (.updatedAt[:10]), (.description // "" | .[:80])] | @tsv'
```

Output (compressed):

```
chrisant996/clink    5194    2026-05-09    Bash's powerful command line editing in cmd.exe
mridgers/clink       3309    2026-05-07    Bash's powerful command line editing in cmd.exe
gamcil/clinker       641     2026-05-02    Gene cluster comparison figure generator
...
```

**Step 2 — Confirm category mismatch.** None of these are AI multi-CLI
managers. The category is clearly "shell editor" or unrelated.

**Step 3 — Surface the mismatch back to the user.** Do not silently
re-interpret the request:

> The repo named `clink` (top result: chrisant996/clink, 5.2k⭐) is a
> cmd.exe shell editor, not a multi-CLI manager for AI agents. Did
> you have a different project in mind, or shall I proceed with a
> category search for "tools that manage multiple AI CLIs"?

**Step 4 — Only after clarification, search alternatives.**

The discipline lesson: **never search for alternatives to a name you
have not yet verified**. One verify call upfront prevents 3-4 wasted
searches and keeps the agent's mental model anchored to reality. See
`discipline.md` §2.

## Adapting these examples

These examples are templates, not scripts. Adapt the angles per the
user's actual need. Each example demonstrates the same loop:

1. **First pass** with 3-6 angles (or a single verify-first call when
   the user named a thing).
2. **Observed shape** — read what came back, classify, name what's
   missing.
3. **Refinement** with 1-4 better angles, OR recovery if the first
   pass derailed.

The third phase always exists. The skill never lands cleanly on the
first pass and stops there.
