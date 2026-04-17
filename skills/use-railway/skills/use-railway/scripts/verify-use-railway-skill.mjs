import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const skillDir = path.resolve(__dirname, "..");

const commandTreePath = path.join(
  skillDir,
  "references/cli/railway-cli-command-tree.json",
);
const skillPath = path.join(skillDir, "SKILL.md");
const coverageDocPath = path.join(
  skillDir,
  "references/cli/command-family-coverage.md",
);

const coverage = [
  {
    command: "add",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Add a service or managed database to the current project.",
  },
  {
    command: "completion",
    primary: "references/cli/local-development-and-shells.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Generate shell-completion scripts for supported shells.",
  },
  {
    command: "connect",
    primary: "references/cli/observability-and-access.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Open a database-native shell for a Railway database service.",
  },
  {
    command: "delete",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Delete a Railway project; distinct from unlinking the local directory.",
  },
  {
    command: "deploy",
    primary: "references/cli/deployments-and-releases.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Provision a Railway template into the project.",
  },
  {
    command: "deployment",
    primary: "references/cli/deployments-and-releases.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "List deployment history or use deployment-scoped release commands.",
  },
  {
    command: "dev",
    primary: "references/cli/local-development-and-shells.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Run Railway-backed services locally and manage local dev state.",
  },
  {
    command: "domain",
    primary: "references/cli/configuration-networking-and-scaling.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Generate Railway domains or attach custom domains to services.",
  },
  {
    command: "docs",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/research/version-drift.md"],
    why: "Open Railway documentation from the CLI.",
  },
  {
    command: "down",
    primary: "references/cli/deployments-and-releases.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Remove the latest deployment without deleting the project.",
  },
  {
    command: "environment",
    primary: "references/cli/configuration-networking-and-scaling.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Create, link, edit, inspect, or delete environments.",
  },
  {
    command: "init",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Create a new Railway project.",
  },
  {
    command: "link",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Associate the current directory with a Railway project context.",
  },
  {
    command: "list",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "List accessible Railway projects.",
  },
  {
    command: "login",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Authenticate the local Railway CLI.",
  },
  {
    command: "logout",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Clear the local Railway CLI session.",
  },
  {
    command: "logs",
    primary: "references/cli/observability-and-access.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Inspect build, deployment, or runtime logs with bounded fetches.",
  },
  {
    command: "open",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Open the current Railway project in the dashboard.",
  },
  {
    command: "project",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Use project-scoped list, link, and delete subcommands.",
  },
  {
    command: "run",
    primary: "references/cli/local-development-and-shells.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Run a single local command with Railway variables injected.",
  },
  {
    command: "service",
    primary: "references/cli/common-workflows.md",
    secondary: [
      "references/cli/context-projects-and-linking.md",
      "references/cli/observability-and-access.md",
      "references/cli/deployments-and-releases.md",
      "references/cli/configuration-networking-and-scaling.md",
      "references/cli/railway-cli-command-reference.md",
    ],
    why: "Split by subcommand: link, status, logs, redeploy, restart, and scale route to different guides.",
  },
  {
    command: "shell",
    primary: "references/cli/local-development-and-shells.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Open a local subshell with Railway variables available.",
  },
  {
    command: "ssh",
    primary: "references/cli/observability-and-access.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Open a service shell or run a remote command in a service container.",
  },
  {
    command: "status",
    primary: "references/cli/observability-and-access.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Inspect linked project and deployment health quickly.",
  },
  {
    command: "unlink",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Remove only the local directory association.",
  },
  {
    command: "up",
    primary: "references/cli/deployments-and-releases.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Upload and deploy code from the current directory.",
  },
  {
    command: "upgrade",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/research/version-drift.md"],
    why: "Upgrade the installed Railway CLI.",
  },
  {
    command: "variable",
    primary: "references/cli/configuration-networking-and-scaling.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "List, set, or delete environment variables for a service.",
  },
  {
    command: "whoami",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Inspect the current logged-in Railway user and auth context.",
  },
  {
    command: "volume",
    primary: "references/cli/functions-and-volumes.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "List, add, attach, detach, update, or delete Railway volumes.",
  },
  {
    command: "redeploy",
    primary: "references/cli/deployments-and-releases.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Rebuild and redeploy the latest service deployment.",
  },
  {
    command: "restart",
    primary: "references/cli/deployments-and-releases.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Restart the latest deployment without rebuilding.",
  },
  {
    command: "scale",
    primary: "references/cli/configuration-networking-and-scaling.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Set explicit per-region instance counts in local 4.29.0.",
  },
  {
    command: "check_updates",
    primary: "references/cli/context-projects-and-linking.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "Inspect update-check behavior for the installed CLI.",
  },
  {
    command: "functions",
    primary: "references/cli/functions-and-volumes.md",
    secondary: ["references/cli/railway-cli-command-reference.md"],
    why: "List, create, link, push, pull, or delete Railway functions.",
  },
  {
    command: "help",
    primary: "references/cli/railway-cli-command-reference.md",
    secondary: ["references/cli/railway-cli-live-help-snapshot.md"],
    why: "Use the generated reference or raw snapshot when the user wants pure help output.",
  },
];

function uniq(values) {
  return [...new Set(values)];
}

function rel(filePath) {
  return path.relative(skillDir, filePath).replaceAll(path.sep, "/");
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function main() {
  const [treeRaw, skillRaw] = await Promise.all([
    fs.readFile(commandTreePath, "utf8"),
    fs.readFile(skillPath, "utf8"),
  ]);

  const tree = JSON.parse(treeRaw);
  const root = tree.commands.find((entry) => entry.key === "railway");
  assert(root, "Root `railway` command not found in command tree.");

  const topLevelCommands = root.commands.map((entry) => entry.name);
  const coverageCommands = coverage.map((entry) => entry.command);
  const missingCoverage = topLevelCommands.filter(
    (command) => !coverageCommands.includes(command),
  );
  const extraCoverage = coverageCommands.filter(
    (command) => !topLevelCommands.includes(command),
  );

  assert(
    missingCoverage.length === 0,
    `Coverage map is missing top-level commands: ${missingCoverage.join(", ")}`,
  );
  assert(
    extraCoverage.length === 0,
    `Coverage map has commands not present in the local tree: ${extraCoverage.join(", ")}`,
  );

  const coveragePaths = uniq(
    coverage.flatMap((entry) => [entry.primary, ...entry.secondary]),
  );

  for (const coveragePath of coveragePaths) {
    const absolute = path.join(skillDir, coveragePath);
    await fs.access(absolute);
  }

  const referencesDir = path.join(skillDir, "references");
  const markdownFiles = [];

  async function walk(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const absolute = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(absolute);
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        markdownFiles.push(rel(absolute));
      }
    }
  }

  await walk(referencesDir);

  const orphanedReferences = markdownFiles.filter((markdownPath) => {
    const basename = path.basename(markdownPath);
    return !skillRaw.includes(basename);
  });

  assert(
    orphanedReferences.length === 0,
    `SKILL.md does not route these markdown files: ${orphanedReferences.join(", ")}`,
  );

  const skillLineCount = skillRaw.split("\n").length;
  assert(
    skillLineCount < 500,
    `SKILL.md exceeds the 500-line target (${skillLineCount} lines).`,
  );

  const coverageMarkdown = [
    "# Command Family Coverage",
    "",
    "Use this file when you need a compact audit trail showing that every local top-level Railway CLI command family is accounted for by the skill's routed references.",
    "",
    "This file is generated from `scripts/verify-use-railway-skill.mjs` against the extracted local `railway 4.29.0` command tree.",
    "",
    "## Coverage summary",
    "",
    `- Local top-level command families captured: \`${topLevelCommands.length}\``,
    `- Coverage entries defined: \`${coverage.length}\``,
    `- Primary workflow or reference routes used: \`${uniq(coverage.map((entry) => entry.primary)).length}\``,
    "",
    "For exact flags, aliases, possible values, and nested subcommands, always pair this matrix with `references/cli/railway-cli-command-reference.md`.",
    "",
    "## Command family matrix",
    "",
    "| Command | Aliases | Primary route | Secondary routes | Why this route exists |",
    "|---|---|---|---|---|",
    ...coverage.map((entry) => {
      const rootCommand = root.commands.find((command) => command.name === entry.command);
      const aliases =
        rootCommand && rootCommand.aliases.length > 0
          ? rootCommand.aliases.map((alias) => "`" + alias + "`").join(", ")
          : "None";
      const secondary =
        entry.secondary.length > 0
          ? entry.secondary.map((item) => "`" + item + "`").join("<br>")
          : "None";

      return `| \`${entry.command}\` | ${aliases} | \`${entry.primary}\` | ${secondary} | ${entry.why} |`;
    }),
    "",
    "## Audit notes",
    "",
    "- `service` is intentionally routed through `references/cli/common-workflows.md` first because its nested subcommands split across linking, observability, deployment, and scaling concerns.",
    "- `help` is covered by the generated command reference and the raw help snapshot rather than by a workflow guide.",
    "- This matrix proves family coverage, not full flag-level coverage; the flag-complete source remains `references/cli/railway-cli-command-reference.md`.",
  ].join("\n");

  await fs.writeFile(coverageDocPath, `${coverageMarkdown}\n`, "utf8");

  console.log("use-railway skill verification passed.");
  console.log(`Top-level command families: ${topLevelCommands.length}`);
  console.log(`Coverage entries: ${coverage.length}`);
  console.log(`Generated coverage doc: ${rel(coverageDocPath)}`);
  console.log(`SKILL.md line count: ${skillLineCount}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
