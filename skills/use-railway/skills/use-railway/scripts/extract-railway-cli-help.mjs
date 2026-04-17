#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const skillRoot = path.resolve(__dirname, "..");
const outputRoot = path.resolve(skillRoot, "references", "cli");

function runRailway(args) {
  const result = spawnSync("railway", args, {
    cwd: skillRoot,
    encoding: "utf8",
  });

  const combined = [result.stdout, result.stderr].filter(Boolean).join("");
  if (result.error) {
    throw result.error;
  }

  return {
    exitCode: result.status ?? 0,
    raw: combined,
    sanitized: sanitizeHelpOutput(combined),
  };
}

function sanitizeHelpOutput(output) {
  return output
    .replace(/^New version available:.*\n/gm, "")
    .replace(/\u001B\[[0-9;]*m/g, "")
    .trimEnd();
}

function splitSections(lines) {
  const sections = [];
  let current = { heading: "intro", lines: [] };

  for (const line of lines) {
    const headingMatch = line.match(/^([A-Z][A-Za-z ]+):$/);
    if (headingMatch) {
      sections.push(current);
      current = { heading: headingMatch[1], lines: [] };
      continue;
    }
    current.lines.push(line);
  }

  sections.push(current);
  return sections;
}

function compactParagraph(lines) {
  const parts = [];
  let paragraph = [];

  for (const line of lines.map((entry) => entry.trimEnd())) {
    if (line.trim() === "") {
      if (paragraph.length) {
        parts.push(paragraph.join(" ").replace(/\s+/g, " ").trim());
        paragraph = [];
      }
      continue;
    }
    paragraph.push(line.trim());
  }

  if (paragraph.length) {
    parts.push(paragraph.join(" ").replace(/\s+/g, " ").trim());
  }

  return parts.join("\n\n");
}

function extractAliases(text) {
  const aliasMatch = text.match(/\[aliases:\s*([^\]]+)\]\s*$/);
  if (!aliasMatch) {
    return {
      text: text.trim(),
      aliases: [],
    };
  }

  return {
    text: text.replace(/\s*\[aliases:\s*[^\]]+\]\s*$/, "").trim(),
    aliases: aliasMatch[1]
      .split(",")
      .map((entry) => entry.trim())
      .filter(Boolean),
  };
}

function extractPossibleValues(text) {
  const matches = [...text.matchAll(/\[possible values:\s*([^\]]+)\]/g)];
  const values = matches
    .flatMap((match) =>
      match[1]
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
    );

  return {
    text: text.replace(/\s*\[possible values:\s*[^\]]+\]/g, "").trim(),
    possibleValues: values,
  };
}

function parseCommandSection(lines) {
  const commands = [];

  for (const line of lines) {
    if (!line.trim()) {
      continue;
    }

    const match = line.match(/^\s{2,}(\S+)(?:\s{2,}(.*))?$/);
    if (!match) {
      continue;
    }

    const name = match[1];
    const remainder = (match[2] ?? "").trim();
    const { text, aliases } = extractAliases(remainder);

    commands.push({
      name,
      description: text,
      aliases,
    });
  }

  return commands;
}

function parseDefinitionSection(lines, sectionName) {
  const entries = [];
  let current = null;

  const startPattern =
    sectionName === "Arguments"
      ? /^\s{2,}(\[[^\]]+\]|<[^>]+>)(?:\s{2,}(.*))?$/
      : /^\s{2,}((?:-\w,\s+)?--[A-Za-z0-9][A-Za-z0-9-]*(?:[ =]\[[^\]]+\]|[ =]<[^>]+>)?|-\w(?:,\s+--[A-Za-z0-9][A-Za-z0-9-]*(?:[ =]\[[^\]]+\]|[ =]<[^>]+>)?)?)(?:\s{2,}(.*))?$/;

  for (const rawLine of lines) {
    if (!rawLine.trim()) {
      if (current) {
        current.body.push("");
      }
      continue;
    }

    const match = rawLine.match(startPattern);
    if (match) {
      if (current) {
        entries.push(finalizeDefinition(current));
      }

      current = {
        spec: match[1].trim(),
        body: [match[2] ?? ""],
      };
      continue;
    }

    if (current) {
      current.body.push(rawLine.trim());
    }
  }

  if (current) {
    entries.push(finalizeDefinition(current));
  }

  return entries;
}

function finalizeDefinition(entry) {
  const paragraph = compactParagraph(entry.body);
  const { text: withoutValues, possibleValues } = extractPossibleValues(paragraph);
  const { text, aliases } = extractAliases(withoutValues);

  return {
    spec: entry.spec,
    aliases,
    description: text,
    possibleValues,
  };
}

function parseHelp(commandPath) {
  const helpArgs = [...commandPath, "--help"];
  const result = runRailway(helpArgs);
  const lines = result.sanitized.split(/\r?\n/);
  const usageIndex = lines.findIndex((line) => line.startsWith("Usage:"));
  const introLines = usageIndex >= 0 ? lines.slice(0, usageIndex) : [];
  const sections = splitSections(lines);
  const introText = compactParagraph(introLines);
  const usageLine = lines.find((line) => line.startsWith("Usage:")) ?? "";

  const commands = parseCommandSection(
    sections.find((section) => section.heading === "Commands")?.lines ?? [],
  );
  const argumentsList = parseDefinitionSection(
    sections.find((section) => section.heading === "Arguments")?.lines ?? [],
    "Arguments",
  );
  const options = parseDefinitionSection(
    sections.find((section) => section.heading === "Options")?.lines ?? [],
    "Options",
  );

  return {
    key: ["railway", ...commandPath].join(" "),
    path: commandPath,
    depth: commandPath.length,
    title: introText.split("\n")[0] ?? "",
    intro: introText,
    usage: usageLine.replace(/^Usage:\s*/, "").trim(),
    commands,
    arguments: argumentsList,
    options,
    rawHelp: result.sanitized,
  };
}

function escapeCell(text) {
  return (text || "").replace(/\|/g, "\\|").replace(/\n/g, "<br><br>");
}

function formatValues(values) {
  return values.length ? values.map((value) => `\`${value}\``).join(", ") : "None";
}

function formatAliases(aliases) {
  return aliases.length ? aliases.map((alias) => `\`${alias}\``).join(", ") : "None";
}

function formatDefinitionTable(entries, emptyLabel) {
  if (!entries.length) {
    return `${emptyLabel}\n`;
  }

  const header = [
    "| Spec | Aliases | Description | Possible values |",
    "|---|---|---|---|",
  ];
  const rows = entries.map((entry) => {
    const description = entry.description || "None";
    return `| \`${escapeCell(entry.spec)}\` | ${formatAliases(entry.aliases)} | ${escapeCell(description)} | ${formatValues(entry.possibleValues)} |`;
  });

  return `${header.concat(rows).join("\n")}\n`;
}

function formatCommandTable(commands, emptyLabel) {
  if (!commands.length) {
    return `${emptyLabel}\n`;
  }

  const header = [
    "| Subcommand | Aliases | Description |",
    "|---|---|---|",
  ];
  const rows = commands.map(
    (command) =>
      `| \`${escapeCell(command.name)}\` | ${formatAliases(command.aliases)} | ${escapeCell(command.description || "None")} |`,
  );

  return `${header.concat(rows).join("\n")}\n`;
}

const discovered = [];
const queue = [[]];
const seen = new Set();

while (queue.length) {
  const commandPath = queue.shift();
  const key = ["railway", ...commandPath].join(" ");
  if (seen.has(key)) {
    continue;
  }

  const parsed = parseHelp(commandPath);
  discovered.push(parsed);
  seen.add(key);

  for (const subcommand of parsed.commands) {
    if (subcommand.name === "help") {
      continue;
    }
    queue.push([...commandPath, subcommand.name]);
  }
}

discovered.sort((left, right) => {
  if (left.depth !== right.depth) {
    return left.depth - right.depth;
  }
  return left.key.localeCompare(right.key);
});

const versionInfo = runRailway(["--version"]).sanitized.trim();
const generatedAt = new Date().toISOString();
const topLevel = discovered.find((entry) => entry.depth === 0);

let markdown = "";
markdown += "# Railway CLI Command Reference\n\n";
markdown += `- Source: live \`railway\` binary on this machine\n`;
markdown += `- Version: \`${versionInfo}\`\n`;
markdown += `- Generated at: \`${generatedAt}\`\n`;
markdown += "- Extraction rule: recursively ran `railway [subcommand...] --help` for every discovered command while skipping `help` recursion to avoid loops\n";
markdown += `- Total command entries captured: \`${discovered.length}\`\n\n`;

markdown += "## Top-level commands\n\n";
markdown += formatCommandTable(topLevel?.commands ?? [], "No top-level commands found.");

for (const entry of discovered) {
  const headingDepth = Math.min(entry.depth + 2, 6);
  const heading = "#".repeat(headingDepth);
  markdown += `\n${heading} \`${entry.key}\`\n\n`;
  markdown += `- Usage: \`${entry.usage || entry.key}\`\n`;
  if (entry.title) {
    markdown += `- Summary: ${entry.title}\n`;
  }
  markdown += `- Depth: \`${entry.depth}\`\n`;

  markdown += "\n### Subcommands\n\n";
  markdown += formatCommandTable(entry.commands, "No subcommands.");

  markdown += "\n### Arguments\n\n";
  markdown += formatDefinitionTable(entry.arguments, "No positional arguments.");

  markdown += "\n### Options\n\n";
  markdown += formatDefinitionTable(entry.options, "No options.");
}

let rawSnapshot = "";
rawSnapshot += "# Railway CLI Live Help Snapshot\n\n";
rawSnapshot += `- Source: \`${versionInfo}\`\n`;
rawSnapshot += `- Generated at: \`${generatedAt}\`\n\n`;

for (const entry of discovered) {
  rawSnapshot += `## \`${entry.key}\`\n\n`;
  rawSnapshot += "```text\n";
  rawSnapshot += `${entry.rawHelp}\n`;
  rawSnapshot += "```\n\n";
}

mkdirSync(outputRoot, { recursive: true });

writeFileSync(
  path.join(outputRoot, "railway-cli-command-tree.json"),
  `${JSON.stringify({ versionInfo, generatedAt, commands: discovered }, null, 2)}\n`,
);
writeFileSync(path.join(outputRoot, "railway-cli-command-reference.md"), markdown);
writeFileSync(path.join(outputRoot, "railway-cli-live-help-snapshot.md"), rawSnapshot);
