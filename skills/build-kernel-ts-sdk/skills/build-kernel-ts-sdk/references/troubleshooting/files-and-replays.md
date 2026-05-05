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
const watch = await kernel.browsers.fs.watch.start(id, { path: '/tmp' });
if (!watch.watch_id) throw new Error('watch.start did not return a watch_id');
for await (const evt of await kernel.browsers.fs.watch.events(watch.watch_id, { id })) {
  // evt.type is the uppercase enum: 'CREATE' | 'WRITE' | 'DELETE' | 'RENAME'
  // evt.path is the affected absolute path.
}
await kernel.browsers.fs.watch.stop(watch.watch_id, { id });
```

## Common file-I/O issues

### `readFile` returns empty / partial body

**Cause:** The file was written by the browser (e.g. via Playwright's download) but Kernel's `fs` has not yet seen it. CDP `download` events fire **before** the file is durably written to the VM's filesystem.

**Fix:**

```ts
// After triggering a download via CDP
async function waitForFile(id: string, path: string, timeoutMs = 10_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const files = await kernel.browsers.fs.listFiles(id, { path: '/tmp' });
      if (files.some(i => i.path === path)) return;   // listFiles returns bare array
    } catch { /* ignore */ }
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error(`file ${path} not visible within ${timeoutMs}ms`);
}
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
const r = await kernel.browsers.replays.start(session.session_id);
// … session work …
await kernel.browsers.replays.stop(r.replay_id, { id: session.session_id });

const list = await kernel.browsers.replays.list(session.session_id);
const dl = await kernel.browsers.replays.download(r.replay_id, { id: session.session_id });
fs.writeFileSync('./replay.webm', Buffer.from(await dl.arrayBuffer()));
```

## Replay-specific issues

### `replays.start` errors with `headless` browsers

**Cause:** Replays require headful — same constraint as live view and GPU. Headless browsers cannot record.

**Fix:** Create the browser with `headless: false`.

### `replays.download` returns nothing or 0 bytes

**Cause:** Replay finalization is asynchronous. After `replays.stop`, the `.webm` is written to the VM's filesystem and uploaded — there can be multi-second finalization on long replays.

**Fix:** Sleep 2–5 seconds after `stop`, or poll `kernel.browsers.fs.listFiles` for the replay artifact path before downloading.

### Multiple replays per session

You can `start`/`stop` multiple times in a single session — each call returns a fresh `replay_id`. Useful for chaptering a long session into named segments. Use `replays.list(session_id)` to enumerate.

### Replay file handles after browser delete

**Cause:** Delete the browser before downloading the replay → 404 on `replays.download`.

**Fix:** Download all replays you need before calling `deleteByID`. Or save them to your own object store from inside the action.

## Where to look next

- General SDK file/upload patterns and `toFile`: `references/guides/client-and-config.md`
- Computer-control screenshot capture (alternative to Playwright `page.screenshot`): `references/patterns/browser-control-surfaces.md`
