# Keep a service auto-updated (poll, redeploy, restart)

Use this when a service should track an upstream registry image and update itself — check for a new image, pull it, and restart — without a human running the deploy each time.

## Decision: what "auto-update" should mean here

| Situation | Do this |
|---|---|
| Service runs an upstream **registry** image (e.g. `vendor/app:latest`) | Poll the registry; on a new digest, trigger a **Coolify redeploy**. This reference. |
| Service runs a **locally built** image (`app:local`, no registry) | You cannot poll a registry. Either push builds to a registry first, or rebuild in CI and redeploy — never schedule heavy local builds on a small box. See `compose-authoring.md` (local-image trap). |
| You only need a one-time bump | Just `PATCH`/redeploy once; skip the poller. |

Auto-update means unattended upstream rollouts. State that tradeoff to the user: a bad upstream release can auto-deploy. The poller waits for `healthy` and warns on failure, but it does not auto-rollback.

## Prerequisite: use a registry image with `pull_policy: always`

The service's compose must reference a pullable image and pull on every deploy:

```yaml
services:
  app:
    image: vendor/app:latest
    pull_policy: always
```

If the service currently runs a `:local` image, switch it first (edit the **source** compose via `PATCH /services/{uuid}` — see `api-contracts.md`), verify (`verify-and-troubleshoot.md`), then add the poller.

If the registry is private, authenticate the **host Docker daemon** before wiring the timer. Coolify may have its own registry credentials for deploys, but the poller runs `docker pull` directly on the box, so Docker itself needs credentials:

```bash
docker login registry.example.com
# prove the poller will be able to pull before scheduling it:
docker pull vendor/app:latest
```

For a floating tag with no immutable fallback (such as `:latest` or `:stable`), record the current digest before enabling auto-update so rollback has a concrete target:

```bash
docker pull vendor/app:latest
PREVIOUS_DIGEST="$(docker inspect vendor/app:latest --format '{{index .RepoDigests 0}}')"
printf '%s\n' "$PREVIOUS_DIGEST" > ./vendor-app.previous-digest.txt
```

Use that digest in rollback (`vendor/app@sha256:...`) if the tag later moves to a bad image.

## Why route updates through Coolify, not Watchtower

Coolify owns the container's labels, injected env, and network wiring. If Watchtower (or a raw `docker pull && up -d`) recreates the container behind Coolify's back, the next Coolify reconcile can fight it or the recreate can drop Coolify-managed labels/networks. The robust pattern on a Coolify-managed box is:

1. A poller detects a new image digest.
2. It calls the **Coolify deploy API** for the resource UUID.
3. Coolify recreates the container correctly (`pull_policy: always` pulls the new image).
4. The poller waits for `running:healthy`.

## The poller logic (registry-agnostic)

Compare the running container's image ID against the freshly pulled tag. If they differ, redeploy.

```bash
IMAGE="vendor/app:latest"
CID="<container-name>"            # e.g. from: docker ps --format '{{.Names}}' | grep <svc>
UUID="<service-uuid>"
BASE="${COOLIFY_BASE_URL:-https://app.coolify.io}"

running_id="$(docker inspect "$CID" --format '{{.Image}}' 2>/dev/null || echo none)"
docker pull -q "$IMAGE" >/dev/null
latest_id="$(docker inspect "$IMAGE" --format '{{.Id}}')"

if [ "$running_id" != "$latest_id" ]; then
  curl -sf -H "Authorization: Bearer $COOLIFY_CLOUD_API_TOKEN" \
    "$BASE/api/v1/deploy?uuid=$UUID&force=false" || { echo "deploy trigger failed"; exit 1; }
  # then poll docker inspect until State.Status=running AND Health.Status=healthy AND Image=$latest_id
fi
```

Comparing image **IDs** (not tags) means "already up to date" is detected correctly and you do not trigger a needless restart when nothing changed. `scripts/auto-update-service.sh` implements exactly this loop, including the health wait.

## Scheduling: cross-platform (Linux systemd vs macOS launchd)

### Linux — systemd timer (recommended)

Install the bundled poller script somewhere stable first:

```bash
sudo cp scripts/auto-update-service.sh /usr/local/bin/auto-update-service.sh
sudo chmod +x /usr/local/bin/auto-update-service.sh
```

Create a service unit and a timer. Source the token file in the ExecStart shell because `EnvironmentFile=` does **not** parse the `export VAR=...` convention used by `~/.config/coolify-cloud.env`:

```ini
# /etc/systemd/system/coolify-autoupdate.service
[Unit]
Description=Auto-update a Coolify service to its latest image
Wants=network-online.target
After=network-online.target docker.service

[Service]
Type=oneshot
# ~/.config/coolify-cloud.env uses `export VAR=...`, which EnvironmentFile= can't parse,
# so source it in a shell instead of using EnvironmentFile=.
ExecStart=/bin/bash -c 'source %h/.config/coolify-cloud.env && exec /usr/local/bin/auto-update-service.sh --image vendor/app:latest --container my-svc --uuid SERVICE_UUID'
```

```ini
# /etc/systemd/system/coolify-autoupdate.timer
[Unit]
Description=Poll for a Coolify service update every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
RandomizedDelaySec=3min
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl daemon-reload
systemctl enable --now coolify-autoupdate.timer
systemctl list-timers coolify-autoupdate.timer   # confirm NEXT is scheduled
journalctl -u coolify-autoupdate.service -f       # watch update runs
```

Note: `%h` in a system unit resolves to root's home; for a user unit (`systemctl --user`) it resolves to that user's home. Use an absolute path if unsure.

### macOS — launchd agent

systemd does not exist on macOS. Use a `launchd` LaunchAgent that runs the script on an interval. Load the token by having the script `source "$HOME/.config/coolify-cloud.env"` itself (simplest cross-platform approach), or set env in the plist.

```xml
<!-- ~/Library/LaunchAgents/com.user.coolify-autoupdate.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.user.coolify-autoupdate</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>source "$HOME/.config/coolify-cloud.env" &amp;&amp; exec "$HOME/.local/bin/auto-update-service.sh" --image vendor/app:latest --container my-svc --uuid SERVICE_UUID</string>
  </array>
  <key>StartInterval</key><integer>1800</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>/tmp/coolify-autoupdate.log</string>
  <key>StandardErrorPath</key><string>/tmp/coolify-autoupdate.log</string>
</dict></plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.user.coolify-autoupdate.plist
launchctl list | grep coolify-autoupdate
```

### Portable fallback — cron

If neither is convenient, a cron entry works on both (macOS cron requires Full Disk Access for `cron` in some setups):

```cron
*/30 * * * * . "$HOME/.config/coolify-cloud.env"; /usr/local/bin/auto-update-service.sh --image vendor/app:latest --container my-svc --uuid SERVICE_UUID >> /tmp/coolify-autoupdate.log 2>&1
```

## Cadence

30 minutes is a sensible default for a daily-ish upstream. Do not poll a remote registry every minute — you gain nothing and add rate-limit risk. The pull check is cheap because Docker only downloads layers when the digest actually changed.

## Rollback

`:latest` can roll in a regression. To roll back:

1. `systemctl disable --now coolify-autoupdate.timer` (or unload the launchd agent) so it does not immediately re-advance.
2. `PATCH /services/{uuid}` with the image pinned to a known-good reference:
   - preferred: a version tag (`vendor/app:1.2.3`)
   - if the service only had a floating tag, use the digest you captured before enabling the timer (`vendor/app@sha256:<old-digest>`)
3. Include `instant_deploy:true`, then verify (`verify-and-troubleshoot.md`).
4. Re-enable the timer only after pinning to a reference you trust, or leave it disabled until upstream is fixed.

## Verify the poller before trusting it

Run the script once by hand and confirm it reports "already up to date" (or performs a controlled update and reaches `running:healthy`). A poller you never exercised is not a verified poller.
