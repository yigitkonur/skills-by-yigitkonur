# Input formats and slug derivation

The render script accepts two input shapes. Both are deliberately simple. The user's job is to produce the right shape; the render script doesn't try to be clever about parsing arbitrary text.

## Shape 1 — Tab-delimited (preferred for URL/markdown lists)

```
aibrandtracking-com<TAB>[AI Brand Tracking](https://aibrandtracking.com/)
profound<TAB>[https://profound/](https://profound/)
nightwatch-io<TAB>[Nightwatch](https://nightwatch.io/)
```

Column 1 → filename (`<slug>.md`). Column 2 → substituted into the template wherever `XXXXXXXXXXXXX` appears. Use this when you want explicit control over filenames.

## Shape 2 — Plain lines (for ID lists)

```
PROD-001
PROD-002
PROD-003
```

Each line becomes both the slug and the substituted content. Use for short IDs, slugs, or single-token inputs.

## Pre-processing common formats

### Markdown link list → tab-delimited

Input:

```
[AI Brand Tracking](https://aibrandtracking.com/)
[Nightwatch](https://nightwatch.io/)
```

One-liner to derive `<domain-with-hyphens><TAB><full-line>`:

```bash
python3 -c '
import sys, re
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    m = re.search(r"\((https?://[^)]+)\)", line)
    if not m: continue
    domain = re.sub(r"^https?://", "", m.group(1)).split("/")[0]
    slug = domain.replace(".", "-")
    print(f"{slug}\t{line}")
' < raw-links.md > inputs.txt
```

### CSV → tab-delimited

```bash
# CSV with columns: id,name,url — use id as slug, full row as content
awk -F, 'NR>1 { printf "%s\t%s\n", $1, $0 }' data.csv > inputs.txt
```

### One file per line (paths) → tab-delimited

```bash
# Use basename without extension as slug
while IFS= read -r path; do
  slug="$(basename "$path" | sed 's/\.[^.]*$//')"
  printf '%s\t%s\n' "$slug" "$path"
done < paths.txt > inputs.txt
```

## Slug derivation rules used by render-prompts.sh

The render script applies these rules to whatever you put in column 1 (or the whole line for plain inputs):

1. Replace any character outside `[a-zA-Z0-9._-]` with `-`.
2. Collapse runs of `-` into a single `-`.
3. Strip leading/trailing `-`.
4. Reject empty slugs (warning to stderr, line skipped).

Examples:

| Input column 1 | Resulting slug |
|---|---|
| `aibrandtracking.com` | `aibrandtracking-com` |
| `profound/` | `profound` |
| `My Product Name!` | `My-Product-Name` |
| `___` | `___` (underscores survive — they're in the keep set) |
| `!!!` | (no kept characters → empty after dash-strip → skipped with warning) |

## Collision handling

If two inputs produce the same slug, the render script writes a warning to stderr and SKIPS the second one:

```
warn: collision on aibrandtracking-com.md (line 5), skipping — disambiguate input
```

This is loud on purpose. Silently overwriting the first prompt would be a footgun. Fix collisions in your input file by adding a discriminator (e.g. `aibrandtracking-com-2`).

## Validating before launching

After rendering, do a quick sanity check:

```bash
# Count
ls prompts/ | wc -l

# Inspect a random sample
ls prompts/ | shuf -n 3 | while read f; do
  echo "=== $f ==="
  head -8 "prompts/$f"
  echo
done

# Check for any remaining placeholder (substitution failed)
grep -l 'XXXXXXXXXXXXX' prompts/*.md
```

A leftover placeholder means the template referenced a different sentinel than the script's default, or the input line didn't contain anything to substitute. Fix before launching the runner.

## Why the script does NOT do URL parsing for you

The skill could theoretically detect markdown links in plain inputs and auto-derive domain slugs. It doesn't, because:

- "Domain with dots → hyphens" is one of many reasonable conventions. Some users want the path included; some want a 3-letter abbreviation; some want `.com` stripped.
- Auto-detection masks errors — if the regex fails on edge cases (malformed links, unicode hostnames), the user gets unexpected slugs without realising.
- Pre-processing with a one-liner the user can edit is more honest about the convention chosen.

If you want auto-domain slugging, write a 5-line wrapper around `render-prompts.sh` for your project. Don't push that complexity into the generic script.
