import { readFile, writeFile, appendFile } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { randomUUID } from 'node:crypto';
import { CliError } from './contracts.mjs';
import { containedPath, stableStringify } from './store.mjs';

const execute = promisify(execFile);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const fail = (code, message, details = []) => { throw new CliError(code, message, 4, details); };
const timeout = record => Math.min(record.readiness.timeout_ms || 10000, 10000);

function sameOwner(record, handle, receipt) {
  const session = record.session;
  return receipt && typeof receipt.alive === 'boolean' && receipt.owner_id === session.owner_id &&
    receipt.owner_token === handle.owner_token && receipt.session_id === session.session_id &&
    (receipt.device_id ?? null) === (session.device_id ?? null) &&
    receipt.tool?.name === session.tool.name && receipt.tool?.version === session.tool.version;
}

async function action(campaign, record, handle, operation, timeoutMs = timeout(record)) {
  const argv = operation === 'attach' ? record.command.argv : record.session[operation].argv;
  let result;
  try {
    result = await execute(argv[0], argv.slice(1), {
      cwd: record.command.cwd, timeout: Math.max(1, timeoutMs), maxBuffer: 1024 * 1024, encoding: 'utf8',
      env: { ...process.env, AGENTIC_RUNTIME_ACTION: operation,
        AGENTIC_RUNTIME_OWNER_TOKEN: handle.owner_token, AGENTIC_RUNTIME_TARGET_ID: record.target_id,
        AGENTIC_RUNTIME_OWNER_ID: record.session.owner_id, AGENTIC_RUNTIME_SESSION_ID: record.session.session_id,
        AGENTIC_RUNTIME_DEVICE_ID: record.session.device_id || '' },
    });
  } catch (error) {
    await appendFile(containedPath(campaign, record.logs.stderr), error.stderr || `Tool ${operation} failed.\n`, { mode: 0o600 });
    fail('TOOL_COMMAND_FAILED', `Tool ${operation} failed or exceeded its bounded timeout.`,
      [{ action: operation, exit_code: Number.isInteger(error.code) ? error.code : null,
        remedy: 'Inspect the saved logs and the client session without restarting or replacing it.' }]);
  }
  await appendFile(containedPath(campaign, record.logs.stdout), `${result.stdout.trim()}\n`, { mode: 0o600 });
  if (result.stderr) await appendFile(containedPath(campaign, record.logs.stderr), result.stderr, { mode: 0o600 });
  let receipt;
  try { receipt = JSON.parse(result.stdout); }
  catch { fail('INVALID_TOOL_RECEIPT', `Tool ${operation} must return one JSON ownership receipt.`); }
  if (!sameOwner(record, handle, receipt)) fail('SESSION_OWNERSHIP_MISMATCH',
    `Tool ${operation} did not identify this exact owner, client session, tool version and device.`,
    [{ action: operation, remedy: 'Inspect the native client ownership ledger; do not clean up or adopt an unrelated session.' }]);
  return receipt;
}

async function readHandle(campaign, record) {
  const expected = `environments/${record.target_id}/session.runtime.json`;
  if (record.session_handle?.handle_path !== expected) return null;
  let handle;
  try { handle = JSON.parse(await readFile(containedPath(campaign, expected), 'utf8')); }
  catch { return null; }
  if (handle.mode !== 'tool-session' || handle.target_id !== record.target_id ||
      handle.owner_token !== record.session_handle.owner_token || handle.source_fingerprint !== record.source.fingerprint ||
      stableStringify(handle.command) !== stableStringify(record.command) ||
      stableStringify(handle.session) !== stableStringify(record.session)) return false;
  return handle;
}

export async function startToolSession(campaign, record) {
  const handle = { mode: 'tool-session', target_id: record.target_id, owner_token: randomUUID(),
    source_fingerprint: record.source.fingerprint, command: record.command, session: record.session };
  record.session_handle = { owner_token: handle.owner_token, handle_path: `environments/${record.target_id}/session.runtime.json` };
  await writeFile(containedPath(campaign, record.session_handle.handle_path), JSON.stringify(handle), { flag: 'wx', mode: 0o600 });
  const deadline = Date.now() + (record.readiness.timeout_ms || 10000);
  const receipt = await action(campaign, record, handle, 'attach', deadline - Date.now());
  if (!receipt.alive) fail('TOOL_SESSION_EXITED', 'Tool attachment did not establish its owned client session.');
  return { handle, deadline };
}

export async function probeToolSession(campaign, record, handle, deadline) {
  let detail = 'No semantic protocol or device readiness receipt was observed.';
  while (Date.now() < deadline) {
    try {
      const receipt = await action(campaign, record, handle, 'probe', Math.min(timeout(record), deadline - Date.now()));
      if (!receipt.alive) fail('TOOL_SESSION_EXITED', 'The tool-owned client session exited before readiness.');
      const evidence = receipt.evidence;
      const kind = record.runtime_type === 'mobile' ? 'device' : 'protocol';
      if (receipt.ready === true && evidence?.kind === kind && typeof evidence.operation === 'string' && evidence.operation.trim() &&
          typeof evidence.result === 'string' && evidence.result.includes(record.readiness.body_contains)) {
        return { alive: true, ownership: 'OWNED', readiness_evidence: evidence };
      }
    } catch (error) {
      if (['SESSION_OWNERSHIP_MISMATCH', 'TOOL_SESSION_EXITED'].includes(error.code)) throw error;
      detail = error.message;
    }
    await pause(Math.min(50, Math.max(0, deadline - Date.now())));
  }
  fail('TOOL_READINESS_TIMEOUT', `Tool readiness timed out: ${detail}`);
}

export async function inspectToolSession(campaign, record) {
  const handle = await readHandle(campaign, record);
  if (handle === null) return { alive: false, ownership: 'MISSING_HANDLE' };
  if (handle === false) return { alive: true, ownership: 'MISMATCH' };
  try {
    const receipt = await action(campaign, record, handle, 'inspect');
    return { alive: receipt.alive, ownership: receipt.alive ? 'OWNED' : 'EXITED', handle };
  } catch (error) {
    return { alive: true, ownership: error.code === 'SESSION_OWNERSHIP_MISMATCH' ? 'MISMATCH' : 'UNAVAILABLE',
      inspection_error: { code: error.code, message: error.message } };
  }
}

export async function stopToolSession(campaign, record) {
  const state = await inspectToolSession(campaign, record);
  if (state.ownership === 'EXITED') return { alive: false, ownership: 'EXITED' };
  if (state.ownership !== 'OWNED') fail('SESSION_OWNERSHIP_MISMATCH', 'Refusing cleanup without the exact tool-owned client session receipt.');
  const receipt = await action(campaign, record, state.handle, 'cleanup');
  if (receipt.alive) fail('SESSION_CLEANUP_FAILED', 'The tool cleanup receipt still reports a live session.');
  const stopped = await inspectToolSession(campaign, record);
  if (stopped.ownership !== 'EXITED') fail('SESSION_CLEANUP_FAILED', 'Read-only inspection did not confirm cleanup of the owned session.');
  return { alive: false, ownership: 'EXITED' };
}
