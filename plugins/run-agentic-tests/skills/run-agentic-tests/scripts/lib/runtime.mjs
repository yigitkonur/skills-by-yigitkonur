import { mkdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { createConnection } from 'node:net';
import { readYaml, readCampaign, readRecords, writeRecord, withController, containedPath } from './store.mjs';
import { CliError, validateRecord } from './contracts.mjs';
import { startOwned, inspectOwned, stopOwned } from './process-host.mjs';

const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const required = (value, message) => { if (!value) throw new CliError('INVALID_RUNTIME', message); };

function validateDraft(draft) {
  required(draft && typeof draft === 'object', 'Environment draft must be an object.');
  required(/^G\d{3,}$/.test(draft.target_id), 'target_id must be a generation ID such as G001.');
  required(['http', 'cli', 'mcp_stdio', 'mcp_http', 'mobile'].includes(draft.runtime_type), 'Invalid runtime_type.');
  required(typeof draft.source?.revision === 'string' && draft.source.revision.length, 'source.revision is required.');
  required(Array.isArray(draft.command?.argv) && draft.command.argv.length &&
    draft.command.argv.every(arg => typeof arg === 'string' && !arg.includes('\0')) && draft.command.argv[0], 'command.argv must be nonempty strings.');
  required(typeof draft.command.cwd === 'string' && path.isAbsolute(draft.command.cwd), 'command.cwd must be absolute.');
  required(!('env' in draft.command), 'Pass environment values through the host; declare env_names only.');
  required(['http', 'process'].includes(draft.readiness?.type), 'Declare an HTTP or process readiness handshake.');
  required(typeof draft.readiness.body_contains === 'string' && draft.readiness.body_contains.length,
    'readiness.body_contains is required; a live PID or HTTP 200 alone is not readiness.');
  if (draft.readiness.type === 'http') {
    let url;
    try { url = new URL(draft.readiness.url); } catch { /* Validation below gives a stable error. */ }
    required(url && ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password,
      'Readiness URL must be HTTP(S) without credentials.');
    required(Number.isInteger(draft.readiness.expected_status) && draft.readiness.expected_status >= 100 &&
      draft.readiness.expected_status <= 599, 'Declare readiness.expected_status.');
  }
  if (draft.readiness.timeout_ms !== undefined) required(Number.isInteger(draft.readiness.timeout_ms) &&
    draft.readiness.timeout_ms >= 100 && draft.readiness.timeout_ms <= 300000, 'timeout_ms must be 100..300000.');
  if (draft.command.env_names) required(Array.isArray(draft.command.env_names) &&
    draft.command.env_names.every(name => /^[A-Za-z_][A-Za-z0-9_]*$/.test(name)), 'Invalid env_names.');
}

async function probe(record, campaign, handle) {
  const deadline = Date.now() + (record.readiness.timeout_ms || 10000);
  let detail = 'Readiness handshake did not match.';
  while (Date.now() < deadline) {
    const ownership = await inspectOwned(handle);
    if (record.runtime_type === 'cli' && record.readiness.type === 'process') {
      const latest = JSON.parse(await readFile(containedPath(campaign, record.process.handle_path), 'utf8'));
      if (latest.state === 'EXITED') {
        if (latest.exit_code !== 0) throw new Error(`CLI readiness probe exited with code ${latest.exit_code ?? latest.exit_signal}.`);
        const logs = await Promise.all(Object.values(record.logs).map(file => readFile(containedPath(campaign, file), 'utf8')));
        if (!logs.some(log => log.includes(record.readiness.body_contains))) throw new Error('CLI exited without its declared readiness marker.');
        if (!ownership.alive) return ownership;
      } else if (ownership.ownership !== 'OWNED') throw new Error('CLI probe exited without a successful completion receipt.');
      await pause(25);
      continue;
    }
    if (ownership.ownership !== 'OWNED') throw new Error('Runtime exited before readiness; inspect saved logs.');
    try {
      if (record.readiness.type === 'http') {
        const response = await fetch(record.readiness.url, {
          signal: AbortSignal.timeout(Math.min(1000, Math.max(1, deadline - Date.now()))), redirect: 'error',
        });
        const body = await response.text();
        if (response.status === record.readiness.expected_status && body.includes(record.readiness.body_contains)) return ownership;
        detail = `Readiness mismatch: status ${response.status}; declared body marker ${body.includes(record.readiness.body_contains) ? 'present' : 'absent'}.`;
      } else {
        const logs = await Promise.all(Object.values(record.logs).map(file => readFile(containedPath(campaign, file), 'utf8')));
        if (logs.some(log => log.includes(record.readiness.body_contains))) return ownership;
      }
    } catch (error) { detail = error.message; }
    await pause(50);
  }
  throw new Error(`Readiness timed out: ${detail}`);
}

async function assertPortAvailable(readiness) {
  if (readiness.type !== 'http') return;
  const url = new URL(readiness.url);
  const occupied = await new Promise(resolve => {
    const socket = createConnection({ host: url.hostname.replace(/^\[|\]$/g, ''), port: Number(url.port || (url.protocol === 'https:' ? 443 : 80)) });
    const finish = result => { socket.destroy(); resolve(result); };
    socket.once('connect', () => finish(true));
    socket.once('error', () => finish(false));
    socket.setTimeout(500, () => finish(false));
  });
  if (occupied) throw new CliError('RUNTIME_PORT_IN_USE',
    'The readiness port already has a listener. Choose a free local app port for this target generation.', 4);
}

async function findEnvironment(campaign, target) {
  const found = (await readRecords(campaign)).filter(({ record }) => record.kind === 'environment' && record.target_id === target);
  if (found.length !== 1) throw new CliError('RUNTIME_NOT_FOUND', `Expected one environment for ${target}.`, 3);
  return found[0];
}

async function inspectEnvironment(campaign, environment) {
  let handle;
  const expectedPath = `environments/${environment.target_id}/process.runtime.json`;
  if (environment.process?.handle_path !== expectedPath) return { alive: false, ownership: 'MISSING_HANDLE' };
  try {
    handle = JSON.parse(await readFile(containedPath(campaign, environment.process.handle_path), 'utf8'));
  } catch { return { alive: false, ownership: 'MISSING_HANDLE' }; }
  if (handle.mode !== 'runtime' || handle.pid !== environment.process.pid || handle.start_token !== environment.process.start_token ||
      JSON.stringify(handle.argv) !== JSON.stringify(environment.command.argv) || handle.cwd !== environment.command.cwd) {
    return { alive: true, ownership: 'MISMATCH' };
  }
  return { ...await inspectOwned(handle, containedPath(campaign, expectedPath)), handle };
}

export async function run(command, options = {}) {
  required(typeof options.campaign === 'string', '--campaign is required.');
  const campaign = path.resolve(options.campaign);
  const campaignRecord = await readCampaign(campaign);
  if (command === 'runtime start') {
    required(typeof options.file === 'string', '--file is required.');
    const draft = await readYaml(path.resolve(options.file));
    validateDraft(draft);
    if (draft.task_id || draft.actor_id) {
      const task = (await readRecords(campaign)).find(({ record }) => record.kind === 'task' && record.task_id === draft.task_id)?.record;
      const output = task?.outputs.find(item => item.kind === 'environment');
      if (!task || task.role !== 'environment-operator' || task.state !== 'RUNNING' || !task.handle ||
          task.actor_id !== draft.actor_id || task.target_id !== draft.target_id ||
          output?.path !== `environments/${draft.target_id}/00-environment.record.yaml` ||
          (draft.record_id && draft.record_id !== output.record_id)) {
        throw new CliError('WRONG_ASSIGNMENT', 'Runtime draft must match its running environment-operator task, actor, target and output.');
      }
      draft.record_id = output.record_id;
    }
    await assertPortAvailable(draft.readiness);
    const base = `environments/${draft.target_id}`;
    const recordPath = `${base}/00-environment.record.yaml`;
    const handlePath = `${base}/process.runtime.json`;
    const logs = { stdout: `${base}/logs/stdout.log`, stderr: `${base}/logs/stderr.log` };
    const record = {
      ...draft, schema_version: 1, kind: 'environment', record_id: draft.record_id || `ENV-${draft.target_id}`,
      campaign_id: campaignRecord.campaign_id, created_at: draft.created_at || new Date().toISOString(),
      status: 'STARTING', logs,
    };
    if (draft.runtime_type === 'cli' && draft.readiness.type === 'process') record.capability_notes = [
      ...(draft.capability_notes || []), 'CLI readiness validates the declared setup/executable probe by marker and exit 0; it is not a running service.',
    ];
    validateRecord(record);
    await withController(campaign, async () => {
      const targetPath = containedPath(campaign, base);
      try { await mkdir(targetPath); }
      catch (error) {
        if (error.code === 'EEXIST') throw new CliError('TARGET_EXISTS', 'Use a new target generation; an existing runtime cannot be overwritten.', 4);
        if (error.code === 'ENOENT') { await mkdir(containedPath(campaign, 'environments'), { recursive: true }); await mkdir(targetPath); }
        else throw error;
      }
      await mkdir(containedPath(campaign, `${base}/logs`));
    });
    let handle;
    try {
      handle = await startOwned(containedPath(campaign, handlePath), {
        mode: 'runtime', argv: draft.command.argv, cwd: draft.command.cwd,
        stdout: containedPath(campaign, logs.stdout), stderr: containedPath(campaign, logs.stderr),
      });
      record.process = { pid: handle.pid, start_token: handle.start_token,
        argv: draft.command.argv, cwd: draft.command.cwd, handle_path: handlePath };
      await withController(campaign, () => writeRecord(campaign, recordPath, record, { immutable: false }));
      const readinessState = await probe(record, campaign, handle);
      record.status = 'READY';
      if (record.readiness.type === 'http') record.endpoint ??= record.readiness.url;
      await withController(campaign, () => writeRecord(campaign, recordPath, record, { immutable: false }));
      return { environment: record, record_path: recordPath, ...readinessState };
    } catch (error) {
      handle ??= error.handle;
      if (handle?.pid && handle.identity) {
        await stopOwned(handle);
        record.process = { pid: handle.pid, start_token: handle.start_token,
          argv: draft.command.argv, cwd: draft.command.cwd, handle_path: handlePath };
      } else delete record.process;
      record.status = 'FAILED'; record.error = error.message;
      await withController(campaign, () => writeRecord(campaign, recordPath, record, { immutable: false }));
      throw new CliError('RUNTIME_START_FAILED', error.message, 5, [{ record_path: recordPath, logs }]);
    }
  }
  if (command === 'runtime inspect' || command === 'runtime stop') {
    required(typeof options['target-id'] === 'string', '--target-id is required.');
    const found = await findEnvironment(campaign, options['target-id']);
    const environment = found.record;
    const state = await inspectEnvironment(campaign, environment);
    if (command === 'runtime inspect') {
      const { handle, ...publicState } = state;
      return { environment, record_path: found.path, ...publicState };
    }
    if (!['OWNED', 'EXITED'].includes(state.ownership)) {
      throw new CliError('PROCESS_OWNERSHIP_MISMATCH', 'Refusing to stop a process without its matching ownership handle.', 4);
    }
    const stopped = state.ownership === 'OWNED' ? await stopOwned(state.handle) : state;
    if (stopped.alive) throw new CliError('PROCESS_OWNERSHIP_MISMATCH', 'Runtime ownership changed during stop.', 4);
    environment.status = 'STOPPED';
    await withController(campaign, () => writeRecord(campaign, found.path, environment, { immutable: false }));
    return { environment, record_path: found.path, alive: false, ownership: 'EXITED' };
  }
  throw new CliError('UNKNOWN_COMMAND', `Unsupported runtime command: ${command}`, 2);
}
