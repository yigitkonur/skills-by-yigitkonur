#!/usr/bin/env node
/**
 * chatgpt-research-runner.mjs
 * 
 * Reusable CLI utility to dispatch structured research queries to native macOS ChatGPT desktop app
 * locally or over SSH bridge (ssh macbook).
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const args = process.argv.slice(2);

function printHelp() {
  console.log(`
ChatGPT macOS Research Runner
=============================
Usage:
  node chatgpt-research-runner.mjs --prompt "Your research query"
  node chatgpt-research-runner.mjs --targets <targets.json> [options]
  node chatgpt-research-runner.mjs --check-bridge

Options:
  --ssh-host=<host>        SSH host alias (default: 'macbook')
  --batch-size=<n>         Number of queries per burst (default: 10)
  --wait-minutes=<n>       Minutes to wait between bursts (default: 5)
  --state-file=<path>      JSON file to track progress (default: .chatgpt_state.json)
  --one-batch              Run only one burst and stop
  --dry-run                Print generated AppleScript & prompts without executing
  --reset                  Reset progress state file
  --help                   Show this help message
`);
}

if (args.length === 0 || args.includes('--help')) {
  printHelp();
  process.exit(0);
}

// Parse options
const dryRun = args.includes('--dry-run');
const checkBridge = args.includes('--check-bridge');
const oneBatch = args.includes('--one-batch');
const resetState = args.includes('--reset');
const sshHost = args.find(a => a.startsWith('--ssh-host='))?.split('=')[1] || process.env.CHATGPT_SSH_HOST || 'macbook';
const batchSize = parseInt(args.find(a => a.startsWith('--batch-size='))?.split('=')[1] || '10', 10);
const waitMinutes = parseFloat(args.find(a => a.startsWith('--wait-minutes='))?.split('=')[1] || '5');
const stateFile = path.resolve(args.find(a => a.startsWith('--state-file='))?.split('=')[1] || '.chatgpt_state.json');

// Check environment
const isLocalMac = process.platform === 'darwin';

function checkHostConnection() {
  if (isLocalMac) {
    try {
      execSync('which osascript && pgrep -l -i chatgpt', { stdio: 'ignore' });
      return { ok: true, mode: 'local' };
    } catch {
      return { ok: false, error: 'Local macOS: osascript found, but ChatGPT app is not running.' };
    }
  }

  try {
    const out = execSync(`ssh -o ConnectTimeout=3 -o BatchMode=yes ${sshHost} "which osascript && pgrep -l -i chatgpt"`, { encoding: 'utf8' });
    return { ok: true, mode: 'ssh', host: sshHost, details: out.trim() };
  } catch (err) {
    return { ok: false, error: `SSH host '${sshHost}' unreachable or ChatGPT not running.` };
  }
}

if (checkBridge) {
  console.log(`Checking ChatGPT bridge connection...`);
  const res = checkHostConnection();
  if (res.ok) {
    console.log(`✅ Bridge operational! Mode: ${res.mode} ${res.host ? `(${res.host})` : ''}`);
    process.exit(0);
  } else {
    console.error(`❌ Bridge check failed: ${res.error}`);
    process.exit(1);
  }
}

function dispatchPrompt(promptText) {
  // Format with browser plugin hook if not present
  let formatted = promptText;
  if (!formatted.includes('[@Browser](plugin://browser@openai-bundled)')) {
    formatted = `[@Browser](plugin://browser@openai-bundled)\n\n${formatted}`;
  }

  if (dryRun) {
    console.log(`\n--- [DRY-RUN] PROMPT DISPATCH ---`);
    console.log(formatted);
    console.log(`---------------------------------\n`);
    return;
  }

  const b64 = Buffer.from(formatted, 'utf8').toString('base64');
  const appleScriptBlock = `tell application "ChatGPT" to activate
delay 0.4
tell application "System Events" to tell process "ChatGPT"
  keystroke "n" using command down
  delay 0.5
  keystroke "v" using command down
  delay 0.3
  key code 36
end tell`;

  if (isLocalMac) {
    execSync(`echo "${b64}" | base64 -d | pbcopy && osascript -e '${appleScriptBlock}'`, { stdio: 'ignore' });
  } else {
    const remoteCmd = `echo "${b64}" | base64 -d | pbcopy && osascript << "APPLESCRIPT"
${appleScriptBlock}
APPLESCRIPT`;
    execSync(`ssh ${sshHost} \x27${remoteCmd}\x27`, { stdio: 'ignore' });
  }
}

// Single prompt execution mode
const promptArg = args.find(a => a.startsWith('--prompt='));
const promptFlagIdx = args.indexOf('--prompt');
let singleQuery = null;
if (promptArg) {
  singleQuery = promptArg.split('=').slice(1).join('=');
} else if (promptFlagIdx !== -1 && args[promptFlagIdx + 1] && !args[promptFlagIdx + 1].startsWith('--')) {
  singleQuery = args[promptFlagIdx + 1];
}

if (singleQuery) {
  console.log(`🚀 Dispatching single research prompt to ChatGPT...`);
  dispatchPrompt(singleQuery);
  if (!dryRun) console.log(`✅ Prompt successfully delivered to ChatGPT app.`);
  process.exit(0);
}

// Batch mode with targets JSON file
const targetsArg = args.find(a => a.startsWith('--targets='))?.split('=')[1] || (args.indexOf('--targets') !== -1 ? args[args.indexOf('--targets') + 1] : null);

if (!targetsArg) {
  console.error(`❌ Error: Specify either --prompt "..." or --targets <file.json>`);
  printHelp();
  process.exit(1);
}

const targetsPath = path.resolve(targetsArg);
if (!fs.existsSync(targetsPath)) {
  console.error(`❌ Targets file not found: ${targetsPath}`);
  process.exit(1);
}

const rawTargets = JSON.parse(fs.readFileSync(targetsPath, 'utf8'));
const targets = Array.isArray(rawTargets) ? rawTargets : rawTargets.items || [];

// Load state
let state = { submitted: [] };
if (!resetState && fs.existsSync(stateFile)) {
  try {
    state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
  } catch {}
}

const submittedSet = new Set(state.submitted || []);
const remaining = targets.filter(t => !submittedSet.has(t.id || t.slug || t.name));

console.log(`======================================================`);
console.log(`🎯 ChatGPT Batch Research Runner`);
console.log(`Total Targets:      ${targets.length}`);
console.log(`Already Completed:  ${submittedSet.size}`);
console.log(`Remaining:          ${remaining.length}`);
console.log(`Batch Size:         ${batchSize}`);
console.log(`Cooldown Interval:  ${waitMinutes} min`);
console.log(`======================================================\n`);

if (remaining.length === 0) {
  console.log(`🎉 All targets have already been submitted! Use --reset to re-run.`);
  process.exit(0);
}

async function runBatch() {
  let index = 0;
  let batchNum = 1;

  while (index < remaining.length) {
    const chunk = remaining.slice(index, index + batchSize);
    console.log(`\n🚀 Batch ${batchNum} starting: ${chunk.length} items dispatching...`);

    for (let i = 0; i < chunk.length; i++) {
      const item = chunk[i];
      const id = item.id || item.slug || item.name;
      const prompt = item.prompt || item.query || JSON.stringify(item, null, 2);

      process.stdout.write(`  [${i + 1}/${chunk.length}] ${id}... `);
      try {
        dispatchPrompt(prompt);
        state.submitted.push(id);
        fs.writeFileSync(stateFile, JSON.stringify(state, null, 2), 'utf8');
        console.log(`✅ Sent`);
      } catch (err) {
        console.log(`❌ Error: ${err.message}`);
      }

      execSync('sleep 0.2');
    }

    index += chunk.length;
    const left = remaining.length - index;
    console.log(`✅ Batch ${batchNum} completed! (Total sent: ${state.submitted.length}/${targets.length})`);

    if (left === 0 || oneBatch) {
      if (oneBatch && left > 0) {
        console.log(`ℹ️  Stopped due to --one-batch flag. ${left} items remaining for next run.`);
      } else {
        console.log(`🎉 All items completed!`);
      }
      break;
    }

    console.log(`\n⏳ Cooldown: waiting ${waitMinutes} minutes (300s) for ChatGPT browser processing...`);
    const totalSecs = Math.round(waitMinutes * 60);
    const interval = 30;
    let elapsed = 0;

    while (elapsed < totalSecs) {
      const step = Math.min(interval, totalSecs - elapsed);
      execSync(`sleep ${step}`);
      elapsed += step;
      const leftSecs = totalSecs - elapsed;
      if (leftSecs > 0) {
        console.log(`   ⏱️  Cooldown remaining: ${Math.ceil(leftSecs / 60)}m (${leftSecs}s)`);
      }
    }

    batchNum++;
  }
}

runBatch().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
