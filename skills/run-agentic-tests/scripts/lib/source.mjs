import { lstat, readFile, readlink, readdir, realpath } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { CliError, validateRecord } from './contracts.mjs';
import { stableStringify, readCampaign, readYaml } from './store.mjs';

const execute = promisify(execFile);
const sha = value => createHash('sha256').update(value).digest('hex');
const digest = value => sha(stableStringify(value));
const inside = (root, file) => file === root || file.startsWith(`${root}${path.sep}`);
const fail = (code, message, details = []) => { throw new CliError(code, message, 3, details); };
const pathIssue = (field, remedy) => [{ field, remedy }];

async function git(root, ...args) {
  const env = { ...process.env, GIT_OPTIONAL_LOCKS: '0' };
  for (const name of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES']) delete env[name];
  return (await execute('git', ['-C', root, ...args], { env, encoding: 'utf8', timeout: 10000, maxBuffer: 32 * 1024 * 1024 })).stdout;
}

function relative(value, field) {
  if (typeof value !== 'string' || !value || path.isAbsolute(value) || value.includes('\\') || value.includes('\0') ||
      (value !== '.' && value.split('/').some(part => !part || part === '..' || part === '.')) || value.split('/').includes('.git')) {
    fail('INVALID_SOURCE_PROVIDER', 'Source paths must stay inside the declared root and exclude Git internals.', pathIssue(field, 'Use a clean source-relative file or directory path.'));
  }
  return value;
}

async function sourceRoot(environment) {
  const source = environment.source;
  if (!source || typeof source !== 'object') fail('SOURCE_ATTESTATION_REQUIRED', 'Declare an inspectable source provider.');
  const supplied = source.provider || {};
  if (supplied.type && !['git', 'files'].includes(supplied.type)) fail('INVALID_SOURCE_PROVIDER', 'Source provider type must be git or files.');
  const requested = supplied.root || source.worktree || environment.command?.cwd;
  if (typeof requested !== 'string' || !path.isAbsolute(requested)) fail('INVALID_SOURCE_PROVIDER', 'Source root must be absolute.');
  let root;
  let cwd;
  try {
    root = await realpath(requested);
    cwd = await realpath(environment.command.cwd);
    if (!(await lstat(root)).isDirectory()) throw new Error('not-directory');
  } catch { fail('SOURCE_MISSING', 'The actual source root or command working directory is unavailable.', pathIssue('source.provider.root', 'Restore the declared source before inspection or allocate a fresh runtime.')); }
  let type = supplied.type;
  if (!type || type === 'git') {
    try {
      const repository = await realpath((await git(root, 'rev-parse', '--show-toplevel')).trim());
      if (supplied.root && repository !== root) fail('INVALID_SOURCE_PROVIDER', 'A Git provider root must be its repository worktree root.');
      root = repository;
      type = 'git';
    } catch (error) {
      if (error instanceof CliError) throw error;
      fail(type === 'git' ? 'SOURCE_MISSING' : 'SOURCE_ATTESTATION_REQUIRED',
        'Source is not an inspectable Git worktree. Declare a files provider with explicit paths for non-Git projects.',
        pathIssue('source.provider', 'Set type: files, root: an absolute directory, and paths: source-relative files/directories.'));
    }
  }
  if (!inside(root, cwd)) fail('INVALID_SOURCE_PROVIDER', 'command.cwd must be inside its declared source root.');
  const paths = supplied.paths || [];
  const config_files = supplied.config_files || [];
  for (const [field, values] of [['paths', paths], ['config_files', config_files]]) {
    if (!Array.isArray(values) || values.some(item => typeof item !== 'string')) fail('INVALID_SOURCE_PROVIDER', `source.provider.${field} must be an array of paths.`);
    values.forEach(value => relative(value, `source.provider.${field}`));
  }
  if (type === 'files' && !paths.length) fail('SOURCE_ATTESTATION_REQUIRED', 'A files provider requires explicit source paths.');
  return { root, cwd, provider: { type, root, ...(paths.length ? { paths: [...new Set(paths)].sort() } : {}),
    ...(config_files.length ? { config_files: [...new Set(config_files)].sort() } : {}) } };
}

async function manifest(root, paths, excluded, { required = false, gitObjects, gitAlgorithm = 'sha1' } = {}) {
  const entries = new Map();
  const visiting = new Set();
  const rememberBlob = (name, contents, mode) => {
    if (!gitObjects) return;
    const bytes = Buffer.isBuffer(contents) ? contents : Buffer.from(contents);
    gitObjects.set(name, { mode, object: createHash(gitAlgorithm).update(`blob ${bytes.length}\0`).update(bytes).digest('hex') });
  };
  const visit = async (relativePath, explicitlyRequired = false) => {
    const absolute = path.resolve(root, relativePath);
    if (!inside(root, absolute)) fail('INVALID_SOURCE_PROVIDER', 'Source path escapes its root.');
    if (excluded.some(directory => inside(directory, absolute))) {
      if (explicitlyRequired) fail('INVALID_SOURCE_PROVIDER', 'Campaign outputs cannot be declared as product source.');
      return;
    }
    if (relativePath.split('/').includes('.git') || entries.has(relativePath) || visiting.has(relativePath)) return;
    let stat;
    try { stat = await lstat(absolute); }
    catch (error) {
      if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
      if (explicitlyRequired) fail('SOURCE_MISSING', 'A declared source or configuration path is missing.', [{ path: relativePath, remedy: 'Restore the path or declare a fresh target with its actual source.' }]);
      entries.set(relativePath, { path: relativePath, kind: 'missing', mode: 0 });
      return;
    }
    // Do not follow an ancestor symlink silently when Git lists a child path.
    const parent = await realpath(path.dirname(absolute));
    if (absolute !== root && !inside(root, parent)) fail('INVALID_SOURCE_PROVIDER', 'A source path resolves outside its root.', [{ path: relativePath }]);
    const mode = stat.mode & 0o7777;
    if (stat.isSymbolicLink()) {
      const link = await readlink(absolute);
      entries.set(relativePath, { path: relativePath, kind: 'symlink', mode, sha256: sha(link) });
      rememberBlob(relativePath, link, '120000');
      let target;
      try { target = await realpath(absolute); } catch { return; }
      if (!inside(root, target) || excluded.some(directory => inside(directory, target))) fail('INVALID_SOURCE_PROVIDER', 'Source symlinks must resolve inside product source, outside campaign outputs.', [{ path: relativePath }]);
      await visit(path.relative(root, target).split(path.sep).join('/'));
    } else if (stat.isDirectory()) {
      visiting.add(relativePath);
      for (const entry of (await readdir(absolute)).sort()) {
        if (entry === '.git') continue;
        await visit(relativePath === '.' ? entry : `${relativePath}/${entry}`);
      }
      visiting.delete(relativePath);
    } else if (stat.isFile()) {
      const bytes = await readFile(absolute);
      entries.set(relativePath, { path: relativePath, kind: 'file', mode, sha256: sha(bytes) });
      rememberBlob(relativePath, bytes, mode & 0o111 ? '100755' : '100644');
    } else fail('INVALID_SOURCE_PROVIDER', 'Source manifests support regular files, directories and symlinks only.', [{ path: relativePath }]);
  };
  for (const item of paths) await visit(item, required);
  return [...entries.values()].sort((a, b) => a.path.localeCompare(b.path));
}

async function campaignOutputs(campaign) {
  const actual = await realpath(campaign);
  const excluded = [actual];
  const current = await readCampaign(actual);
  const project = await realpath(current.project);
  const container = path.join(project, 'agentic-tests');
  if (path.dirname(actual) !== container) return excluded;
  for (const entry of await readdir(container, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const candidate = path.join(container, entry.name);
    if (candidate === actual) continue;
    try {
      const record = await readYaml(path.join(candidate, '00-campaign.record.yaml'));
      validateRecord(record);
      if (record.kind === 'campaign' && await realpath(record.project) === project &&
          entry.name === `${record.slug}--${record.campaign_id.slice(2)}`) excluded.push(candidate);
    } catch { /* A product directory is not excluded merely because it is under agentic-tests. */ }
  }
  return excluded;
}

export function sourceIdentity(sourceOrEnvironment) {
  const source = sourceOrEnvironment?.source || sourceOrEnvironment;
  return source?.attestation?.version === 1 && /^[a-f0-9]{64}$/.test(source.attestation.source_digest || '')
    ? source.attestation.source_digest : null;
}

export async function attestSource(campaign, environment) {
  try {
    const { root, cwd, provider } = await sourceRoot(environment);
    const excluded = await campaignOutputs(campaign);
    let revision = environment.source.revision;
    let gitHead;
    let gitClean;
    let tree = [];
    let paths = [];
    if (provider.type === 'git') {
      try {
        gitHead = (await git(root, 'rev-parse', '--verify', 'HEAD^{commit}')).trim();
        const requested = (await git(root, 'rev-parse', '--verify', '--end-of-options', `${revision}^{commit}`)).trim();
        if (requested !== gitHead) fail('SOURCE_REVISION_MISMATCH', 'Declared source revision is not the actual worktree HEAD.', pathIssue('source.revision', 'Use the actual checked-out commit or prepare its isolated worktree.'));
        revision = gitHead;
        tree = (await git(root, 'ls-tree', '-r', '-z', 'HEAD')).split('\0').filter(Boolean).map(entry => {
          const [header, ...filename] = entry.split('\t');
          const [mode, type, object] = header.split(' ');
          return { path: filename.join('\t'), mode, type, object };
        });
        paths = [...new Set([
          ...tree.map(entry => entry.path),
          ...(await git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')).split('\0'),
        ].filter(Boolean))].sort();
      } catch (error) {
        if (error instanceof CliError) throw error;
        fail('SOURCE_REVISION_MISMATCH', 'Cannot resolve the declared source revision against the actual Git worktree.', pathIssue('source.revision', 'Declare the current committed HEAD; caller-provided labels are not Git proof.'));
      }
    }
    const gitObjects = new Map();
    const implicit = await manifest(root, paths, excluded, { gitObjects, gitAlgorithm: gitHead?.length === 64 ? 'sha256' : 'sha1' });
    if (gitHead) {
      const productPath = file => !excluded.some(directory => inside(directory, path.resolve(root, file)));
      const committedPaths = new Set(tree.map(entry => entry.path));
      gitClean = tree.filter(entry => productPath(entry.path)).every(entry => {
        const actual = gitObjects.get(entry.path);
        return actual?.object === entry.object && actual.mode === entry.mode;
      }) && paths.filter(productPath).every(file => committedPaths.has(file));
    }
    const declared = await manifest(root, provider.paths || [], excluded, { required: true });
    const files = [...new Map([...implicit, ...declared].map(entry => [entry.path, entry])).values()].sort((a, b) => a.path.localeCompare(b.path));
    if (!files.some(entry => entry.kind === 'file')) fail('SOURCE_MISSING', 'The source manifest contains no actual product files.');
    const config = await manifest(root, provider.config_files || [], excluded, { required: true });
    const source_digest = digest({ type: provider.type, revision, manifest: files });
    const configuration_digest = digest({ command: environment.command, cwd, readiness: environment.readiness,
      runtime_type: environment.runtime_type, session: environment.session || null, config_manifest: config,
      environment: [...new Set(environment.command.env_names || [])].sort().map(name => ({ name,
        sha256: process.env[name] === undefined ? null : sha(process.env[name]) })) });
    const attestation = { version: 1, algorithm: 'sha256', source_digest, configuration_digest,
      ...(gitHead ? { git_head: gitHead, git_clean: gitClean } : {}), manifest: files, config_manifest: config };
    return { ...environment.source, revision, worktree: root, provider,
      fingerprint: `sha256:${digest({ source_digest, configuration_digest })}`, attestation };
  } catch (error) {
    if (error instanceof CliError) throw error;
    fail('SOURCE_INSPECTION_FAILED', 'Source inspection could not read the actual files.', [{ cause: error.code || 'READ_FAILED', remedy: 'Restore source access, then retry inspection.' }]);
  }
}

export async function verifySource(campaign, environment) {
  if (!sourceIdentity(environment) || !environment.source.provider) return { valid: false, code: 'SOURCE_ATTESTATION_REQUIRED',
    message: 'This legacy environment has no actual source attestation. Recover into a fresh target before using it as current proof.' };
  try {
    const actual = await attestSource(campaign, environment);
    if (stableStringify(actual) !== stableStringify(environment.source)) return { valid: false, code: 'SOURCE_CHANGED',
      message: 'Actual source or declared runtime configuration differs from the frozen target.',
      details: [{ remedy: 'Preserve historical proof and prepare a fresh target for the changed source/configuration.' }] };
    return { valid: true };
  } catch (error) {
    return { valid: false, code: error.code === 'SOURCE_REVISION_MISMATCH' ? 'SOURCE_CHANGED' : error.code,
      message: error.message, details: error.details || [] };
  }
}
