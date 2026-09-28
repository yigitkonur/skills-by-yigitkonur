import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm, copyFile } from 'node:fs/promises';
import { createServer } from 'node:net';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';

const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
const product = fileURLToPath(new URL('./fixtures/product.mjs', import.meta.url));
const { YAML } = await loadDependencies({ setup: true });

function invoke(args, expectedExit = 0) {
  const result = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8', timeout: 20000 });
  assert.equal(result.status, expectedExit, `${args.join(' ')}\n${result.stdout}\n${result.stderr}`);
  assert.ok(!result.error, result.error?.message);
  return JSON.parse(result.stdout);
}

async function availablePort() {
  const socket = createServer();
  await new Promise(resolve => socket.listen(0, '127.0.0.1', resolve));
  const port = socket.address().port;
  await new Promise(resolve => socket.close(resolve));
  return port;
}

test('public CLI runs a real HTTP case through independent role records and rejects changed proof', async t => {
  const project = await mkdtemp(path.join(tmpdir(), 'agentic-public-'));
  const runtimeProduct = path.join(project, 'product.mjs');
  await copyFile(product, runtimeProduct);
  let campaign;
  t.after(async () => {
    if (campaign) {
      spawnSync(process.execPath, [cli, 'report', 'stop', '--campaign', campaign], { encoding: 'utf8', timeout: 10000 });
      spawnSync(process.execPath, [cli, 'runtime', 'stop', '--campaign', campaign, '--target-id', 'G001'], { encoding: 'utf8', timeout: 10000 });
    }
    await rm(project, { recursive: true, force: true });
  });
  const initialized = invoke(['init', '--project', project, '--slug', 'greeting', '--host-capacity', '4']);
  campaign = initialized.campaign_path;
  const command = (words, ...args) => invoke([...words.split(' '), '--campaign', campaign, ...args]);
  let serial = 0;
  async function task(request) {
    const file = path.join(project, `request-${++serial}.yaml`);
    await writeFile(file, YAML.stringify(request));
    const created = command('task create', '--request', file).task;
    command('task dispatch', '--task-id', created.task_id);
    command('task bind', '--task-id', created.task_id, '--handle', `contract-fixture-context-${created.task_id}`);
    return created;
  }
  async function draftFor(assigned, body) {
    const file = path.join(campaign, assigned.draft_paths[0]);
    const draft = { ...YAML.parse(await readFile(file, 'utf8')), ...body };
    await writeFile(file, YAML.stringify(draft));
    return { file, draft };
  }
  async function publish(assigned, body) {
    const { file } = await draftFor(assigned, body);
    const receipt = command('submit', '--task-id', assigned.task_id, '--file', file);
    assert.equal(receipt.submission_status, 'ACCEPTED');
    command('task close', '--task-id', assigned.task_id, '--finished');
    return YAML.parse(await readFile(path.join(campaign, assigned.outputs[0].path), 'utf8'));
  }

  const author = await task({ role: 'scenario-author', slug: 'greeting', requested_action: 'Bootstrap the approved greeting scenario.' });
  const specDirectory = path.dirname(path.join(campaign, author.outputs[0].path));
  await writeFile(path.join(specDirectory, '01-test-case.md'), 'Feature: Greeting\nScenario: Named greeting\nGiven the greeting service is ready\nWhen Ada requests a greeting\nThen [E1] the response contains "Hello, Ada!"\n');
  await writeFile(path.join(specDirectory, '03-how-to-run.md'), 'POST /greet with JSON {"name":"Ada"}. Save the exact response bytes to evidences/response.json. Record HTTP status and response content.');
  const expectation = { id: 'E1', statement: 'The successful response greets Ada by name.', source: { type: 'approved_scenario', reference: 'Fixture greeting contract: POST /greet with Ada returns Hello, Ada!' }, priority: 'P2', review_count: 1, observable: { description: 'HTTP 200 with JSON message Hello, Ada!' }, evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Exact response body from POST /greet.' }] };
  await publish(author, { expectations: [expectation] });

  const operator = await task({ role: 'environment-operator', requested_action: 'Start the actual fixture HTTP runtime.' });
  const port = await availablePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const environmentFile = path.join(project, 'environment.yaml');
  await writeFile(environmentFile, YAML.stringify({
    target_id: operator.target_id, task_id: operator.task_id, actor_id: operator.actor_id,
    runtime_type: 'http', source: { revision: 'fixture-v1', provider: { type: 'files', root: project, paths: ['product.mjs'] } },
    command: { argv: [process.execPath, runtimeProduct, 'http', String(port)], cwd: project },
    readiness: { type: 'http', url: `${baseUrl}/health`, expected_status: 200, body_contains: 'agentic-fixture', timeout_ms: 3000 },
  }));
  const started = command('runtime start', '--file', environmentFile);
  assert.equal(started.environment.status, 'READY');
  command('task close', '--task-id', operator.task_id, '--finished');

  const planner = await task({ role: 'planner', target_id: 'G001', requested_action: 'Plan the greeting scenario with independent review.' });
  const plan = await publish(planner, {
    scope: { in_scope: ['Named greeting'], out_of_scope: [] },
    cases: [{ case_id: 'T0001', spec_revision: 'S001', target_id: 'G001', depends_on: [], resources: [] }],
    coverage: [{ source: 'Approved greeting scenario', case_ids: ['T0001'] }],
  });
  const auditor = await task({ role: 'plan-auditor', plan_id: plan.record_id, requested_action: 'Audit scenario coverage and runtime selection.' });
  await publish(auditor, { outcome: 'approved', findings: [], artifacts: [] });
  command('plan accept', '--file', path.join(campaign, planner.outputs[0].path), '--audit', path.join(campaign, auditor.outputs[0].path));

  const executor = await task({ role: 'executor', case_ids: ['T0001'], purpose: 'final', requested_action: 'Perform the actual HTTP request and preserve its response.' });
  const response = await fetch(`${baseUrl}/greet`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: 'Ada' }) });
  const responseText = await response.text();
  assert.equal(response.status, 200);
  assert.deepEqual(JSON.parse(responseText), { message: 'Hello, Ada!' });
  const artifact = `${path.posix.dirname(executor.outputs[0].path)}/evidences/response.json`;
  await writeFile(path.join(campaign, artifact), responseText);
  const executionBody = {
    execution_status: 'COMPLETED', observations: [{ expectation_id: 'E1', observed: { status: response.status, body: JSON.parse(responseText) }, evidence_ids: ['EV1'], gaps: [] }],
    evidence: [{ id: 'EV1', path: artifact, type: 'json', expectation_ids: ['E1'], requirement_ids: ['ER1'], source: `${baseUrl}/greet`, tool: 'Node fetch' }],
  };
  const { file: executionDraft } = await draftFor(executor, executionBody);
  const checked = command('submit', '--task-id', executor.task_id, '--file', executionDraft, '--check');
  assert.equal(checked.worker_may_finish, false);
  assert.equal(command('records', '--kind', 'execution').records.length, 0, 'check must not accept the draft');
  const receipt = command('submit', '--task-id', executor.task_id, '--file', executionDraft);
  assert.equal(receipt.worker_may_finish, true);
  assert.equal(receipt.test_verdict, 'NOT_DECIDED');
  assert.equal(command('submit', '--task-id', executor.task_id, '--file', executionDraft).record_id, receipt.record_id);
  command('task close', '--task-id', executor.task_id, '--finished');
  assert.equal(command('status').complete, false, 'executing a test alone cannot complete a campaign');

  const execution = YAML.parse(await readFile(path.join(campaign, executor.outputs[0].path), 'utf8'));
  assert.equal(execution.evidence[0].sha256, createHash('sha256').update(responseText).digest('hex'));
  const verifier = await task({ role: 'verifier', case_ids: ['T0001'], round_id: executor.round_id, requested_action: 'Read saved JSON and compare it with the approved expectation without rerunning.' });
  await publish(verifier, {
    execution_record_id: execution.record_id,
    reviews: [{ expectation_id: 'E1', verdict: 'PASS', expected: expectation.statement, observed: JSON.parse(responseText), evidence_ids: ['EV1'], reason: 'The saved response message is exactly Hello, Ada! and execution captured HTTP 200.' }],
    inspected_evidence: [{ id: 'EV1', sha256: execution.evidence[0].sha256, method: 'Read and parse saved JSON', observation: 'message equals Hello, Ada!' }],
  });
  command('reconcile');
  const verdicts = command('records', '--kind', 'verdict').records;
  assert.equal(verdicts.length, 1);
  assert.equal(verdicts[0].outcome, 'PASS');
  assert.equal(command('status').complete, false, 'independent closure audit remains required');

  const closure = await task({ role: 'plan-auditor', plan_id: plan.record_id, phase: 'closure', requested_action: 'Audit current-target proof and unresolved obligations without executing the application.' });
  await publish(closure, { outcome: 'approved', findings: [], artifacts: [] });
  command('reconcile');
  assert.equal(command('status').complete, true, 'completed independent closure can finish current-target proof');

  command('report build');
  const html = await readFile(path.join(campaign, 'report/index.html'), 'utf8');
  assert.match(html, /Hello, Ada!/);
  assert.match(html, /The successful response greets Ada by name/);

  command('task interrupt', '--task-id', verifier.task_id, '--reason', 'Fixture withdrawal: replace a review without rerunning the application.', '--finished');
  assert.equal(command('status').complete, false);
  const replacement = await task({ role: 'verifier', case_ids: ['T0001'], round_id: executor.round_id, verification_slot: 'a', requested_action: 'Freshly inspect the same saved response without application interaction.' });
  const replacedReview = await publish(replacement, {
    execution_record_id: execution.record_id,
    reviews: [{ expectation_id: 'E1', verdict: 'PASS', expected: expectation.statement, observed: JSON.parse(responseText), evidence_ids: ['EV1'], reason: 'Independent replacement inspection reads the unchanged saved JSON message Hello, Ada!.' }],
    inspected_evidence: [{ id: 'EV1', sha256: execution.evidence[0].sha256, method: 'Parse the saved original JSON', observation: 'message is Hello, Ada!' }],
  });
  command('reconcile');
  const superseding = command('records', '--kind', 'verdict').records.find(record => record.supersedes_record_id === verdicts[0].record_id);
  assert.ok(superseding);
  assert.deepEqual(superseding.verification_record_ids, [replacedReview.record_id]);
  assert.equal(command('records', '--kind', 'execution').records.length, 1, 'Replacing a reviewer must not require executing the application again.');
  assert.equal(command('status').complete, false, 'A superseding proof needs a current closure audit.');
  const replacementClosure = await task({ role: 'plan-auditor', plan_id: plan.record_id, phase: 'closure', requested_action: 'Audit the current replacement proof and retained history.' });
  await publish(replacementClosure, { outcome: 'approved', findings: [], artifacts: [] });
  command('reconcile');
  assert.equal(command('status').complete, true);
  command('report build');
  const replacementHtml = await readFile(path.join(campaign, 'report/index.html'), 'utf8');
  const model = JSON.parse(replacementHtml.match(/<script id="report-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  assert.deepEqual(model.cases[0].rounds.find(round => round.current).verification_record_ids, [replacedReview.record_id]);

  const streamed = spawnSync(process.execPath, [cli, 'records', '--campaign', campaign, '--kind', 'execution', '--format', 'yaml-stream'], { encoding: 'utf8' });
  assert.equal(streamed.status, 0, streamed.stderr);
  const exported = YAML.parseAllDocuments(streamed.stdout).map(document => document.toJSON());
  assert.equal(exported[0].record_id, execution.record_id);

  await writeFile(path.join(campaign, artifact), '{"message":"Replaced after verification"}');
  command('reconcile');
  const stale = command('status');
  assert.equal(stale.complete, false);
  assert.match(JSON.stringify(stale), /EVIDENCE_CHANGED/);
  command('report build');
  assert.match(await readFile(path.join(campaign, 'report/index.html'), 'utf8'), /EVIDENCE_CHANGED|changed|stale/i);
});

test('canonical record export is a YAML stream without the JSON receipt wrapper', async t => {
  const project = await mkdtemp(path.join(tmpdir(), 'agentic-export-'));
  t.after(() => rm(project, { recursive: true, force: true }));
  const initialized = invoke(['init', '--project', project, '--slug', 'export', '--host-capacity', '1']);
  const result = spawnSync(process.execPath, [cli, 'records', '--campaign', initialized.campaign_path, '--format', 'yaml-stream'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stdout);
  const records = YAML.parseAllDocuments(result.stdout).map(document => document.toJSON());
  assert.equal(records.length, 1);
  assert.equal(records[0].kind, 'campaign');
  assert.equal(records[0].campaign_id, initialized.campaign.campaign_id);
  assert.ok(!Object.hasOwn(records[0], 'ok'));
});
