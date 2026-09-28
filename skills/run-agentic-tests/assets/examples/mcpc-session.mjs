#!/usr/bin/env node
// Optional MCPC session adapter. The installed MCPC client owns the server's stdio.
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import { createHash } from 'node:crypto';

const execute = promisify(execFile);
const fail = (code, message) => { throw Object.assign(new Error(message), { code }); };
const required = name => process.env[name] || fail('MISSING_IDENTITY', `The controller must provide ${name}.`);

async function main() {
  const options = {};
  const allowed = new Set(['state-dir', 'config', 'required-tool', 'binary', 'timeout-ms']);
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].slice(2);
    if (!args[i].startsWith('--') || !allowed.has(key) || !args[i + 1] || options[key]) fail('USAGE', 'Use --state-dir ABSOLUTE --config FILE:ENTRY --required-tool NAME [--binary PATH] [--timeout-ms N].');
    options[key] = args[i + 1];
  }
  if (!path.isAbsolute(options['state-dir'] || '') || !options.config || !options['required-tool']) fail('USAGE', 'Declare an absolute owned state directory, config entry, and required tool.');
  const timeout = Number(options['timeout-ms'] || 10000);
  if (!Number.isInteger(timeout) || timeout < 100 || timeout > 300000) fail('USAGE', 'timeout-ms must be an integer from 100 to 300000.');
  const action = required('AGENTIC_RUNTIME_ACTION');
  if (!['attach', 'probe', 'inspect', 'cleanup'].includes(action)) fail('USAGE', 'Unsupported runtime action.');
  const identity = {
    owner_token: required('AGENTIC_RUNTIME_OWNER_TOKEN'), owner_id: required('AGENTIC_RUNTIME_OWNER_ID'),
    target_id: required('AGENTIC_RUNTIME_TARGET_ID'), session_id: required('AGENTIC_RUNTIME_SESSION_ID'),
  };
  if (!/^@[A-Za-z0-9_-]+$/.test(identity.session_id)) fail('USAGE', 'Use a namespaced @session with letters, digits, underscores, or hyphens.');
  const state = options['state-dir'];
  const ownerFile = path.join(state, 'owner.json');
  const env = { ...process.env, MCPC_HOME_DIR: path.join(state, 'client') };
  const client = async argv => {
    try {
      const result = await execute(options.binary || 'mcpc', argv, { env, timeout, maxBuffer: 4 * 1024 * 1024, encoding: 'utf8' });
      return result.stdout;
    } catch { fail('MCPC_COMMAND_FAILED', 'The bounded MCPC operation failed. Inspect the owned client logs; no automatic restart was attempted.'); }
  };
  const json = async argv => {
    try { return JSON.parse(await client(['--json', ...argv])); }
    catch (error) { if (error.code) throw error; fail('MCPC_OUTPUT_INVALID', 'Expected structured MCPC output.'); }
  };
  await mkdir(state, { recursive: true, mode: 0o700 });
  const tool = { name: 'mcpc', version: (await client(['--version'])).trim() };
  if (tool.version !== '0.6.0') fail('MCPC_VERSION_UNSUPPORTED', 'This example uses the verified MCPC 0.6.0 session-file contract. Check the installed client contract before adapting it.');
  const list = async () => {
    // `mcpc --json` can reconnect crashed bridges; inspect its private state
    // without invoking a command that could change this runtime generation.
    let result;
    try { result = JSON.parse(await readFile(path.join(env.MCPC_HOME_DIR, 'sessions.json'), 'utf8')); }
    catch (error) { if (error.code === 'ENOENT') return undefined; fail('MCPC_OUTPUT_INVALID', 'The private MCPC session file is unreadable.'); }
    if (!result.sessions || Array.isArray(result.sessions) || typeof result.sessions !== 'object') fail('MCPC_OUTPUT_INVALID', 'The private MCPC session format is unsupported.');
    return result.sessions[identity.session_id];
  };
  const nativeIdentity = session => ({ pid: session.pid, created_at: session.createdAt, server: session.server });
  const processIdentity = async session => {
    if (!Number.isInteger(session?.pid) || session.pid <= 0) return null;
    try {
      const result = await execute('ps', ['-p', String(session.pid), '-o', 'lstart=', '-o', 'command='], { encoding: 'utf8', timeout: Math.min(timeout, 3000) });
      return result.stdout.trim() ? createHash('sha256').update(result.stdout.trim()).digest('hex') : null;
    } catch { return null; }
  };
  const receipt = (alive, extra = {}) => ({ tool, ...identity, alive, ...extra });
  let owner;
  try { owner = JSON.parse(await readFile(ownerFile, 'utf8')); }
  catch (error) { if (error.code !== 'ENOENT') fail('SESSION_OWNERSHIP_MISMATCH', 'The saved ownership record is unreadable.'); }
  if (owner && (Object.entries(identity).some(([key, value]) => owner[key] !== value) || owner.tool?.version !== tool.version)) {
    fail('SESSION_OWNERSHIP_MISMATCH', 'The stored owner/session/tool identity differs; the client session was left untouched.');
  }
  let current = await list();
  if (action === 'attach' && !owner) {
    if (current) fail('SESSION_ALREADY_EXISTS', 'A same-name client session exists; choose a fresh owned session.');
    owner = { ...identity, tool, config: options.config };
    await writeFile(ownerFile, JSON.stringify(owner, null, 2), { flag: 'wx', mode: 0o600 });
    let connectError;
    try { await json(['connect', options.config, identity.session_id]); }
    catch (error) { connectError = error; }
    current = await list();
    // A failed handshake may still have launched a client-owned bridge. Retain
    // its exact identity before returning the failure so cleanup stays scoped.
    if (current && Number.isInteger(current.pid) && current.createdAt) {
      owner.native = nativeIdentity(current);
      owner.process_identity = await processIdentity(current);
      await writeFile(ownerFile, JSON.stringify(owner, null, 2), { mode: 0o600 });
    }
    if (connectError) throw connectError;
    if (!current || !Number.isInteger(current.pid) || !current.createdAt) fail('MCPC_OUTPUT_INVALID', 'Connection did not expose a native session identity.');
  }
  if (!owner) fail('SESSION_OWNERSHIP_MISMATCH', 'No saved ownership exists for this session.');
  if (current && JSON.stringify(owner.native) !== JSON.stringify(nativeIdentity(current))) {
    fail('SESSION_OWNERSHIP_MISMATCH', 'The native client session was replaced; it was left untouched.');
  }
  const actualProcess = await processIdentity(current);
  if (actualProcess && actualProcess !== owner.process_identity) fail('SESSION_OWNERSHIP_MISMATCH', 'The native process identity changed; the client session was left untouched.');
  const alive = !!current && !!actualProcess && !['connecting', 'reconnecting', 'unauthorized', 'expired', 'crashed'].includes(current.status);
  if (action === 'cleanup') {
    if (current) await json(['close', identity.session_id]);
    if (await list()) fail('MCPC_CLEANUP_FAILED', 'The owned client session remains registered after close.');
    return receipt(false);
  }
  if (action === 'probe') {
    if (!alive) fail('MCPC_SESSION_UNAVAILABLE', 'The owned client session is not live; allocate a fresh runtime for recovery.');
    const result = await json([identity.session_id, 'tools-list']);
    const tools = Array.isArray(result) ? result : result.tools;
    if (!Array.isArray(tools) || !tools.some(tool => tool.name === options['required-tool'])) fail('MCPC_TOOL_UNAVAILABLE', 'Actual tool discovery did not expose the required tool.');
    return receipt(true, { ready: true, evidence: { kind: 'protocol', operation: 'tools/list', result: JSON.stringify(tools.map(tool => tool.name)) } });
  }
  return receipt(alive);
}

try { process.stdout.write(`${JSON.stringify(await main())}\n`); }
catch (error) {
  process.stdout.write(`${JSON.stringify({ error: { code: error.code || 'MCPC_ADAPTER_FAILED', message: error.message } })}\n`);
  process.exitCode = 3;
}
