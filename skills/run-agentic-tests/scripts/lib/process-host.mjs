// Scoped process helper. It owns one POSIX process group, never a task queue.
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { randomUUID, createHash } from 'node:crypto';
import { readFile, writeFile, rename, open, lstat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import path from 'node:path';
import { constants } from 'node:fs';

const exec = promisify(execFile);
const helper = fileURLToPath(import.meta.url);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

async function save(file, value) {
  const temporary = `${file}.${process.pid}.${randomUUID()}.tmp`;
  await writeFile(temporary, JSON.stringify(value), { mode: 0o600 });
  await rename(temporary, file);
}

async function identity(pid) {
  if (!Number.isSafeInteger(pid) || pid <= 1) return null;
  try {
    const { stdout } = await exec('ps', ['-p', String(pid), '-o', 'stat=', '-o', 'lstart=', '-o', 'command=']);
    const line = stdout.trim();
    if (!line || line.startsWith('Z')) return null;
    return line.replace(/^\S+\s+/, '');
  } catch { return null; }
}

async function groupMembers(group) {
  return new Promise((resolve, reject) => {
    const query = execFile('ps', ['-axo', 'pid=,pgid=,stat='], (error, stdout) => {
      if (error) return reject(error);
      resolve(stdout.trim().split('\n').map(line => line.trim().split(/\s+/)).filter(([pid, pgid, state]) =>
        Number(pgid) === group && Number(pid) !== group && Number(pid) !== query.pid && !state?.startsWith('Z')));
    });
  });
}

export async function inspectOwned(handle, manifestPath = handle?.manifest_path) {
  const current = await identity(handle?.pid);
  if (!current) return { alive: false, ownership: 'EXITED' };
  if (typeof handle.start_token !== 'string' || !handle.start_token || !manifestPath ||
      handle.manifest_path !== manifestPath ||
      current !== handle.identity || !current.endsWith(` ${handle.start_token}`) ||
      !current.endsWith(`${helper} --host ${manifestPath} ${handle.start_token}`)) return { alive: true, ownership: 'MISMATCH' };
  return { alive: true, ownership: 'OWNED' };
}

export async function stopOwned(handle, manifestPath = handle?.manifest_path) {
  if (process.platform === 'win32') throw new Error('Owned process groups require macOS or Linux.');
  let state = await inspectOwned(handle, manifestPath);
  if (state.ownership !== 'OWNED') return state;
  try { process.kill(-handle.pid, 'SIGTERM'); }
  catch (error) { if (error.code !== 'ESRCH') throw error; }
  // The helper remains the group leader during this grace period, so a later
  // escalation can revalidate ownership instead of signalling a reused PID.
  const deadline = Date.now() + 800;
  while (Date.now() < deadline) {
    state = await inspectOwned(handle, manifestPath);
    if (!state.alive) return state;
    await pause(40);
  }
  state = await inspectOwned(handle, manifestPath);
  if (state.ownership === 'OWNED') {
    try { process.kill(-handle.pid, 'SIGKILL'); }
    catch (error) { if (error.code !== 'ESRCH') throw error; }
  }
  for (let i = 0; i < 50; i++) {
    state = await inspectOwned(handle, manifestPath);
    if (!state.alive) return state;
    // ps can observe a dying macOS process as `(node)` before it becomes a
    // zombie or disappears. Do not signal that ambiguous identity again;
    // wait for disappearance, and retain a persistent mismatch as a refusal.
    await pause(20);
  }
  if (state.ownership === 'MISMATCH') return state;
  throw new Error('Owned process did not stop.');
}

export async function startOwned(manifestPath, config) {
  if (process.platform === 'win32') throw new Error('Owned process groups require macOS or Linux.');
  const start_token = randomUUID();
  await writeFile(manifestPath, JSON.stringify({ ...config, manifest_path: manifestPath, start_token, state: 'STARTING' }),
    { flag: 'wx', mode: 0o600 });
  const stdout = await open(config.stdout, 'a', 0o600);
  const stderr = await open(config.stderr, 'a', 0o600);
  let child;
  try {
    child = spawn(process.execPath, [helper, '--host', manifestPath, start_token], {
      detached: true, stdio: ['ignore', stdout.fd, stderr.fd],
    });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.unref();
  } finally { await stdout.close(); await stderr.close(); }
  const deadline = Date.now() + 5000;
  let handle;
  while (Date.now() < deadline) {
    handle = JSON.parse(await readFile(manifestPath, 'utf8'));
    if (handle.pid && handle.identity) {
      if (handle.state === 'FAILED') throw Object.assign(new Error(handle.error), { handle });
      if (handle.state !== 'STARTING') return handle;
    }
    if (!(await identity(child.pid))) {
      const latest = JSON.parse(await readFile(manifestPath, 'utf8'));
      // The host may publish its terminal receipt after our STARTING read but
      // before process inspection. Preserve that receipt even after exit.
      if (latest.pid === child.pid && latest.identity) {
        if (latest.state === 'FAILED') throw Object.assign(new Error(latest.error), { handle: latest });
        if (latest.state === 'EXITED') return latest;
        handle = latest;
      }
      throw Object.assign(new Error('Process helper exited before startup; inspect stderr.'), { handle });
    }
    await pause(25);
  }
  if (handle?.pid) await stopOwned(handle);
  throw Object.assign(new Error('Process helper startup timed out; inspect stderr.'), { handle });
}

async function host(manifestPath, token) {
  let config = JSON.parse(await readFile(manifestPath, 'utf8'));
  if (config.start_token !== token || config.manifest_path !== manifestPath) throw new Error('Process ownership token mismatch.');
  config = { ...config, pid: process.pid, identity: await identity(process.pid) };
  let stopping = false;
  const stop = () => {
    if (stopping) return;
    stopping = true;
    config.state = 'STOPPED';
    save(manifestPath, config).catch(() => {});
    // Keep the leader alive until the owner can safely escalate its group.
    setTimeout(() => process.exit(0), 3000);
  };
  process.on('SIGTERM', stop);
  process.on('SIGINT', stop);
  if (config.mode === 'report') {
    const server = createServer(async (request, response) => {
      const refuse = (status, message) => { response.writeHead(status, { 'Content-Type': 'text/plain', 'Cache-Control': 'no-store' }); response.end(message); };
      if (!['GET', 'HEAD'].includes(request.method)) return refuse(405, 'Read-only report server.');
      try {
        const pathname = decodeURIComponent(request.url.split('?')[0]);
        if (!pathname.startsWith('/') || /[\\\0]/.test(pathname) || pathname.split('/').some(part => part === '.' || part === '..')) return refuse(404, 'Not found.');
        const relative = pathname === '/' ? 'index.html' : pathname.slice(1);
        const manifest = JSON.parse(await readFile(config.bundle_path, 'utf8'));
        const entry = manifest.files.find(item => item.path === relative);
        if (!entry || !/^(index\.html|artifacts\/[a-f0-9]{64}\.[a-z0-9]+)$/.test(relative)) return refuse(404, 'Not found.');
        let current = config.root;
        for (const component of relative.split('/')) {
          if ((await lstat(current)).isSymbolicLink()) return refuse(404, 'Not found.');
          current = path.join(current, component);
        }
        const file = await open(current, constants.O_RDONLY | constants.O_NOFOLLOW);
        let body;
        try {
          if (!(await file.stat()).isFile()) return refuse(404, 'Not found.');
          body = await file.readFile();
        } finally { await file.close(); }
        if (createHash('sha256').update(body).digest('hex') !== entry.sha256) return refuse(409, 'Report content changed. Rebuild the report.');
        response.writeHead(200, {
          'Content-Type': entry.content_type,
          'Content-Length': body.length,
          'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
          'Referrer-Policy': 'no-referrer',
          'Content-Security-Policy': "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
          ...(entry.download ? { 'Content-Disposition': `attachment; filename="${path.basename(relative)}"` } : {}),
        });
        response.end(request.method === 'HEAD' ? undefined : body);
      } catch { if (!response.headersSent) refuse(404, 'Not found.'); else response.end(); }
    });
    server.once('error', async error => {
      config.state = 'FAILED'; config.error = error.message;
      await save(manifestPath, config); console.error(error.message); process.exit(1);
    });
    server.listen(config.port, '127.0.0.1', async () => {
      config.state = 'RUNNING'; config.url = `http://127.0.0.1:${server.address().port}/`;
      await save(manifestPath, config);
    });
    return;
  }
  if (config.mode !== 'runtime') throw new Error('Unknown process helper mode.');
  const child = spawn(config.argv[0], config.argv.slice(1), {
    cwd: config.cwd, stdio: ['ignore', 'inherit', 'inherit'], shell: false,
  });
  child.once('error', async error => {
    console.error(error.message);
    config.state = 'FAILED'; config.error = error.message;
    await save(manifestPath, config);
    if (!stopping) process.exit(1);
  });
  child.once('spawn', async () => {
    config.state = 'RUNNING'; config.child_pid = child.pid;
    await save(manifestPath, config);
  });
  child.once('exit', async (code, signal) => {
    if (stopping) return;
    // A launcher may exit after starting a non-detached background child.
    // Retain the original group leader as the identity anchor until every
    // group member exits; otherwise a later stop cannot safely own the PGID.
    config.state = 'DRAINING'; config.exit_code = code; config.exit_signal = signal;
    await save(manifestPath, config);
    while (!stopping) {
      let members;
      try { members = await groupMembers(process.pid); }
      catch { await pause(100); continue; }
      if (!members.length) break;
      await pause(50);
    }
    if (stopping) return;
    config.state = 'EXITED'; config.exit_code = code; config.exit_signal = signal;
    await save(manifestPath, config);
    process.exit(code === 0 ? 0 : 1);
  });
}

if (process.argv[1] === helper && process.argv[2] === '--host') {
  host(process.argv[3], process.argv[4]).catch(error => { console.error(error.message); process.exit(1); });
}
