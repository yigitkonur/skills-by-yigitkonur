# Skills Testing (SEP-2640)

`[EXPERIMENTAL]` client support for the draft MCP skills extension, shipped in `mcpc`
since v0.3.1. Skills are not a new MCP primitive — a `skill://` URI convention layered on
Resources, so `skills-list`/`skills-get` are sugar over `resources-read` and work against
any compliant server without server-side mcpc awareness.

## Discovery convention

- Servers MAY publish `skill://index.json` — JSON with a `skills` array of
  `{ name, description, type, url }`. `mcpc` tries the index first; if absent, falls back
  to scanning `resources-list` for `skill://*/SKILL.md` URIs — a missing index is never
  proof of no skills.
- Recognized `type`: `skill-md`, `archive` (`.tar.gz`/`.zip`, fetch via
  `resources-read <url>`), `mcp-resource-template` (parameterized namespace). Unrecognized
  `type` entries are skipped silently.
- Capability advertised under `capabilities.extensions["io.modelcontextprotocol/skills"]`
  (spec) or `capabilities.experimental[...]` (SDK escape-hatch) — check with
  `mcpc --json @session | jq '.capabilities'`.

## Commands

```bash
mcpc @session skills-list
mcpc --json @session skills-list          # -> [{ name, description, type, url }, ...]
mcpc @session skills-get <name>
mcpc @session skills-get <name> --raw     # bare markdown, pipeable to a file/LLM
mcpc --json @session skills-get <name>    # -> ReadResourceResult; --raw ignored in --json
```

`<name>` accepts a bare name (`git-workflow`), a nested path (`acme/billing/refunds` —
name is the final path segment), or a full `skill://.../SKILL.md` URI.

## Server with skills vs server without

The no-skills case is a diagnostic, not a failure — live-verified against
`research-mcp.yigitkonur.com/mcp` (exposes no `skill://` resources):

```bash
mcpc @check skills-list
# (no skills found — server does not expose skill://index.json and no
#  skill://*/SKILL.md resources are listed)
mcpc --json @check skills-list   # -> []
```

Both exit `0` — empty is not an error. `skills-get <missing-name>` is the error case:
`Error: Failed to read resource skill://<name>/SKILL.md: ... not found`, exit `2`
(live-verified). Positive-path index/fallback/archive behavior above is from upstream
`test/e2e/suites/basic/skills.test.sh` and PR #207 — not live-verified, no public server
exposing real skills was available; cross-check entry-type and JSON-shape details against
a real server before hard-asserting.

## Relationship to `resources-list`

Skills are resources underneath: `skill://index.json` (if present) and every
`skill://*/SKILL.md` also show up in plain `resources-list`. If `skills-list` looks wrong,
cross-check there before assuming a server bug.

## Smoke-test assertions

| Check | Command | Expect |
|---|---|---|
| capability advertised when expected | `mcpc --json @session \| jq '.capabilities.extensions,.capabilities.experimental'` | skills key present under either |
| `skills-list` exits clean either way | `mcpc @session skills-list; echo $?` | exit `0` |
| JSON shape is an array | `mcpc --json @session skills-list \| jq 'type=="array"'` | `true` |
| known skill readable | `mcpc @session skills-get <name> --raw` | markdown body |
| unknown skill fails cleanly | `mcpc @session skills-get bogus; echo $?` | exit `2` |

Skill content is untrusted input — `mcpc` only reads and prints it; it never executes
hooks, scripts, or frontmatter-declared behavior. Don't test otherwise.
