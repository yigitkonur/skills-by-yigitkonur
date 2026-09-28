import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, readdir, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createServer } from 'node:net';
import { createServer as httpServer } from 'node:http';
import { spawn, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { run as runtime } from '../../skills/run-agentic-tests/scripts/lib/runtime.mjs';
import { run as report } from '../../skills/run-agentic-tests/scripts/lib/report.mjs';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';
import { writeRecord, readCampaign, readYaml, stableStringify } from '../../skills/run-agentic-tests/scripts/lib/store.mjs';
import { assessCampaign, run as workflow } from '../../skills/run-agentic-tests/scripts/lib/workflow.mjs';

await loadDependencies({ setup: true });

async function fixture(t) {
  const root = await mkdtemp(path.join(tmpdir(), 'agentic-runtime-'));
  const campaign = path.join(root, 'campaign');
  await mkdir(campaign);
  t.after(async () => {
    await report('report stop', { campaign }).catch(() => {});
    for (const target of ['G001', 'G002']) await runtime('runtime stop', { campaign, 'target-id': target }).catch(() => {});
    await rm(root, { recursive: true, force: true });
  });
  await writeFile(path.join(campaign, '00-campaign.record.yaml'), JSON.stringify({
    schema_version: 1, kind: 'campaign', record_id: 'C0001', campaign_id: 'C0001',
    created_at: '2026-09-28T00:00:00.000Z', project: root, slug: 'runtime-proof',
    mode: 'autonomous', max_active: 4, host_capacity: 4, max_attempts: 5,
    active_plan_id: null, final_target_id: 'G001', locale: 'en', state: 'OPEN',
  }));
  return { root, campaign };
}

async function freePort() {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

async function environment(f, overrides = {}) {
  const port = await freePort();
  const script = path.join(f.root, 'app.mjs');
  await writeFile(script, `import http from 'node:http';
console.log('fixture launching');
http.createServer((q,s)=>s.end('agentic app ready')).listen(${port}, '127.0.0.1');\n`);
  const draft = {
    target_id: 'G001', runtime_type: 'http', source: { revision: 'revision-one', worktree: f.root },
    command: { argv: [process.execPath, script], cwd: f.root },
    readiness: { type: 'http', url: `http://127.0.0.1:${port}/`, expected_status: 200,
      body_contains: 'agentic app ready', timeout_ms: 3000 }, ...overrides,
  };
  const file = path.join(f.root, 'environment.draft.yaml');
  await writeFile(file, JSON.stringify(draft));
  return { file, draft };
}

const common = (kind, record_id) => ({ schema_version: 1, kind, record_id, campaign_id: 'C0001', created_at: '2026-09-28T00:00:00.000Z' });
const sha = value => createHash('sha256').update(value).digest('hex');

async function until(check, message, timeout = 5000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await check()) return;
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  assert.fail(message);
}

function liveProcess(pid) {
  try { return !/^Z/.test(execFileSync('ps', ['-p', String(pid), '-o', 'stat='], { encoding: 'utf8' }).trim()); }
  catch { return false; }
}

async function completedTask(f, record, outputPath, role, extra = {}) {
  const task = { ...common('task', `TASK-${record.task_id}`), task_id: record.task_id, actor_id: record.actor_id,
    role, state: 'DONE', worker_finished: true, handle: `fixture-context-${record.task_id}`,
    case_ids: record.case_id ? [record.case_id] : [], dependencies: [], resources: [], required_inputs: [],
    outputs: [{ kind: record.kind, record_id: record.record_id, path: outputPath, ...(record.case_id ? { case_id: record.case_id } : {}) }],
    draft_paths: [`tasks/${record.task_id}/draft/result.draft.yaml`], requested_action: `Complete the fixture ${role} assignment.`,
    ...(record.spec_revision ? { spec_revision: record.spec_revision } : {}),
    ...(record.target_id ? { target_id: record.target_id } : {}),
    ...(record.round_id ? { round_id: record.round_id } : {}), ...extra,
  };
  await writeRecord(f.campaign, `tasks/${record.task_id}/00-task.record.yaml`, task);
}

async function reportFixture(f, { latestOutcome = 'FAIL', pending = true, finding = true } = {}) {
  const campaign = await readCampaign(f.campaign);
  campaign.active_plan_id = 'P001'; campaign.final_target_id = 'G002';
  await writeRecord(f.campaign, '00-campaign.record.yaml', campaign, { immutable: false });
  const expectation = {
    ...common('expectations', 'SPEC-T0001'), task_id: 'J00001', actor_id: 'A00001', author_actor_id: 'A00001',
    case_id: 'T0001', spec_revision: 'S001', expectations: [{ id: 'E1', statement: 'The checkout confirms the order.',
      source: { type: 'user_request', reference: 'approved checkout contract' }, priority: 'P2', review_count: 1,
      observable: { description: 'Confirmation payload' }, evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'response' }] }],
  };
  await writeRecord(f.campaign, 'cases/T0001-checkout/specs/S001/02-expectations.record.yaml', expectation);
  await completedTask(f, expectation, 'cases/T0001-checkout/specs/S001/02-expectations.record.yaml', 'scenario-author');
  const specHashes = [];
  for (const [name, text] of [['01-test-case.md', 'Given checkout is ready\nWhen ordering\nThen [E1] an order is confirmed.'],
    ['03-how-to-run.md', 'Open checkout, submit the order, and save the real response.']]) {
    await writeFile(path.join(f.campaign, 'cases/T0001-checkout/specs/S001', name), text);
  }
  for (const name of ['01-test-case.md', '02-expectations.record.yaml', '03-how-to-run.md']) {
    const relative = `cases/T0001-checkout/specs/S001/${name}`;
    specHashes.push({ path: relative, sha256: sha(await readFile(path.join(f.campaign, relative))) });
  }
  const hashesByCase = new Map([['T0001', specHashes]]);
  if (pending) {
    const profileSpec = { ...structuredClone(expectation), record_id: 'SPEC-T0002', task_id: 'J00007', actor_id: 'A00007',
      author_actor_id: 'A00007', case_id: 'T0002' };
    profileSpec.expectations[0].statement = 'The profile loads the saved account details.';
    profileSpec.expectations[0].source.reference = 'approved profile contract';
    const specRoot = 'cases/T0002-profile/specs/S001';
    await writeRecord(f.campaign, `${specRoot}/02-expectations.record.yaml`, profileSpec);
    await completedTask(f, profileSpec, `${specRoot}/02-expectations.record.yaml`, 'scenario-author');
    await writeFile(path.join(f.campaign, specRoot, '01-test-case.md'), 'Given an account exists\nWhen opening the profile\nThen [E1] the saved account details appear.');
    await writeFile(path.join(f.campaign, specRoot, '03-how-to-run.md'), 'Open the real profile and save the account response.');
    const hashes = [];
    for (const name of ['01-test-case.md', '02-expectations.record.yaml', '03-how-to-run.md']) {
      const relative = `${specRoot}/${name}`;
      hashes.push({ path: relative, sha256: sha(await readFile(path.join(f.campaign, relative))) });
    }
    hashesByCase.set('T0002', hashes);
  }
  const environments = new Map();
  for (const target of ['G001', 'G002']) {
    const record = { ...common('environment', `ENV-${target}`), target_id: target, runtime_type: 'http',
      source: { revision: `revision-${target}`, worktree: f.root }, command: { argv: ['fixture-app'], cwd: f.root },
      readiness: { type: 'http', url: 'http://127.0.0.1:12345/', expected_status: 200, body_contains: 'ready' },
      status: 'READY', logs: { stdout: `environments/${target}/logs/stdout.log`, stderr: `environments/${target}/logs/stderr.log` },
    };
    await writeRecord(f.campaign, `environments/${target}/00-environment.record.yaml`, record);
    environments.set(target, record);
  }
  const plan = { ...common('plan', 'P001'), task_id: 'J00002', actor_id: 'A00002', target_id: 'G002',
    scope: { in_scope: ['checkout', 'profile'], out_of_scope: [{ item: 'native iOS device', reason: 'No device available.' }] },
    cases: (pending ? ['T0001', 'T0002'] : ['T0001']).map(case_id => ({ case_id, spec_revision: 'S001', target_id: 'G002', depends_on: [], resources: [], spec_hashes: hashesByCase.get(case_id) })),
    coverage: [{ source: 'approved checkout contract', case_ids: pending ? ['T0001', 'T0002'] : ['T0001'] }],
  };
  await writeRecord(f.campaign, 'plans/P001/10-plan.record.yaml', plan);
  await completedTask(f, plan, 'plans/P001/10-plan.record.yaml', 'planner');
  for (const [round, target, outcome, actual] of [['R001', 'G001', 'PASS', 'Order confirmed'], ['R002', 'G002', latestOutcome, latestOutcome === 'FAIL' ? 'Checkout returned an error' : 'Order confirmed']]) {
    const roundPath = `cases/T0001-checkout/rounds/${round}`;
    const artifactPath = `${roundPath}/evidences/response.json`;
    const content = JSON.stringify({ actual });
    await mkdir(path.join(f.campaign, roundPath, 'evidences'), { recursive: true });
    await writeFile(path.join(f.campaign, artifactPath), content);
    const execution = { ...common('execution', `EX-${round}`), task_id: round === 'R001' ? 'J00003' : 'J00005', actor_id: round === 'R001' ? 'A00003' : 'A00005', case_id: 'T0001',
      spec_revision: 'S001', round_id: round, target_id: target, execution_status: 'COMPLETED',
      observations: [{ expectation_id: 'E1', observed: actual, evidence_ids: ['EV1'], gaps: [] }],
      evidence: [{ id: 'EV1', path: artifactPath, type: 'json', expectation_ids: ['E1'], requirement_ids: ['ER1'],
        source: 'http://127.0.0.1/checkout', sha256: sha(content), size: Buffer.byteLength(content) }],
    };
    const verification = { ...common('verification', `VERIFY-${round}`), task_id: round === 'R001' ? 'J00004' : 'J00006', actor_id: round === 'R001' ? 'A00004' : 'A00006',
      case_id: 'T0001', spec_revision: 'S001', round_id: round, target_id: target, execution_record_id: execution.record_id,
      reviews: [{ expectation_id: 'E1', verdict: outcome, expected: expectation.expectations[0].statement,
        observed: actual, evidence_ids: ['EV1'], reason: 'Compared saved response with the approved contract.' }],
      inspected_evidence: [{ id: 'EV1', sha256: sha(content), method: 'read JSON', observation: actual }],
    };
    const env = environments.get(target);
    const context = { ...common('round_context', `CTX-${round}`), case_id: 'T0001', spec_revision: 'S001',
      round_id: round, target_id: target, execution_task_id: execution.task_id, expectations_record_id: expectation.record_id,
      plan_id: 'P001', purpose: 'final', finding_ids: [], spec_hashes: specHashes,
      target_source_digest: sha(stableStringify({ source: env.source, command: env.command, readiness: env.readiness })),
    };
    await writeRecord(f.campaign, `${roundPath}/00-context.record.yaml`, context);
    await writeRecord(f.campaign, `${roundPath}/10-execution.record.yaml`, execution);
    await writeRecord(f.campaign, `${roundPath}/20-verification-a.record.yaml`, verification);
    await completedTask(f, execution, `${roundPath}/10-execution.record.yaml`, 'executor', { purpose: 'final', plan_id: 'P001' });
    await completedTask(f, verification, `${roundPath}/20-verification-a.record.yaml`, 'verifier', { verification_slot: 'a', plan_id: 'P001' });
    await writeRecord(f.campaign, `${roundPath}/30-verdict--${outcome}.record.yaml`, {
      ...common('verdict', `VERDICT-${round}`), case_id: 'T0001', spec_revision: 'S001', round_id: round,
      target_id: target, outcome, execution_record_id: execution.record_id, verification_record_ids: [verification.record_id],
      finding_ids: outcome === 'FAIL' ? ['F0001'] : [], evidence_hashes: [{ path: artifactPath, sha256: sha(content) }],
      inputs_digest: sha(stableStringify({ expectations: expectation, execution, verifications: [verification], context })),
      expectation_verdicts: [{ expectation_id: 'E1', outcome, reason: 'Independent review.' }],
    });
  }
  if (finding) await writeRecord(f.campaign, 'findings/F0001-checkout/00-finding.record.yaml', {
    ...common('finding', 'F0001'), finding_id: 'F0001', class: 'PRODUCT_DEFECT', priority: 'P2', case_ids: ['T0001'],
    source_record_ids: ['EX-R002'], scope: 'in_scope', state: 'OPEN', lineage_id: 'F0001', attempts: 1,
    attempt_rounds: [{ case_id: 'T0001', round_id: 'R002', execution_record_id: 'EX-R002' }],
    issue_url: 'https://github.com/example/app/issues/12', pr_urls: ['https://github.com/example/app/pull/13'], summary: 'Checkout error',
  });
}

test('an owned real HTTP runtime starts, inspects and stops without killing another process', async t => {
  const f = await fixture(t);
  const { file, draft } = await environment(f);
  const unrelated = spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)'], { stdio: 'ignore' });
  t.after(() => unrelated.kill());
  t.after(() => runtime('runtime stop', { campaign: f.campaign, 'target-id': 'G001' }).catch(() => {}));
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  assert.equal(started.environment.status, 'READY');
  assert.equal(await (await fetch(draft.readiness.url)).text(), 'agentic app ready');
  const inspected = await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' });
  assert.equal(inspected.ownership, 'OWNED');
  assert.equal(inspected.alive, true);
  const stopped = await runtime('runtime stop', { campaign: f.campaign, 'target-id': 'G001' });
  assert.equal(stopped.environment.status, 'STOPPED');
  assert.equal(stopped.alive, false);
  assert.equal(process.kill(unrelated.pid, 0), true);
  await assert.rejects(fetch(draft.readiness.url));
  assert.match(await readFile(path.join(f.campaign, started.environment.logs.stdout), 'utf8'), /fixture launching/);
});

test('a wrapper exit preserves the owned group handle until its background child is stopped', async t => {
  const f = await fixture(t);
  const wrapper = path.join(f.root, 'wrapper.mjs');
  const background = path.join(f.root, 'background.mjs');
  const pidFile = path.join(f.root, 'background.pid');
  const orphanReady = path.join(f.root, 'orphan-ready');
  await writeFile(background, `import {writeFileSync} from 'node:fs';import {execFileSync} from 'node:child_process';
let checks=0;setInterval(()=>{const parent=Number(execFileSync('ps',['-p',String(process.pid),'-o','ppid='],{encoding:'utf8'}));
if(parent!==Number(process.argv[2])&&++checks>=5)writeFileSync(${JSON.stringify(orphanReady)},'orphan still running');},25);`);
  await writeFile(wrapper, `import {spawn} from 'node:child_process';import {writeFileSync} from 'node:fs';
const child=spawn(process.execPath,[${JSON.stringify(background)},String(process.pid)],{stdio:'ignore'});child.unref();
writeFileSync(${JSON.stringify(pidFile)},String(child.pid));console.log('wrapper ready');setTimeout(()=>process.exit(0),500);`);
  let childPid;
  t.after(() => {
    if (!childPid) return;
    try {
      const command = execFileSync('ps', ['-p', String(childPid), '-o', 'command='], { encoding: 'utf8' });
      if (command.includes(background)) process.kill(childPid, 'SIGKILL');
    } catch { /* The verified owned background process already exited. */ }
  });
  const { file } = await environment(f, { runtime_type: 'mcp_stdio', command: { argv: [process.execPath, wrapper], cwd: f.root },
    readiness: { type: 'process', body_contains: 'wrapper ready', timeout_ms: 2000 } });
  await runtime('runtime start', { campaign: f.campaign, file });
  childPid = Number(await readFile(pidFile, 'utf8'));
  await until(async () => (await readFile(orphanReady, 'utf8').catch(() => '')) === 'orphan still running', 'background fixture did not observe wrapper exit');
  const inspected = await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' });
  assert.equal(inspected.ownership, 'OWNED');
  assert.equal(inspected.alive, true);
  await runtime('runtime stop', { campaign: f.campaign, 'target-id': 'G001' });
  await until(() => !liveProcess(childPid), 'owned background child survived runtime stop');
});

test('HTTP readiness cannot claim an unrelated listener as the new runtime', async t => {
  const f = await fixture(t);
  const unrelated = httpServer((request, response) => response.end('agentic app ready'));
  await new Promise(resolve => unrelated.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => unrelated.close(resolve)));
  const { file } = await environment(f, {
    command: { argv: [process.execPath, '-e', 'setInterval(()=>{},1000)'], cwd: f.root },
    readiness: { type: 'http', url: `http://127.0.0.1:${unrelated.address().port}/`,
      expected_status: 200, body_contains: 'agentic app ready', timeout_ms: 300 },
  });
  t.after(() => runtime('runtime stop', { campaign: f.campaign, 'target-id': 'G001' }).catch(() => {}));
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file }),
    error => error.code === 'RUNTIME_PORT_IN_USE');
  assert.equal(await (await fetch(`http://127.0.0.1:${unrelated.address().port}`)).text(), 'agentic app ready');
});

test('failed readiness preserves logs and a failed record while cleaning up the owned runtime', async t => {
  const f = await fixture(t);
  const { file, draft } = await environment(f);
  draft.readiness.body_contains = 'this marker never appears';
  draft.readiness.timeout_ms = 200;
  await writeFile(file, JSON.stringify(draft));
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file }),
    error => error.code === 'RUNTIME_START_FAILED' && /Readiness timed out/.test(error.message));
  const inspected = await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' });
  assert.equal(inspected.environment.status, 'FAILED');
  assert.equal(inspected.alive, false, JSON.stringify({ ownership: inspected.ownership, error: inspected.environment.error, process: inspected.environment.process }));
  await assert.rejects(fetch(draft.readiness.url));
  assert.match(await readFile(path.join(f.campaign, inspected.environment.logs.stdout), 'utf8'), /fixture launching/);
});

test('runtime stop refuses a replaced process identity and preserves the unrelated process', async t => {
  const f = await fixture(t);
  const { file } = await environment(f);
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  const unrelated = spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)'], { stdio: 'ignore' });
  t.after(() => unrelated.kill());
  const changed = structuredClone(started.environment);
  changed.process.pid = unrelated.pid;
  changed.process.start_token = 'stale-or-forged-token';
  await writeRecord(f.campaign, started.record_path, changed, { immutable: false });
  try {
    assert.equal((await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' })).ownership, 'MISMATCH');
    await assert.rejects(runtime('runtime stop', { campaign: f.campaign, 'target-id': 'G001' }),
      error => error.code === 'PROCESS_OWNERSHIP_MISMATCH');
    assert.equal(process.kill(unrelated.pid, 0), true);
  } finally { await writeRecord(f.campaign, started.record_path, started.environment, { immutable: false }); }
});

test('a declared process handshake supports a persistent stdio adapter without equating existence with readiness', async t => {
  const f = await fixture(t);
  const { file } = await environment(f, { runtime_type: 'mcp_stdio',
    command: { argv: [process.execPath, '-e', "console.log('fixture handshake');setInterval(()=>{},1000)"], cwd: f.root },
    readiness: { type: 'process', body_contains: 'fixture handshake', timeout_ms: 1000 },
  });
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  assert.equal(started.environment.status, 'READY');
  assert.equal(started.environment.runtime_type, 'mcp_stdio');
  assert.match(await readFile(path.join(f.campaign, started.environment.logs.stdout), 'utf8'), /fixture handshake/);
});

test('a one-shot CLI probe requires its declared marker and exit zero without a keepalive process', async t => {
  const f = await fixture(t);
  const { file } = await environment(f, { runtime_type: 'cli',
    command: { argv: [process.execPath, '-e', "console.log('CLI configuration is ready')"], cwd: f.root },
    readiness: { type: 'process', body_contains: 'CLI configuration is ready', timeout_ms: 1000 },
  });
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  assert.equal(started.environment.status, 'READY');
  assert.equal(started.alive, false);
  const inspected = await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' });
  assert.equal(inspected.ownership, 'EXITED');
  assert.match(await readFile(path.join(f.campaign, inspected.environment.logs.stdout), 'utf8'), /CLI configuration is ready/);
  const invalid = await environment(f, { target_id: 'G002', runtime_type: 'cli',
    command: { argv: [process.execPath, '-e', "console.log('CLI configuration is ready');process.exit(7)"], cwd: f.root },
    readiness: { type: 'process', body_contains: 'CLI configuration is ready', timeout_ms: 1000 },
  });
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file: invalid.file }),
    error => error.code === 'RUNTIME_START_FAILED');
  assert.equal((await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G002' })).environment.status, 'FAILED');
});

test('runtime startup writes the assigned environment operator output that task close can accept', async t => {
  const f = await fixture(t);
  const request = path.join(f.root, 'operator-request.yaml');
  await writeFile(request, JSON.stringify({ role: 'environment-operator', requested_action: 'Start the real fixture runtime.' }));
  const task = (await workflow('task create', { campaign: f.campaign, request })).task;
  await workflow('task dispatch', { campaign: f.campaign, 'task-id': task.task_id });
  await workflow('task bind', { campaign: f.campaign, 'task-id': task.task_id, handle: 'runtime-test-operator-context' });
  const { file, draft } = await environment(f, { target_id: task.target_id, task_id: task.task_id, actor_id: task.actor_id });
  await writeFile(file, JSON.stringify({ ...draft, actor_id: 'A99999' }));
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file }), error => error.code === 'WRONG_ASSIGNMENT');
  await writeFile(file, JSON.stringify(draft));
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  assert.equal(started.environment.record_id, task.outputs[0].record_id);
  const closed = await workflow('task close', { campaign: f.campaign, 'task-id': task.task_id, finished: true });
  assert.equal(closed.task.state, 'DONE');
});

test('a report stop handle copied from an app runtime cannot stop that app', async t => {
  const f = await fixture(t);
  const { file, draft } = await environment(f);
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  const handle = await readFile(path.join(f.campaign, started.environment.process.handle_path));
  await writeFile(path.join(f.campaign, '.report-server.runtime.json'), handle);
  await assert.rejects(report('report stop', { campaign: f.campaign }),
    error => error.code === 'PROCESS_OWNERSHIP_MISMATCH');
  assert.equal(await (await fetch(draft.readiness.url)).text(), 'agentic app ready');
});

test('failed executable startup records the failure and cannot reuse the target identity', async t => {
  const f = await fixture(t);
  const { file } = await environment(f, { runtime_type: 'cli',
    command: { argv: [path.join(f.root, 'missing-executable')], cwd: f.root },
    readiness: { type: 'process', body_contains: 'ready', timeout_ms: 500 },
  });
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file }), error => error.code === 'RUNTIME_START_FAILED');
  const inspected = await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' });
  assert.equal(inspected.environment.status, 'FAILED');
  assert.equal(inspected.alive, false);
  assert.match(await readFile(path.join(f.campaign, inspected.environment.logs.stderr), 'utf8'), /ENOENT|missing-executable/);
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file }), error => error.code === 'TARGET_EXISTS');
});

test('an exited startup helper cannot be confused with the controller when process inspection is delayed', async t => {
  const f = await fixture(t);
  const bin = path.join(f.root, 'bin');
  await mkdir(bin);
  // Preserve real ps output, but force the caller's read/death interleaving.
  await writeFile(path.join(bin, 'ps'), `#!/bin/sh
parent_command=$(/bin/ps -p "$PPID" -o command=)
case "$parent_command" in *process-host.mjs*) ;; *) /bin/sleep 0.15 ;; esac
exec /bin/ps "$@"
`, { mode: 0o755 });
  const previousPath = process.env.PATH;
  process.env.PATH = `${bin}:${previousPath}`;
  t.after(() => { process.env.PATH = previousPath; });
  const { file } = await environment(f, { runtime_type: 'cli',
    command: { argv: [path.join(f.root, 'missing-executable')], cwd: f.root },
    readiness: { type: 'process', body_contains: 'ready', timeout_ms: 500 },
  });
  await assert.rejects(runtime('runtime start', { campaign: f.campaign, file }), error => error.code === 'RUNTIME_START_FAILED');
  const inspected = await runtime('runtime inspect', { campaign: f.campaign, 'target-id': 'G001' });
  assert.notEqual(inspected.environment.process?.pid, process.pid, 'A failed helper must never record the controller PID as its runtime.');
  assert.equal(inspected.alive, false);
});

test('CLI argv stays literal and environment values are inherited without entering records or handles', async t => {
  const f = await fixture(t);
  const literal = '; $(touch should-never-exist)';
  const secretName = 'AGENTIC_RUNTIME_TEST_SECRET';
  const previous = process.env[secretName];
  process.env[secretName] = 'fixture-secret-that-must-stay-out-of-records';
  t.after(() => { if (previous === undefined) delete process.env[secretName]; else process.env[secretName] = previous; });
  const { file } = await environment(f, { runtime_type: 'cli',
    command: { argv: [process.execPath, '-e', "console.log(JSON.stringify({argument:process.argv[1],secretPresent:Boolean(process.env.AGENTIC_RUNTIME_TEST_SECRET)}))", literal], cwd: f.root, env_names: [secretName] },
    readiness: { type: 'process', body_contains: '"secretPresent":true', timeout_ms: 1000 },
  });
  const started = await runtime('runtime start', { campaign: f.campaign, file });
  const output = JSON.parse(await readFile(path.join(f.campaign, started.environment.logs.stdout), 'utf8'));
  assert.equal(output.argument, literal);
  assert.equal(output.secretPresent, true);
  await assert.rejects(readFile(path.join(f.root, 'should-never-exist')), error => error.code === 'ENOENT');
  for (const relative of [started.record_path, started.environment.process.handle_path]) {
    assert.doesNotMatch(await readFile(path.join(f.campaign, relative), 'utf8'), /fixture-secret-that-must-stay-out-of-records/);
  }
});

test('a report built from an empty campaign exposes incomplete coverage rather than a green summary', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.campaign, '.env'), 'PRIVATE_TOKEN=must-not-be-published');
  const result = await report('report build', { campaign: f.campaign });
  assert.equal(result.summary.overall, 'INCOMPLETE');
  assert.equal(result.summary.total, 0);
  const html = await readFile(path.join(f.campaign, result.report_path), 'utf8');
  assert.match(html, /INCOMPLETE/);
  assert.match(html, /No accepted plan/);
  assert.doesNotMatch(html, /PRIVATE_TOKEN/);
  assert.match(html, /data-filter/);
});

test('the report server uses a free port, serves only report files, and stops its owned process', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.campaign, '.env'), 'PRIVATE_TOKEN=must-not-be-published');
  await report('report build', { campaign: f.campaign });
  const served = await report('report serve', { campaign: f.campaign, port: '0' });
  assert.match(served.url, /^http:\/\/127\.0\.0\.1:\d+\/$/);
  const response = await fetch(served.url);
  assert.equal(response.status, 200);
  assert.match(await response.text(), /INCOMPLETE/);
  for (const suffix of ['.env', '00-campaign.record.yaml', 'artifacts/', '%2e%2e/.env', '%2e%2e%2f.env', 'index.html/extra']) {
    const denied = await fetch(served.url + suffix);
    assert.notEqual(denied.status, 200, suffix);
    assert.doesNotMatch(await denied.text(), /PRIVATE_TOKEN/);
  }
  assert.equal((await fetch(served.url, { method: 'POST' })).status, 405);
  const stopped = await report('report stop', { campaign: f.campaign });
  assert.equal(stopped.alive, false);
  await assert.rejects(fetch(served.url));
});

test('repeated report shutdowns settle exited processes without misidentifying a dying PID', async t => {
  const f = await fixture(t);
  await report('report build', { campaign: f.campaign });
  for (let iteration = 0; iteration < 8; iteration++) {
    const served = await report('report serve', { campaign: f.campaign, port: '0' });
    assert.equal((await fetch(served.url)).status, 200);
    const stopped = await report('report stop', { campaign: f.campaign });
    assert.equal(stopped.ownership, 'EXITED');
    assert.equal(stopped.alive, false);
  }
});

test('the report preserves historical rounds while counting current observations, blocked coverage, and linked findings', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.total, 2);
  assert.equal(built.summary.counts.FAIL, 1);
  assert.equal(built.summary.counts.NOT_RUN, 1);
  assert.equal(built.summary.counts.PASS, 0);
  assert.equal(built.summary.overall, 'FAIL');
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  for (const text of ['R001', 'R002', 'Historical', 'Current', 'The checkout confirms the order.',
    'Checkout returned an error', 'Order confirmed', 'native iOS device', 'No device available.']) assert.ok(html.includes(text), text);
  assert.match(html, /href="https:\/\/github.com\/example\/app\/issues\/12"/);
  assert.match(html, /href="https:\/\/github.com\/example\/app\/pull\/13"/);
  const linkedArtifacts = [...html.matchAll(/href="(artifacts\/[a-f0-9]+\.json)"/g)].map(match => match[1]);
  assert.equal(new Set(linkedArtifacts).size, 2);
  for (const artifact of new Set(linkedArtifacts)) assert.match(await readFile(path.join(f.campaign, 'report', artifact), 'utf8'), /actual/);
});

test('changed or missing canonical evidence invalidates current proof and is not republished', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const currentArtifact = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/evidences/response.json');
  await writeFile(currentArtifact, '{"actual":"changed after verification"}');
  let built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.counts.INVALID_EVIDENCE, 1);
  assert.notEqual(built.summary.overall, 'PASS');
  assert.ok(built.summary.gaps.some(gap => /hash|changed/i.test(gap)));
  let html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  assert.doesNotMatch(html, new RegExp(`href="artifacts/${sha('{"actual":"changed after verification"}')}`));
  await rm(currentArtifact);
  built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.counts.INVALID_EVIDENCE, 1);
  assert.ok(built.summary.gaps.some(gap => /Missing evidence/.test(gap)));
});

test('a verifier record from another target cannot substantiate the current round', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const file = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/20-verification-a.record.yaml');
  const verification = await readYaml(file);
  verification.target_id = 'G001';
  await writeFile(file, JSON.stringify(verification));
  const built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.counts.INVALID_EVIDENCE, 1);
  assert.ok(built.summary.gaps.some(gap => /target|source|provenance/i.test(gap)));
});

test('agent-controlled HTML and unsafe links render as text without script or URL injection', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const file = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/10-execution.record.yaml');
  const execution = await readYaml(file);
  execution.observations[0].observed = '</script><img src=x onerror="alert(1)"><script>alert(2)</script>';
  await writeFile(file, JSON.stringify(execution));
  const findingFile = path.join(f.campaign, 'findings/F0001-checkout/00-finding.record.yaml');
  const finding = await readYaml(findingFile);
  finding.issue_url = 'javascript:alert(3)';
  finding.pr_urls = ['https://user:password@example.test/private', 'data:text/html,<script>alert(4)</script>'];
  await writeFile(findingFile, JSON.stringify(finding));
  const built = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  assert.doesNotMatch(html, /<img src=x|<script>alert\(|href="(?:javascript:|data:|https:\/\/user:password)/);
  assert.match(html, /&lt;\/script&gt;&lt;img/);
  assert.match(html, /\\u003c\/script\\u003e/);
  assert.doesNotMatch(html, /user:password/);
});

test('report publication omits structured and free-text credentials and exposes the omission as a blocking gap', async t => {
  const f = await fixture(t);
  await reportFixture(f, { latestOutcome: 'PASS', pending: false, finding: false });
  const campaign = await readCampaign(f.campaign);
  campaign.slug = 'sk-fixturetitlecredential1234567890';
  await writeFile(path.join(f.campaign, '00-campaign.record.yaml'), JSON.stringify(campaign));
  const base = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002');
  const execution = await readYaml(path.join(base, '10-execution.record.yaml'));
  execution.observations[0].observed = { message: 'Order confirmed', api_key: 'review-fixture-secret-12345',
    detail: 'password: free-text-private-54321', raw: 'Tool output {"api_key":"embedded-json-secret-45678"}',
    headers: [{ name: 'Authorization', value: 'Bearer credential-23456' }] };
  await writeFile(path.join(base, '10-execution.record.yaml'), JSON.stringify(execution));
  const verification = await readYaml(path.join(base, '20-verification-a.record.yaml'));
  verification.reviews[0].reason = 'Saved response matches. access_token = review-label-private-34567';
  await writeFile(path.join(base, '20-verification-a.record.yaml'), JSON.stringify(verification));
  const verdict = await readYaml(path.join(base, '30-verdict--PASS.record.yaml'));
  const expectations = await readYaml(path.join(f.campaign, 'cases/T0001-checkout/specs/S001/02-expectations.record.yaml'));
  const context = await readYaml(path.join(base, '00-context.record.yaml'));
  verdict.inputs_digest = sha(stableStringify({ expectations, execution, verifications: [verification], context }));
  await writeFile(path.join(base, '30-verdict--PASS.record.yaml'), JSON.stringify(verdict));
  const assessment = await assessCampaign(f.campaign);
  const audit = { ...common('plan_audit', 'CLOSURE-SECRET'), task_id: 'J00009', actor_id: 'A00009', phase: 'closure',
    subject_record_id: 'P001', subject_digest: assessment.closure_subject_digest, outcome: 'approved', findings: [], artifacts: [] };
  await writeRecord(f.campaign, 'plans/P001/30-closure.record.yaml', audit);
  await completedTask(f, audit, 'plans/P001/30-closure.record.yaml', 'plan-auditor', { phase: 'closure', plan_id: 'P001' });
  assert.equal((await assessCampaign(f.campaign)).complete, true);
  const built = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  for (const value of [campaign.slug, 'review-fixture-secret-12345', 'free-text-private-54321', 'credential-23456', 'review-label-private-34567', 'embedded-json-secret-45678']) {
    assert.equal(html.includes(value), false, 'Credential value entered the published HTML.');
  }
  assert.match(html, /REDACTED/);
  assert.notEqual(built.summary.overall, 'PASS');
  assert.ok(built.summary.gaps.some(gap => /sensitive|credential|omitted/i.test(gap)));
});

test('a replacement sealed verdict shows its accepted review and preserves the superseded verdict trail', async t => {
  const f = await fixture(t);
  await reportFixture(f, { latestOutcome: 'PASS', pending: false, finding: false });
  const base = 'cases/T0001-checkout/rounds/R002';
  const previousTaskPath = path.join(f.campaign, 'tasks/J00006/00-task.record.yaml');
  const previousTask = await readYaml(previousTaskPath);
  previousTask.state = 'CANCELLED';
  await writeFile(previousTaskPath, JSON.stringify(previousTask));
  const previous = await readYaml(path.join(f.campaign, base, '30-verdict--PASS.record.yaml'));
  const verification = await readYaml(path.join(f.campaign, base, '20-verification-a.record.yaml'));
  verification.record_id = 'VERIFY-R002-REPLACEMENT';
  verification.task_id = 'J00008'; verification.actor_id = 'A00008';
  verification.reviews[0].verdict = 'FAIL';
  verification.reviews[0].reason = 'Replacement review found a missing confirmation identifier.';
  const verificationPath = `${base}/21-verification-a-replacement.record.yaml`;
  await writeRecord(f.campaign, verificationPath, verification);
  await completedTask(f, verification, verificationPath, 'verifier', { verification_slot: 'a', plan_id: 'P001' });
  const expectations = await readYaml(path.join(f.campaign, 'cases/T0001-checkout/specs/S001/02-expectations.record.yaml'));
  const execution = await readYaml(path.join(f.campaign, base, '10-execution.record.yaml'));
  const context = await readYaml(path.join(f.campaign, base, '00-context.record.yaml'));
  const replacement = { ...previous, record_id: `${previous.record_id}-V002`, outcome: 'FAIL',
    supersedes_record_id: previous.record_id, verification_record_ids: [verification.record_id],
    inputs_digest: sha(stableStringify({ expectations, execution, verifications: [verification], context })),
    expectation_verdicts: [{ expectation_id: 'E1', outcome: 'FAIL', reason: verification.reviews[0].reason }] };
  await writeRecord(f.campaign, `${base}/31-verdict--FAIL--V002.record.yaml`, replacement);
  const assessment = await assessCampaign(f.campaign);
  assert.equal(assessment.cases[0].verdict_record_id, replacement.record_id);
  const built = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  const published = JSON.parse(html.match(/<script id="report-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  const current = published.cases[0].rounds.find(round => round.current);
  assert.deepEqual(current.verification_record_ids, [verification.record_id]);
  assert.equal(current.reviews[0].reason, verification.reviews[0].reason);
  assert.equal(current.recorded_outcome, 'FAIL');
  assert.deepEqual(current.verdict_history.map(verdict => verdict.record_id), [replacement.record_id, previous.record_id]);
  assert.equal(current.verdict_history[0].supersedes_record_id, previous.record_id);
  assert.match(html, /Sealed verdict history/);
  assert.match(html, /supersedes VERDICT-R002/);
  assert.match(html, /Superseded seal VERDICT-R002/);
});

test('replacement metacharacters in observations, sources, and findings remain literal in HTML and JSON', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const literal = "$& token, $' suffix, $` prefix {{DATA}} {{CASES}}";
  const executionFile = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/10-execution.record.yaml');
  const execution = await readYaml(executionFile);
  execution.observations[0].observed = literal;
  await writeFile(executionFile, JSON.stringify(execution));
  const specFile = path.join(f.campaign, 'cases/T0001-checkout/specs/S001/02-expectations.record.yaml');
  const spec = await readYaml(specFile);
  spec.expectations[0].source.reference = literal;
  await writeFile(specFile, JSON.stringify(spec));
  const findingFile = path.join(f.campaign, 'findings/F0001-checkout/00-finding.record.yaml');
  const finding = await readYaml(findingFile);
  finding.summary = literal;
  await writeFile(findingFile, JSON.stringify(finding));
  const built = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  const published = JSON.parse(html.match(/<script id="report-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  const current = published.cases.find(item => item.case_id === 'T0001').rounds.find(item => item.round_id === 'R002');
  assert.equal(current.observations[0].observed, literal);
  assert.equal(current.expectations[0].source.reference, literal);
  assert.equal(published.cases[0].findings[0].summary, literal);
  assert.equal(html.includes("$&amp; token, $&#39; suffix, $` prefix"), true);
  assert.equal((html.match(/<script id="report-data"/g) || []).length, 1);
});

test('a report refuses evidence traversal, symlinks, and credential files even inside the evidence directory', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const file = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/10-execution.record.yaml');
  const execution = await readYaml(file);
  const original = execution.evidence[0].path;
  const secret = 'PRIVATE_TOKEN=do-not-publish-this-credential';
  await writeFile(path.join(f.campaign, '.env'), secret);
  for (const relative of ['../../.env', 'cases/T0001-checkout/rounds/R002/evidences/.env', 'cases/T0001-checkout/rounds/R002/evidences/secret-link.txt']) {
    if (relative.endsWith('/.env')) await writeFile(path.join(f.campaign, relative), secret);
    if (relative.endsWith('secret-link.txt')) await symlink(path.join(f.campaign, '.env'), path.join(f.campaign, relative));
    execution.evidence[0].path = relative;
    execution.evidence[0].sha256 = sha(secret); execution.evidence[0].size = Buffer.byteLength(secret);
    await writeFile(file, JSON.stringify(execution));
    const verdictFile = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/30-verdict--FAIL.record.yaml');
    const verdict = await readYaml(verdictFile);
    verdict.evidence_hashes = [{ path: relative, sha256: sha(secret) }];
    await writeFile(verdictFile, JSON.stringify(verdict));
    const verifierFile = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/20-verification-a.record.yaml');
    const verification = await readYaml(verifierFile);
    verification.inspected_evidence[0].sha256 = sha(secret);
    await writeFile(verifierFile, JSON.stringify(verification));
    const built = await report('report build', { campaign: f.campaign });
    assert.equal(built.summary.counts.INVALID_EVIDENCE, 1, relative);
    for (const artifact of await readdir(path.join(f.campaign, 'report/artifacts'))) {
      assert.doesNotMatch(await readFile(path.join(f.campaign, 'report/artifacts', artifact), 'utf8'), /PRIVATE_TOKEN|do-not-publish/);
    }
  }
  execution.evidence[0].path = original;
});

test('published evidence is served with safe content types and rejects content changed after report build', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const built = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  const artifact = html.match(/href="(artifacts\/[a-f0-9]+\.json)"/)[1];
  const served = await report('report serve', { campaign: f.campaign, port: '0' });
  let response = await fetch(served.url + artifact);
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type'), /application\/json/);
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
  assert.match(response.headers.get('content-disposition'), /attachment/);
  assert.equal((await response.json()).actual, 'Order confirmed');
  await writeFile(path.join(f.campaign, 'report', artifact), 'mutated published evidence');
  response = await fetch(served.url + artifact);
  assert.equal(response.status, 409);
  assert.doesNotMatch(await response.text(), /mutated published/);
  await rm(path.join(f.campaign, 'report', artifact));
  await symlink(path.join(f.campaign, '00-campaign.record.yaml'), path.join(f.campaign, 'report', artifact));
  response = await fetch(served.url + artifact);
  assert.equal(response.status, 404);
});

test('a PNG screenshot is previewed and served as a verified image', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const base = 'cases/T0001-checkout/rounds/R002';
  const file = path.join(f.campaign, base, '10-execution.record.yaml');
  const execution = await readYaml(file);
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6k+cAAAAASUVORK5CYII=', 'base64');
  const evidencePath = `${base}/evidences/screenshot.png`;
  await writeFile(path.join(f.campaign, evidencePath), png);
  execution.evidence = [{ id: 'EV1', type: 'screenshot', path: evidencePath, expectation_ids: ['E1'], sha256: sha(png), size: png.length }];
  await writeFile(file, JSON.stringify(execution));
  const verifierFile = path.join(f.campaign, base, '20-verification-a.record.yaml');
  const verification = await readYaml(verifierFile);
  verification.inspected_evidence[0].sha256 = sha(png);
  await writeFile(verifierFile, JSON.stringify(verification));
  const verdictFile = path.join(f.campaign, base, '30-verdict--FAIL.record.yaml');
  const verdict = await readYaml(verdictFile);
  verdict.evidence_hashes = [{ path: evidencePath, sha256: sha(png) }];
  await writeFile(verdictFile, JSON.stringify(verdict));
  const built = await report('report build', { campaign: f.campaign });
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  const preview = html.match(/<img src="(artifacts\/[a-f0-9]+\.png)"/)[1];
  const served = await report('report serve', { campaign: f.campaign, port: '0' });
  const response = await fetch(served.url + preview);
  assert.equal(response.headers.get('content-type'), 'image/png');
  assert.deepEqual(Buffer.from(await response.arrayBuffer()), png);
});

test('the report requires the core closure digest and invalidates old completion on target advance', async t => {
  const f = await fixture(t);
  await reportFixture(f, { latestOutcome: 'PASS', pending: false, finding: false });
  const audit = { ...common('plan_audit', 'CLOSURE-STALE'), task_id: 'J00009', actor_id: 'A00009', phase: 'closure',
    subject_record_id: 'P001', subject_digest: 'b'.repeat(64), outcome: 'approved', findings: [], artifacts: [] };
  await writeRecord(f.campaign, 'plans/P001/30-stale-closure.record.yaml', audit);
  await completedTask(f, audit, 'plans/P001/30-stale-closure.record.yaml', 'plan-auditor', { phase: 'closure', plan_id: 'P001' });
  let built = await report('report build', { campaign: f.campaign });
  assert.notEqual(built.summary.overall, 'PASS', 'an approved closure for another proof digest cannot complete this report');
  const assessed = await assessCampaign(f.campaign);
  const currentAudit = { ...audit, task_id: 'J00010', actor_id: 'A00010', record_id: 'CLOSURE-CURRENT', subject_digest: assessed.closure_subject_digest };
  await writeRecord(f.campaign, 'plans/P001/31-valid-closure.record.yaml', currentAudit);
  await completedTask(f, currentAudit, 'plans/P001/31-valid-closure.record.yaml', 'plan-auditor', { phase: 'closure', plan_id: 'P001' });
  built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.overall, 'PASS');
  const config = await readCampaign(f.campaign);
  config.final_target_id = 'G003';
  await writeRecord(f.campaign, '00-campaign.record.yaml', config, { immutable: false });
  built = await report('report build', { campaign: f.campaign });
  assert.notEqual(built.summary.overall, 'PASS');
  assert.equal(built.summary.counts.PASS, 0);
  assert.ok(built.summary.gaps.some(gap => /G003|EXECUTION_REQUIRED/.test(gap)));
});

test('a partially reviewed round shows its accepted observations and review while the verdict is pending', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  await rm(path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/30-verdict--FAIL.record.yaml'));
  const file = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/20-verification-a.record.yaml');
  const verification = await readYaml(file);
  verification.reviews[0].reason = 'First independent review inspected this current response; aggregation is pending.';
  await writeFile(file, JSON.stringify(verification));
  const built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.counts.NOT_ASSESSED, 1);
  assert.notEqual(built.summary.overall, 'PASS');
  const html = await readFile(path.join(f.campaign, built.report_path), 'utf8');
  assert.match(html, /First independent review inspected this current response/);
  assert.match(html, /VERIFICATION_REQUIRED/);
});

test('a verdict pointing at the wrong record kind produces an invalid-evidence report instead of aborting', async t => {
  const f = await fixture(t);
  await reportFixture(f);
  const file = path.join(f.campaign, 'cases/T0001-checkout/rounds/R002/30-verdict--FAIL.record.yaml');
  const verdict = await readYaml(file);
  verdict.verification_record_ids = ['F0001'];
  await writeFile(file, JSON.stringify(verdict));
  const built = await report('report build', { campaign: f.campaign });
  assert.equal(built.summary.counts.INVALID_EVIDENCE, 1);
  assert.ok(built.summary.gaps.some(gap => /verifier record is missing/i.test(gap)));
});
