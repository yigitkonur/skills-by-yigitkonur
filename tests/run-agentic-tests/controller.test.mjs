import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { loadDependencies, getDependencies } from '../../skills/run-agentic-tests/scripts/lib/dependencies.mjs';
const cli = fileURLToPath(new URL('../../skills/run-agentic-tests/scripts/agentic-tests.mjs', import.meta.url));
await loadDependencies({ setup: true });
function call(command, args = {}, expected = 0) {
  const argv = command.split(' ').concat(Object.entries(args).flatMap(([k, v]) => [`--${k}`, String(v)]));
  const r = spawnSync(process.execPath, [cli, ...argv], { encoding: 'utf8' });
  assert.equal(r.status, expected, `${command}: ${r.stdout}\n${r.stderr}`);
  return JSON.parse(r.stdout);
}
async function setup(t) {
  const project = await mkdtemp(path.join(tmpdir(), 'controller space-'));
  t.after(() => rm(project, { recursive: true, force: true }));
  await writeFile(path.join(project, 'app.mjs'), 'console.log("ready")\n');
  const init = call('init', { project, slug: 'public', 'host-capacity': 8 });
  let seq = 0;
  const c = { project, campaign: init.campaign_path, config: init.campaign };
  c.json = async obj => { const f = path.join(c.campaign, `request-${++seq}.json`); await writeFile(f, JSON.stringify(obj)); return f; };
  c.create = async (request, expected = 0) => call('task create', { campaign: c.campaign, request: await c.json(request) }, expected);
  c.start = task => { call('task dispatch', { campaign: c.campaign, 'task-id': task.task_id }); call('task bind', { campaign: c.campaign, 'task-id': task.task_id, handle: `host-${task.task_id}` }); };
  c.draft = async (task, i = 0) => getDependencies().YAML.parse(await readFile(path.join(c.campaign, task.draft_paths[i]), 'utf8'));
  c.submit = async (task, draft, expected = 0) => call('submit', { campaign: c.campaign, 'task-id': task.task_id, file: await c.json(draft) }, expected);
  c.close = task => call('task close', { campaign: c.campaign, 'task-id': task.task_id, finished: true });
  c.records = options => call('records', { campaign: c.campaign, ...options }).records;
  return c;
}

test('typed project inputs are resolved read-only with concrete bounded handoffs and symlink containment', async t => {
  const c = await setup(t);
  await mkdir(path.join(c.project, 'src'));
  await writeFile(path.join(c.project, 'src', 'product.mjs'), 'export const product = true;\n');
  const { task, handoff_path } = await c.create({ role: 'feature-scout', requested_action: 'Discover product features', required_inputs: [{ base: 'project', path: '.' }, { base: 'project', path: 'src/product.mjs' }] });
  c.start(task);
  const handoff = await readFile(path.join(c.campaign, handoff_path), 'utf8');
  for (const value of [cli, c.project, c.campaign, 'src/product.mjs', 'references/roles/feature-scout.md', 'submit', '--check', '--task-id', task.task_id, 'worker_may_finish', 'Write scope']) assert.ok(handoff.includes(value), value);
  await symlink(tmpdir(), path.join(c.project, 'escape'));
  const rejected = await c.create({ role: 'feature-scout', requested_action: 'Read outside source', required_inputs: [{ base: 'project', path: 'escape' }] }, 3);
  assert.equal(rejected.error.code, 'UNSAFE_INPUT');
  const bad = await c.create({ role: 'feature-scout', requested_action: 'Read traversal', required_inputs: [{ base: 'project', path: '../other' }] }, 3);
  assert.equal(bad.error.code, 'UNSAFE_INPUT');
});

test('validation failures name bad fields and allowed values without echoing supplied secrets', async t => {
  const c = await setup(t);
  const invalid = await c.create({ role: 'bad-role-SECRET_VALUE', requested_action: 'Inspect features', api_secret: 'SECRET_VALUE' }, 3);
  assert.equal(invalid.error.code, 'INVALID_RECORD');
  assert.ok(invalid.error.issues.some(i => i.field === '/role' && i.rule === 'enum' && i.allowed.includes('feature-scout')));
  assert.ok(invalid.error.issues.some(i => i.property === 'api_secret' && i.remedy));
  assert.ok(invalid.next_actions.length);
  assert.ok(!JSON.stringify(invalid).includes('SECRET_VALUE'));
});
