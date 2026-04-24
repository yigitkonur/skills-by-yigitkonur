# `.mcp-use/project.json`

Project-local link between this working copy and a specific cloud deployment. This is the **one** file that makes `mcp-use deploy` remember where to ship code to.

Source: `libraries/typescript/packages/cli/src/utils/project-link.ts`. Exports:

- `MCP_USE_DIR = ".mcp-use"`
- `MCP_USE_DIR_PROJECT = "project.json"`

---

## Schema

```ts
export interface ProjectLink {
  deploymentId: string;
  deploymentName: string;
  deploymentUrl?: string;
  linkedAt: string;  // ISO timestamp
  serverId?: string;
}
```

Example on disk:

```json
{
  "deploymentId": "dep_01HZABC123...",
  "deploymentName": "acme-mcp",
  "deploymentUrl": "https://acme-mcp.mcp-use.com",
  "linkedAt": "2025-11-20T18:42:07.551Z",
  "serverId": "srv_01HZDEF456..."
}
```

Fields:

| Field | Required | Notes |
|---|---|---|
| `deploymentId` | Yes | UUID the CLI calls `restart`/`get`/etc. against. If this stops resolving server-side → HTTP 404 on redeploy. |
| `deploymentName` | Yes | Used in CLI output so the user sees the name, not just the id. |
| `deploymentUrl` | No | Stored for convenience (`--open`, copy in logs). |
| `linkedAt` | Yes | ISO 8601 timestamp of the initial link. |
| `serverId` | No | When present, short-circuits the "find server by deployment" API call. |

---

## Lifecycle

### When it's created

- Written by `saveProjectLink()` immediately after `mcp-use deploy` **succeeds for the first time** in a given `cwd`.
- Not created by `mcp-use login`, `mcp-use whoami`, or any local build command.
- Creation flow:
  1. `mkdir -p .mcp-use/` if missing
  2. Write `.mcp-use/project.json` with the four required fields
  3. Append `.mcp-use` to `.gitignore` (with a `# mcp-use deployment` comment header) if not already present

### When it's read

- Beginning of every subsequent `mcp-use deploy` run, unless `--new` is passed.
- The CLI calls `readProjectLink()`; if the file exists and parses, it hits the API with `deploymentId` and issues a new deployment on that server.
- If the file is missing, malformed, or the `deploymentId` 404s, the CLI falls back to the "new server" path.

### When it's updated

- On **any** successful deploy from this `cwd` (including `--new`). Fields are refreshed; `linkedAt` is bumped each time.
- If `--new` + `--org <different>` is used, the file now points at a deployment in a different org.

### How to unlink

Three ways, pick the one that matches intent:

1. **Delete the file.** Safest for a one-off break.
   ```bash
   rm .mcp-use/project.json
   ```
   Next `deploy` creates a fresh link.

2. **Force-new on deploy.** Keeps `.mcp-use/` around; overwrites link after.
   ```bash
   mcp-use deploy --new --yes
   ```
   Useful when you want to keep the local link file but ship to a new deployment.

3. **Cross-org new server.** Force a completely different org.
   ```bash
   mcp-use deploy --new --org other-org --yes
   ```

---

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `mcp-use deploy` → HTTP 404 referencing the deployment id | The linked deployment was deleted (via `deployments delete` or dashboard) | `rm .mcp-use/project.json` or `mcp-use deploy --new` |
| `deploy` sends updates to a dead server | Linked server was deleted; deployment id still technically exists but server metadata gone | Same: delete the link file or `--new` |
| "Org mismatch" style failure when you `mcp-use org switch`ed recently | Active org in `~/.mcp-use/config.json` ≠ org owning the linked deployment | Pass `--org <slug>` on deploy, or `--new --org <slug>` to re-link into the active org |
| Parse error on deploy start | Hand-edited `project.json` with invalid JSON | Delete and re-deploy |
| Link missing after `git clone` | `.mcp-use/` is gitignored by design — the link is per-machine | First-run teammate should `mcp-use deploy --new` or ask the original dev to document the target server/deployment |
| Two teammates redeploying same server step on each other | Both have valid `project.json` pointing at the same deployment | Normal; each deploy replaces the running instance. If undesired, put per-env servers behind different branches / orgs. |

---

## Relation to `.gitignore`

`saveProjectLink()` appends `.mcp-use` (the whole directory) to `.gitignore`. This means:

- `project.json`, `sessions.json`, `tool-registry.d.ts` all stay out of git by default.
- Switching machines requires re-linking (`mcp-use deploy` or manual recreation).
- If you want `tool-registry.d.ts` committed, unignore it explicitly:
  ```
  # keep tool-registry.d.ts under version control
  !.mcp-use/tool-registry.d.ts
  ```
  after the auto-appended `.mcp-use` block.
