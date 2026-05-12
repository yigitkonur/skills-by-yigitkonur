# R2 media bucket — single-file ops + bulk upload + custom-domain serving

Cloudflare R2 is the S3-compatible object store paired with Cloudflare Pages. When a project's static dist is too large to fit Pages' 25 MiB-per-file / 20k-file limits, or when the media set is meaningful enough to want a separate CDN-style host, R2 is the right destination. This reference covers the canonical Makefile targets for managing R2 buckets, applying CORS, uploading single files via wrangler, and bulk-uploading thousands of files in parallel via rclone (with a wrangler-OAuth fallback for when S3 keys aren't available).

The whole flow assumes the bucket already exists and is bound to a custom domain in the CF dashboard (e.g., `files.example.com`). Custom-domain binding is a one-time dashboard action; the skill does not generate it. The skill DOES manage everything else — CORS, uploads, validation, dedup.

## Target inventory

| Target | One-line description |
|---|---|
| `r2-info` | Bucket info + custom-domain status |
| `r2-cors-apply` | Apply `.r2-cors.json` (CF-native schema) to the bucket |
| `r2-cors-get` | Print current CORS rules |
| `r2-put` | Upload one file: `make r2-put KEY=<key> SRC=<path>` |
| `r2-get` | Download one file |
| `r2-rm` | Delete one file |
| `r2-stage` | Build `$(STAGING_DIR)/` as a hardlink mirror minus denylist |
| `r2-stage-stats` | File count + total bytes + top basenames + sanity zeros |
| `r2-stage-clean` | `rm -rf $(STAGING_DIR)` (only hardlinks — source untouched) |
| `rclone-install` | `brew install rclone` (idempotent) |
| `rclone-configure` | Write `[<remote>]` to `~/.config/rclone/rclone.conf` from `.env` |
| `rclone-check` | `rclone lsd` + `rclone ls | head` to verify auth |
| `r2-sync-dry` | Dry-run preview of the upload |
| `r2-sync` | Real `rclone copy` (additive by default; see safety rationale below) |
| `r2-size` | Total object count + bytes in bucket |
| `r2-bulk-wrangler` | Fallback: parallel upload via wrangler (no S3 keys needed) |
| `r2-bulk-status` | Ledger progress for the wrangler-bulk path |
| `r2-bulk-reset` | Clear the wrangler-bulk ledger |

Helpers (hidden): `_check-wrangler`, `_check-rclone`.

## Variables

```makefile
R2_BUCKET      ?= my-bucket
R2_PUBLIC_URL  ?= https://files.example.com               # custom domain bound in CF dashboard
R2_S3_ENDPOINT ?= https://<account-id>.r2.cloudflarestorage.com
RCLONE_REMOTE  ?= $(R2_BUCKET)                            # same name as bucket by convention
RCLONE_LOG     ?= tmp/rclone-r2-sync.log
STAGING_DIR    ?= ../r2-staging                           # outside the repo, same filesystem
```

## Authentication: cfat_/cfut_ tokens vs. S3 HMAC keys

The most common point of confusion. When you create an R2 API token in the CF dashboard, **the modal shows three values**, all distinct:

| Value | Format | What it authenticates |
|---|---|---|
| Token | `cfat_…` or `cfut_…` (47-53 chars) | Cloudflare REST API via `Authorization: Bearer …` — used by wrangler, the verify endpoint, the native R2 REST API |
| Access Key ID | 32 hex chars | S3 SigV4 protocol — paired with the secret below |
| Secret Access Key | 64 hex chars | S3 SigV4 secret |

**The cfat_/cfut_ token alone cannot drive rclone, aws-cli, boto3, or any S3 client.** There is no SHA-256 derivation that produces a working AKID — the AKID and secret are independently generated server-side and only shown alongside the token at creation time. If a project has only the cfat_/cfut_ value, the user must regenerate or look up the token in the dashboard and copy the S3 pair.

Convention for `.env`:

```bash
# CF API tokens (Bearer auth — wrangler, CF REST API)
R2_TOKEN_READ=cfat_…                          # read-only scope
R2_TOKEN_WRITE=cfut_…                         # write scope

# S3 HMAC pair for the write token (used by rclone)
R2_S3_ACCESS_KEY_ID=<32 hex>
R2_S3_SECRET_ACCESS_KEY=<64 hex>

# S3 HMAC pair for the read token (optional — audits, external tools)
R2_S3_READ_ACCESS_KEY_ID=<32 hex>
R2_S3_READ_SECRET_ACCESS_KEY=<64 hex>
```

The skill writes these comments into the generated `.env` so the user remembers the distinction.

### Token verify endpoint

For sanity check from a script:

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/<account_id>/tokens/verify" \
     -H "Authorization: Bearer <cfat_or_cfut>" \
  | jq '.success, (.result | {id, status, expires_on})'
```

`success: true` with `status: "active"` means the token is alive. **Validity ≠ permissions.** A token that verifies can still 401 on every operation if no permission groups are bound. Confirm permissions by running an actual op: `wrangler r2 bucket info <bucket>` with `CLOUDFLARE_API_TOKEN=cfat_…` set.

## `rclone-configure` — non-interactive config write

```makefile
.PHONY: rclone-configure _check-rclone
rclone-configure: _check-rclone
	@if [ ! -f .env ]; then \
	  printf "$(R).env not found — paste R2_S3_ACCESS_KEY_ID and R2_S3_SECRET_ACCESS_KEY first$(Z)\n"; exit 1; \
	fi
	@set -a; . ./.env; set +a; \
	if [ -z "$${R2_S3_ACCESS_KEY_ID:-}" ] || [ -z "$${R2_S3_SECRET_ACCESS_KEY:-}" ]; then \
	  printf "$(R)R2_S3_ACCESS_KEY_ID and/or R2_S3_SECRET_ACCESS_KEY missing from .env$(Z)\n"; \
	  printf "$(D)Get them from CF dashboard → R2 → Manage R2 API Tokens (alongside the cfat_/cfut_ value)$(Z)\n"; \
	  exit 1; \
	fi; \
	conf=$$HOME/.config/rclone/rclone.conf; \
	if [ -f "$$conf" ] && grep -q '^\[$(RCLONE_REMOTE)\]' "$$conf" && [ "$${FORCE:-0}" != "1" ]; then \
	  printf "$(Y)[$(RCLONE_REMOTE)] already exists in $$conf$(Z)\n"; \
	  printf "$(D)Re-run with FORCE=1 to overwrite$(Z)\n"; \
	  exit 0; \
	fi; \
	rclone config delete $(RCLONE_REMOTE) >/dev/null 2>&1 || true; \
	rclone config create $(RCLONE_REMOTE) s3 \
	  provider=Cloudflare \
	  access_key_id="$$R2_S3_ACCESS_KEY_ID" \
	  secret_access_key="$$R2_S3_SECRET_ACCESS_KEY" \
	  endpoint="$(R2_S3_ENDPOINT)" \
	  acl=private \
	  no_check_bucket=true \
	  region=auto \
	  >/dev/null; \
	printf "$(G)✓ wrote [$(RCLONE_REMOTE)] to $$conf$(Z)\n"

_check-rclone:
	@command -v rclone >/dev/null 2>&1 || { \
	  printf "$(R)rclone not installed$(Z)  $(D)brew install rclone$(Z)\n"; exit 1; }
```

Why each rclone option:

- `provider=Cloudflare` — opts into R2-specific defaults (no checksum trailers, etc.)
- `region=auto` — required; R2 doesn't use AWS regions
- `no_check_bucket=true` — skips a HEAD that R2 sometimes 400s on with restricted tokens
- `acl=private` — R2 default; public access is via custom domain, not ACL
- `secret_access_key` is double-quoted to keep `&` / `=` / `+` characters intact

`set -a; . ./.env; set +a` is the secret-safe load. Variables stay in the make recipe's process; nothing echoed to terminal or shell history. The `FORCE=1` gate prevents accidental overwrite of an existing remote.

## CRITICAL: `rclone copy` vs `rclone sync` — pick by tenancy

This is the highest-stakes single decision in the bulk-upload flow.

| Tool | Behavior | Use when |
|---|---|---|
| `rclone sync` | Mirror — uploads new files AND deletes anything in dest not in source | Bucket is **single-tenant** for this project; cruft cleanup desired |
| `rclone copy` | Additive — uploads new files; **never** deletes from dest | Bucket is **mixed-tenant** (other projects, other people's data, anything not under our prefix) |

**Default to `rclone copy`.** R2 buckets are cheap and often used as a junk drawer across multiple projects. Running `sync` against a shared bucket can silently delete 90% of someone else's data. The skill generates `copy` semantics for `make r2-sync`. Users who explicitly want strict sync (single-tenant, clean-on-each-run) can change the recipe.

**Always inspect the bucket before any first-run `r2-sync`:**

```bash
rclone size <remote>:<bucket>                            # how much is already there?
rclone lsf <remote>:<bucket> --dirs-only | head -20      # top-level prefixes — recognize them all?
```

If unfamiliar prefixes show up, treat the bucket as mixed-tenant. Examples seen in the wild:
- An unrelated project's top-level prefix sitting alongside yours — two tenants sharing one R2 bucket
- `.secrets/`, `_backup/`, `tmp/` — leftover from previous tooling experiments
- Top-level loose files (test.txt, hello.json) — manual upload tests

A custom domain bound to the bucket makes **everything** in the bucket publicly readable. Always check for accidentally-uploaded secrets:

```bash
for key in ".secrets/credentials.json" "config/api-key.txt" ".env" "id_rsa"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$R2_PUBLIC_URL/$key")
  printf "  %s %s\n" "$code" "$key"
done
```

Anything returning 200 is publicly accessible right now. Surface it to the user immediately, never bulk-delete autonomously.

## CORS — CF-native schema (NOT S3 schema)

R2's CORS API uses the Cloudflare-native shape, **not** the AWS S3 CORS shape. Wrangler 4.x requires:

```json
{
  "rules": [
    {
      "allowed": {
        "origins": ["https://app.example.com", "http://localhost:5173"],
        "methods": ["GET", "HEAD"],
        "headers": ["Range", "If-Match", "If-None-Match", "If-Modified-Since", "Content-Type"]
      },
      "exposeHeaders": ["Content-Length", "Content-Range", "Content-Type", "ETag", "Last-Modified", "Accept-Ranges"],
      "maxAgeSeconds": 3600
    }
  ]
}
```

Common mistake: writing the S3-style array-at-root (`[{ "AllowedOrigins": […], … }]`). Wrangler rejects this with: `The CORS configuration file must contain a 'rules' array`.

Apply with `wrangler r2 bucket cors set <bucket> --file=.r2-cors.json`. **The verb is `set`, not `put`.** Wrangler 4.x renamed `cors put` → `cors set`; older docs and templates may still say `put`.

```makefile
.PHONY: r2-cors-apply r2-cors-get
r2-cors-apply: _check-wrangler
	@wrangler r2 bucket cors set $(R2_BUCKET) --file=.r2-cors.json
	@printf "$(G)✓ CORS applied to $(R2_BUCKET)$(Z)\n"

r2-cors-get: _check-wrangler
	@wrangler r2 bucket cors list $(R2_BUCKET)
```

CORS scope guidance:
- Audio `<audio>` tags don't need CORS unless `crossorigin` is set on the element.
- `fetch()` calls (lyrics, metadata JSON, etc.) need CORS.
- `Range` request headers need `Range` in `AllowedHeaders` even though they're "simple" — R2 enforces explicit allowlisting.
- Use `["*"]` for `AllowedOrigins` only if every byte in the bucket is genuinely public — even then, named origins is more auditable.

## Staging dir via hardlinks — the dedup pattern

For bulk uploads from a structured source directory, build a staging directory of hardlinks that mirrors the **intended R2 layout** minus denylist files. Hardlinks consume zero extra disk on the same APFS / ext4 volume and rebuild in seconds.

Generic node script template:

```javascript
#!/usr/bin/env node
import { readdir, lstat, mkdir, rm, link } from "node:fs/promises";
import path from "node:path";

const SOURCE = path.resolve(process.env.SOURCE ?? "../source-data");
const STAGING = path.resolve(process.env.STAGING_DIR ?? "../r2-staging");
const DENY_BASENAMES = new Set([".DS_Store"]);
const DENY_EXTS = new Set([".webloc", ".tmp"]);

async function buildStaging() {
  await rm(STAGING, { recursive: true, force: true });
  await mkdir(STAGING, { recursive: true });

  for (const slug of await readdir(SOURCE)) {
    const srcDir = path.join(SOURCE, slug);
    const stat = await lstat(srcDir);
    if (!stat.isDirectory()) continue;

    const dstDir = path.join(STAGING, slug);
    await mkdir(dstDir, { recursive: true });

    for (const name of await readdir(srcDir)) {
      if (DENY_BASENAMES.has(name)) continue;
      if (DENY_EXTS.has(path.extname(name).toLowerCase())) continue;
      const srcFile = path.join(srcDir, name);
      const lst = await lstat(srcFile);
      if (!lst.isFile()) continue;  // skips symlinks, sockets, dirs
      // ... project-specific dedup logic here ...
      await link(srcFile, path.join(dstDir, name));
    }
  }
}
```

Variation: project-specific dedup. If the source dir routinely contains two byte-identical copies of the same payload under different basenames (a common pattern: a `canonical.<ext>` file plus a legacy-named alias), drop the alias from staging when their sizes match. The check is one extra `lstat` per directory; the win can be tens of GiB on large media archives.

```javascript
// Inside the per-source-dir loop, before the for-loop over file entries:
let canonicalSize = null;
if (entries.includes("canonical.bin")) {
  const s = await lstat(path.join(srcDir, "canonical.bin"));
  if (s.isFile()) canonicalSize = s.size;
}

// Inside the loop, when the alias basename appears at matching size, skip it:
if (name === "alias.bin" && canonicalSize !== null && lst.size === canonicalSize) {
  continue;  // dedup against canonical.bin
}
```

Hardlinks require source and staging on the **same filesystem**. Pre-check before generating:

```bash
df . | tail -1 | awk '{print $1}'             # repo filesystem
df "$SOURCE" | tail -1 | awk '{print $1}'     # source filesystem
# If these differ, hardlinks won't work — fall back to symlinks (rclone --copy-links) or rsync staging.
```

## `r2-stage-stats` — sanity check before upload

```makefile
.PHONY: r2-stage-stats
r2-stage-stats:
	@if [ ! -d "$(STAGING_DIR)" ]; then \
	  printf "$(R)$(STAGING_DIR) does not exist — run: make r2-stage$(Z)\n"; exit 1; \
	fi
	@total=$$(find $(STAGING_DIR) -type f 2>/dev/null | wc -l | tr -d ' '); \
	  bytes=$$(find $(STAGING_DIR) -type f -exec stat -f '%z' {} + 2>/dev/null | awk '{s+=$$1} END {print s+0}'); \
	  size=$$(du -sh $(STAGING_DIR) 2>/dev/null | awk '{print $$1}'); \
	  printf "$(B)staging:$(Z) $(STAGING_DIR)\n"; \
	  printf "  files:  $$total\n  bytes:  $$bytes\n  du:     $$size\n"
	@printf "\n$(B)top basenames:$(Z)\n"
	@find $(STAGING_DIR) -mindepth 2 -maxdepth 2 -type f 2>/dev/null \
	  | awk -F/ '{print $$NF}' | sort | uniq -c | sort -rn | head -20 \
	  | awk '{printf "  %-28s %s\n", $$2, $$1}'
	@printf "\n$(B)sanity (should all be 0):$(Z)\n"
	@printf "  .DS_Store: %s\n" "$$(find $(STAGING_DIR) -name '.DS_Store' 2>/dev/null | wc -l | tr -d ' ')"
	@printf "  symlinks:  %s\n" "$$(find $(STAGING_DIR) -type l 2>/dev/null | wc -l | tr -d ' ')"
```

Customize the sanity-zero list per project. If staging applies dedup, assert that the count of the kept alias in staging equals the count of source dirs where the alias was *not* a byte-identical copy of the canonical file.

## `r2-sync` — bulk rclone copy

```makefile
.PHONY: r2-sync-dry r2-sync
r2-sync-dry: _check-rclone
	@if [ ! -d "$(STAGING_DIR)" ]; then \
	  printf "$(R)$(STAGING_DIR) does not exist — run: make r2-stage$(Z)\n"; exit 1; \
	fi
	@rclone copy $(STAGING_DIR)/ $(RCLONE_REMOTE):$(R2_BUCKET)/ \
	  --transfers=20 --checkers=40 \
	  --s3-upload-concurrency=4 --s3-chunk-size=16M \
	  --use-mmap \
	  --exclude '.DS_Store' \
	  --dry-run --stats=10s --stats-one-line

r2-sync: _check-rclone
	@if [ ! -d "$(STAGING_DIR)" ]; then \
	  printf "$(R)$(STAGING_DIR) does not exist — run: make r2-stage$(Z)\n"; exit 1; \
	fi
	@mkdir -p $$(dirname $(RCLONE_LOG))
	@printf "$(D)→ bulk upload starting (rclone copy = additive); log: $(RCLONE_LOG)$(Z)\n"
	@rclone copy $(STAGING_DIR)/ $(RCLONE_REMOTE):$(R2_BUCKET)/ \
	  --transfers=20 --checkers=40 \
	  --s3-upload-concurrency=4 --s3-chunk-size=16M \
	  --use-mmap \
	  --exclude '.DS_Store' \
	  --progress --stats=10s --stats-one-line \
	  --log-level=INFO --log-file=$(RCLONE_LOG)
	@printf "$(G)✓ copy complete$(Z)  $(D)log: $(RCLONE_LOG)$(Z)\n"
```

Flag rationale:

| Flag | Why |
|---|---|
| `--transfers=20` | 20 concurrent uploads — saturates most home upstream + dodges R2 per-connection limits |
| `--checkers=40` | 2× transfers so metadata pre-walk doesn't gate uploads |
| `--s3-upload-concurrency=4` + `--s3-chunk-size=16M` | R2-tuned multipart; bounds peak RAM at `transfers × concurrency × chunk = 20 × 4 × 16 MiB ≈ 1.2 GiB` |
| `--use-mmap` | Memory-map large source files instead of streaming through heap |
| `--exclude '.DS_Store'` | Defense in depth (staging build also drops it) |
| `--progress --stats=10s --stats-one-line` | Visible progress without log spam |
| `--log-file=$(RCLONE_LOG)` | Durable record under `tmp/` (gitignored) |

**Do NOT** generate `--no-traverse --no-check-dest` flags for `rclone copy` if you want idempotent re-runs. Those flags skip the destination-listing pass and force every file to upload regardless — fast for empty buckets, wrong for re-runs. Default `copy` semantics already do the right thing: list dest, compare sizes, upload only missing/changed files.

Tuning headroom: at default settings, rclone saturates most residential upstreams for tens of thousands of small-to-medium files. Sustained throughput is gated by the network upstream, not these flags. If throughput is bandwidth-limited, `--transfers=20` is already plenty — bumping it further usually hurts (more connection setup, no extra bytes/sec).

## `r2-bulk-wrangler` — fallback when S3 keys aren't available

If the user has only the cfat_/cfut_ token and can't (or won't) generate the S3 HMAC pair, a parallel Node script using `spawn('wrangler', ['r2', 'object', 'put', …])` works without S3 keys. Wrangler authenticates via OAuth or `CLOUDFLARE_API_TOKEN`, which the cfat_/cfut_ token satisfies.

Trade-offs:

| Approach | Pros | Cons |
|---|---|---|
| rclone with S3 keys | Sustained streams, ~50 MiB/s, robust resumption | Needs S3 HMAC pair |
| wrangler-bulk parallel | Uses existing OAuth, no extra keys | Per-call Node startup (~1-2 sec overhead); slower per-file; resumes via ledger |

Skeleton of the fallback script:

```javascript
#!/usr/bin/env node
import { readdir, appendFile, mkdir, readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";

const STAGING = path.resolve(process.env.STAGING_DIR ?? "../r2-staging");
const BUCKET = process.env.R2_BUCKET;
const CONCURRENCY = Number(process.env.PARALLEL ?? "20") | 0;
const DONE_FILE = "tmp/r2-bulk-upload.done";
const FAIL_FILE = "tmp/r2-bulk-upload.failed";

// Walk staging, load ledger of done keys, build worker pool of N concurrent
// `wrangler r2 object put` invocations, append to ledger on success.
// Re-runs skip already-done keys.
```

Always emit ledger entries on success so an interrupted run resumes without re-uploading. Failed entries go to a separate file so a retry pass can target them. Concurrency = 20 matches the rclone default; higher values stress wrangler's per-process startup more than they help.

## Failure modes encountered

| Symptom | Cause | Fix |
|---|---|---|
| `Credential access key has length 64, should be 32` | Passed the cfat_/cfut_ token (or SHA-256 hash, or some other derivation) as `access_key_id` to rclone | Use the 32-char Access Key ID shown alongside the token in the CF dashboard, not derived |
| `401 Unauthorized` from rclone against R2 | AKID/Secret pair doesn't match an active token in the dashboard | Re-issue the token; verify with `wrangler r2 bucket info <bucket>` using the cfat_/cfut_ value |
| Wrangler `bucket info` returns `Authentication error [code: 10000]` | Token verifies but lacks the `Workers R2 Storage` permission group | Edit the token in the dashboard, add the permission group, save |
| `Credential access key has length 53, should be 32` | Passed the cfat_/cfut_ token as AKID | Same — get the real AKID from the dashboard |
| `400 The CORS configuration file must contain a 'rules' array` | Wrote `.r2-cors.json` in S3 style (array at root) | Wrap in `{ "rules": [ … ] }` (CF-native schema) |
| `wrangler r2 object list` not found | Wrangler 4.x doesn't have it | Use `aws s3 ls --endpoint-url=…` with the S3 keys, or rclone `ls`, or the CF dashboard |
| `wrangler r2 bucket cors put` not found | Wrangler 4.x renamed it | Use `wrangler r2 bucket cors set` |
| `rclone sync` deletes another project's data | The bucket was multi-tenant and `sync` mirrors | Always probe `rclone size + lsf` before first sync; default the Makefile to `rclone copy` (additive) |
| `.secrets/credentials.json` (or similar) reachable via custom domain at HTTP 200 | An earlier process uploaded what was meant to be a private key into a public-domain-bound bucket | Delete with `wrangler r2 object delete <bucket>/<key> --remote`; consider rotating any exposed credential; audit with `curl` against likely-leak paths before declaring the bucket clean |
| Range request against `/media/<key>` through `_redirects` 302 returns 200 instead of 206 | Browser ignored the redirect or the Range header was dropped | Verify directly against the R2 custom domain — if that returns 206, browser-side flow is fine; if not, check R2 CORS includes `Range` in `AllowedHeaders` |
| Hardlinks fail with `EXDEV cross-device link` | Source and staging on different filesystems | `df` both; either move staging onto the source's filesystem, or fall back to symlinks (`ln -s`) + `rclone --copy-links` |
| First `make r2-sync` against fresh bucket extremely slow on listing | rclone's default does a full LIST before upload | For empty-dest first run, add `--no-check-dest --no-traverse`; remove on subsequent runs so size-skip works |
| Audio plays but seeks broken on iOS Safari | iOS Safari Range-request handling is sensitive to `Accept-Ranges` not being exposed | Add `Accept-Ranges` to `exposeHeaders` in `.r2-cors.json`; re-apply with `make r2-cors-apply` |

## Public-access audit

Custom-domain binding makes the bucket publicly readable. Run this audit before declaring the bucket safe:

```makefile
.PHONY: r2-audit-public
r2-audit-public:
	@for key in ".secrets/credentials.json" ".env" "id_rsa" "id_ed25519" \
	            "config/secrets.yml" ".aws/credentials" "client_secrets.json"; do \
	  code=$$(curl -s -o /dev/null -w "%{http_code}" --max-time 6 "$(R2_PUBLIC_URL)/$$key"); \
	  case $$code in \
	    200) printf "  $(R)$$code$(Z) $(R2_PUBLIC_URL)/$$key  $(R)<- PUBLIC$(Z)\n" ;; \
	    *)   printf "  $(D)$$code$(Z) $(R2_PUBLIC_URL)/$$key\n" ;; \
	  esac; \
	done
```

This is a fixed-pattern check — not exhaustive. Combine with a one-time directory listing if you have S3 keys (`rclone ls <remote>:<bucket> | grep -iE '(secret|key|cred|password|env)'`).

## DO-NOT list

- **DO NOT default `make r2-sync` to `rclone sync`.** Use `rclone copy` unless you've personally verified the bucket is single-tenant.
- **DO NOT generate `make r2-sync` without `make r2-sync-dry` alongside.** Users must be able to preview before bytes move.
- **DO NOT commit `.env` or `~/.config/rclone/rclone.conf`.** Both contain HMAC secrets.
- **DO NOT pass S3 credentials on the command line** (visible in `ps`); always source from `.env` in the recipe.
- **DO NOT hash the cfat_/cfut_ token to derive an Access Key ID.** That doesn't work; get the real AKID from the dashboard.
- **DO NOT generate a hardcoded `region=us-east-1` for R2.** R2 uses `region=auto`.
- **DO NOT delete files from the bucket autonomously** when an audit surfaces unexpected content. Surface to the user with the public URL, paths, and sizes; let them decide.
- **DO NOT skip `make r2-stage-stats`.** The sanity-zero checks catch hardlink-followed symlinks, missed denylist entries, and dedup logic that didn't apply.
- **DO NOT use `rclone --copy-dest`** thinking it'll skip already-uploaded files. That flag is for local-to-local incremental — for R2, the default size-match skip is what you want.
- **DO NOT generate R2 targets for projects without a custom-domain binding.** If reads happen via `pub-<hash>.r2.dev` (R2's auto-generated dev URL), the workflow still works but should be flagged — dev URLs aren't meant for production traffic and CF rate-limits them.

## Cross-references

- `makefile-base.md` — universal preamble, ANSI palette, help target
- `makefile-cloudflare-pages.md` — Pages deploy + `_redirects` rule that complements the R2 custom domain
- `env-vars-conventions.md` — `.env` layout for `R2_S3_*` keys
- `verification-ladder.md` — what `make r2-sync` claims (rclone exit 0 + size match = rung 5); rung 6 is the manual cellular probe
- `ci-cd-workflow.md` — GitHub Actions wiring for automated R2 uploads (`R2_S3_ACCESS_KEY_ID` / `R2_S3_SECRET_ACCESS_KEY` as repo secrets)
