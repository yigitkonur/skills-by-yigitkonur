# Event monitoring for long-running Herdr agents

Use this only when one bounded `herdr agent wait` is not enough: a long-running background agent, several lifecycle transitions, or a harness that should react immediately without polling.

## Prefer push events

Herdr's server exposes subscriptions over its local Unix socket. The behavior below was live-tested on the installed `0.7.5-preview.2026-07-21-0f10e1453a7f` build: `working` and `done` arrived roughly one second after each transition. Treat that as evidence for the method, not a promise about later builds. The installed schema always wins.

The CLI does not currently expose an `events` command group, so inspect the protocol first:

```bash
herdr status server
herdr api schema --json
```

The server status prints the socket path. The schema defines method names, fields, event kinds, and enum spellings.

## Wire model

The socket uses newline-delimited JSON:

1. Connect to the Unix socket.
2. Send one JSON request plus `\n`.
3. `events.subscribe` replies with `subscription_started`.
4. The connection then receives event envelopes until the client closes it.

A lifecycle event is shaped like:

```json
{"event":"pane.agent_status_changed","data":{"pane_id":"w1:p2","agent_status":"working"}}
```

Useful subscriptions include `pane.agent_status_changed`, `pane.output_matched`, `pane.agent_detected`, `pane.exited`, and workspace/tab/pane topology events.

Socket enum values can differ from CLI spelling. For example, the CLI reads `recent-unwrapped`, while the socket schema uses `recent_unwrapped`. Do not translate by intuition; inspect the schema.

## Bounded lifecycle watcher

This is an inline probe, not a bundled helper script. Submit the long-running prompt first, then start the watcher immediately: the subscription catches future transitions and the snapshot closes the race if the agent changed state before connection. Set the pane ID and deadline, then adapt each stdout line to the current harness's background-monitor facility:

```bash
PANE_ID="w1:p2"
DEADLINE_SECONDS=3600
SOCK=$(herdr status server | sed -n 's/^socket: //p')
test -n "$SOCK" && test -n "$PANE_ID"
python3 - "$SOCK" "$PANE_ID" "$DEADLINE_SECONDS" <<'PY'
import json
import socket
import subprocess
import sys
import time

socket_path, pane_id, deadline_text = sys.argv[1:]
deadline = time.monotonic() + int(deadline_text)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(socket_path)
request = {
    "id": "watch",
    "method": "events.subscribe",
    "params": {
        "subscriptions": [
            {"type": "pane.agent_status_changed", "pane_id": pane_id}
        ]
    },
}
sock.sendall((json.dumps(request) + "\n").encode())

buffer = b""
subscribed = False
try:
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print("monitor_timeout", flush=True)
            raise SystemExit(124)
        sock.settimeout(min(remaining, 30))
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            print("monitor_socket_closed", flush=True)
            raise SystemExit(1)
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            message = json.loads(line)
            if message.get("error"):
                print("monitor_error=" + json.dumps(message["error"]), flush=True)
                raise SystemExit(1)
            if message.get("id") == "watch":
                subscribed = message.get("result", {}).get("type") == "subscription_started"
                if not subscribed:
                    print("monitor_subscription_failed", flush=True)
                    raise SystemExit(1)
                print("subscribed", flush=True)
                snapshot = subprocess.run(
                    ["herdr", "agent", "get", pane_id],
                    capture_output=True, text=True, check=False,
                )
                if snapshot.returncode != 0:
                    print("monitor_snapshot_error=" + snapshot.stderr.strip(), flush=True)
                    raise SystemExit(1)
                try:
                    snapshot_data = json.loads(snapshot.stdout)
                    snapshot_state = snapshot_data["result"]["agent"]["agent_status"]
                except (json.JSONDecodeError, KeyError, TypeError):
                    print("monitor_snapshot_invalid=" + snapshot.stdout.strip(), flush=True)
                    raise SystemExit(1)
                print("snapshot_state=" + snapshot_state, flush=True)
                if snapshot_state in {"idle", "done", "blocked"}:
                    raise SystemExit(0)
                continue
            if message.get("event") == "pane.agent_status_changed":
                state = message["data"]["agent_status"]
                print("state=" + state, flush=True)
                if state in {"idle", "done", "blocked"}:
                    raise SystemExit(0)
finally:
    sock.close()
PY
```

The watcher validates the subscription acknowledgment, takes the required current-state snapshot, emits each status transition, exits on a settled state, reports socket/API failures, and has a hard deadline. A background harness should treat exit 0 as “settled — now read output,” exit 124 as timeout, and other nonzero exits as monitor failure.

## Events signal; reads prove

A status event only means classification changed. It does not include the full response and does not prove the requested task succeeded. After `idle`, `done`, or `blocked`:

```bash
herdr agent get <target>
herdr agent read <target> --source recent-unwrapped --lines 120
```

Then verify the task's real completion condition: tests, output file, runtime state, or the exact question awaiting input.

## Output-match subscriptions

For ordinary terminal processes, `pane.output_matched` can react to a narrow marker. Its schema includes:

```json
{
  "type": "pane.output_matched",
  "pane_id": "w1:p2",
  "source": "recent_unwrapped",
  "match": {"type": "substring", "value": "READY"}
}
```

Use a marker specific enough not to match old scrollback. The server may emit an immediate match from existing captured output; decide whether that behavior is desirable before treating it as new work.

## Recovery

- **No transition arrives:** the initial snapshot may already show a settled state; stop the watcher and read the agent.
- **`invalid_request`:** inspect the exact request definition in `herdr api schema --json`.
- **Socket closes:** read `herdr status server`; reconnect only after confirming the intended session is alive.
- **Too many events:** narrow the subscription or stdout filter. Never stream raw logs into conversation notifications.
- **Fallback polling is unavoidable:** use a deadline and emit every terminal state, not success only. In zsh, `status` is a read-only special variable; choose another loop variable name.

For one completion or one blocked state, return to `herdr agent wait`; the socket path is for workflows that genuinely need streaming.
