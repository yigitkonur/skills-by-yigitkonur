# Skills Testing (io.modelcontextprotocol/skills)

Client support for the official MCP Skills extension (`io.modelcontextprotocol/skills`, MCP 2026-07-28+), released in `mcpc 0.7.0`.

> [!IMPORTANT]
> The draft SEP-2640 convention (`skill://index.json`, `skill-md`, `archive`) was **completely replaced** in mcpc 0.7.0 by the official MCP Skills specification. Do not use or test `skill://index.json`.

A skill is a directory of files, minimally a `SKILL.md` with YAML frontmatter, that a server publishes alongside its tools, resources, and prompts. The extension adds two methods on top of the Resources primitive:
- `skills/list`: Enumerates skills served by the server. Each entry is a complete manifest: the skill's verbatim frontmatter plus every file with its SHA-256 digest and byte size (or `"dynamic"`).
- `skills/get`: Returns the entry for a skill, named by the URI of its `SKILL.md`, whether or not it appears in the listing.

## Commands

```bash
# List all skills published by the server
mcpc @session skills-list
mcpc --json @session skills-list

# Read a skill's SKILL.md
mcpc @session skills-get <skill>
mcpc @session skills-get <skill> --raw     # bare markdown, pipeable to file or LLM

# Read a specific file inside a skill
mcpc @session skills-get <skill> <file>
mcpc @session skills-get pdf-processing references/FORMS.md
mcpc @session skills-get pdf-processing references/FORMS.md --raw

# JSON output
mcpc --json @session skills-get <skill>
mcpc --json @session skills-get <skill> <file>
```

`<skill>` accepts:
- A bare name: `git-workflow`
- A prefixed path: `acme/billing/refunds`
- An absolute URI: `skill://git-workflow/SKILL.md` (or directory URI `skill://git-workflow/`)

If a bare name matches multiple skills across prefixes, mcpc refuses to pick silently, prints all matching URIs, and exits with code `1`.

## Content Verification & Manifest Integrity

When reading a skill or file via `skills-get`:
1. **Manifest check:** mcpc fetches the fresh skill entry from the server. If `file` is not listed in `resources` (and resources is not `"dynamic"`), reading is rejected as unverified.
2. **Path traversal protection:** `..` segments in file paths are rejected immediately.
3. **Byte size check:** Retrieved data length must match `size` in the manifest.
4. **Digest verification:** Raw bytes are hashed with SHA-256 and matched against `sha256:<hex>` declared in `digest`. Mismatched content is never output.
5. **Frontmatter consistency:** For `SKILL.md`, frontmatter fields in the document body must match the advertised listing frontmatter.

Any mismatch produces a `ServerError` and exits with code `2`.

## JSON Output Shapes

`mcpc --json @session skills-list`:
```json
[
  {
    "uri": "skill://git-workflow/SKILL.md",
    "frontmatter": {
      "name": "git-workflow",
      "description": "Standard git workflow instructions"
    },
    "resources": [
      {
        "uri": "skill://git-workflow/SKILL.md",
        "digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "size": 1024
      }
    ]
  }
]
```

`mcpc --json @session skills-get <skill>`:
```json
{
  "skill": {
    "uri": "skill://git-workflow/SKILL.md",
    "frontmatter": {
      "name": "git-workflow",
      "description": "Standard git workflow instructions"
    },
    "resources": [ ... ]
  },
  "contents": [
    {
      "uri": "skill://git-workflow/SKILL.md",
      "mimeType": "text/markdown",
      "text": "---\nname: git-workflow\n..."
    }
  ]
}
```

## Directory Resources (`resources-directory-read`)

In addition to skills, servers may expose directory resources when `"directoryRead": true` is advertised in resource capabilities. Use:

```bash
mcpc @session resources-directory-read <uri>
mcpc --json @session resources-directory-read <uri>
```

This invokes `resources/directory/read`, automatically paginating with `fetchAllPages()` and returning the list of child `Resource` objects.

## Server with skills vs server without

Servers without skills return empty listings without error:

```bash
mcpc @session skills-list
# (no skills found)
mcpc --json @session skills-list   # -> []
```

Both exit `0`. Asking for a nonexistent skill fails cleanly:
`mcpc @session skills-get bogus` exits `2` with `Failed to read resource ... not found`.

## Smoke-test assertions

| Check | Command | Expect |
|---|---|---|
| capability advertised when expected | `mcpc --json @session | jq '.capabilities.extensions["io.modelcontextprotocol/skills"]'` | extension object or null |
| `skills-list` exits clean | `mcpc @session skills-list; echo $?` | exit `0` |
| JSON shape is an array | `mcpc --json @session skills-list | jq 'type=="array"'` | `true` |
| known skill readable | `mcpc @session skills-get <name> --raw` | markdown body |
| sub-file readable | `mcpc @session skills-get <name> <file> --raw` | sub-file body |
| digest/size mismatch rejected | server alters file without updating manifest | exit `2` (`ServerError`) |
| unknown skill fails cleanly | `mcpc @session skills-get bogus; echo $?` | exit `2` |
