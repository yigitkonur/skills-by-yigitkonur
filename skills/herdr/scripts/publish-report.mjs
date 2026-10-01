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
const commit = (value, key) => {
  if (value !== null && (typeof value !== 'string' || !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(value))) fail(key + ': expected full Git object ID or null');
};
let stageDirectory;


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
  const descriptor = fs.openSync(partial, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
  let identity, bytes;
  try {
    identity = fs.fstatSync(descriptor);
    if (!identity.isFile()) fail('Partial must be a regular file, not a symlink');
    bytes = fs.readFileSync(descriptor);
  } finally { fs.closeSync(descriptor); }
  const sameSource = () => {
    const current = fs.lstatSync(partial);
    return current.isFile() && current.dev === identity.dev && current.ino === identity.ino && hash(fs.readFileSync(partial)) === hash(bytes);
  };
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
  for (const key of ['base', 'head']) commit(report.git[key], `git.${key}`);
  for (const key of ['branch', 'worktree']) nullableString(report.git[key], `git.${key}`);
  if (report.git.pr !== null && typeof report.git.pr !== 'string' && !Number.isInteger(report.git.pr)) fail('git.pr: expected string, integer or null');
  if (typeof report.git.pr === 'string') string(report.git.pr, 'git.pr');
  for (const key of ['files', 'unresolved_effects']) {
    if (!Array.isArray(report[key])) fail(`${key}: expected array`);
    for (const item of report[key]) string(item, `${key} item`);
  }
  for (const file of report.files) {
    if (path.isAbsolute(file) || path.win32.isAbsolute(file) || file.split(/[\\/]/).includes('..') || file.includes('\0')) fail('files: expected checkout-relative path without traversal');
  }
  if (!['review', 'merge', 'unblock_decision', 'integrate', 'none'].includes(report.requested_action)) fail('requested_action: unsupported value');
  if (report.candidate_snapshot !== undefined) {
    mapping(report.candidate_snapshot, 'candidate_snapshot');
    const snapshot = report.candidate_snapshot;
    string(snapshot.path, 'candidate_snapshot.path');
    if (!path.isAbsolute(snapshot.path)) fail('candidate_snapshot.path: expected absolute path');
    commit(snapshot.base, 'candidate_snapshot.base');
    if (typeof snapshot.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(snapshot.sha256)) fail('candidate_snapshot.sha256: expected SHA256');
    if (hash(fs.readFileSync(snapshot.path)) !== snapshot.sha256) fail('candidate_snapshot: digest mismatch');
  }
  const sha256 = hash(bytes);
  // Link our private byte snapshot, never a producer pathname that can be swapped.
  stageDirectory = fs.mkdtempSync(path.join(path.dirname(partial), '.herdr-publish-'));
  const stable = path.join(stageDirectory, 'report');
  fs.writeFileSync(stable, bytes, {flag: 'wx', mode: 0o600});
  fs.linkSync(stable, destination);
  if (hash(fs.readFileSync(destination)) !== sha256) fail('Published bytes changed; preserve artifacts and do not notify');
  if (report.candidate_snapshot && hash(fs.readFileSync(report.candidate_snapshot.path)) !== report.candidate_snapshot.sha256) fail('candidate_snapshot: changed during publication; do not notify');
  if (!sameSource()) fail('Partial changed during publication; preserve artifacts and do not notify');
  fs.unlinkSync(partial);
  if (fs.existsSync(partial) || hash(fs.readFileSync(destination)) !== sha256) fail('Publication verification failed; preserve artifacts and do not notify');
  console.log(JSON.stringify({ path: destination, sha256 }));
} catch (error) {
  console.error(JSON.stringify({ error: error.message, code: error.code ?? 'invalid_report' }));
  process.exitCode = 1;
} finally {
  if (stageDirectory) fs.rmSync(stageDirectory, {recursive: true});
}
