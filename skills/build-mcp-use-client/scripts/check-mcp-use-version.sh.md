# check-mcp-use-version.sh

Read-only preflight for `mcp-use` client projects.

## Usage

```bash
bash scripts/check-mcp-use-version.sh
bash scripts/check-mcp-use-version.sh /path/to/project
```

Run it from the skill directory or pass an explicit project root. It does not edit files, install packages, or write project-local output.

## What It Checks

| Check | Source |
|---|---|
| local Node version | `node -p process.versions.node` |
| package manager hints | lockfiles in the project root |
| declared `mcp-use` version | `package.json` dependency fields |
| installed `mcp-use` version | `node_modules/mcp-use/package.json`, when present |
| latest package metadata | `npm view mcp-use version engines peerDependencies --json` |
| Node engine compatibility | local semver check for common npm range forms |
| stale declared or installed version | compares first semver in the spec and installed version to npm latest |

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Completed, including warning-only findings |
| `2` | Hard prerequisite missing: Node, npm, or project root |
| `3` | `package.json` exists but is not parseable JSON |

If `npm view` cannot reach the registry, the script prints a warning and exits `0` because no project state is changed and the local checks still ran.

## Interpretation

Warnings are diagnostic, not an automatic upgrade instruction. Use them to decide whether the project should update Node, reinstall dependencies, or refresh examples before implementation.
