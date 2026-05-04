# File I/O and replays — troubleshooting

Each browser exposes a VM filesystem (`kernel.browsers.fs.*`) and a recording API (`kernel.browsers.replays.*`). Most issues come from misunderstanding when artifacts become available.

## File I/O surface

```ts
await kernel.browsers.fs.writeFile(id, {
  path: '/tmp/data.json',
  contents: JSON.stringify(obj),
  encoding: 'utf8',                    // 'utf8' | 'base64'
});

const resp = await kernel.browsers.fs.readFile(id, { path: '/tmp/data.json' });
const text = await resp.text();        // Response object — pick text/arrayBuffer/blob

const list = await kernel.browsers.fs.listFiles(id, { path: '/tmp' });
const info = await kernel.browsers.fs.fileInfo(id, { path: '/tmp/data.json' });

await kernel.browsers.fs.upload(id, { path: '/tmp/upload.zip', file: fs.createReadStream('./local.zip') });
await kernel.browsers.fs.uploadZip(id, { path: '/tmp/extract', file: zip });
const dl = await kernel.browsers.fs.downloadDirZip(id, { path: '/tmp/extract' });

await kernel.browsers.fs.move(id, { from: '/tmp/a', to: '/tmp/b' });
await kernel.browsers.fs.deleteFile(id, { path: '/tmp/a' });
await kernel.browsers.fs.createDirectory(id, { path: '/tmp/dir' });
await kernel.browsers.fs.deleteDirectory(id, { path: '/tmp/dir' });
await kernel.browsers.fs.setFilePermissions(id, { path: '/tmp/a', mode: 0o644 });

// Watch for changes
const watch = await kernel.browsers.fs.watch.start(id, { path: '/tmp' });
for await (const evt of await kernel.browsers.fs.watch.events(id, { watch_id: watch.watch_id })) {
  // … evt.type, evt.path …
}
await kernel.browsers.fs.watch.stop(id, { watch_id: watch.watch_id });
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
      const list = await kernel.browsers.fs.listFiles(id, { path: '/tmp' });
      if (list.items.some(i => i.path === path)) return;
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

// Stream — fastest for large files
await kernel.browsers.fs.upload(id, {
  path: '/tmp/big.zip',
  file: fs.createReadStream('./big.zip'),
});

// Buffer / Uint8Array — wrap with toFile
await kernel.browsers.fs.upload(id, {
  path: '/tmp/data.bin',
  file: await toFile(buf, 'data.bin'),
});
```

### Encoding mismatch on `writeFile`

**Cause:** Writing binary as UTF-8 corrupts bytes. Writing text as base64 produces nonsense files.

**Fix:**

```ts
// Binary
await kernel.browsers.fs.writeFile(id, {
  path: '/tmp/img.png',
  contents: buf.toString('base64'),
  encoding: 'base64',
});

// Text
await kernel.browsers.fs.writeFile(id, {
  path: '/tmp/data.json',
  contents: JSON.stringify(obj),
  encoding: 'utf8',
});
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
