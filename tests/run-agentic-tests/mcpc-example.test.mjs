import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const adapter = fileURLToPath(new URL('../../skills/run-agentic-tests/assets/examples/mcpc-session.mjs', import.meta.url));

async function fixture(t) {
  const root = await mkdtemp(path.join(tmpdir(), 'mcpc adapter space-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const executable = path.join(root, 'mcpc-fixture');
  await writeFile(executable, `#!${process.execPath}
import fs from 'node:fs';
import path from 'node:path';
const dir=process.env.MCPC_HOME_DIR;
fs.mkdirSync(dir,{recursive:true});
const file=path.join(dir,'sessions.json');
const args=process.argv.slice(2).filter(x=>x!=='--json');
fs.appendFileSync(path.join(dir,'calls.jsonl'),JSON.stringify(args)+'\\n');
let sessions=fs.existsSync(file)?Object.values(JSON.parse(fs.readFileSync(file,'utf8')).sessions):[];
const save=()=>fs.writeFileSync(file,JSON.stringify({sessions:Object.fromEntries(sessions.map(s=>[s.name,s]))}));
if(args[0]==='--version') console.log('0.6.0');
else if(!args.length) console.log(JSON.stringify({sessions,profiles:[]}));
else if(args[0]==='connect') {
  sessions.push({name:args[2],pid:Number(process.env.MCPC_FIXTURE_PID),createdAt:'2026-09-28T00:00:00Z',status:'live',server:{command:'fixture'}});
  save(); console.log('[]'); if(process.env.MCPC_FIXTURE_START_FAIL)process.exitCode=2;
} else if(args[0]==='close') {
  sessions=sessions.filter(s=>s.name!==args[1]); save(); console.log('{}');
} else if(args[1]==='tools-list') console.log(JSON.stringify([{name:'greet'}]));
else {console.error('unexpected command');process.exitCode=2;}
`, { mode: 0o755 });
  const state = path.join(root, 'owned');
  const argv = [adapter, '--state-dir', state, '--config', path.join(root, 'config.json:fixture'), '--required-tool', 'greet', '--binary', executable];
  const env = { ...process.env, MCPC_FIXTURE_PID: String(process.pid), AGENTIC_RUNTIME_OWNER_TOKEN: 'token-one', AGENTIC_RUNTIME_OWNER_ID: 'A001', AGENTIC_RUNTIME_TARGET_ID: 'G001', AGENTIC_RUNTIME_SESSION_ID: '@owned-g001' };
  const call = (action, extra = {}, exit = 0) => {
    const result = spawnSync(process.execPath, argv, { env: { ...env, ...extra, AGENTIC_RUNTIME_ACTION: action }, encoding: 'utf8', timeout: 10000 });
    assert.equal(result.status, exit, result.stdout + result.stderr);
    return JSON.parse(result.stdout);
  };
  return { root, state, call };
}

test('MCPC example preserves a client-owned session and checks real tool-discovery output', async t => {
  const f = await fixture(t);
  const attached = f.call('attach');
  assert.equal(attached.session_id, '@owned-g001');
  assert.equal(attached.owner_token, 'token-one');
  const probed = f.call('probe');
  assert.equal(probed.ready, true);
  assert.equal(probed.evidence.kind, 'protocol');
  assert.match(probed.evidence.result, /greet/);
  assert.equal(f.call('inspect').alive, true);
  assert.equal(f.call('cleanup').alive, false);
  assert.equal(f.call('inspect').alive, false);
});

test('MCPC example refuses changed ownership and native session replacement without closing it', async t => {
  const f = await fixture(t);
  f.call('attach');
  assert.equal(f.call('cleanup', { AGENTIC_RUNTIME_OWNER_TOKEN: 'other-owner' }, 3).error.code, 'SESSION_OWNERSHIP_MISMATCH');
  const native = path.join(f.state, 'client/sessions.json');
  const sessions = JSON.parse(await readFile(native, 'utf8'));
  sessions.sessions['@owned-g001'].pid = 202;
  await writeFile(native, JSON.stringify(sessions));
  assert.equal(f.call('cleanup', {}, 3).error.code, 'SESSION_OWNERSHIP_MISMATCH');
  assert.equal(JSON.parse(await readFile(native, 'utf8')).sessions['@owned-g001'].pid, 202);
});

test('MCPC example refuses to adopt an existing same-name session', async t => {
  const f = await fixture(t);
  await mkdir(path.join(f.state, 'client'), { recursive: true });
  const native = path.join(f.state, 'client/sessions.json');
  await writeFile(native, JSON.stringify({ sessions: { '@owned-g001': { name: '@owned-g001', pid: 303, createdAt: 'earlier', status: 'live' } } }));
  assert.equal(f.call('attach', {}, 3).error.code, 'SESSION_ALREADY_EXISTS');
  assert.equal(JSON.parse(await readFile(native, 'utf8')).sessions['@owned-g001'].pid, 303);
});

test('MCPC inspection never invokes the client session-list command that can reconnect bridges', async t => {
  const f = await fixture(t); f.call('attach');
  const calls = path.join(f.state, 'client/calls.jsonl');
  const before = (await readFile(calls, 'utf8')).trim().split('\n').length;
  assert.equal(f.call('inspect').alive, true);
  const invoked = (await readFile(calls, 'utf8')).trim().split('\n').slice(before).map(JSON.parse);
  assert.ok(invoked.every(args => args.length === 1 && args[0] === '--version'), JSON.stringify(invoked));
});

test('MCPC attach failure retains the native identity for scoped cleanup', async t => {
  const f = await fixture(t);
  assert.equal(f.call('attach', { MCPC_FIXTURE_START_FAIL: '1' }, 3).error.code, 'MCPC_COMMAND_FAILED');
  assert.equal(f.call('cleanup').alive, false);
  assert.deepEqual(JSON.parse(await readFile(path.join(f.state, 'client/sessions.json'), 'utf8')).sessions, {});
});
