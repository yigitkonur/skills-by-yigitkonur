# Recipe — Triage, Comments, and Image Fetch

Process an inbound triage queue, leave findings as comments, link or fetch attachments, and pull screenshots into a multimodal review.

## Daily triage

```bash
linear-cli tr list                          # all unassigned, no-project items
linear-cli tr list -t ENG                   # filter to a team
linear-cli tr list --output json --compact \
  --fields identifier,title,createdAt
```

For each item:

```bash
# Read the body and issue metadata
linear-cli i get LIN-501 --output json --fields title,description,labels.nodes.name

# Read existing comments and attachments
linear-cli cm list LIN-501 --output json
linear-cli att list LIN-501 --output json
```

Then act:

```bash
linear-cli tr claim LIN-501                 # assign to me, leave triage
linear-cli tr snooze LIN-501 --duration 1d  # come back tomorrow (1d, 2d, 1w, 2w, 1m)
```

## Snooze durations

`1d`, `2d`, `1w`, `2w`, `1m`. After the duration the issue reappears in the triage queue.

## Leaving findings as comments

```bash
linear-cli cm create LIN-501 -b "Reproduces on Safari 17.4. Tag: macOS-only."
linear-cli cm create LIN-501 -b "$(cat findings.md)"     # body from a file
```

Update or delete:

```bash
linear-cli cm update COMMENT_ID -b "Updated text"
linear-cli cm delete COMMENT_ID --force
```

## Attachments — link a URL

```bash
linear-cli att link-url LIN-501 https://sentry.io/issues/12345
linear-cli att create LIN-501 -T "Repro recording" -u https://drive.example.com/abc
linear-cli att list LIN-501
linear-cli att get ATTACHMENT_ID
linear-cli att update ATTACHMENT_ID -T "New title"
linear-cli att delete ATTACHMENT_ID --force
```

## Fetching screenshots / uploaded images

Linear stores user-uploaded images at `https://uploads.linear.app/...`. Use `up fetch` to bring one local for inspection.

```bash
# Find URLs in the issue body or comments (dots in regex must be escaped)
linear-cli i get LIN-501 --output json | jq -r '..|strings|select(test("uploads\\.linear\\.app"))'
linear-cli cm list LIN-501 --output json | jq -r '..|strings|select(test("uploads\\.linear\\.app"))'

# Download to file
linear-cli up fetch "https://uploads.linear.app/<org>/<id>/screenshot.png" -f /tmp/screenshot.png

# Pipe to stdout
linear-cli up fetch "https://uploads.linear.app/..." > out.png
linear-cli up fetch "https://uploads.linear.app/..." | base64
```

### Multimodal pattern (Claude Code, Cursor, etc.)

```bash
# 1. Download
linear-cli up fetch "https://uploads.linear.app/..." -f /tmp/repro.png

# 2. Read the file with the agent's image-capable tool (Claude Code: the Read tool).
#    The agent sees the screenshot directly.
```

`up fetch` only accepts `uploads.linear.app` URLs — other hosts are rejected for safety. Use `curl` for arbitrary hosts.

## Bulk-claim everything in your queue

```bash
linear-cli tr list -t ENG --output json --fields identifier --compact \
  | jq -r '.[].identifier' \
  | xargs -I{} linear-cli tr claim {}
```

(Use cautiously. Prefer reading and snoozing item-by-item for real triage work.)

## Status check during triage

```bash
linear-cli st list -t ENG --output json --compact --fields name,type
```

Useful when the team has custom workflow states beyond the default `Triage / Backlog / In Progress / Done / Cancelled`.

## End-of-shift report

```bash
linear-cli i list --mine --since 1d --output json \
  --fields identifier,title,state.name --compact \
  | jq -r '.[] | "\(.identifier) — \(.state.name) — \(.title)"'
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `tr list` | Unassigned + no project — the *triage* queue specifically. |
| `i list` | Every visible issue. Bigger, less focused. |
| `cm create` | Issue comment. |
| `pu create` | *Project* update (status update on a project). Different command. |
| `att create` | Attachment object on an issue. |
| `up fetch` | Download from `uploads.linear.app`. Read-only side. |

## See also

- `issues/search-and-filter.md` — `i list` flag matrix and `--filter` for triage views.
- `data/attachments-and-uploads.md` — full attachment CRUD and URL handling.
- `recipes/git-and-pr-loop.md` — promote a triage finding into a tracked work item.
- `output-and-scripting.md` — the JSON / `xargs` plumbing.
