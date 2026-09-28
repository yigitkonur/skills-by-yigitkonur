import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { loadDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';

const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
const { YAML } = await loadDependencies({ setup: true });
const repository = 'fixture/tested-product';
const product = variant => `const name=process.argv[2];
if(name==='--ready') console.log('greeting service ready');
else console.log(JSON.stringify({message:'Hello, '+name+${variant === 0 ? "''" : variant === 1 ? "(name==='Ada'?'!':'')" : "'!'"}}));\n`;

function processResult(command, args, cwd, env = process.env, expected = 0) {
  const result = spawnSync(command, args, { cwd, env, encoding: 'utf8', timeout: 30000 });
  assert.equal(result.status, expected, `${command} ${args.join(' ')}\n${result.stdout}\n${result.stderr}`);
  return result;
}

test('real isolated fixes and local Git delivery recover an integrated runtime with intact independent proof', async t => {
  const root = await mkdtemp(path.join(tmpdir(), 'agentic-local-delivery-'));
  const project = path.join(root, 'product');
  await mkdir(project);
  const git = (...args) => processResult('git', args, project).stdout.trim();
  git('init', '-b', 'main'); git('config', 'user.name', 'Local acceptance'); git('config', 'user.email', 'fixture@example.invalid');
  await writeFile(path.join(project, 'app.mjs'), product(0));
  await writeFile(path.join(project, 'requirements.md'), 'Named greetings must return JSON containing message "Hello, NAME!" for Ada and Grace.\n');
  await writeFile(path.join(project, '.gitignore'), 'agentic-tests/\n');
  git('add', '.'); git('commit', '-m', 'Fixture with missing punctuation');
  const bare = path.join(root, 'remote.git');
  processResult('git', ['init', '--bare', bare], root);
  git('remote', 'add', 'origin', `https://github.com/${repository}.git`);
  git('remote', 'set-url', '--push', 'origin', bare);
  git('push', '-u', 'origin', 'main');

  // Only the hosted API boundary is simulated. Application processes, patches,
  // commits, pushes to the local bare remote, and integrations are real.
  const gh = path.join(root, 'gh-stub');
  const ghState = path.join(root, 'gh-state.json');
  await writeFile(ghState, JSON.stringify({ calls: [], prs: {} }));
  await writeFile(gh, `#!${process.execPath}
import fs from 'node:fs';import {execFileSync} from 'node:child_process';
const file=process.env.GH_LOCAL_STATE; const state=JSON.parse(fs.readFileSync(file,'utf8'));const a=process.argv.slice(2);
if(a[a.indexOf('--repo')+1]!==${JSON.stringify(repository)}||!a.includes('--repo'))throw Error('wrong repository');
state.calls.push(a);
if(a[0]==='issue'&&a[1]==='create')console.log('https://github.com/${repository}/issues/1');
else if(a[0]==='pr'&&a[1]==='create'){const id=Object.keys(state.prs).length+2;state.prs[id]=a[a.indexOf('--head')+1];console.log('https://github.com/${repository}/pull/'+id);}
else if(a[0]==='pr'&&a[1]==='merge'){execFileSync('git',['-C',process.env.GH_LOCAL_PROJECT,'merge','--ff-only',state.prs[a[2]]]);execFileSync('git',['-C',process.env.GH_LOCAL_PROJECT,'push','origin','main']);console.log('Merged locally');}
else throw Error('unexpected hosted command');fs.writeFileSync(file,JSON.stringify(state));
`, { mode: 0o755 });
  const ghEnv = { ...process.env, GH_LOCAL_STATE: ghState, GH_LOCAL_PROJECT: project };
  const hosted = args => processResult(gh, args, project, ghEnv).stdout.trim();
  const call = (command, options = {}, expected = 0) => {
    const args = command.split(' ').concat(Object.entries(options).flatMap(([key, value]) => [`--${key}`, String(value)]));
    return JSON.parse(processResult(process.execPath, [cli, ...args], project, process.env, expected).stdout);
  };
  const initialized = call('init', { project, slug: 'real-repair', 'host-capacity': 4 });
  const campaign = initialized.campaign_path;
  const invoke = (command, options = {}, expected = 0) => call(command, { campaign, ...options }, expected);
  const targets = [];
  t.after(async () => {
    for (const target of targets) invoke('runtime stop', { 'target-id': target });
    if (process.env.AT_RETAIN_LOCAL_ACCEPTANCE) console.log(`Retained local acceptance: ${root}`);
    else await rm(root, { recursive: true, force: true });
  });
  let fileNumber = 0;
  const jsonFile = async value => {
    const file = path.join(campaign, `request-${++fileNumber}.json`);
    await writeFile(file, JSON.stringify(value)); return file;
  };
  const create = async request => invoke('task create', { request: await jsonFile(request) }).task;
  const start = task => { invoke('task dispatch', { 'task-id': task.task_id }); invoke('task bind', { 'task-id': task.task_id, handle: `scripted-fixture-${task.task_id}` }); };
  const finish = task => invoke('task close', { 'task-id': task.task_id, finished: true });
  const records = options => invoke('records', options).records;
  const preserved = new Map();
  async function publish(task, body, index = 0) {
    const file = path.join(campaign, task.draft_paths[index]);
    const draft = { ...YAML.parse(await readFile(file, 'utf8')), ...body };
    await writeFile(file, YAML.stringify(draft));
    const result = invoke('submit', { 'task-id': task.task_id, file });
    const acceptedPath = path.join(campaign, task.outputs[index].path);
    preserved.set(acceptedPath, await readFile(acceptedPath));
    return { record: records({ 'record-id': result.record_id })[0], receipt: result };
  }
  const prior = (change, hypothesis) => ({ previous_failure: 'The saved named greeting lacks required punctuation.', what_changed: change, hypothesis, do_not_repeat: ['Do not patch only one literal name.', 'Do not replay a prior target.'], remaining_attempts: 5 - (records({ kind: 'finding' })[0]?.attempts || 0) });
  const cases = [];
  for (const name of ['Ada', 'Grace']) {
    const task = await create({ role: 'scenario-author', slug: name.toLowerCase(), requested_action: `Import the approved named greeting for ${name}.`, required_inputs: [{ base: 'project', path: 'requirements.md' }] }); start(task);
    const spec = path.dirname(path.join(campaign, task.outputs[0].path));
    await writeFile(path.join(spec, '01-test-case.md'), `Feature: Named greetings\nScenario: Greet ${name}\nGiven a ready greeting CLI\nWhen the user requests ${name}\nThen [E1] JSON message is Hello, ${name}!\n`);
    await writeFile(path.join(spec, '03-how-to-run.md'), `Run node app.mjs ${name} in the assigned source worktree and save argv, exit code, stdout and stderr in evidences/command.json.`);
    const statement = `JSON message is Hello, ${name}!`;
    const { record } = await publish(task, { expectations: [{ id: 'E1', statement, source: { type: 'user_request', reference: 'project:requirements.md' }, priority: 'P2', review_count: 1, observable: { description: 'Saved stdout JSON from the actual CLI process' }, evidence_requirements: [{ id: 'ER1', type: 'json', capture: 'Command output and exit status' }] }] }); finish(task);
    cases.push({ id: record.case_id, name, statement });
  }
  async function environment(target, revision, operator, fail = false) {
    const worktree = path.join(root, `target-${target}`);
    git('worktree', 'add', '--detach', worktree, revision);
    const task = operator || await create({ role: 'environment-operator', target_id: target, requested_action: 'Prepare the isolated real CLI source and readiness probe.' }); start(task);
    const file = path.join(campaign, task.draft_paths[0]);
    const draft = YAML.parse(await readFile(file, 'utf8'));
    Object.assign(draft, { runtime_type: 'cli', source: { revision, provider: { type: 'git', root: worktree } }, command: { argv: [process.execPath, path.join(worktree, 'app.mjs'), '--ready'], cwd: worktree }, readiness: { type: 'process', body_contains: fail ? 'unavailable readiness marker' : 'greeting service ready', timeout_ms: 500 } });
    await writeFile(file, YAML.stringify(draft));
    const result = invoke('runtime start', { file }, fail ? 5 : 0);
    if (fail) assert.equal(result.error.code, 'RUNTIME_START_FAILED');
    else assert.equal(result.environment.status, 'READY');
    targets.push(target); finish(task); return worktree;
  }
  async function plan(target) {
    const task = await create({ role: 'planner', target_id: target, requested_action: 'Plan both independent named greeting variants on the selected target.' }); start(task);
    await publish(task, { scope: { in_scope: ['Ada and Grace greetings'], out_of_scope: [] }, cases: cases.map(item => ({ case_id: item.id, spec_revision: 'S001', target_id: target, depends_on: [], resources: [] })), coverage: [{ source: 'project:requirements.md', case_ids: cases.map(item => item.id) }] }); finish(task);
    const auditor = await create({ role: 'plan-auditor', plan_id: task.plan_id, requested_action: 'Independently audit the two-case contract and target.' }); start(auditor);
    await publish(auditor, { outcome: 'approved', findings: [], artifacts: [] }); finish(auditor);
    invoke('plan accept', { file: path.join(campaign, task.outputs[0].path), audit: path.join(campaign, auditor.outputs[0].path) });
  }
  async function execute(items, target, worktree, request = {}, gap = false) {
    const task = await create({ role: 'executor', case_ids: items.map(item => item.id), target_id: target, requested_action: 'Execute each named greeting as a fresh real CLI invocation.', ...(items.length > 1 ? { group: { shared_setup: 'Same immutable CLI source', reset: 'New process for every name', independent: true } } : {}), ...request }); start(task);
    for (let i = 0; i < items.length; i++) {
      const item = items[i]; const result = processResult(process.execPath, ['app.mjs', item.name], worktree);
      const observed = { argv: ['node', 'app.mjs', item.name], exit_code: result.status, stdout: result.stdout, stderr: result.stderr };
      const artifact = `${path.posix.dirname(task.outputs[i].path)}/evidences/command.json`;
      if (!gap) await writeFile(path.join(campaign, artifact), JSON.stringify(observed));
      await publish(task, { execution_status: gap ? 'PARTIAL' : 'COMPLETED', observations: [{ expectation_id: 'E1', observed, evidence_ids: gap ? [] : ['EV1'], gaps: gap ? [{ requirement_id: 'ER1', reason: 'Initial capture procedure omitted the artifact.' }] : [] }], evidence: gap ? [] : [{ id: 'EV1', path: artifact, type: 'json', expectation_ids: ['E1'], requirement_ids: ['ER1'] }] }, i);
    }
    finish(task);
    const verifier = await create({ role: 'verifier', case_ids: task.case_ids, target_id: target, round_id: task.round_id, requested_action: 'Read the saved output and frozen expected message without rerunning the application.', ...(task.group ? { group: task.group } : {}) }); start(verifier);
    for (let i = 0; i < items.length; i++) {
      const item = items[i]; const execution = records({ 'record-id': task.outputs[i].record_id })[0];
      const saved = gap ? null : JSON.parse(await readFile(path.join(campaign, execution.evidence[0].path), 'utf8'));
      const outcome = gap ? 'INCONCLUSIVE' : JSON.parse(saved.stdout).message === `Hello, ${item.name}!` ? 'PASS' : 'FAIL';
      await publish(verifier, { execution_record_id: execution.record_id, reviews: [{ expectation_id: 'E1', verdict: outcome, expected: item.statement, observed: saved || 'Required capture is absent.', evidence_ids: gap ? [] : ['EV1'], reason: gap ? 'No saved artifact supports a result.' : 'Read the saved actual CLI output and compare its message with the required named greeting.' }], inspected_evidence: execution.evidence.map(e => ({ id: e.id, sha256: e.sha256, method: 'Read saved JSON', observation: saved.stdout })), findings: outcome === 'FAIL' && records({ kind: 'finding' }).length ? [{ class: 'PRODUCT_DEFECT', lineage_id: 'F0001', summary: 'Shared greeting formatter omits punctuation.', expectation_ids: ['E1'] }] : [] }, i);
    }
    finish(verifier); invoke('reconcile'); return task;
  }
  const initialTree = await environment('G001', git('rev-parse', 'HEAD'));
  await plan('G001');
  await execute([cases[0]], 'G001', initialTree, {}, true);
  assert.equal(records({ kind: 'finding' })[0].class, 'EVIDENCE_GAP');
  await execute(cases, 'G001', initialTree, { finding_id: 'F0001', prior_context: prior('Capture raw stdout for both variants.', 'Saved process output will establish the formatter defect.') });
  assert.equal(records({ kind: 'finding' }).length, 1);
  assert.equal(records({ kind: 'finding' })[0].class, 'PRODUCT_DEFECT');
  assert.deepEqual(records({ kind: 'finding' })[0].case_ids, cases.map(item => item.id));

  const diagnosis = await create({ role: 'diagnostician', finding_id: 'F0001', requested_action: 'Inspect the formatter source against the independently captured missing punctuation.', required_inputs: [{ base: 'project', path: 'app.mjs' }] }); start(diagnosis);
  await publish(diagnosis, { conclusion: 'confirmed', summary: 'The shared formatter does not append the required punctuation.', root_cause: 'app.mjs joins Hello and the name without an exclamation mark.', evidence_record_ids: records({ kind: 'execution' }).map(record => record.record_id), artifacts: [] }); finish(diagnosis);
  const ticket = await create({ role: 'ticket-writer', finding_id: 'F0001', requested_action: 'Document the confirmed shared formatter defect.' }); start(ticket);
  const issueBody = 'findings/issue.md'; await writeFile(path.join(campaign, issueBody), 'Expected both named greetings to end with an exclamation mark. Actual saved CLI outputs omit it. Local hosted-API acceptance stub.');
  const issue = hosted(['issue', 'create', '--repo', repository, '--body-file', path.join(campaign, issueBody)]);
  await publish(ticket, { issue_url: issue, dedup_marker: `agentic-tests:${initialized.campaign.campaign_id}:F0001`, body_path: issueBody, artifacts: [] }); finish(ticket);

  for (const number of [1, 2]) {
    const fixer = await create({ role: 'implementer', finding_id: 'F0001', requested_action: number === 1 ? 'Implement a first candidate punctuation fix.' : 'Repair the still-failing Grace variant using the previous fix and retest history.', required_inputs: [{ base: 'project', path: 'app.mjs' }], prior_context: prior(number === 1 ? 'First isolated formatter correction.' : 'Generalize punctuation after the literal-name patch failed Grace.', number === 1 ? 'Adding punctuation to the observed Ada path may satisfy the scenario.' : 'Apply the same suffix to every name instead of special-casing Ada.') });
    if (number === 2) {
      const handoff = await readFile(path.join(campaign, `tasks/${fixer.task_id}/10-handoff.md`), 'utf8');
      assert.match(handoff, /R003|R002/);
      assert.match(handoff, /pull\/2/);
      assert.match(handoff, /implementation|IMPL-/i);
      assert.match(handoff, /Grace/);
    }
    start(fixer);
    const branch = `fix-${number}`; const worktree = path.join(root, branch);
    git('worktree', 'add', '-b', branch, worktree, 'main');
    await writeFile(path.join(worktree, 'app.mjs'), product(number));
    const developerCheck = processResult(process.execPath, ['app.mjs', 'Ada'], worktree);
    assert.equal(JSON.parse(developerCheck.stdout).message, 'Hello, Ada!');
    processResult('git', ['add', 'app.mjs'], worktree); processResult('git', ['commit', '-m', `Formatter correction ${number}`], worktree);
    processResult('git', ['push', 'origin', branch], worktree);
    const commit = processResult('git', ['rev-parse', 'HEAD'], worktree).stdout.trim();
    const body = `findings/pr-${number}.md`; const check = `findings/check-${number}.log`;
    await writeFile(path.join(campaign, body), `Related to #1. Formatter correction ${number}. Ada developer check passed; independent two-case retest remains required.`);
    await writeFile(path.join(campaign, check), developerCheck.stdout);
    const pr = hosted(['pr', 'create', '--repo', repository, '--head', branch, '--base', 'main', '--body-file', path.join(campaign, body)]);
    const { record: implementation } = await publish(fixer, { worktree, commit, pr_url: pr, pr_body_path: body, changed_files: ['app.mjs'], checks: [{ command: 'node app.mjs Ada', exit_code: 0, artifact_path: check }], summary: `Formatter correction ${number}`, artifacts: [] }); finish(fixer);
    const integrator = await create({ role: 'integrator', finding_id: 'F0001', requested_action: 'Integrate the real local branch and allocate independent retests.' }); start(integrator);
    hosted(['pr', 'merge', pr.split('/').at(-1), '--repo', repository, '--merge']);
    assert.equal(git('rev-parse', 'HEAD'), commit);
    const target = integrator.target_id;
    await publish(integrator, { implementation_record_id: implementation.record_id, new_target_id: target, commit, affected_case_ids: cases.map(item => item.id), retest_obligations: cases.map(item => ({ case_id: item.id, reason: 'Shared formatter changed.' })), artifacts: [] }); finish(integrator);
    if (number === 1) {
      const next = await environment(target, commit); await plan(target);
      await execute(cases, target, next, { finding_id: 'F0001', purpose: 'retest', prior_context: prior('First formatter patch integrated.', 'Check both names independently; the developer check only covered Ada.') });
      assert.equal(invoke('status').complete, false);
      assert.equal(invoke('status').cases.find(item => item.case_id === cases[1].id).outcome, 'FAIL');
    } else {
      await environment(target, commit, undefined, true);
      const recovery = invoke('runtime recover', { 'target-id': target, file: await jsonFile({ requested_action: 'Recover the same integrated source with the correct readiness marker.', reason: 'The first runtime used an incorrect readiness marker; see its preserved runtime logs.', prior_context: prior('Correct readiness marker without modifying source.', 'The actual ready marker will establish access to the same integrated code.') }) });
      const successor = recovery.task.target_id;
      const next = await environment(successor, commit, recovery.task); await plan(successor);
      await execute(cases, successor, next, { finding_id: 'F0001', purpose: 'final', prior_context: prior('General formatter correction integrated and runtime recovered.', 'Both independent named calls now use the shared punctuation path.') });
      assert.equal(records({ kind: 'finding' })[0].state, 'RESOLVED');
      assert.ok(records({ kind: 'finding' })[0].attempts <= 5);
      const auditor = await create({ role: 'plan-auditor', phase: 'closure', requested_action: 'Audit current final target proof, linked finding, preserved history, and completed repairs.' }); start(auditor);
      await publish(auditor, { outcome: 'approved', findings: [], artifacts: [] }); finish(auditor);
      assert.equal(invoke('reconcile').complete, true);
      const report = invoke('report build'); assert.equal(report.summary.overall, 'PASS');
      const html = await readFile(path.join(campaign, report.report_path), 'utf8');
      assert.match(html, /pull\/2/); assert.match(html, /pull\/3/); assert.match(html, /Hello, Grace!/);
    }
  }
  const calls = JSON.parse(await readFile(ghState, 'utf8')).calls;
  assert.equal(calls.filter(args => args[0] === 'issue').length, 1);
  assert.equal(calls.filter(args => args[0] === 'pr' && args[1] === 'merge').length, 2);
  for (const [file, bytes] of preserved) assert.deepEqual(await readFile(file), bytes, `Historical record changed: ${file}`);
});
