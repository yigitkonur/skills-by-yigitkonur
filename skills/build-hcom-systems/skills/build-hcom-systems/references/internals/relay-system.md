# hcom Relay System — Complete Reference

MQTT pub/sub for cross-device agent communication. Full implementation in `src/relay/`.

## MQTT Broker Setup

### Public Brokers (Default)

hcom ships with 3 public MQTT brokers tried in order during setup:
1. `broker.emqx.io:8883` (TLS)
2. `broker.hivemq.com:8883` (TLS)
3. `test.mosquitto.org:8886` (TLS)

First working broker pinned to config (`config.relay`). Broker list is append-only in `DEFAULT_BROKERS` to preserve v0x01 token compatibility (broker index encoded in token).

### Private Brokers

```bash
hcom relay new --broker mqtts://my-broker.com:8883
hcom relay new --broker mqtts://my-broker.com:8883 --password secret
```
Custom broker URL stored in `config.relay`. Authentication via `config.relay_token`.

### Broker Discovery

`relay/broker.rs` tests all public brokers in parallel via TCP+TLS handshake (no async runtime needed). First successful connection wins.

### Configuration Path

`~/.hcom/config.toml` under `[relay]`:
```toml
[relay]
id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
url = "mqtts://broker.emqx.io:8883"
token = "optional-password"
enabled = true
```

---

## Token System

### v0x01 (Public Broker)

Format: `0x01` + 16 UUID bytes + 1 broker index byte = 18 bytes -> ~24 char base64url

Compact because broker URL replaced with index into `DEFAULT_BROKERS`. Example: `AaGyw9Tl9niQq83vEjRWeJAA`

### v0x02 (Private Broker)

Format: `0x02` + 16 UUID bytes + broker URL string bytes = variable length base64url

Encodes full broker URL for maximum flexibility. Used when `--broker` flag specified.

### Device ID System

- **Device UUID**: 36-char UUID stored in `~/.hcom/.tmp/device_id` (created once, persists)
- **Device short ID**: 4-char CVCV word (consonant-vowel pattern) via FNV-1a hash
  - Examples: `VUNO`, `MOVA`, `REVA`, `BOXE`
  - Used in instance naming: `instance_name:SHORTID` (e.g., `luna:BOXE`)

### Token Sharing

```bash
hcom relay new                              # Generate and display token
hcom relay connect AaGyw9Tl...              # Join with token
hcom relay connect <token> --password X     # With auth for private broker
```

---

## Daemon Lifecycle

### Daemon Process

- Runs as `hcom relay-worker` (separate background process)
- Entry point: `src/relay/worker.rs::run()`
- PID file: `~/.hcom/.tmp/relay.pid`
- Auto-detaches via `setsid()` (survives terminal close)

### Startup

**Explicit:** `hcom relay daemon start` -> calls `ensure_worker(false)` with readiness polling

**Auto-start:** CLI operations (send, hooks) call `ensure_worker(true)`:
- `ensure_worker(true)`: Only spawn if active local instances exist (no-op if nothing to sync)
- `ensure_worker(false)`: Always spawn when relay is enabled (explicit command path)
- Polling: Waits up to 300-500ms for TCP notify port to become live before returning

### Auto-Exit Watchdog

Spawned as thread in worker process:
- Checks every 30s if any local (non-remote) instances exist
- If 0 instances for 2 consecutive checks -> sends shutdown command
- Prevents daemon from running indefinitely after all agents stopped

### Signal Handling

- SIGTERM/SIGINT -> triggers graceful shutdown
- Graceful shutdown publishes empty retained message to clear device state from broker
- PID file cleaned up on exit

### Daemon Status

```bash
hcom relay daemon status      # Shows PID if running
hcom relay daemon start       # Start worker
hcom relay daemon stop        # Graceful shutdown
hcom relay daemon restart     # Stop + start
```

**Health checking:**
- `is_relay_worker_running()`: checks PID file + validates process alive via `/proc`
- `is_relay_handled_by_daemon()`: TCP probe to `relay_daemon_port` with 100ms timeout

### CLI-to-Daemon Notify Port

Worker binds random TCP port on `127.0.0.1:0`:
- Port stored in KV: `relay_daemon_port`
- CLI operations connect (without sending data) to trigger immediate push
- Thread listens for incoming connections, each connection = Push command
- Enables sub-second push latency instead of waiting for 5s periodic cycle

---

## Push/Pull Sync Mechanism

### What Gets Synced

**State:** Current local instances (name, status, context, detail, parent, session, agent_id, directory, transcript)
**Events:** Recent activity (up to 100 per push cycle, batched with 10s drain budget)

**Exclusions:**
- Remote instances (`origin_device_id != ''`)
- Internal instances (name starts with `_` or `sys_`)
- Events with `_relay` marker (already imported, prevents loops)
- Control events (handled separately via control topic)

### Push Cycle (5s periodic or immediate)

1. `build_state()`: Snapshot all local instances (excluding remote)
2. `build_push_payload()`: Fetch up to 101 events since `relay_last_push_id` cursor
3. `push()`: Publish JSON to MQTT state topic `{relay_id}/{device_uuid}`
4. Advance cursor only after successful publish enqueue (rumqttc handles QoS retransmission)

**Push payload format:**
```json
{
  "state": {
    "instances": {
      "luna": {
        "status": "listening",
        "context": "poll",
        "detail": "",
        "parent": "",
        "session_id": "abc123",
        "agent_id": "f1a2b3c",
        "directory": "/home/user/project",
        "transcript": "/home/user/.claude/chats/...",
        "tag": "worker",
        "tool": "claude"
      }
    },
    "short_id": "VUNO",
    "reset_ts": 1704067200.0
  },
  "events": [
    {
      "id": 123,
      "ts": "2024-01-01T00:00:00Z",
      "type": "message",
      "instance": "luna",
      "data": {
        "from": "luna",
        "text": "hello",
        "scope": "broadcast",
        "sender_kind": "instance"
      }
    }
  ]
}
```

### Pull Cycle (on MQTT message arrival)

1. `handle_state_message()`: Receive state from remote device
2. **Collision detection**: Check if short_id already claimed by different device UUID
3. **Reset detection**: If remote `reset_ts` > cached `reset_ts`, delete old remote data and reimport
4. **Instance upsert**: INSERT ON CONFLICT for remote instances with device suffix (e.g., `luna:REVA`)
5. **Stale cleanup**: Delete instances no longer in remote state
6. **Event import**: Dedup by event ID, namespace instance names, import with `_relay` marker
7. **Wake notifications**: `notify_all_instances()` via TCP to wake local agents

### Conflict Resolution

- **Last-write-wins**: Status timestamp determines canonical state
- **Cursor-based dedup**: `relay_last_push_id` and `relay_events_{device_id}` prevent re-sending/re-importing
- **Device reset handling**: If remote max event ID < cached ID, assume DB recreated -> full clean reimport
- **ID regression detection**: Remote ID regression triggers deletion of all that device's data, then reimport

### Sync Frequency

- Default: 5s periodic push
- Immediate: CLI operations trigger via TCP notify (sub-second)
- Pull: Event-driven on MQTT message arrival (real-time)

---

## MQTT Topic Layout

```
{relay_id}/{device_uuid}     -> Retained state message per device
{relay_id}/control           -> Non-retained control events (shared)
{relay_id}/+                 -> Wildcard subscription pattern
```

### State Topic (`{relay_id}/{device_uuid}`)
- **Retained**: Persists on broker until device disconnects or publishes empty
- **Contains**: Full state snapshot + batched events
- **Updated**: Every 5s or on immediate push trigger
- **Empty payload**: On disconnect triggers `handle_device_gone()` on other devices

### Control Topic (`{relay_id}/control`)
- **Non-retained**: Ephemeral, lost if subscribers not connected
- **QoS**: AtLeastOnce (at-least-once delivery guarantee)
- **Used for**: Time-sensitive stop/kill commands targeting remote instances

**Control message format:**
```json
{
  "from_device": "<sender_uuid>",
  "events": [{
    "ts": 1234567890.0,
    "type": "control",
    "instance": "_control",
    "data": {
      "action": "stop",
      "target": "instance_name",
      "target_device": "REVA",
      "from": "_:VUNO",
      "from_device": "<sender_uuid>"
    }
  }]
}
```

### LWT (Last Will & Testament)
- Published automatically by MQTT broker on ungraceful disconnect
- Topic: state topic (`{relay_id}/{device_uuid}`)
- Payload: empty bytes
- Triggers `handle_device_gone()` on other devices -> deletes all remote instances from that device

---

## Remote Instance Visibility

### Instance Import and Namespacing
- Remote instances stored with `origin_device_id` field set to sender's device UUID
- Instance name suffix: `{original_name}:{SHORT_ID}` (e.g., `luna:REVA`)
- Appears in `hcom list` as remote (prefixed with device short ID)

### Parent/Dependency Resolution
- Parent instances also namespaced: `parent:REVA`
- Session ID preserved for agent tracking

### Device Visibility
```bash
hcom relay status  # Shows connected remote devices with instance counts
```
- Retrieved from KV: `relay_short_{short_id}` -> device_id
- Filtered by freshness: `relay_sync_time_{device_id}` must be < 90s old
- Instance counts per remote device via SQL `GROUP BY origin_device_id`

### Cleanup on Disconnect
- Empty retained payload (LWT or graceful disconnect) triggers `handle_device_gone()`
- Deletes all instances WHERE `origin_device_id = <device_uuid>`
- Clears per-device KV entries (cursors, timestamps, mappings)

---

## Cross-Device Message Routing

### Routing Flow

```
hcom send @luna:BOXE -- "hello"
  -> Event inserted locally with mentions=["luna:BOXE"]
  -> Push cycle syncs to remote device (via TCP trigger = sub-second)
  -> Remote imports event, delivers to local "luna" instance
  -> luna receives message via normal hook delivery
```

### Control Message Handling (`handle_control_events()`)

1. Parse incoming control event
2. Match `target_device` to own short ID (case-insensitive)
3. Match `action` ("stop", "kill", etc.)
4. Execute locally: call `stop_instance()` with `initiated_by=remote`
5. Dedup via timestamp: `relay_ctrl_{source_device}` cursor prevents re-processing

### Event Namespace Handling
- Strip own device suffix during import to avoid seeing `agent:VUNO` when sent to `agent`
- Namespace `from` field to match remote device origin
- ISO 8601 timestamps in push payload, converted to epoch f64 during import

---

## Error Handling and Resilience

### Connection Resilience
- Manual exponential backoff: 1s -> 2s -> 4s ... -> 60s max
- Re-subscribe on reconnect
- Auto-reconnect on connection errors
- TCP probe with 100ms timeout for daemon health check
- Stale PID detection: clears port after 3 consecutive TCP probe failures

### Push Reliability
- **QoS AtLeastOnce**: MQTT broker sends PUBACK, rumqttc handles retransmission
- **Cursor-based dedup**: If daemon crashes mid-push, cursor stays at old position, events re-sent next cycle
- **Batching**: 100 events per publish with 10s drain budget

### Pull Resilience
- Event ID dedup: Only imports if event_id > last_event_id
- Collision detection: Prevents cross-device data corruption if short_id collision occurs
- Reset detection: ID regression triggers full clean of device data
- Timestamp validation: Skips events older than local reset timestamp

---

## Performance

| Metric | Value |
|--------|-------|
| Push trigger latency | <50ms TCP connect |
| Publish enqueue | ~1-10ms (blocking channel) |
| Push cycle | 5s periodic or immediate |
| Pull (receive to import) | ~10-100ms |
| Event batch size | 100 per MQTT publish |
| State payload size | <10KB typical (10-20 instances) |

---

## Command Reference

```bash
# Setup
hcom relay new                                # Create relay group
hcom relay connect <token>                    # Join group
hcom relay connect <token> --password X       # With auth
hcom relay new --broker mqtts://host:port     # Private broker

# Management
hcom relay status                             # Show connection state
hcom relay on                                 # Enable
hcom relay off                                # Disable

# Daemon
hcom relay daemon start                       # Start worker
hcom relay daemon stop                        # Graceful shutdown
hcom relay daemon restart                     # Restart
hcom relay daemon status                      # Show PID
```

---

## KV Tracking Keys

| Key | Description |
|-----|-------------|
| `relay_status` | "ok", "error", "disconnected", "waiting" |
| `relay_last_error` | Error message if status="error" |
| `relay_daemon_port` | TCP port for CLI push notifications |
| `relay_daemon_fail_count` | Consecutive TCP probe failures (resets after 3) |
| `relay_last_push` | Last push timestamp |
| `relay_last_push_id` | Event cursor for push dedup |
| `relay_last_sync` | Global sync timestamp |
| `relay_events_{device_id}` | Per-device event import cursor |
| `relay_sync_time_{device_id}` | Per-device last sync time |
| `relay_reset_{device_id}` | Per-device reset timestamp |
| `relay_short_{short_id}` | Short ID -> device UUID mapping |
| `relay_ctrl_{source_device}` | Control message dedup cursor |

---

## File Reference

| File | Purpose |
|------|---------|
| `src/relay/mod.rs` | Broker config, device UUID, topic helpers, status tracking |
| `src/relay/broker.rs` | Parallel broker discovery via TCP+TLS |
| `src/relay/client.rs` | MQTT client lifecycle, connection event loop |
| `src/relay/token.rs` | v0x01/v0x02 token encoding/decoding |
| `src/relay/worker.rs` | Daemon process, PID file, auto-spawn, watchdog |
| `src/relay/push.rs` | Build state/events payload, publish to MQTT |
| `src/relay/pull.rs` | Receive state, upsert instances, import events |
| `src/relay/control.rs` | Build/send control messages, handle stops/kills |
| `src/commands/relay.rs` | CLI: new, connect, status |
| `src/commands/daemon.rs` | Daemon lifecycle: start, stop, restart, status |
