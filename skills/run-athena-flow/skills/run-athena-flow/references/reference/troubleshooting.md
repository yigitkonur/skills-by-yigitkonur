# Troubleshooting

## Harness not found

**Symptom:** `Claude Code not detected` or `Codex not detected` at startup.

**Cause:** Athena runs `detectVersion()` at startup and can't find the harness binary.

**Fix:**
- For Claude Code: install and verify with `claude --version`
- For Codex: install and verify with `codex --version` (minimum 0.37.0)
- Ensure the binary is on your `PATH`

## Socket connection failure

**Symptom:** Events don't appear in the feed. Hook forwarder exits with connection errors.

**Cause:** The Unix Domain Socket at `<projectDir>/.claude/run/ink-<PID>.sock` failed to open or was removed.

**Fix:**
- Check if another Athena instance is running on the same project
- Verify the `.claude/run/` directory exists and is writable
- Restart Athena — the socket is created fresh on startup

## Hook timeout / auto-passthrough

**Symptom:** Tool calls proceed without Athena evaluating them. Feed shows events arriving late.

**Cause:** The hook forwarder has a 5-second auto-passthrough timeout. If Athena can't respond in time, the forwarder exits with code `0` (allow). Permission and question events have a 5-minute timeout.

**Fix:**
- Check system load — SQLite writes and policy evaluation should be sub-millisecond
- If running in degraded mode (SQLite unavailable), the bottleneck may be the fallback in-memory store

## Session corruption / can't resume

**Symptom:** `athena-flow resume` fails or shows incomplete data.

**Cause:** The SQLite database at `~/.config/athena/sessions/<uuid>/session.db` may be corrupted (disk full during write, forced kill).

**Fix:**
- Try opening the database with `sqlite3` to check: `sqlite3 ~/.config/athena/sessions/<uuid>/session.db ".tables"`
- If corrupted, delete the session directory — that session's history is lost but Athena will work normally for new sessions

## Plugin loading errors

**Symptom:** `Plugin not found` or `Missing plugin.json` errors at startup.

**Cause:** The plugin path doesn't point to a valid plugin directory (missing `.claude-plugin/plugin.json`).

**Fix:**
- Verify the path: `ls <plugin-path>/.claude-plugin/plugin.json`
- For marketplace refs, check that the marketplace repo is accessible: `ls ~/.config/athena/marketplaces/<owner>/<repo>/`
- If offline, Athena uses the cached marketplace. If no cache exists, the plugin can't be resolved

## MCP server name collision

**Symptom:** `MCP server name collision: "my-server" is defined by multiple plugins.`

**Cause:** Two loaded plugins define MCP servers with the same name.

**Fix:** Rename one of the MCP servers in its plugin's `.mcp.json` file. Names must be unique across all loaded plugins.

## Degraded mode

**Symptom:** Header shows degraded state indicator. Sessions can't be resumed.

**Cause:** SQLite database can't be opened (disk full, permissions, locked by another process).

**Fix:**
- Check disk space: `df -h`
- Check permissions on `~/.config/athena/sessions/`
- If another Athena instance holds a WAL lock, close it first

## Workflow not found

**Symptom:** `Workflow "my-workflow" not found in local registry.`

**Cause:** The workflow hasn't been installed. `--workflow` looks up `~/.config/athena/workflows/<name>/workflow.json`.

**Fix:**

```bash
athena workflow install my-workflow@owner/repo --name my-workflow
```

## Debug logging

Set `ATHENA_DEBUG=1` to enable verbose debug output from hook registration and the socket server:

```bash
ATHENA_DEBUG=1 athena-flow
```

## Stale socket files

**Symptom:** Socket errors or connection refused on startup.

**Cause:** Previous Athena instance crashed without cleaning up the `.sock` file.

**Fix:** Athena includes a `cleanupStaleSockets()` function that removes stale `.sock` files automatically. If this doesn't work, manually remove:

```bash
rm <projectDir>/.claude/run/ink-*.sock
```
