import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { CliError } from './contracts.mjs';
const execute = promisify(execFile);
const deliveryRoles = new Set(['ticket-writer', 'implementer', 'integrator']);
export const isDeliveryRole = role => deliveryRoles.has(role);

export function githubRepository(value) {
  const match = String(value).trim().match(/^(?:git@github\.com:|(?:https?|ssh):\/\/(?:git@)?github\.com\/)([\w.-]+\/[\w.-]+?)(?:\.git)?\/?$/i);
  return match ? match[1].toLowerCase() : null;
}

export async function discoverRepository(project, remote = 'origin') {
  if (!/^[A-Za-z0-9_.-]+$/.test(remote) || remote.startsWith('-')) throw new CliError('GITHUB_REMOTE_REQUIRED', 'Select a named remote of the tested project.');
  try {
    const env = { ...process.env, GIT_OPTIONAL_LOCKS: '0', GIT_NO_REPLACE_OBJECTS: '1' };
    for (const name of Object.keys(env)) if (/^GIT_CONFIG(?:_|$)/.test(name) || ['GIT_DIR', 'GIT_COMMON_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE'].includes(name)) delete env[name];
    const { stdout } = await execute('git', ['-C', project, 'remote', 'get-url', remote], { env, timeout: 3000 });
    const repository = githubRepository(stdout);
    return repository ? { remote, repository } : null;
  } catch { return null; }
}

export async function verifyRepository(config) {
  const binding = config.github_repository;
  if (!binding) throw new CliError('GITHUB_REMOTE_REQUIRED', 'Campaign delivery requires the tested project GitHub remote. Initialize with its origin or --github-remote; never use the skill installation repository.', 4);
  const current = await discoverRepository(config.project, binding.remote);
  if (current?.repository !== binding.repository) throw new CliError('GITHUB_REMOTE_DRIFT', 'The tested project selected GitHub remote no longer matches this campaign. Restore that remote or start a campaign for the new repository; unrelated local work may continue.', 4);
  return binding;
}

export function verifyDeliveryUrls(binding, record) {
  for (const field of ['issue_url', 'pr_url']) if (record[field]) {
    const expectedKind = field === 'issue_url' ? 'issues' : 'pull';
    const match = record[field].match(/^https:\/\/github\.com\/([\w.-]+\/[\w.-]+)\/(issues|pull)\/\d+\/?$/i);
    if (!match || match[1].toLowerCase() !== binding.repository || match[2] !== expectedKind) throw new CliError('GITHUB_REPOSITORY_MISMATCH', 'Issue and pull request references must belong to the campaign tested-project GitHub repository.');
  }
}
