# Download Patterns

## Verify `skill-dl` before downloading

Always start with:

```bash
skill-dl --version
```

If `skill-dl` is missing, save the installer locally, inspect it, then run it and verify again. On macOS, if `bash --version` is 3.x, install a newer Bash first with `brew install bash`.

```bash
curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh -o /tmp/install-skill-dl.sh
sed -n '1,160p' /tmp/install-skill-dl.sh

# Linux, or macOS where `bash --version` is already 4+:
bash /tmp/install-skill-dl.sh

# macOS if `bash --version` is 3.x (the default /bin/bash is 3.2):
"$(brew --prefix)"/bin/bash /tmp/install-skill-dl.sh

skill-dl --version
```

The installer needs `git` plus `curl` or `wget`. On macOS, the Bash 4+ requirement applies to the installer script; a preinstalled `skill-dl` can still be used directly once `skill-dl --version` succeeds.

## URL format

All skill URLs follow: `https://playbooks.com/skills/{owner}/{repo}/{skill-name}`

## Single skill download

```bash
skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ./corpus
```

Add `-f` to overwrite existing:

```bash
skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ./corpus -f
```

## Multiple URLs inline

For 2-4 ad hoc downloads, pass multiple URLs directly and skip the temporary URL file:

```bash
skill-dl \
  https://playbooks.com/skills/owner/repo/skill-one \
  https://playbooks.com/skills/owner/repo/skill-two \
  -o ./corpus --no-auto-category
```

Use a URL file instead when you need comments, want to reuse the shortlist, or are downloading a larger corpus.

## Batch download from file

Create a URL file with one URL per line. Use `#` for comments:

```
# MCP server skills
https://playbooks.com/skills/owner/repo/skill-one
https://playbooks.com/skills/owner/repo/skill-two

# Testing skills
https://playbooks.com/skills/other/repo/skill-three
```

Download all:

```bash
skill-dl urls.txt -o ./corpus --no-auto-category -f
```

Always run `--dry-run` first for batches over 20 URLs:

```bash
skill-dl urls.txt --dry-run
```

## Pipe search results to download

Chain search and download in one command:

```bash
skill-dl search react hooks testing | grep -oE 'https://playbooks\.com/skills/[^ |]+' | skill-dl - -o ./corpus -f
```

The `-` argument tells `skill-dl` to read URLs from stdin.

## Parallel download for large batches

`skill-dl` groups URLs by repo internally (one clone per repo) but processes repos sequentially. For 50+ URLs across many repos, parallelize at the repo level.

### Option A: Split by repo, then parallel (preferred)

Avoids redundant clones of the same repo:

```bash
tmp=$(mktemp -d)
while IFS= read -r url; do
  [[ "$url" =~ ^# ]] || [[ -z "$url" ]] && continue
  repo=$(echo "$url" | sed 's|.*/skills/\([^/]*/[^/]*\)/.*|\1|' | tr '/' '_')
  echo "$url" >> "${tmp}/${repo}.txt"
done < urls.txt

ls "${tmp}"/*.txt | xargs -P 6 -I {} skill-dl {} -o ./corpus --no-auto-category -f
rm -rf "$tmp"
```

### Option B: One URL per process (simple)

Re-clones shared repos but simpler to run:

```bash
grep -v '^#' urls.txt | grep -v '^$' | xargs -P 6 -I {} skill-dl {} -o ./corpus --no-auto-category -f
```

Use Option A for large corpora with many skills from the same repo. Use Option B for quick grabs across unique repos.

## Flags reference

| Flag | Purpose | Default |
|---|---|---|
| `-o <dir>` | Output directory | `./skills-collection` |
| `-f` | Overwrite existing skills | Off |
| `--no-auto-category` | Flat output, no category subfolders | Auto-categorize on |
| `-c <name>` | Force all skills into one named category folder | None |
| `--dry-run` | Preview what would be downloaded, no actual download | Off |
| `-v` | Verbose mode — shows search paths and available skills | Off |

## Output naming

Downloaded skills land in folders named `{owner}--{repo}--{skill}/` containing `SKILL.md` plus any bundled `references/`, `scripts/`, `rules/`, `examples/`, or other skill folders copied from the source repo.

## Auto-categorization

By default, `skill-dl` sorts downloaded skills into subfolders based on name patterns. The path shape is `<output>/<auto-category>/<owner>--<repo>--<skill>/`. Example: `./corpus/pro-and-review/mcollina--skills--typescript-magician/`.

Use `--no-auto-category` to keep everything flat at `<output>/<owner>--<repo>--<skill>/`. Use `-c <name>` to force a single category such as `./corpus/my-typescript-skills/<owner>--<repo>--<skill>/`.

## Skill search paths (how skill-dl finds skills in repos)

`skill-dl` checks these locations in order when extracting a skill from a cloned repo:

1. `skills/{skill}`
2. `{skill}`
3. `.skills/{skill}`
4. `.claude/skills/{skill}`
5. `.agent/skills/{skill}`
6. `.opencode/skills/{skill}`
7. `.cursor/skills/{skill}`
8. `.agents/skills/{skill}`
9. `src/skills/{skill}`

Fallback: recursive search for SKILL.md with matching parent directory name, then root-level SKILL.md for single-skill repos.

## Troubleshooting

| Problem | Diagnosis | Fix |
|---|---|---|
| `skill-dl: command not found` | Not installed or not on `PATH` | Use the saved-installer flow above. If the installer falls back to `~/.local/bin`, add that directory to `PATH` and rerun `skill-dl --version`. |
| `[ERR] Could not clone` | Repo is private, renamed, or deleted | Check URL manually in a browser |
| `[ERR] Not found in repo` | Skill name does not match any path | Run with `-v` to see available skills; the repo may use non-standard layout |
| Slow on many repos | Sequential repo processing | Use parallel download (Option A above) |
| Partial failures in batch | Some URLs invalid | Collect failed URLs from output, save to new file, re-run |
| Duplicate skills across runs | Multiple search rounds overlap | Deduplicate URL files with `sort -u` before downloading |

## Environment variables

| Variable | Purpose | Notes |
|---|---|---|
| `SERPER_API_KEY` | Google search via Serper | Built-in default included; override for higher quota |
| `SCRAPEDO_API_KEY` | Proxy fallback for scraping | Built-in default included; override if rate-limited |
