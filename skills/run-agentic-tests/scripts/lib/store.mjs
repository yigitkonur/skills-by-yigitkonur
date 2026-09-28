import { readFile, mkdir, readdir, open, rename, unlink, link, rm } from 'node:fs/promises';
import { realpathSync, lstatSync, existsSync } from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { getDependencies } from './dependencies.mjs';
import { CliError, validateRecord } from './contracts.mjs';

export const stableStringify = value => JSON.stringify(value, (_key, item) => item && typeof item === 'object' && !Array.isArray(item)
  ? Object.fromEntries(Object.entries(item).sort(([a], [b]) => a.localeCompare(b))) : item);

export function containedPath(campaign, relativePath) {
  if (typeof relativePath !== 'string' || !relativePath || path.isAbsolute(relativePath) || relativePath.includes('\\') || relativePath.split('/').some(part => part === '..' || part === '.' || !part)) {
    throw new CliError('UNSAFE_PATH', 'Use a clean campaign-relative path.');
  }
  const base = realpathSync(campaign);
  const target = path.resolve(base, relativePath);
  if (!target.startsWith(`${base}${path.sep}`)) throw new CliError('UNSAFE_PATH', 'Path escapes the campaign.');
  let current = base;
  for (const part of relativePath.split('/')) {
    current = path.join(current, part);
    try {
      if (lstatSync(current).isSymbolicLink()) throw new CliError('UNSAFE_PATH', 'Symlinks are forbidden in campaign paths.');
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  return target;
}

export async function readYaml(file) {
  const { YAML } = getDependencies();
  const source = await readFile(file, 'utf8');
  try {
    const documents = YAML.parseAllDocuments(source, { strict: true, uniqueKeys: true, version: '1.2', schema: 'core' });
    if (documents.length !== 1 || documents[0].errors.length || documents[0].warnings.length) {
      throw new Error('Expected one valid, unambiguous YAML document.');
    }
    YAML.visit(documents[0], (_key, node) => {
      if (YAML.isPair(node) && (!YAML.isScalar(node.key) || typeof node.key.value !== 'string')) {
        throw new Error('Mapping keys must be strings; implicit key coercion is forbidden.');
      }
      if (YAML.isAlias(node) || node?.anchor || node?.tag || (YAML.isPair(node) && node.key?.value === '<<')) {
        throw new Error('Anchors, aliases, tags, and merge keys are forbidden.');
      }
      if (YAML.isScalar(node) && typeof node.value === 'number' && !Number.isFinite(node.value)) {
        throw new Error('Non-finite numbers are forbidden.');
      }
    });
    const data = documents[0].toJS({ maxAliasCount: 0, mapAsMap: false });
    if (!data || Array.isArray(data) || typeof data !== 'object') throw new Error('Document root must be a mapping.');
    return data;
  } catch (error) { throw new CliError('INVALID_YAML', `Invalid YAML in ${file}: ${error.message}`); }
}

export async function readCampaign(campaign) {
  const record = await readYaml(containedPath(campaign, '00-campaign.record.yaml'));
  validateRecord(record);
  if (record.kind !== 'campaign') throw new CliError('INVALID_RECORD', '00-campaign.record.yaml must be a campaign record.');
  return record;
}

export async function readRecords(campaign) {
  const records = [];
  const walk = async relative => {
    const directory = relative ? containedPath(campaign, relative) : realpathSync(campaign);
    for (const entry of (await readdir(directory, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
      if (entry.name.startsWith('.') || ['report', 'draft', 'evidences', 'logs', 'node_modules'].includes(entry.name)) continue;
      const rel = relative ? `${relative}/${entry.name}` : entry.name;
      if (entry.isSymbolicLink()) { if (entry.name.endsWith('.record.yaml')) throw new CliError('UNSAFE_PATH', 'Canonical records cannot be symlinks.'); continue; }
      if (entry.isDirectory()) await walk(rel);
      else if (entry.isFile() && entry.name.endsWith('.record.yaml')) {
        const record = await readYaml(containedPath(campaign, rel));
        validateRecord(record);
        records.push({ record, path: rel });
      }
    }
  };
  await walk('');
  const seen = new Set();
  for (const { record } of records) {
    if (seen.has(record.record_id)) throw new CliError('DUPLICATE_RECORD', `Duplicate canonical record ID ${record.record_id}.`);
    seen.add(record.record_id);
  }
  return records;
}

export async function writeRecord(campaign, relativePath, record, { immutable = true } = {}) {
  validateRecord(record);
  if (!relativePath.endsWith('.record.yaml')) throw new CliError('UNSAFE_PATH', 'Canonical records require the .record.yaml suffix.');
  const destination = containedPath(campaign, relativePath);
  if (existsSync(destination)) {
    const previous = await readYaml(destination);
    if (stableStringify(previous) === stableStringify(record)) return previous;
    if (immutable) throw new CliError('RECORD_CONFLICT', `Record already exists with different content: ${relativePath}`, 4);
    if (previous.record_id !== record.record_id || previous.kind !== record.kind || previous.campaign_id !== record.campaign_id) throw new CliError('RECORD_CONFLICT', 'A mutable record cannot change identity.', 4);
    if (record.kind === 'environment') {
      for (const key of ['target_id', 'runtime_type', 'source', 'command', 'readiness']) {
        if (stableStringify(previous[key]) !== stableStringify(record[key])) throw new CliError('RECORD_CONFLICT', `Environment ${key} is frozen; allocate a new target.`, 4);
      }
    } else if (!['campaign', 'task', 'finding'].includes(record.kind)) {
      throw new CliError('RECORD_CONFLICT', `${record.kind} records are immutable.`, 4);
    }
  }
  await mkdir(path.dirname(destination), { recursive: true });
  containedPath(campaign, relativePath);
  const temporary = `${destination}.${randomUUID()}.tmp`;
  const handle = await open(temporary, 'wx', 0o600);
  try {
    await handle.writeFile(getDependencies().YAML.stringify(record, { aliasDuplicateObjects: false }));
    await handle.sync();
  } finally { await handle.close(); }
  try {
    if (immutable) {
      try { await link(temporary, destination); } catch (error) {
        if (error.code !== 'EEXIST') throw error;
        const previous = await readYaml(destination);
        if (stableStringify(previous) !== stableStringify(record)) throw new CliError('RECORD_CONFLICT', `Conflicting concurrent record: ${relativePath}`, 4);
      }
    } else await rename(temporary, destination);
  } finally { await rm(temporary, { force: true }); }
  return record;
}

export async function withController(campaign, operation) {
  const lockPath = containedPath(campaign, '.controller.lock');
  let lock;
  try { lock = await open(lockPath, 'wx', 0o600); } catch (error) {
    if (error.code === 'EEXIST') throw new CliError('CONTROLLER_BUSY', 'Another controller holds the campaign lock. Inspect .controller.lock; remove only after confirming the owner process has stopped.', 4);
    throw error;
  }
  try {
    await lock.writeFile(JSON.stringify({ pid: process.pid, created_at: new Date().toISOString() }));
    return await operation();
  } finally { await lock.close(); await unlink(lockPath); }
}
