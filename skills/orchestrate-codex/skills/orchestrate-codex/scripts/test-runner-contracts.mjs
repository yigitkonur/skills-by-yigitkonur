#!/usr/bin/env node
// test-runner-contracts.mjs — dispatcher/runner contract tests.
//
// These tests run every mode through a temp dry-run path. They catch the
// concrete contract failures that Monitor-only tests cannot see: flag parsing,
// manifest shape, rendered prompt names, terminal statuses, and rescue
// redispatch selection.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DISPATCHER = path.join(SCRIPT_DIR, "orchestrate-codex.mjs");
const MANIFEST_UPDATE = path.join(SCRIPT_DIR, "manifest-update.sh");

let passCount = 0;
let failCount = 0;

function pass(name) {
  passCount += 1;
  process.stdout.write(`  PASS  ${name}\n`);
}

function fail(name, detail) {
  failCount += 1;
  process.stdout.write(`  FAIL  ${name}\n`);
  if (detail) process.stdout.write(`        ${detail}\n`);
}

function expect(cond, name, detail = "") {
  if (cond) pass(name);
  else fail(name, detail);
}

function tmpdir(name) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `orchestrate-contract-${name}-`));
}

function runNode(args, cwd, extraEnv = {}) {
  const r = spawnSync(process.execPath, [DISPATCHER, ...args], {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      ORCHESTRATE_SKIP_PREFLIGHT: "1",
      ORCHESTRATE_RUNNER_FOREGROUND: "1",
      ...extraEnv,
    },
    maxBuffer: 16 * 1024 * 1024,
  });
  let json = null;
  try {
    json = JSON.parse(r.stdout);
  } catch (e) {
    return { ...r, json: null, parseError: e.message };
  }
  return { ...r, json };
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text, "utf8");
}

function gitInit(dir) {
  spawnSync("git", ["init", "-q", "-b", "main"], { cwd: dir });
  spawnSync("git", ["config", "user.email", "test@example.com"], { cwd: dir });
  spawnSync("git", ["config", "user.name", "Test"], { cwd: dir });
}

function scenarioHelpAndBadArgs() {
  process.stdout.write("\n[1] dispatcher envelopes\n");
  const cwd = tmpdir("help");
  const help = runNode(["help"], cwd);
  expect(help.status === 0 && help.json?.ok === true, "help returns ok envelope");
  expect(String(help.json?.result?.usage || "").includes("exec"), "help lists modes");

  const bad = runNode(["single"], cwd);
  expect(bad.status !== 0 && bad.json?.ok === false, "bad args return error envelope");
  expect(bad.json?.error?.code === "missing_required_arg", "bad arg code is stable");
}

function scenarioExec() {
  process.stdout.write("\n[2] exec dry-run contract\n");
  const cwd = tmpdir("exec");
  write(path.join(cwd, "tasks.json"), JSON.stringify([
    { id: "task-one", branch: "feat/task-one", base_branch: "main", prompt: "touch proof.txt" },
  ]));
  const out = runNode(["exec", "--cwd", cwd, "--tasks", "tasks.json", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "exec dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "exec runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  const entry = manifest.entries[0];
  expect(entry.id === "task-one" && entry.status === "done", "exec entry reaches done in dry-run");
  expect(entry.branch === "feat/task-one" && entry.base_branch === "main", "exec seeds branch fields");
  expect(Boolean(entry.prompt_path && entry.log_path && entry.answer_path), "exec seeds prompt/log/answer paths");
}

function scenarioBatch() {
  process.stdout.write("\n[3] batch render + dry-run contract\n");
  const cwd = tmpdir("batch");
  write(path.join(cwd, "inputs.txt"), "Alpha\nBeta\n");
  write(path.join(cwd, "template.md"), "Research XXXXXXXXXXXXX\n");
  const out = runNode(["batch", "--cwd", cwd, "--inputs", "inputs.txt", "--template", "template.md", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "batch dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "batch runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  expect(manifest.entries.map((e) => e.id).join(",") === "alpha,beta", "batch ids match rendered prompt basenames");
  expect(manifest.entries.every((e) => e.status === "done"), "batch entries reach done in dry-run");
  expect(fs.existsSync(out.json.result.audit_report), "batch writes audit report");
}

function scenarioSingle() {
  process.stdout.write("\n[4] single dry-run contract\n");
  const cwd = tmpdir("single");
  const out = runNode(["single", "--cwd", cwd, "--prompt", "Summarize this", "--reuse-worktree", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "single dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "single runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  const entry = manifest.entries[0];
  expect(entry.id === "single" && entry.status === "done", "single entry id and status are deterministic");
  expect(entry.jsonl_path === out.json.result.jsonl_path, "single runner honors jsonl path");
  expect(fs.existsSync(entry.answer_path), "single writes answer file in dry-run");
}

function scenarioReview() {
  process.stdout.write("\n[5] review loop fixture\n");
  const cwd = tmpdir("review");
  gitInit(cwd);
  const out = runNode(["review", "--cwd", cwd, "--branches", "feat/auth", "feat/billing", "--base", "main", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "review dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "review runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  expect(manifest.entries.length === 2, "review parses --branches plus branch positionals");
  expect(manifest.entries.every((e) => e.status === "converged"), "review entries reach terminal converged state");
  expect(manifest.entries.every((e) => e.last_findings_path), "review records findings artifacts");
}

function scenarioRescue() {
  process.stdout.write("\n[6] rescue classification + redispatch\n");
  const cwd = tmpdir("rescue");
  write(path.join(cwd, "inputs.txt"), "Alpha\nBeta\n");
  write(path.join(cwd, "template.md"), "Research XXXXXXXXXXXXX\n");
  const first = runNode(["batch", "--cwd", cwd, "--inputs", "inputs.txt", "--template", "template.md", "--dry-run"], cwd);
  const manifestPath = first.json.result.manifest_path;
  const update = spawnSync("bash", [MANIFEST_UPDATE, "entry", manifestPath, "alpha", "status=failed", "last_error=test"], {
    cwd,
    encoding: "utf8",
  });
  expect(update.status === 0, "fixture can mark alpha failed");

  const classify = runNode(["rescue", "--cwd", cwd, "--manifest", manifestPath], cwd);
  expect(classify.status === 0 && classify.json?.ok === true, "rescue classification returns ok");
  expect(classify.json.result.classification.redispatch_options.failed_only.includes("alpha"), "rescue classifies failed entry");

  const redo = runNode(["rescue", "--cwd", cwd, "--manifest", manifestPath, "--redo", "failed", "--dry-run"], cwd);
  expect(redo.status === 0 && redo.json?.ok === true, "rescue redispatch returns ok");
  expect(redo.json.result.redispatch.selected_ids.includes("alpha"), "rescue redispatch selects failed entry");
  const manifest = readJson(manifestPath);
  expect(manifest.entries.find((e) => e.id === "alpha")?.status === "done", "redispatched entry reaches done");
}

scenarioHelpAndBadArgs();
scenarioExec();
scenarioBatch();
scenarioSingle();
scenarioReview();
scenarioRescue();

process.stdout.write(`\nPASS: ${passCount}  FAIL: ${failCount}\n`);
process.exit(failCount === 0 ? 0 : 1);
