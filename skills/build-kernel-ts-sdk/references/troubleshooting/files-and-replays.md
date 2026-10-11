# File I/O and replays — troubleshooting

Each browser exposes a VM filesystem (`kernel.browsers.fs.*`) and a recording API (`kernel.browsers.replays.*`). Most issues come from misunderstanding when artifacts become available.

## File I/O surface

```ts
// writeFile takes `contents` as a positional second arg (raw bytes/string,
// sent as application/octet-stream — no encoding param). For text, pass the
// string directly; for binary, pass a Buffer/Uint8Array.
await kernel.browsers.fs.writeFile(id, JSON.stringify(obj), { path: '/tmp/data.json' });

const resp = await kernel.browsers.fs.readFile(id, { path: '/tmp/data.json' });
const text = await resp.text();        // Response object — pick text/arrayBuffer/blob

// listFiles returns a bare Array<...> (no `.items` wrapper)
const files = await kernel.browsers.fs.listFiles(id, { path: '/tmp' });
const info = await kernel.browsers.fs.fileInfo(id, { path: '/tmp/data.json' });

// upload takes a `files` array of { dest_path, file }
await kernel.browsers.fs.upload(id, {
  files: [{ dest_path: '/tmp/upload.zip', file: fs.createReadStream('./local.zip') }],
});
// uploadZip uses `dest_path` + `zip_file`
await kernel.browsers.fs.uploadZip(id, { dest_path: '/tmp/extract', zip_file: zip });
const dl = await kernel.browsers.fs.downloadDirZip(id, { path: '/tmp/extract' });

// move uses `src_path` + `dest_path` (not from/to)
await kernel.browsers.fs.move(id, { src_path: '/tmp/a', dest_path: '/tmp/b' });
await kernel.browsers.fs.deleteFile(id, { path: '/tmp/a' });
await kernel.browsers.fs.createDirectory(id, { path: '/tmp/dir' });
await kernel.browsers.fs.deleteDirectory(id, { path: '/tmp/dir' });
// `mode` is a string (chmod-style), NOT a JS octal number. '0644' or '644', not 0o644.
await kernel.browsers.fs.setFilePermissions(id, { path: '/tmp/a', mode: '0644' });

// Watch for changes — note watch.events and watch.stop take watch_id as
// the FIRST positional arg (the browser session id goes in params). Also
// note: `watch.start` returns `watch_id` as OPTIONAL — guard before use.
const watch = await kernel.browsers.fs.watch.start(id, { path: '/tmp', recursive: true });
if (!watch.watch_id) throw new Error('watch.start did not return a watch_id');
for await (const evt of await kernel.browsers.fs.watch.events(watch.watch_id, { id_or_name: id })) {
  // evt.type is the uppercase enum: 'CREATE' | 'WRITE' | 'DELETE' | 'RENAME'
  // evt.path is the affected absolute path.
}
await kernel.browsers.fs.watch.stop(watch.watch_id, { id_or_name: id });
```

## Common file-I/O issues

### Where downloads land and how to read them

Files exist only while the browser session is alive; deleting the browser (or its timeout) permanently deletes everything in the VM, so read them out first.

A user-initiated download (a click) is saved to the default download directory, `/home/kernel/Downloads` (also what Stagehand v4 gets with no configuration). With CDP, enable download events and read the final path from `Browser.downloadProgress`:

```ts
const client = await context.newCDPSession(page);
await client.send('Browser.setDownloadBehavior', { behavior: 'default', eventsEnabled: true });
// client.on('Browser.downloadProgress', e => e.state === 'completed' ? e.filePath : …)
```

A download triggered programmatically (JavaScript, not a click) is blocked by Chromium under `'default'`: use `behavior: 'allow'` with a `downloadPath` such as `/tmp/downloads`.

Then poll the VM filesystem until the file is listed (skip in-progress `*.crdownload` files) and read it:

```ts
import { dirname, basename } from 'node:path';

async function waitForFile(id: string, filePath: string, timeoutMs = 30_000) {
  const dir = dirname(filePath);
  const name = basename(filePath);
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const files = await kernel.browsers.fs.listFiles(id, { path: dir }); // bare array
    if (files.some(f => f.name === name)) return;
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error(`file ${filePath} not visible within ${timeoutMs}ms`);
}

await waitForFile(id, '/home/kernel/Downloads/report.pdf');
const resp = await kernel.browsers.fs.readFile(id, { path: '/home/kernel/Downloads/report.pdf' });
fs.writeFileSync('./report.pdf', Buffer.from(await resp.arrayBuffer()));
```

### Multipart upload errors

**Cause:** Hand-built `FormData`. The SDK accepts `fs.createReadStream`, `Buffer`/`Uint8Array` (via `toFile`), `File`, or `Response` — and builds the multipart payload itself.

**Fix:**

```ts
import Kernel, { toFile } from '@onkernel/sdk';
import fs from 'node:fs';

// Upload accepts a `files` array — each entry is { dest_path, file }
await kernel.browsers.fs.upload(id, {
  files: [
    // Stream — fastest for large files
    { dest_path: '/tmp/big.zip', file: fs.createReadStream('./big.zip') },
    // Buffer / Uint8Array — wrap with toFile
    { dest_path: '/tmp/data.bin', file: await toFile(buf, 'data.bin') },
  ],
});
```

### Binary vs text on `writeFile`

**Cause:** `writeFile` accepts `contents` as a positional argument and ships it as raw `application/octet-stream`. There is no `encoding` parameter — pass a Buffer/Uint8Array for binary, or a string for text.

**Fix:**

```ts
// Binary — pass a Buffer/Uint8Array directly
await kernel.browsers.fs.writeFile(id, buf, { path: '/tmp/img.png' });

// Text — pass a string directly
await kernel.browsers.fs.writeFile(id, JSON.stringify(obj), { path: '/tmp/data.json' });
```

### File watch is silent

**Cause:** `watch.start` returns immediately — the events come from `watch.events`, which is an async iterable.

**Fix:** Wrap the consumer in a separate task; don't block the `start` call.

## Replays

```ts
const r = await kernel.browsers.replays.start(session.session_id, {
  record_audio: true,            // optional, default false (video only)
  framerate: 30,                 // optional; values above 20 require gpu: true on the browser
  max_duration_in_seconds: 600,  // optional
});
// … session work …
await kernel.browsers.replays.stop(r.replay_id, { id_or_name: session.session_id });

const list = await kernel.browsers.replays.list(session.session_id);
const dl = await kernel.browsers.replays.download(r.replay_id, { id_or_name: session.session_id });
// Replays are mp4 — the SDK sends `Accept: video/mp4` on this call.
fs.writeFileSync(`./replay-${r.replay_id}.mp4`, Buffer.from(await dl.arrayBuffer()));
```

## Replay-specific issues

### `replays.start` on `headless` browsers

**Cause:** Replays are not available in headless mode (same as live view). GPU also requires headful.

**Fix:** Create the browser with `headless: false`.

### `replays.download` returns nothing or 0 bytes

**Cause:** Replay finalization is asynchronous. After `replays.stop`, the mp4 is still being processed and uploaded — there can be multi-second finalization on long replays.

**Fix:** Poll `kernel.browsers.replays.list(session_id)` until the entry for your `replay_id` has a non-null `finished_at`, then `download`. Fall back to a 2–5s sleep only if you cannot poll. Neither the SDK nor the Kernel docs document a replay artifact path on the browser VM filesystem, so don't try to use `fs.listFiles` as the readiness signal.

```ts
async function waitForReplay(sessionId: string, replayId: string, timeoutMs = 60_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const replays = await kernel.browsers.replays.list(sessionId);  // bare array
    const hit = replays.find(x => x.replay_id === replayId);
    if (hit?.finished_at) return hit;
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error(`replay ${replayId} did not finalize within ${timeoutMs}ms`);
}
```

### Multiple replays per session and MP4 Chapter Markers

You can `start`/`stop` multiple times in a single session — each call returns a fresh `replay_id`. Use `replays.list(session_id)` to enumerate. Kernel can embed named markers in recordings as MP4 chapters (docs changelog, Jul 31), but no SDK or CLI call for creating a marker is documented. Each `list` item has `replay_id`, `replay_view_url`, `started_at`, `finished_at`; `replay_view_url` can be embedded in an iframe (treat the URL as sensitive; the docs' `frame-src` is `https://*.kernel.sh:8443 https://*.onkernel.com:8443 https://kernel-api-prod.s3.us-east-1.amazonaws.com`, plus `allow="fullscreen"`).

### Replay file handles after browser delete

**Cause:** Delete the browser before downloading the replay → 404 on `replays.download`.

**Fix:** Download all replays you need before calling `deleteByID`. Or save them to your own object store from inside the action.

## Where to look next

- General SDK file/upload patterns and `toFile`: `references/guides/client-and-config.md`
- Computer-control screenshot capture (alternative to Playwright `page.screenshot`): `references/patterns/browser-control-surfaces.md`
