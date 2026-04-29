# Attachments and Uploads

Two related but distinct surfaces:

- **Attachments** — first-class metadata records on an issue (title + URL). CRUD via `att`.
- **Uploads** — the binary asset side. Linear-hosted file URLs at `uploads.linear.app`. Read-only via `up fetch`.

## Attachment CRUD

```bash
linear-cli att list LIN-123
linear-cli att list LIN-123 --output json

linear-cli att get ATTACHMENT_ID

linear-cli att create LIN-123 -T "Design Doc" -u https://example.com
linear-cli att link-url LIN-123 https://sentry.io/issues/12345     # shorthand for create

linear-cli att update ATTACHMENT_ID -T "New Title"
linear-cli att delete ATTACHMENT_ID --force
```

| Flag | Meaning |
|---|---|
| `-T TITLE` | Attachment title (display label) |
| `-u URL` | Target URL |
| `--output json` | JSON output |
| `--force` | Skip delete confirmation |

`att link-url` is sugar for `att create -T <auto> -u <URL>`.

## `up fetch` — download Linear-hosted images

User-uploaded images and files live at `https://uploads.linear.app/<org>/<id>/<filename>`. `up fetch` is the only way to download them safely.

```bash
linear-cli up fetch "https://uploads.linear.app/<org>/<id>/screenshot.png" -f /tmp/screenshot.png
linear-cli up fetch "https://uploads.linear.app/..." > out.png
linear-cli up fetch "https://uploads.linear.app/..." | base64
```

| Flag | Meaning |
|---|---|
| `-f FILE` / `--file FILE` | Write to file instead of stdout |

### Host restriction

`up fetch` rejects URLs that aren't on `uploads.linear.app`. This is a deliberate safety boundary: `linear-cli` will not act as a generic HTTP fetcher with your Linear credentials. For arbitrary hosts, use `curl` or `wget`.

### Discovering upload URLs

Upload URLs appear in:

- Issue descriptions: `linear-cli i get LIN-123 --output json | jq -r '..|strings|select(test("uploads.linear.app"))'`
- Comments: `linear-cli cm list LIN-123 --output json | jq -r '..|strings|select(test("uploads.linear.app"))'`

URL pattern: `https://uploads.linear.app/{org}/{upload}/{filename}`.

## Multimodal review pattern (Claude Code, Cursor, etc.)

```bash
# 1. Discover
URL=$(linear-cli i get LIN-501 --output json \
  | jq -r '..|strings|select(test("uploads.linear.app"))' | head -1)

# 2. Download
linear-cli up fetch "$URL" -f /tmp/repro.png

# 3. Read with the agent's image-capable tool.
#    In Claude Code: pass /tmp/repro.png to the Read tool — Claude sees the image.
```

## Recipe: copy every screenshot from an issue to a folder

```bash
mkdir -p /tmp/lin-501
linear-cli i get LIN-501 --output json \
  | jq -r '..|strings|select(test("uploads.linear.app"))' \
  | while read -r url; do
      name=$(basename "$url")
      linear-cli up fetch "$url" -f "/tmp/lin-501/$name"
    done
```

## Recipe: link a Sentry / Datadog / Loom URL

```bash
linear-cli att link-url LIN-501 https://sentry.io/issues/123 --output json
```

`att link-url` autogenerates a title from the URL. To set a specific title, use `att create -T "Sentry — InvalidSession" -u https://...`.

## Common confusions

| Looks like | Is actually |
|---|---|
| `att list` | Linear *attachment* records (metadata + URL). |
| `up fetch` | Download a binary asset from `uploads.linear.app`. |
| `att link-url` | Sugar for `att create` with auto title. |
| `--force` | Skip confirmation on delete. |

## See also

- `recipes/triage-and-comments.md` — fetching screenshots during triage.
- `output-and-scripting.md` — JSON parsing patterns used to find upload URLs.
- `troubleshooting.md` — what to do when `up fetch` rejects a non-`uploads.linear.app` URL.
