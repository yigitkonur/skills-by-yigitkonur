import { realpath, access } from 'node:fs/promises';
import path from 'node:path';
import { containedPath } from './store.mjs';
import { CliError } from './contracts.mjs';

export async function resolveInput(campaign, project, input) {
  if (typeof input === 'string') return containedPath(campaign, input);
  const relative = input?.path;
  if (input?.base !== 'project' || typeof relative !== 'string' || !relative || path.isAbsolute(relative) || relative.includes('\\') || (relative !== '.' && relative.split('/').some(part => !part || part === '..' || part === '.'))) throw new CliError('UNSAFE_INPUT', 'Use {base: project, path: a clean project-relative path}; project root is ".".');
  const root = await realpath(project);
  const lexical = path.resolve(root, relative);
  let actual;
  try { actual = await realpath(lexical); } catch (error) { if (error.code === 'ENOENT') throw new CliError('MISSING_INPUT', `Project input is missing: ${relative}`); throw error; }
  if (actual !== root && !actual.startsWith(`${root}${path.sep}`)) throw new CliError('UNSAFE_INPUT', 'Project input resolves outside the campaign project.');
  await access(actual);
  return actual;
}

export const inputLabel = input => typeof input === 'string' ? input : `project:${input.path}`;
