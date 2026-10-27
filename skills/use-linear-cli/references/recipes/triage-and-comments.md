# Recipe — Triage, Comments, and Image Fetch

Process an inbound triage queue, leave findings as comments, link or fetch attachments, and pull screenshots into a multimodal review.

## Daily triage

```bash
linear-cli tr list                          # up to 50 unassigned issues in triage/backlog states
linear-cli tr list -t ENG                   # filter to a team
linear-cli tr list --output json --compact \
  --fields identifier,title,createdAt
```

For each item:

```bash
# Read the body and issue metadata
linear-cli i get LIN-501 --output json --fields title,description,labels.nodes

# Read existing comments and attachments
linear-cli cm list LIN-501 --output json
linear-cli att list LIN-501 --output json
```

Then act:

```bash
linear-cli tr claim LIN-501                 # assign to me, leave triage
linear-cli tr snooze LIN-501 --duration 1d  # come back tomorrow (1d, 2d, 3d, 1w, 2w, 30d)
```

## Snooze durations

Use `1d`, `2d`, `3d`, `1w`, `2w`, or an integer day count such as `30d`. In 0.3.28 `1m` silently falls back to one day; it does not mean a month. The CLI list does not filter `snoozedUntilAt`, so snoozed issues may still appear in `tr list`.

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

For upload discovery and download examples, see `data/attachments-and-uploads.md`.

## Status check during triage

```bash
linear-cli st list -t ENG --output json | jq '.statuses | map({name,type})'
```

Useful when the team has custom workflow states beyond the default `Triage / Backlog / In Progress / Done / Cancelled`.

## Issues created since yesterday (not an activity report)

```bash
linear-cli i list --mine --since=-1d --output json \
  --fields identifier,title,state.name --compact \
  | jq -r '.[] | "\(.identifier) — \(.state.name) — \(.title)"'
```
