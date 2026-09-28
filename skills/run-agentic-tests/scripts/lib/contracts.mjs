export { loadDependencies } from './dependencies.mjs';
import { readFileSync } from 'node:fs';
import { getDependencies } from './dependencies.mjs';

const schema = JSON.parse(readFileSync(new URL('../../schemas/records.schema.json', import.meta.url), 'utf8'));
const runtimeSchema = JSON.parse(readFileSync(new URL('../../schemas/runtime.schema.json', import.meta.url), 'utf8'));
Object.assign(schema.definitions, runtimeSchema.definitions);
const validators = new Map();

export class CliError extends Error {
  constructor(code, message, exitCode = 3, details = []) {
    super(message);
    this.name = 'CliError';
    this.code = code;
    this.exitCode = exitCode;
    this.details = details;
  }
}

export function validateRecord(record) {
  return validateShape(record?.kind, record);
}

export function validateShape(kind, record) {
  if (!schema.definitions[kind]) throw new CliError('INVALID_RECORD', `Unknown record kind ${kind}.`);
  if (!validators.has(kind)) validators.set(kind, new (getDependencies().Ajv)({ allErrors: true, strict: true }).compile(schema.definitions[kind]));
  const validate = validators.get(kind);
  if (!validate(record)) {
    const meaningful = validate.errors.filter(error => !error.schemaPath.includes('/oneOf/') || error.keyword === 'additionalProperties');
    throw new CliError('INVALID_RECORD', `Invalid ${record?.kind || 'unknown'} record.`, 3, (meaningful.length ? meaningful : validate.errors).map(error => `${error.instancePath || '/'} ${error.message}`));
  }
  return record;
}
