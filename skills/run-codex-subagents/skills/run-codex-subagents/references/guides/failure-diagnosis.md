# Failure Diagnosis

Use this sequence whenever a thread fails or stalls.

## 1. Check daemon and runtime health

```bash
codex-worker --output json doctor
codex-worker daemon status
```

Look for:
- `daemonRunning`
- `profiles`
- `stateRoot`

## 2. Inspect the failing thread

```bash
codex-worker read <thread-id>
codex-worker logs <thread-id>
```

Key clues:
- `Status: failed`
- `Pending requests: <n>`
- readable error lines in `displayLog`
- transcript and log paths under `artifacts`

## 3. Separate blocked from failed

Blocked:

```bash
codex-worker request list
codex-worker request read <request-id>
```

Failed:
- the turn already stopped
- `request list` is empty or unrelated
- `logs` contains the actual runtime error

## 4. Inspect account and model surfaces

```bash
codex-worker account read
codex-worker account rate-limits
codex-worker model list
```

Use this when a failure looks auth-, quota-, or model-selection-related.

## Common Cases

### `Codex reported an error.`

This is the generic runtime failure bucket. Inspect `logs`, the transcript, and the repo state before retrying blindly.

### Pending request but no progress

You answered the request incorrectly, or the turn hit a second request. Re-run:

```bash
codex-worker request list
codex-worker wait --thread-id <thread-id>
```

### No useful output in `logs`

Tail the raw files directly:

```bash
tail -f "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.logPath')"
jq . "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.transcriptPath')"
```
