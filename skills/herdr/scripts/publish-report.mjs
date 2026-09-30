#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fail = message => { throw new Error(message); };
const mapping = (value, key) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${key}: expected mapping`);
};
const string = (value, key) => {
  if (typeof value !== 'string' || !value.trim()) fail(`${key}: expected nonempty string`);
};
const nullableString = (value, key) => { if (value !== null) string(value, key); };

try {
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: node publish-report.mjs ABSOLUTE_PARTIAL_JSON ABSOLUTE_REPORT_YAML');
    process.exit(0);
  }
  if (args.length !== 2 || args.some(p => !path.isAbsolute(p))) fail('Supply two absolute paths: partial JSON, destination .yaml');
  const [partial, destination] = args;
  if (partial === destination || path.extname(destination) !== '.yaml') fail('Destination must be a separate .yaml path');
  if (!fs.lstatSync(partial).isFile()) fail('Partial must be a regular file, not a symlink');
  const bytes = fs.readFileSync(partial);
  const report = JSON.parse(bytes);
  mapping(report, 'report');
  if (report.schema_version !== 1) fail('schema_version: expected 1');
  for (const key of ['mission_id', 'task_id', 'report_id', 'summary']) string(report[key], key);
  if (!Number.isInteger(report.attempt) || report.attempt < 1) fail('attempt: expected positive integer');
  for (const key of ['producer', 'manager', 'cto', 'git']) mapping(report[key], key);
  const producer = report.producer;
  for (const key of ['runtime', 'model', 'role', 'pane_id', 'tab_id', 'terminal_id', 'skill_path', 'skill_revision']) string(producer[key], `producer.${key}`);
  if (!['agy', 'codex', 'claude'].includes(producer.runtime)) fail('producer.runtime: unsupported runtime');
  if (!['implementer', 'reviewer', 'integrator', 'manager', 'recovery_executor'].includes(producer.role)) fail('producer.role: unsupported role');
  nullableString(producer.session_id, 'producer.session_id');
  for (const owner of ['manager', 'cto']) for (const key of ['pane_id', 'tab_id']) nullableString(report[owner][key], `${owner}.${key}`);
  if (!['in_progress', 'completed', 'blocked', 'failed', 'milestone', 'registered'].includes(report.status)) fail('status: unsupported value');
  if (!Array.isArray(report.evidence)) fail('evidence: expected array');
  for (const item of report.evidence) {
    mapping(item, 'evidence item');
    string(item.command, 'evidence.command');
    if (typeof item.result !== 'string') fail('evidence.result: expected string');
    if (!Number.isInteger(item.exit_code)) fail('evidence.exit_code: expected integer');
  }
  for (const key of ['base', 'head', 'branch', 'worktree']) nullableString(report.git[key], `git.${key}`);
  if (report.git.pr !== null && typeof report.git.pr !== 'string' && !Number.isInteger(report.git.pr)) fail('git.pr: expected string, integer or null');
  for (const key of ['files', 'unresolved_effects']) {
    if (!Array.isArray(report[key])) fail(`${key}: expected array`);
    for (const item of report[key]) string(item, `${key} item`);
  }
  if (!['review', 'merge', 'unblock_decision', 'integrate', 'none'].includes(report.requested_action)) fail('requested_action: unsupported value');
  if (report.candidate_snapshot !== undefined) {
    mapping(report.candidate_snapshot, 'candidate_snapshot');
    const snapshot = report.candidate_snapshot;
    string(snapshot.path, 'candidate_snapshot.path');
    if (!path.isAbsolute(snapshot.path)) fail('candidate_snapshot.path: expected absolute path');
    nullableString(snapshot.base, 'candidate_snapshot.base');
    if (typeof snapshot.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(snapshot.sha256)) fail('candidate_snapshot.sha256: expected SHA256');
    if (hash(fs.readFileSync(snapshot.path)) !== snapshot.sha256) fail('candidate_snapshot: digest mismatch');
  }
  const sha256 = hash(bytes);
  // Atomic no-clobber publication. link fails on collision or another filesystem.
  fs.linkSync(partial, destination);
  if (hash(fs.readFileSync(destination)) !== sha256) fail('Published bytes changed; preserve artifacts and do not notify');
  fs.unlinkSync(partial);
  if (fs.existsSync(partial) || hash(fs.readFileSync(destination)) !== sha256) fail('Publication verification failed; preserve artifacts and do not notify');
  console.log(JSON.stringify({ path: destination, sha256 }));
} catch (error) {
  console.error(JSON.stringify({ error: error.message, code: error.code ?? 'invalid_report' }));
  process.exitCode = 1;
}
