# Desktop IPC & Raycast Architecture Patterns (Manifest V3)

Verified: 2026-10-10 against Chrome Manifest V3 specifications and modern desktop companion architectures (Raycast Companion, 1Password, local AI daemons).

## Overview

Chrome Manifest V3 extensions operate within sandboxed browser processes where background tasks are executed by ephemeral service workers. To interact with host operating systems—such as triggering system automations, reading local files outside browser downloads, querying desktop app state, or integrating with productivity launchers like Raycast—extensions must bridge the boundary between the browser sandbox and the desktop runtime.

There are two primary architectural patterns to achieve desktop IPC:

1. **Local WebSocket Transport (Raycast Companion Architecture):**
   The desktop application or background daemon exposes an HTTP/WebSocket server on `127.0.0.1:<port>`. The extension service worker connects directly via `ws://127.0.0.1:<port>` using bidirectional JSON-RPC 2.0. An active heartbeat ping (<30s interval, typically 20–25s) resets the MV3 service worker idle timer, maintaining a persistent link without requiring native messaging host registration. Strict Cross-Site WebSocket Hijacking (CSWSH) defenses (HTTP `Origin` header validation and pre-shared authentication tokens) are mandatory.
2. **Native Messaging Protocol (`chrome.runtime.connectNative`):**
   Chrome acts as the IPC broker, spawning a registered native binary as a child process and communicating over standard input/output (`stdin`/`stdout`) using a 32-bit length-prefixed JSON wire protocol. An open `connectNative` port naturally keeps the MV3 service worker active. However, installation requires registering an OS-level JSON manifest file (or Windows Registry key), and responses sent from the native host to Chrome are strictly capped at 1 MB.

```
                      ┌──────────────────────────────────────────────┐
                      │          Chrome Extension (MV3)              │
                      │             Service Worker                   │
                      └───────┬──────────────────────────────┬───────┘
                              │                              │
         Pattern A: Local WS  │                              │  Pattern B: Native Messaging
         ws://127.0.0.1:port  │                              │  connectNative()
                              ▼                              ▼
                 ┌─────────────────────────┐   ┌───────────────────────────┐
                 │ Local Daemon / Desktop  │   │   Chrome Browser Engine   │
                 │ (Raycast, Node, Go, Rust)│   │       (IPC Broker)        │
                 └─────────────────────────┘   └─────────────┬─────────────┘
                                                             │ stdin/stdout
                                                             ▼ (32-bit uint prefix)
                                               ┌───────────────────────────┐
                                               │ Native Messaging Host App │
                                               │ (CLI tool, binary, script)│
                                               └───────────────────────────┘
```

---

## Architecture Comparison & Decision Matrix

| Dimension | Pattern A: Local WebSocket (Raycast Companion) | Pattern B: Native Messaging (`connectNative`) |
|---|---|---|
| **Installation Friction** | **Zero browser-side friction.** User only installs the desktop app. No OS config files or registry keys needed for the extension. | **High friction.** Requires installing a JSON manifest file into specific OS directories or creating Windows registry keys. Cannot be installed by extension alone. |
| **Web Store Review** | Standard review. Requires `host_permissions` for `http://127.0.0.1/*` (or `http://localhost/*`). | Heightened scrutiny for `nativeMessaging` permission in `permissions`. |
| **Cross-Origin Security** | **Requires active defenses.** Any web page can attempt `new WebSocket("ws://127.0.0.1:port")`. Server must validate `Origin` and enforce auth tokens. | **Enforced by Chrome.** Only extensions listed in `allowed_origins` in the host manifest can communicate. Web pages cannot access it. |
| **Service Worker Keepalive** | Requires active message transmission (<30s interval, e.g. 24s ping) to prevent MV3 idle termination (Chrome 116+). | An open `connectNative` port keeps the Service Worker alive automatically while the native host process runs. |
| **Process Management** | Desktop application runs independently; handles its own lifecycle and restarts. | Chrome spawns the native process on `connectNative` / `sendNativeMessage` and terminates it when the port closes. |
| **Payload Size Limits** | Standard WebSocket frame limits (virtually unlimited, constrained only by memory). | **Strict 1 MB limit** on messages sent from Native Host to Chrome. Chrome terminates host if exceeded. (Chrome to Host: up to 4 GB). |
| **Multi-Client Support** | Trivially supports multiple browser windows, profiles, or different browsers (e.g. Chrome + Arc + Brave) simultaneously. | 1 host process spawned per `connectNative()` call (higher memory footprint if multiple contexts connect). |
| **Debugging & Logging** | Normal console/logging. | Standard output (`stdout`) is strictly reserved for the binary wire protocol. Any `console.log()` to stdout immediately crashes the connection. All logs must go to `stderr`. |

### Decision Rule
- **Choose Local WebSocket** when building a companion for an existing desktop app (e.g., Raycast, Alfred, 1Password, local AI daemons), where the desktop app is already installed and running, or when you need bidirectional streaming without 1 MB limits.
- **Choose Native Messaging** when building a specialized hardware bridge, enterprise utility, or bundled system tool where a dedicated desktop installer (PKG/MSI/deb) already handles system provisioning, or where zero localhost network exposure is required.

---

## Pattern A: Local WebSocket Transport (Raycast Companion Architecture)

### Topology & Port Conventions
The Raycast Companion model connects the browser extension to a local WebSocket server hosted by the desktop application.
- **Binding Address:** Strictly `127.0.0.1` (IPv4 loopback) or `::1` (IPv6 loopback). **Never** `0.0.0.0`.
- **Port Strategy:** Reserve a dedicated port range (e.g. `7261` to `7265` for development, internal, debug, and release builds). If a single port is occupied, the client falls back sequentially through the port list.
- **Manifest Permissions:**
  ```jsonc
  {
    "manifest_version": 3,
    "host_permissions": [
      "http://127.0.0.1:*/*",
      "http://localhost:*/*"
    ]
  }
  ```

### Bidirectional JSON-RPC 2.0 Specification
All messages across the WebSocket connection must strictly conform to JSON-RPC 2.0:

#### 1. Client Request
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "browser.getActiveTabContext",
  "params": {
    "includeHtml": false,
    "includeSelection": true
  }
}
```

#### 2. Server Response (Success)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "url": "https://developer.chrome.com",
    "title": "Chrome for Developers",
    "selectedText": "Manifest V3 service workers..."
  }
}
```

#### 3. Server Response (Error)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": { "availableMethods": ["browser.getActiveTabContext", "ping"] }
  }
}
```

#### 4. Notification (No Response Expected)
```json
{
  "jsonrpc": "2.0",
  "method": "desktop.focusChanged",
  "params": { "isFocused": true }
}
```

#### Standard Error Codes:
- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid Request (missing required JSON-RPC 2.0 fields)
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000` to `-32099`: Server-defined application errors (e.g. `-32001: Unauthorized`)

### Service Worker Keepalive & Reconnection Strategy
In Chrome Manifest V3:
1. **Idle Expiration:** An idle Service Worker is terminated after ~30 seconds without events or network activity.
2. **WebSocket Activity (Chrome 116+):** Active message transmission over a WebSocket resets the 30-second idle timer. Opening an idle socket without traffic does not keep the worker alive.
3. **Keepalive Cadence:** The extension must send a heartbeat ping every **20 to 25 seconds** (e.g., 24 seconds, the exact cadence utilized by Raycast Companion).
4. **Alarm Safety Net:** In addition to internal `setInterval` keepalives (which only execute while the Service Worker is awake), configure a `chrome.alarms` fallback (e.g. every 1 minute) to revive the Service Worker if an unexpected network drop or system sleep terminates it.
5. **Exponential Backoff:** On socket close or connection refusal, retry with exponential backoff and jitter (`min: 1s`, `max: 30s`).

### Security: Cross-Site WebSocket Hijacking (CSWSH) Defense
Because web pages can execute `new WebSocket("ws://127.0.0.1:<port>")` without Cross-Origin Resource Sharing (CORS) preflight checks, a local WebSocket daemon is vulnerable to CSWSH unless hardened.

The local daemon MUST enforce the following four layers of defense:

1. **Strict HTTP Upgrade `Origin` Verification:**
   During the WebSocket upgrade handshake, the HTTP server inspects the `Origin` header.
   - For Chrome extensions, the browser sets `Origin: chrome-extension://<EXTENSION_ID>`.
   - The server must match this header against an allowlist containing only the trusted extension ID.
   - Requests from `http://`, `https://`, or untrusted extensions MUST be rejected immediately with HTTP `403 Forbidden` before completing the handshake.
2. **Host Header Validation (DNS Rebinding Defense):**
   Verify that `Host` is strictly `127.0.0.1:<port>` or `localhost:<port>`. Reject requests where `Host` represents an external domain that rebinds to `127.0.0.1`.
3. **Cryptographic Token Handshake:**
   The desktop application generates a cryptographically secure random session token (e.g. 256-bit hex). The extension supplies this token in the query string (`ws://127.0.0.1:7265?token=...`) or within an immediate `auth.handshake` message within 3 seconds of connecting. Connections failing the handshake are closed immediately.
4. **Localhost-Only Interface Binding:**
   The server socket must bind strictly to `127.0.0.1`. Never bind to `0.0.0.0` or expose the port to the local LAN.

---

### Production TypeScript Implementation: Extension WebSocket Client

This module runs in the extension Service Worker:

```typescript
// src/desktop/raycast-client.ts

export interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params?: Record<string, unknown>;
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: number;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

export interface JsonRpcNotification {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
}

export interface ClientOptions {
  ports: number[]; // e.g. [7265, 7264, 7263, 7262, 7261]
  authToken?: string;
  pingIntervalMs?: number; // Default 24000 (<30s)
  requestTimeoutMs?: number; // Default 10000
}

type NotificationHandler = (params?: Record<string, unknown>) => void;

export class DesktopWebSocketClient {
  private socket: WebSocket | null = null;
  private currentPortIndex = 0;
  private nextId = 1;
  private keepaliveTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pendingRequests = new Map<
    number,
    {
      resolve: (value: unknown) => void;
      reject: (reason: Error) => void;
      timer: ReturnType<typeof setTimeout>;
    }
  >();
  private notificationHandlers = new Map<string, Set<NotificationHandler>>();
  private isExplicitlyClosed = false;
  private backoffDelayMs = 1000;

  constructor(private options: ClientOptions) {
    this.options.pingIntervalMs = options.pingIntervalMs ?? 24_000;
    this.options.requestTimeoutMs = options.requestTimeoutMs ?? 10_000;
  }

  public connect(): void {
    this.isExplicitlyClosed = false;
    this.cleanupSocket();

    const port = this.options.ports[this.currentPortIndex];
    const url = new URL(`ws://127.0.0.1:${port}`);
    if (this.options.authToken) {
      url.searchParams.set("token", this.options.authToken);
    }

    try {
      this.socket = new WebSocket(url.toString());
      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
    } catch {
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    this.cleanupSocket();
  }

  public async request<T = unknown>(
    method: string,
    params?: Record<string, unknown>
  ): Promise<T> {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("Desktop WebSocket is not connected");
    }

    const id = this.nextId++;
    const payload: JsonRpcRequest = {
      jsonrpc: "2.0",
      id,
      method,
      params,
    };

    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error(`JSON-RPC request '${method}' (id: ${id}) timed out`));
      }, this.options.requestTimeoutMs);

      this.pendingRequests.set(id, {
        resolve: resolve as (value: unknown) => void,
        reject,
        timer,
      });

      this.socket!.send(JSON.stringify(payload));
    });
  }

  public notify(method: string, params?: Record<string, unknown>): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    const payload: JsonRpcNotification = {
      jsonrpc: "2.0",
      method,
      params,
    };
    this.socket.send(JSON.stringify(payload));
  }

  public on(method: string, handler: NotificationHandler): () => void {
    if (!this.notificationHandlers.has(method)) {
      this.notificationHandlers.set(method, new Set());
    }
    this.notificationHandlers.get(method)!.add(handler);
    return () => this.notificationHandlers.get(method)?.delete(handler);
  }

  private handleOpen(): void {
    this.backoffDelayMs = 1000;
    this.startKeepalive();
    this.notify("client.ready", {
      extensionId: chrome.runtime.id,
      timestamp: Date.now(),
    });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data) as
        | JsonRpcResponse
        | JsonRpcNotification;

      // Handle Request Response
      if ("id" in data && typeof data.id === "number") {
        const pending = this.pendingRequests.get(data.id);
        if (!pending) return;

        clearTimeout(pending.timer);
        this.pendingRequests.delete(data.id);

        if (data.error) {
          const err = new Error(data.error.message);
          Object.assign(err, { code: data.error.code, data: data.error.data });
          pending.reject(err);
        } else {
          pending.resolve(data.result);
        }
        return;
      }

      // Handle Server Notification
      if ("method" in data && typeof data.method === "string") {
        const handlers = this.notificationHandlers.get(data.method);
        if (handlers) {
          for (const handler of handlers) {
            handler(data.params);
          }
        }
      }
    } catch (e) {
      console.warn("Failed to parse incoming WebSocket message:", e);
    }
  }

  private handleClose(): void {
    this.cleanupSocket();
    if (!this.isExplicitlyClosed) {
      this.cyclePortOrBackoff();
    }
  }

  private handleError(): void {
    // onclose handles cleanup and reconnection
  }

  private startKeepalive(): void {
    if (this.keepaliveTimer) clearInterval(this.keepaliveTimer);
    // Ping cadence <30s to keep MV3 Service Worker alive
    this.keepaliveTimer = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.request("ping").catch(() => {
          this.socket?.close();
        });
      }
    }, this.options.pingIntervalMs);
  }

  private cyclePortOrBackoff(): void {
    this.currentPortIndex = (this.currentPortIndex + 1) % this.options.ports.length;
    if (this.currentPortIndex === 0) {
      const jitter = Math.random() * 500;
      this.scheduleReconnect(this.backoffDelayMs + jitter);
      this.backoffDelayMs = Math.min(this.backoffDelayMs * 2, 30_000);
    } else {
      this.connect();
    }
  }

  private scheduleReconnect(delay = 1000): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  private cleanupSocket(): void {
    if (this.keepaliveTimer) {
      clearInterval(this.keepaliveTimer);
      this.keepaliveTimer = null;
    }
    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onmessage = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.close();
      }
      this.socket = null;
    }
    for (const [, req] of this.pendingRequests.entries()) {
      clearTimeout(req.timer);
      req.reject(new Error("Desktop connection closed"));
    }
    this.pendingRequests.clear();
  }
}
```

---

### Production TypeScript Implementation: Desktop Daemon (Node.js/Bun)

This module executes in the host environment as part of the desktop application:

```typescript
// desktop-daemon/server.ts
import http from "node:http";
import { WebSocketServer, WebSocket } from "ws";

const ALLOWED_EXTENSION_IDS = new Set([
  "abcdefghijklmnopabcdefghijklmnop", // Replace with your extension ID
]);
const EXPECTED_AUTH_TOKEN = process.env.DESKTOP_IPC_SECRET || "dev-secret-token";
const PORT = 7265;
const HOST = "127.0.0.1"; // STRICT LOOPBACK BINDING

const server = http.createServer((req, res) => {
  res.writeHead(404);
  res.end();
});

const wss = new WebSocketServer({ noServer: true });

// CSWSH Defense: HTTP Upgrade Handler
server.on("upgrade", (req, socket, head) => {
  const origin = req.headers["origin"] || "";
  const host = req.headers["host"] || "";

  // 1. Verify Host header (DNS Rebinding defense)
  if (!host.startsWith("127.0.0.1") && !host.startsWith("localhost")) {
    socket.write("HTTP/1.1 403 Forbidden\r\n\r\n");
    socket.destroy();
    return;
  }

  // 2. Verify Origin header (Strict Extension Allowlist)
  // Format: chrome-extension://<EXTENSION_ID>
  const match = origin.match(/^chrome-extension:\/\/([a-z0-9]{32})$/);
  if (!match || !ALLOWED_EXTENSION_IDS.has(match[1])) {
    console.warn(`[IPC Server] Rejected CSWSH connection from Origin: ${origin}`);
    socket.write("HTTP/1.1 403 Forbidden\r\n\r\n");
    socket.destroy();
    return;
  }

  // 3. Verify Pre-Shared Token in Query Params
  const reqUrl = new URL(req.url || "/", `http://${req.headers.host}`);
  const token = reqUrl.searchParams.get("token");
  if (token !== EXPECTED_AUTH_TOKEN) {
    console.warn(`[IPC Server] Invalid or missing auth token from ${origin}`);
    socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
    socket.destroy();
    return;
  }

  // Upgrade accepted
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit("connection", ws, req);
  });
});

// JSON-RPC 2.0 Dispatcher
wss.on("connection", (ws: WebSocket) => {
  console.log("[IPC Server] Extension connected securely.");

  ws.on("message", (raw: string) => {
    try {
      const msg = JSON.parse(raw);
      if (!msg || msg.jsonrpc !== "2.0") return;

      // Ping Heartbeat Handler
      if (msg.method === "ping") {
        ws.send(JSON.stringify({ jsonrpc: "2.0", id: msg.id, result: "pong" }));
        return;
      }

      // Application Methods
      if (msg.method === "browser.getActiveTabContext") {
        ws.send(
          JSON.stringify({
            jsonrpc: "2.0",
            id: msg.id,
            result: { status: "ready", appVersion: "1.0.0" },
          })
        );
        return;
      }

      // Method Not Found
      if (typeof msg.id !== "undefined") {
        ws.send(
          JSON.stringify({
            jsonrpc: "2.0",
            id: msg.id,
            error: { code: -32601, message: `Method '${msg.method}' not found` },
          })
        );
      }
    } catch {
      ws.send(
        JSON.stringify({
          jsonrpc: "2.0",
          id: null,
          error: { code: -32700, message: "Parse error" },
        })
      );
    }
  });
});

server.listen(PORT, HOST, () => {
  console.log(`[IPC Server] Listening securely on ws://${HOST}:${PORT}`);
});
```

---

## Pattern B: Native Messaging Protocol

### Process Model & Chrome Broker
When an extension invokes `chrome.runtime.connectNative(hostName)` or `chrome.runtime.sendNativeMessage(hostName, message)`:
1. Chrome verifies the extension's `manifest.json` declares `"nativeMessaging"` in `permissions`.
2. Chrome searches operating system manifest directories for `<hostName>.json`.
3. Chrome parses the host manifest and verifies the extension's ID is explicitly listed in `allowed_origins`.
4. Chrome executes the binary specified in `path` as a child process with standard streams:
   - `stdin`: Pipe from Chrome to Host.
   - `stdout`: Pipe from Host to Chrome.
   - `stderr`: Redirected to Chrome's console/standard error output.
5. While the port is open and the process runs, Chrome's broker maintains the link, keeping the MV3 service worker active.

### Binary Stdio Wire Protocol Specification
All messages across `stdin` and `stdout` are framed as:

```
+-----------------------------------+-----------------------------------+
| 32-bit uint Length Prefix (4 bytes)| UTF-8 Encoded JSON String Payload |
+-----------------------------------+-----------------------------------+
```

- **Byte Order:** Native byte order (little-endian on x86, x64, ARM64).
- **Header:** 4 bytes representing an unsigned 32-bit integer (`uint32`).
- **Payload Limits:**
  - **Host to Chrome:** **1 MB maximum (1,048,576 bytes)**. Exceeding 1 MB causes Chrome to immediately terminate the host and close the port with an error.
  - **Chrome to Host:** 4 GB maximum.
- **The Stdio Rule (CRITICAL):**
  Standard output (`stdout`) belongs exclusively to the binary wire protocol. Never write debug statements, logs, or unformatted text to `stdout` (`console.log()` or `print()`). Any stray character written to `stdout` corrupts the 4-byte length prefix, causing Chrome to fail message parsing and crash the connection. All logging must be directed to `stderr` (`console.error()` or `process.stderr.write()`).

### Native Host Manifest Specification
A native messaging host manifest is a JSON file named `<name>.json`:

```json
{
  "name": "com.mycompany.myhost",
  "description": "Desktop Native Messaging Bridge",
  "path": "/usr/local/bin/my-native-host",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://kniljahocnnipgnmhnenbhllihapadbh/"
  ]
}
```

*Note: The `allowed_origins` entry must include the trailing slash (`/`).*

### OS-Specific Installation Locations

#### macOS
- **Per-User (Recommended):**  
  `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.mycompany.myhost.json`
- **System-Wide:**  
  `/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.mycompany.myhost.json`
- *Other Chromium Browsers on macOS:*
  - Brave: `~/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts/`
  - Edge: `~/Library/Application Support/Microsoft Edge/NativeMessagingHosts/`
  - Chromium: `~/Library/Application Support/Chromium/NativeMessagingHosts/`

#### Linux
- **Per-User (Recommended):**  
  `~/.config/google-chrome/NativeMessagingHosts/com.mycompany.myhost.json`
- **System-Wide:**  
  `/etc/opt/chrome/native-messaging-hosts/com.mycompany.myhost.json`
- *Chromium on Linux:*  
  `~/.config/chromium/NativeMessagingHosts/`

#### Windows
Manifest files are registered via the Windows Registry pointing to the manifest file on disk.
- **Per-User (Recommended):**  
  `HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.mycompany.myhost`
- **System-Wide:**  
  `HKEY_LOCAL_MACHINE\Software\Google\Chrome\NativeMessagingHosts\com.mycompany.myhost`
- **Value:** Set the default key value `(Default)` of type `REG_SZ` to the full path of the manifest file:
  `C:\Program Files\MyCompany\com.mycompany.myhost.json`

---

### Production TypeScript Implementation: Extension Native Client

This module runs in the extension Service Worker:

```typescript
// src/desktop/native-client.ts

export interface NativeClientOptions {
  hostName: string;
  autoReconnect?: boolean;
}

export class NativeMessagingClient {
  private port: chrome.runtime.Port | null = null;
  private messageListeners = new Set<(msg: unknown) => void>();
  private disconnectListeners = new Set<(error?: string) => void>();
  private isConnecting = false;

  constructor(private options: NativeClientOptions) {}

  public connect(): void {
    if (this.port || this.isConnecting) return;
    this.isConnecting = true;

    try {
      this.port = chrome.runtime.connectNative(this.options.hostName);

      this.port.onMessage.addListener((msg) => {
        for (const listener of this.messageListeners) {
          listener(msg);
        }
      });

      this.port.onDisconnect.addListener(() => {
        const err = chrome.runtime.lastError?.message;
        console.warn(`[NativeIPC] Disconnected: ${err ?? "Normal closure"}`);
        this.port = null;
        this.isConnecting = false;

        for (const listener of this.disconnectListeners) {
          listener(err);
        }

        if (this.options.autoReconnect) {
          setTimeout(() => this.connect(), 2000);
        }
      });

      this.isConnecting = false;
      console.log(`[NativeIPC] Connected to native host: ${this.options.hostName}`);
    } catch (err) {
      this.isConnecting = false;
      console.error("[NativeIPC] Failed to connectNative:", err);
    }
  }

  public postMessage(message: unknown): void {
    if (!this.port) {
      throw new Error("Cannot postMessage: Native port is not connected");
    }
    this.port.postMessage(message);
  }

  public disconnect(): void {
    if (this.port) {
      this.port.disconnect();
      this.port = null;
    }
  }

  public onMessage(handler: (msg: unknown) => void): () => void {
    this.messageListeners.add(handler);
    return () => this.messageListeners.delete(handler);
  }

  public onDisconnect(handler: (error?: string) => void): () => void {
    this.disconnectListeners.add(handler);
    return () => this.disconnectListeners.delete(handler);
  }

  // One-off request without maintaining a persistent port
  public static async sendOneShot<T = unknown>(
    hostName: string,
    message: unknown
  ): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      chrome.runtime.sendNativeMessage(hostName, message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response as T);
        }
      });
    });
  }
}
```

---

### Production Node.js Implementation: Native Messaging Host Binary

This executable executes on the desktop host, invoked directly by Chrome:

```typescript
#!/usr/bin/env node
// native-host.ts (Build and compile or run with Node/tsx)
import process from "node:process";

// REDIRECT ALL LOGS TO STDERR! STDOUT MUST BE 100% PURE WIRE PROTOCOL!
function logDebug(...args: unknown[]): void {
  process.stderr.write(`[Host] ${args.map(String).join(" ")}\n`);
}

const MAX_PAYLOAD_BYTES = 1024 * 1024; // 1 MB limit

class NativeHostStdioBridge {
  private buffer = Buffer.alloc(0);

  constructor() {
    process.stdin.on("data", this.handleChunk.bind(this));
    process.stdin.on("end", () => {
      logDebug("stdin ended, exiting host.");
      process.exit(0);
    });
  }

  private handleChunk(chunk: Buffer): void {
    this.buffer = Buffer.concat([this.buffer, chunk]);

    while (this.buffer.length >= 4) {
      const msgLen = this.buffer.readUInt32LE(0);

      if (this.buffer.length < 4 + msgLen) {
        break; // Wait for more data
      }

      const payloadBuf = this.buffer.subarray(4, 4 + msgLen);
      this.buffer = this.buffer.subarray(4 + msgLen);

      try {
        const jsonStr = payloadBuf.toString("utf-8");
        const message = JSON.parse(jsonStr);
        this.processMessage(message);
      } catch (err) {
        logDebug("JSON decode error:", err);
      }
    }
  }

  private processMessage(msg: Record<string, unknown>): void {
    logDebug("Received message:", JSON.stringify(msg));

    if (msg.action === "PING") {
      this.sendMessage({ status: "PONG", timestamp: Date.now() });
      return;
    }

    if (msg.action === "GET_SYSTEM_INFO") {
      this.sendMessage({
        platform: process.platform,
        arch: process.arch,
        nodeVersion: process.version,
      });
      return;
    }

    this.sendMessage({ error: "Unknown action" });
  }

  public sendMessage(obj: unknown): void {
    const jsonStr = JSON.stringify(obj);
    const payload = Buffer.from(jsonStr, "utf-8");

    if (payload.length > MAX_PAYLOAD_BYTES) {
      logDebug(`ERROR: Message length (${payload.length}) exceeds 1MB limit!`);
      const errorPayload = Buffer.from(
        JSON.stringify({ error: "PAYLOAD_TOO_LARGE_EXCEEDED_1MB" }),
        "utf-8"
      );
      this.writeFrame(errorPayload);
      return;
    }

    this.writeFrame(payload);
  }

  private writeFrame(payload: Buffer): void {
    const header = Buffer.alloc(4);
    header.writeUInt32LE(payload.length, 0);
    process.stdout.write(Buffer.concat([header, payload]));
  }
}

new NativeHostStdioBridge();
logDebug("Native messaging host initialized and waiting for stdin.");
```

---

### Host Installation Scripts

#### macOS & Linux Setup Script (`install-host.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail

HOST_NAME="com.mycompany.myhost"
EXTENSION_ID="kniljahocnnipgnmhnenbhllihapadbh" # Replace with real Extension ID
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_BIN="${SCRIPT_DIR}/native-host"

chmod +x "${TARGET_BIN}"

if [[ "$OSTYPE" == "darwin"* ]]; then
  TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
else
  TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
fi

mkdir -p "$TARGET_DIR"

MANIFEST_PATH="${TARGET_DIR}/${HOST_NAME}.json"

cat <<EOF > "$MANIFEST_PATH"
{
  "name": "${HOST_NAME}",
  "description": "Desktop Native Messaging Host",
  "path": "${TARGET_BIN}",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://${EXTENSION_ID}/"
  ]
}
EOF

chmod 644 "$MANIFEST_PATH"
echo "Successfully installed native host manifest to: $MANIFEST_PATH"
```

#### Windows Registry Setup (`install-host.reg`)
```ini
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.mycompany.myhost]
@="C:\\Program Files\\MyCompany\\com.mycompany.myhost.json"
```
