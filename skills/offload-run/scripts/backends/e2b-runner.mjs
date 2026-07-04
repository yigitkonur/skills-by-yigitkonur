// e2b-runner.mjs — fork a warm E2B template, upload the worktree tar, run the command,
// stream stdout/stderr, exit with the remote exit code. Reads config from env (see e2b.sh).
// NOTE: reference implementation — verify against the current `e2b` SDK before relying on it.
import { readFileSync } from 'node:fs'
import Sandbox from 'e2b'

const template = process.env.E2B_TEMPLATE
const tarPath  = process.env.E2B_TAR
const cmd      = process.env.E2B_CMD
const work     = process.env.E2B_WORK || '/work'

const sbx = await Sandbox.create(template)        // forks the warm, deps-baked template
try {
  await sbx.files.write(`${work}/src.tgz`, readFileSync(tarPath))
  await sbx.commands.run(`rm -rf ${work}/x && mkdir -p ${work}/x && tar -xzf ${work}/src.tgz -C ${work}/x`)
  const r = await sbx.commands.run(cmd, {
    cwd: `${work}/x`,
    onStdout: (d) => process.stdout.write(d),
    onStderr: (d) => process.stderr.write(d),
  }).catch((e) => e.result ?? { exitCode: 1 })
  process.exitCode = r.exitCode ?? 0
} finally {
  await sbx.kill()
}
