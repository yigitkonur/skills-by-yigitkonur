# Remote Sources

## Discovery

### skill-dl search

`skill-dl search` is the primary discovery method. It is implemented in portable Node.js (`scripts/skill-dl.mjs`) with an executable shim at `scripts/skill-dl` (no global installation needed) and emits a prioritized markdown table to stdout.

Discovery channels:

1. **Primary** — `npx -y skills find <keyword>` per keyword. No API key required; searches the open `skills.sh` registry.
2. **GitHub Intelligence** — `gh search code` or `gh search repos` for real-world production implementations and patterns.
3. **Deep Research Grounding** — `skills/run-research` for multi-source consensus search across authoritative documentation and specs.

```bash
# Basic search — pass 3–20 keywords
node scripts/skill-dl.mjs search "agent browser" "headless automation" "browser testing"

# Or using the executable shim:
bash scripts/skill-dl search "typescript" "mcp" "server" --top 20

# Minimum recommended: at least 3 keywords
# Maximum: 20 keywords per invocation
```

**Output format:** a markdown table with columns: rank, skill name, owner/repo, keywords matched, match count, URL. Skills are ranked by how many of your keywords they matched — cross-keyword overlap is the primary signal.

**Usage pattern:**

1. Run `node scripts/skill-dl.mjs search` with 3–20 keywords covering the topic from multiple angles
2. **Triage**: if results exceed 50 rows, use `--min-match 2` to focus on cross-keyword hits, or `--top 20` to cap output. For niche topics where the max match count is ≤2, broaden keyword variety or manually curate from the full list
3. Review the table — higher keyword match count = higher priority
4. Run a second search with different phrasing if the first result set looks narrow
5. Deduplicate by URL across multiple search runs before building the URL file

### Canonical URL Patterns

- Skills Registry: `https://skills.sh/{owner}/{repo}/{skill}`
- GitHub Repository: `https://github.com/{owner}/{repo}/tree/main/skills/{skill}`
- Raw triple: `{owner}/{repo}/{skill}`

### What to collect

For each candidate, capture: skill name, owner/repo, detail URL, keywords matched, match count, and selection rationale.

## Prerequisites

```bash
# Verify the bundled script is ready
node scripts/skill-dl.mjs --where

# Required runtime tools: node (v18+), git, npx
for cmd in node git npx; do command -v "$cmd" >/dev/null || echo "MISSING: $cmd"; done
```

**Fallback chain (when `npx` is unavailable):**
1. `node scripts/skill-dl.mjs ...` (default) — requires `npx` for registry search.
2. GitHub CLI (`gh search code "filename:SKILL.md <topic>"`) — search public skills directly on GitHub.
3. Deep research via `run-research` — search official documentation, RFCs, and open source repositories.

## Downloading with skill-dl

`skill-dl` batch-downloads skills via `git clone --depth 1` against `github.com/<owner>/<repo>`. URLs may be skills.sh, GitHub URLs, or a raw `<owner>/<repo>/<skill>` triple.

```bash
# Help and verification
node scripts/skill-dl.mjs --help
node scripts/skill-dl.mjs --where

# Search registry
node scripts/skill-dl.mjs search typescript mcp server --top 20

# Download skills from a file list
node scripts/skill-dl.mjs urls.txt -o ./corpus --no-auto-category -f
```

### Quick start

```bash
# Single skill download
node scripts/skill-dl.mjs https://skills.sh/vercel-labs/agent-browser/agent-browser -o ./corpus

# Download by owner/repo/skill triple
node scripts/skill-dl.mjs anthropics/skills/mcp-builder -o ./corpus

# Batch from file
node scripts/skill-dl.mjs urls.txt -o ./corpus --no-auto-category -f

# Dry run first
node scripts/skill-dl.mjs urls.txt --dry-run
```

### Specification Inspection

`skill-dl` also audits downloaded or local skills for `agentskills.io` specification compliance:

```bash
# Audit a single skill or an entire downloaded corpus
node scripts/skill-dl.mjs inspect ./corpus
node scripts/skill-dl.mjs inspect ./skills/build-skill
```

The inspector verifies:
- Line 1 starts with `---` frontmatter delimiter
- Required fields `name` and `description` are present
- `name` matches directory name and naming rules (1-64 chars, lowercase kebab-case)
- Frontmatter contains only spec-allowed fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`)
- No unknown or fabricated fields (e.g. `disable-model-invocation`, `user-invocable`)
- Description is under 1024 characters and free of raw XML brackets (`<`, `>`)
- Sizing recommendations (<500 lines)

### Flags reference

| Flag | Purpose |
|---|---|
| `-o <dir>` | Output directory (default: `./skills-collection`) |
| `--no-auto-category` | Flat output, no category subfolders |
| `-c <name>` | Force all into one category folder |
| `-f` | Overwrite existing directories |
| `--dry-run` | Preview only without cloning |
| `-v` | Verbose output (shows resolved paths) |
| `--top <N>` | Limit search results to top N matches |
| `--min-match <N>` | Minimum keyword hits required for search results |

### Output naming

Folders: `{owner}--{repo}--{skill}/` containing `SKILL.md` + bundled references.

### Auto-categorization

By default, `skill-dl` sorts downloaded skills into subfolders based on name patterns. The path shape is `<output>/<auto-category>/<owner>--<repo>--<skill>/`. Use `--no-auto-category` for flat `<output>/<owner>--<repo>--<skill>/` layout, or `-c <name>` to force a single category folder.

### Skill search paths

skill-dl checks these locations in order inside cloned repositories:
`skills/{skill}`, `{skill}`, `.skills/{skill}`, `.claude/skills/{skill}`, `.agent/skills/{skill}`, `.opencode/skills/{skill}`, `.cursor/skills/{skill}`, `.agents/skills/{skill}`, `src/skills/{skill}`.
Fallback: full-repo search for `SKILL.md` with matching parent dir name, then root-level `SKILL.md`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot find module ... skill-dl.mjs` | Run from the repository root or provide the full path to `scripts/skill-dl.mjs`. |
| Search returns 0 results | Check network connectivity and that `npx` is functional (`npx --version`). Try broader keywords. |
| `[ERR] could not clone` | Repo is private, renamed, or deleted. Check the repository URL manually. |
| `[ERR] not found in repo` | Skill name doesn't match any path in the repo. Run with `-v` to see resolved paths; the skill may use a custom directory layout. |
| Need to retry failures | Pipe failed URLs from summary into a new file and re-run. |

## Using downloaded skills as evidence

Downloaded skills are evidence for comparison, not templates to clone.

After download:
1. `tree` the corpus to understand structure.
2. Read high-signal skills (by keyword match count or unique architecture).
3. Audit them with `node scripts/skill-dl.mjs inspect <corpus-dir>`.
4. Cite relative paths in your comparison table.
5. Inherit patterns selectively and discard anti-patterns.
6. Synthesize the final result to be original, spec-compliant, and repo-fit.
