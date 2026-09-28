import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, realpath } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';

await loadDependencies({ setup: true });
const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
const invoke = (...args) => {
  const result = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' });
  return { status: result.status, data: result.stdout.trim() ? JSON.parse(result.stdout) : null, stderr: result.stderr };
};
const accepted = result => { assert.equal(result.status, 0, JSON.stringify(result)); return result.data; };

// The client owns a real local process and checks its identity through a protocol request.
// Each controller action uses this short-lived CLI, never the service's stdin or PID directly.
const client = `import {readFile,writeFile} from 'node:fs/promises';
import {spawn} from 'node:child_process';
const file=process.argv[2], action=process.env.AGENTIC_RUNTIME_ACTION;
const expected={tool:{name:'fixture-client',version:'1'},owner_id:process.env.AGENTIC_RUNTIME_OWNER_ID,
 owner_token:process.env.AGENTIC_RUNTIME_OWNER_TOKEN,session_id:process.env.AGENTIC_RUNTIME_SESSION_ID};
if(process.env.AGENTIC_RUNTIME_DEVICE_ID) expected.device_id=process.env.AGENTIC_RUNTIME_DEVICE_ID;
let saved;
try { saved=JSON.parse(await readFile(file,'utf8')); } catch {}
if(action==='attach') {
 if(saved?.alive) throw new Error('client session already exists');
 const program=\`const http=require('node:http'); const fs=require('node:fs');
 const identity=JSON.parse(process.env.FIXTURE_IDENTITY);
 const server=http.createServer((req,res)=>res.end(JSON.stringify({identity,operation:'list-tools',result:'fixture echo available'})));
 server.listen(0,'127.0.0.1',()=>fs.writeFileSync(process.env.FIXTURE_LEDGER,JSON.stringify({...identity,pid:process.pid,port:server.address().port,alive:true})));
 process.on('SIGTERM',()=>server.close(()=>process.exit(0)));\`;
 const child=spawn(process.execPath,['-e',program],{detached:true,stdio:'ignore',env:{...process.env,FIXTURE_IDENTITY:JSON.stringify(expected),FIXTURE_LEDGER:file}});
 child.unref();
 const deadline=Date.now()+1500;
 while(Date.now()<deadline) { try { saved=JSON.parse(await readFile(file,'utf8')); break; } catch { await new Promise(r=>setTimeout(r,10)); } }
}
if(!saved) { console.log(JSON.stringify({...expected,alive:false})); process.exit(0); }
let remote;
if(saved.alive) {
 try { remote=await (await fetch('http://127.0.0.1:'+saved.port,{signal:AbortSignal.timeout(300)})).json(); }
 catch { saved.alive=false; }
}
if(remote && JSON.stringify(remote.identity)!==JSON.stringify({...expected})) {
 console.log(JSON.stringify({...remote.identity,alive:true})); process.exit(0);
}
if(action==='cleanup' && saved.alive) {
 process.kill(saved.pid,'SIGTERM');
 const deadline=Date.now()+1000;
 while(Date.now()<deadline) { try { await fetch('http://127.0.0.1:'+saved.port,{signal:AbortSignal.timeout(100)}); await new Promise(r=>setTimeout(r,10)); } catch { break; } }
 saved.alive=false; await writeFile(file,JSON.stringify(saved));
}
const output={...saved}; delete output.pid; delete output.port;
if(action==='probe') { output.ready=!!saved.alive; output.evidence={kind:expected.device_id?'device':'protocol',operation:remote?.operation||'unavailable',result:remote?.result||'unavailable'}; }
console.log(JSON.stringify(output));
`;

async function fixture(t, runtime_type = 'mcp_stdio') {
  const root = await realpath(await mkdtemp(path.join(tmpdir(), 'agentic-tool-')));
  const project = path.join(root, 'project');
  await mkdir(project);
  await writeFile(path.join(project, 'client.mjs'), client);
  const campaign = accepted(invoke('init', '--project', project, '--slug', 'tool-proof')).campaign_path;
  const ledger = path.join(root, 'client-session.json');
  const argv = [process.execPath, 'client.mjs', ledger];
  const draft = {
    target_id: 'G001', runtime_type,
    source: { revision: 'fixture-client-v1', provider: { type: 'files', root: project, paths: ['client.mjs'] } },
    command: { argv, cwd: project },
    readiness: { type: 'tool', body_contains: 'fixture echo available', timeout_ms: 2500 },
    session: { tool: { name: 'fixture-client', version: '1' }, owner_id: 'fixture-operator', session_id: 'fixture-G001',
      ...(runtime_type === 'mobile' ? { device_id: 'fixture-device-001' } : {}), attachment: 'fixture-client fixture-G001',
      probe: { argv }, inspect: { argv }, cleanup: { argv } },
  };
  const file = path.join(root, 'environment.json');
  const save = () => writeFile(file, JSON.stringify(draft));
  await save();
  const stop = () => invoke('runtime', 'stop', '--campaign', campaign, '--target-id', 'G001');
  t.after(async () => {
    stop();
    try { const entry = JSON.parse(await readFile(ledger, 'utf8')); if (entry.alive) process.kill(entry.pid, 'SIGTERM'); } catch {}
    await rm(root, { recursive: true, force: true });
  });
  return { root, project, campaign, ledger, draft, file, save, stop,
    start: () => invoke('runtime', 'start', '--campaign', campaign, '--file', file),
    inspect: () => accepted(invoke('runtime', 'inspect', '--campaign', campaign, '--target-id', 'G001')) };
}

test('tool-owned sessions attach, prove protocol readiness, inspect and clean up their exact client session', async t => {
  const f = await fixture(t);
  const started = accepted(f.start());
  assert.equal(started.environment.status, 'READY');
  assert.equal(started.ownership, 'OWNED');
  assert.equal(started.environment.process, undefined);
  assert.match(started.environment.session_handle.owner_token, /^[a-f0-9-]{36}$/);
  const before = f.inspect();
  assert.equal(before.alive, true);
  assert.equal(before.source_verification.valid, true);
  const stopped = accepted(f.stop());
  assert.equal(stopped.alive, false);
  assert.equal(stopped.environment.status, 'STOPPED');
  assert.equal(f.inspect().ownership, 'EXITED');
});

test('tool cleanup refuses a session or device ownership mismatch and leaves the live service intact', async t => {
  const f = await fixture(t, 'mobile');
  accepted(f.start());
  const original = await readFile(f.ledger, 'utf8');
  const receipt = JSON.parse(original);
  await writeFile(f.ledger, JSON.stringify({ ...receipt, device_id: 'unrelated-device' }));
  try {
    assert.equal(f.inspect().ownership, 'MISMATCH');
    assert.equal(f.stop().data.error?.code, 'SESSION_OWNERSHIP_MISMATCH');
    assert.equal((await (await fetch(`http://127.0.0.1:${receipt.port}`)).json()).identity.device_id, 'fixture-device-001');
  } finally { await writeFile(f.ledger, original); }
  assert.equal(accepted(f.stop()).alive, false);
});

test('readiness requires protocol evidence instead of an alive client and a printed marker', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.project, 'client.mjs'), client.replace("output.ready=!!saved.alive; output.evidence=", "output.ready=!!saved.alive; output.marker='fixture echo available'; output.unaccepted_evidence="));
  f.draft.readiness.timeout_ms = 400;
  await f.save();
  const failed = f.start();
  assert.equal(failed.data.error?.code, 'RUNTIME_START_FAILED');
  assert.match(failed.data.error.message, /readiness timed out/i);
  const inspected = f.inspect();
  assert.equal(inspected.environment.status, 'FAILED');
  assert.equal(inspected.alive, false);
  assert.equal(JSON.parse(await readFile(f.ledger, 'utf8')).alive, false);
});

test('a blocked attach command is bounded and inspection never silently starts a replacement session', async t => {
  const f = await fixture(t);
  f.draft.command.argv = [process.execPath, '-e', 'setInterval(()=>{},1000)'];
  f.draft.readiness.timeout_ms = 200;
  await f.save();
  const startedAt = Date.now();
  const result = f.start();
  assert.equal(result.data.error?.code, 'RUNTIME_START_FAILED');
  assert.match(result.data.error.message, /timeout/i);
  assert.ok(Date.now() - startedAt < 3000);
  assert.equal(f.inspect().ownership, 'EXITED');
  await assert.rejects(readFile(f.ledger), error => error.code === 'ENOENT');
});

test('an unavailable owned client stays exited when inspected rather than being repaired or restarted', async t => {
  const f = await fixture(t);
  accepted(f.start());
  const receipt = JSON.parse(await readFile(f.ledger, 'utf8'));
  process.kill(receipt.pid, 'SIGTERM');
  const deadline = Date.now() + 1000;
  let state;
  do { state = f.inspect(); } while (state.alive && Date.now() < deadline);
  assert.equal(state.ownership, 'EXITED');
  assert.equal(JSON.parse(await readFile(f.ledger, 'utf8')).pid, receipt.pid);
});
