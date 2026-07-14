# gh search repos Cheatsheet

Copy-paste reference for valid, compact GitHub repo searches.

For the mental model around when to use which qualifier (and which to
avoid in first-pass discovery), read `discipline.md` first.

## Command structure

```bash
gh search repos 'QUERY' --limit 20 --sort=stars \
  --json fullName,description,stargazersCount,updatedAt,url \
  --jq '...'
```

Use shell quotes around the whole query string when helpful. Inside
that query string, GitHub still parses search operators and qualifiers.

## Useful qualifiers

| Qualifier | Example | Use |
|---|---|---|
| `stars:>N` | `stars:>200` | Filter noise — pick N per ecosystem maturity (see below). |
| `pushed:>DATE` | `pushed:>2025-01-01` | Bias toward active repos. |
| `language:X` | `language:TypeScript` | Hard language constraint. |
| `fork:false` | `fork:false` | Drop forks from discovery. |
| `archived:false` | `archived:false` | Drop archived repos. |
| `license:mit` | `license:mit` | Filter by license when needed. |
| `in:name` | `agent in:name` | Name-only check. |
| `in:description` | `knowledge base in:description` | Description-only check. |
| `in:readme` | `playwright in:readme` | High false-positive rate; last-resort qualifier. |
| `topic:X` | `topic:mcp` | **Helpful for shortlisted repos, noisy for broad discovery — see warning below.** |

## OR rules — three classes

`OR` is parsed by token, not by phrase. There are three classes of OR
usage and they behave differently:

```
Class A — OR between SINGLE TOKENS: WORKS
  ✓ outline OR affine
  ✓ agent OR copilot
  ✓ tmux OR zellij OR screen

Class B — OR between QUOTED PHRASES: WORKS
  ✓ "claude code" OR "openai codex"
  ✓ "code review bot" OR "review agent"

Class C — OR between BARE MULTI-WORD TERMS: AMBIGUOUS, AVOID
  ✗ claude code OR codex agents
  ✗ notion alternative OR self-hosted wiki
```

Why Class C breaks: GitHub's parser splits on whitespace and applies
OR per-token, so the agent intends `(claude code) OR (codex agents)`
but gets `(claude AND code) OR (codex AND agents)`. The query returns
broad, weakly-relevant results that include any pair of the four
tokens.

When the concept is multi-word, the fix is one of:

- **Quote the phrases** to lift them into Class B:
  `"claude code" OR "openai codex"`
- **Split into separate searches** and merge per `gh-output.md` recipe
  4: run two searches, `sort -u` the union.

Examples:

```bash
# Class A (works)
gh search repos 'outline OR affine fork:false archived:false' --limit 20 --sort=stars

# Class B (works)
gh search repos '"claude code" OR "openai codex" fork:false' --limit 20 --sort=stars

# Class C (avoid — split or quote instead)
# WRONG: gh search repos 'claude code OR codex agents fork:false' --limit 20

# Class C fix via split + merge
{
  gh search repos '"claude code" fork:false' --limit 20 --json fullName --jq '.[].fullName';
  gh search repos '"openai codex" fork:false' --limit 20 --json fullName --jq '.[].fullName';
} | sort -u
```

## Topic discovery warning

`topic:X` filters to repos with the hand-tagged topic `X`. Topics are
**user-supplied metadata** and are spam-prone, especially in trending
categories. Two repos sharing `topic:claude-code` may be entirely
different shapes — a wrapper, a tutorial collection, an agent harness,
an MCP server. Star count in topic-filtered searches correlates with
topic-spam reach, not relevance.

**Rule.** Use `topic:` only AFTER candidates are shortlisted, to
broaden adjacent discovery (e.g., "what other topics does my best
candidate carry?"). **Never use `topic:` in a first-pass discovery
search.** See `discipline.md` §5 for the canonical noise example.

## Star threshold guidance

Pick `stars:>N` per ecosystem maturity, not by reflex:

| Ecosystem maturity | Threshold |
|---|---|
| Very young (12-24 months: AI coding agents, MCP, agent orchestrators) | none, or `stars:>1` |
| Young (2-4 years: recent JS frameworks, vibe-coding tools) | `stars:>10` to `stars:>50` |
| Mature (5+ years: web frameworks, Docker tooling) | `stars:>500` |
| Very mature (10+ years: linters, build tools, classic CLIs) | `stars:>1000` |

**Decision rule.** Start with **no threshold** for young ecosystems —
quality repos exist below 100⭐ and a threshold filters them out. Add
a threshold only after the first pass returns materially too much
noise. See `discipline.md` §3 for full reasoning.

## Heuristics

- Start broad, then filter internally.
- Prefer 20-30 results per search over giant dumps.
- Use `--sort=stars` for discovery; use recency as a later signal, not
  the primary sort.
- Always use `--json` with `--jq`; raw JSON is noisy and expensive.
- If you need repo topics or README intros, inspect only the top few
  candidates after the first pass.
- Avoid stacking 4+ technical tokens AND-ed in one query — routinely
  returns empty results (see `discipline.md` §7).
