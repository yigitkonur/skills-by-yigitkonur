# Fleet Mode

Fleet mode enables multi-profile Codex execution, rotating tasks across multiple Codex CLI installations to avoid rate limits and increase parallelism. This is an advanced feature — most users do not need it.

## Enabling Fleet Mode

Set the environment variable before starting the daemon:

```bash
export CODEX_ENABLE_FLEET=1
```

When active, the CLI appends a `[codex-worker-fleet]` sentinel to the `developer_instructions` of every spawned task. This sentinel is how the daemon tracks fleet-managed tasks internally.

## How It Works

### Profile rotation

Fleet mode uses multiple Codex CLI "profiles" — independent installations with their own auth tokens, config, and session state. Tasks are distributed across profiles in a round-robin pattern with cooldowns.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `CODEX_ENABLE_FLEET` | `0` | Set to `1` to enable fleet mode |
| `CODEX_HOME_DIRS` | — | Colon-separated list of profile root directories |
| `PROFILE_COOLDOWN_MS` | `60000` | Minimum ms between tasks on the same profile |

### Profile roots

Each entry in `CODEX_HOME_DIRS` is a directory containing a complete Codex CLI configuration:

```bash
export CODEX_HOME_DIRS="/Users/me/.codex-profile-a:/Users/me/.codex-profile-b:/Users/me/.codex-profile-c"
```

Each profile directory should contain:
- Valid authentication credentials
- Codex CLI configuration
- Independent session storage

### Rotation logic

```
Task arrives → pick profile with oldest last_used timestamp
  → if (now - last_used) >= PROFILE_COOLDOWN_MS → use this profile
  → else → try next profile
  → if all profiles are in cooldown → queue task until one is available
```

The cooldown prevents hitting per-account rate limits when dispatching many tasks rapidly.

## When to Use Fleet Mode

**Good use cases:**
- Dispatching 10+ parallel tasks that would hit single-account rate limits
- Running continuous integration pipelines with high task throughput
- Organizations with multiple Codex API accounts

**Not needed for:**
- Standard 1-5 parallel task workflows
- Sequential task chains
- Single-user development

## Setup Checklist

1. Install Codex CLI in multiple profile directories
2. Authenticate each profile independently
3. Set `CODEX_HOME_DIRS` to colon-separated list of profile roots
4. Set `CODEX_ENABLE_FLEET=1`
5. Restart the daemon
6. Verify by spawning a task and checking for `[codex-worker-fleet]` in developer_instructions

## Monitoring Fleet Tasks

Fleet tasks appear on the same scoreboard as regular tasks. The `[codex-worker-fleet]` sentinel in developer_instructions is the only distinguishing marker. Profile assignment is not exposed in the task metadata.

To see which profile handled a task, check the Codex CLI logs in the respective profile directory.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Tasks queue indefinitely | All profiles in cooldown | Add more profiles or reduce `PROFILE_COOLDOWN_MS` |
| Auth errors on some tasks | Profile credentials expired | Re-authenticate the specific profile |
| `[codex-worker-fleet]` missing | Fleet mode not enabled | Check `CODEX_ENABLE_FLEET=1` is set |
| Tasks all go to one profile | Other profiles misconfigured | Verify each profile directory exists and has valid config |

## Interaction with Other Features

- **Labels:** Work normally. Fleet-dispatched tasks can have labels like any other task.
- **depends_on:** Dependency chains work across profiles. The CLI handles sequencing regardless of which profile runs each task.
- **context_files:** File paths must be absolute and accessible from all profile roots.
- **`task cancel`:** Cancels the task regardless of which profile is running it.

## Security Note

Each profile directory contains authentication credentials. Protect these directories with appropriate filesystem permissions. Do not share profile roots between users or commit them to version control.
