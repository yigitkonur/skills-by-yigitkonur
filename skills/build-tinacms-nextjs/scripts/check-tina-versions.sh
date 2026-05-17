#!/usr/bin/env sh
set -eu

ROOT=${1:-.}

if [ ! -d "$ROOT" ]; then
  echo "error: project root not found: $ROOT" >&2
  exit 1
fi

cd "$ROOT"

if [ ! -f package.json ]; then
  echo "error: package.json not found in $(pwd)" >&2
  exit 1
fi

node <<'NODE'
const fs = require('fs')
const path = require('path')

const cwd = process.cwd()
const pkg = JSON.parse(fs.readFileSync(path.join(cwd, 'package.json'), 'utf8'))
const sections = ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']
const deps = Object.assign({}, ...sections.map((section) => pkg[section] || {}))
const packages = ['tinacms', '@tinacms/cli', 'next', 'react', 'react-dom']
const lockfiles = [
  'pnpm-lock.yaml',
  'package-lock.json',
  'yarn.lock',
  'bun.lock',
  'bun.lockb',
].filter((file) => fs.existsSync(path.join(cwd, file)))

function existsAny(paths) {
  return paths.some((candidate) => fs.existsSync(path.join(cwd, candidate)))
}

function script(name) {
  return pkg.scripts && pkg.scripts[name] ? pkg.scripts[name] : null
}

console.log('TinaCMS version and project-shape check')
console.log(`root: ${cwd}`)
console.log('')

console.log('Package manager')
console.log(`- packageManager field: ${pkg.packageManager || '(not set)'}`)
console.log(`- lockfiles: ${lockfiles.length ? lockfiles.join(', ') : '(none found)'}`)
if (lockfiles.length > 1) {
  console.log('- warning: multiple lockfiles detected; confirm the project uses one package manager')
}
console.log('')

console.log('Dependencies from package.json')
for (const name of packages) {
  console.log(`- ${name}: ${deps[name] || '(not declared)'}`)
}
console.log('')

console.log('Scripts')
for (const name of ['dev', 'build', 'start']) {
  console.log(`- ${name}: ${script(name) || '(missing)'}`)
}
if (script('build') && !script('build').includes('tinacms build')) {
  console.log('- warning: build script does not visibly run tinacms build before next build')
}
if (script('dev') && !script('dev').includes('tinacms dev')) {
  console.log('- warning: dev script does not visibly wrap next dev with tinacms dev')
}
console.log('')

console.log('Router shape')
console.log(`- App Router: ${existsAny(['app', 'src/app']) ? 'yes' : 'no'}`)
console.log(`- Pages Router: ${existsAny(['pages', 'src/pages']) ? 'yes' : 'no'}`)
console.log(`- tina/config: ${existsAny(['tina/config.ts', 'tina/config.tsx', 'tina/config.js', 'tina/config.jsx']) ? 'yes' : 'no'}`)
console.log(`- tina lock: ${existsAny(['tina/tina-lock.json']) ? 'yes' : 'no'}`)
console.log('')

console.log('Next reference routes')
console.log('- references/setup/01-prerequisites.md')
console.log('- references/setup/04-package-scripts.md')
console.log('- references/rendering/01-app-router-pattern.md')
console.log('- references/troubleshooting/02-build-and-types.md')
NODE
