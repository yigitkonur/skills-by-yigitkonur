export { loadDependencies } from './dependencies.mjs';
import { readFileSync } from 'node:fs';
import { getDependencies } from './dependencies.mjs';

const schema = JSON.parse(readFileSync(new URL('../../schemas/records.schema.json', import.meta.url), 'utf8'));
let validate;

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
  if (!validate) validate = new (getDependencies().Ajv)({ allErrors: true, strict: true }).compile(schema);
  if (!validate(record)) {
    const meaningful = validate.errors.filter(error => !error.schemaPath.includes('/oneOf/') || error.keyword === 'additionalProperties');
    throw new CliError('INVALID_RECORD', `Invalid ${record?.kind || 'unknown'} record.`, 3, (meaningful.length ? meaningful : validate.errors).map(error => `${error.instancePath || '/'} ${error.message}`));
  }
  return record;
}
