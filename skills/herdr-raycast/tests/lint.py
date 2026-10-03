#!/usr/bin/env python3
"""Static checks for the herdr-raycast skill (layers S and H in tests/README.md).

1. Drift: every herdr command, flag and enumerated value shown in a code span
   must exist in the installed CLI (`herdr completion zsh` for the tree,
   `--help` for flags and value sets).
2. Coverage: the agent subcommands and read sources must all be named.
3. Regression rules R1-R9: contradictions found once must not come back.
4. Trace: every case in tests/README.md has a Trace line, and every Trace
   phrase still stands in the file it names.
5. Hygiene: SKILL.md under 500 lines, relative links resolve, no code span
   wraps onto the next line (the checks above cannot read one that does).
6. Frontmatter (FRONT): SKILL.md's name is still its folder's and no key is
   gone. Raycast loads a selected skill through a symlinked plugin folder and
   once rewrote SKILL.md through it.

The skill files get every check. tests/README.md gets drift, links, spans and
Trace only: its rule table and runbook quote the old wordings on purpose.

Only `--help` and `completion zsh` run; neither executes a command. Paths whose
usage the top-level binary routes itself (update, server, attach, ...) are
never probed. Exit 1 on any FAIL.

usage: python3 tests/lint.py            # checks
       python3 tests/lint.py --tree [group ...]   # leaves with their flags
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = ["SKILL.md", "SYSTEM_PROMPT.md"] + sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "references").glob("*.md"))
README = "tests/README.md"
DENY_FIRST = {"update", "server", "terminal", "completion", "completions"}
DENY_ANY = {"attach", "observe", "control"}
DENY_PATHS = {("config", "reset-keys"), ("channel", "set"), ("machine", "reconnect"),
              ("plugin", "install"), ("plugin", "run"), ("session", "stop"),
              ("session", "delete")}
GLOBAL = {"--session", "--machine", "--remote", "--remote-keybindings", "--help",
          "--handoff", "--default-config", "--skill", "--version"}
NUM = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
fails, warns = [], []


def herdr(*args):
    p = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=20)
    return p.stdout + p.stderr


def denied(p):
    return p[0] in DENY_FIRST or any(x in DENY_ANY for x in p) or p[:2] in DENY_PATHS


def build_tree():
    comp = herdr("completion", "zsh")
    funcs = {}
    for m in re.finditer(r"^(_herdr\S*?)_commands\(\) \{\n(.*?)^\}", comp, re.S | re.M):
        funcs[m.group(1).replace("-", "_")] = re.findall(r"^'([a-z][a-z0-9-]*):", m.group(2), re.M)
    node = {}

    def walk(p):
        key = "_herdr" + "".join("__subcmd__" + x for x in p)
        node[p] = [n for n in funcs.get(key.replace("-", "_"), []) if n != "help"]
        for n in node[p]:
            walk(p + (n,))
    walk(())
    flags, values = {}, {}
    for p in node:
        if not p or denied(p):
            continue
        fl, last = set(), None
        for line in herdr(*p, "--help").splitlines():
            m = re.match(r"\s{2,}(?:-[A-Za-z], )?(--[a-z0-9][a-z0-9-]*)", line)
            if m:
                last = m.group(1)
                fl.add(last)
            v = re.search(r"\[possible values: ([^\]]+)\]", line)
            if v and last:
                values[(p, last)] = {x.strip() for x in v.group(1).split(",")}
        flags[p] = fl
    return node, flags, values


def code_spans(text):
    fenced = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            yield i, line
            continue
        if line.startswith("    ") and not re.match(r"\s*([-*|]|\d+\.)\s", line):
            yield i, line.strip()
        for m in re.finditer(r"`([^`]+)`", line):
            yield i, m.group(1)


def commands(code, roots):
    code = re.sub(r"\[--machine [^\]]*\]", " ", code).split(" #")[0]
    for seg in re.split(r"&&|;", code):
        toks = [t.strip("[](),\"'") for t in seg.split()]
        toks = [t for t in toks if t]
        if "herdr" in toks:
            toks = toks[toks.index("herdr") + 1:]
        while len(toks) > 1 and toks[0] in ("--machine", "--session"):
            toks = toks[2:]
        if toks and toks[0] in roots:
            yield toks


def sentences(text):
    para, start = [], None
    lines = text.splitlines() + [""]
    for i, line in enumerate(lines, 1):
        item = re.match(r"\s*([-*]|\d+\.)\s", line)
        if line.strip() == "" or line.lstrip().startswith(("```", "#", "|")) or (item and para):
            if para:
                joined = " ".join(x.strip() for x in para)
                for s in re.split(r"(?<=[.!?])\s+(?=[A-Z`*(\"])", joined):
                    yield start, s
            para, start = [], None
            if line.lstrip().startswith("|"):
                yield i, line
                continue
        if line.strip() and not line.lstrip().startswith(("```", "#", "|")):
            if start is None:
                start = i
            para.append(line)


def section(text, title):
    m = re.search(rf"^## {title}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def flat(s):
    return " ".join(s.split())


def drift(f, text, node, flags, values, roots, mentioned):
    """DRIFT on every code span of one file; returns the words seen in code."""
    words = set()
    for i, code in code_spans(text):
        words.update(re.findall(r"[a-z][a-z-]*", code))
        for toks in commands(code, roots):
            p, rest = (), toks
            while rest and rest[0] in node.get(p, []):
                p, rest = p + (rest[0],), rest[1:]
            mentioned.add(p)
            if node.get(p) and rest and re.fullmatch(r"[a-z][a-z0-9-]*", rest[0]):
                fails.append(f"DRIFT {f}:{i} unknown subcommand: {' '.join(p + (rest[0],))}")
            known = flags.get(p)
            for j, t in enumerate(rest):
                if t == "--":
                    break
                for alt in t.split("|"):
                    if not re.fullmatch(r"--[a-z][a-z0-9-]*", alt):
                        continue
                    if known is not None and alt not in known | GLOBAL:
                        fails.append(f"DRIFT {f}:{i} {' '.join(p)}: no flag {alt}")
                    nxt = rest[j + 1] if j + 1 < len(rest) else ""
                    if (p, alt) in values and re.fullmatch(r"[a-z][a-z|-]*", nxt):
                        for val in nxt.split("|"):
                            if val not in values[(p, alt)]:
                                fails.append(f"DRIFT {f}:{i} {' '.join(p)} {alt}: no value {val}")
    return words


def hygiene(f, text):
    fenced = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and line.count("`") % 2:
            fails.append(f"SPAN {f}:{i} a code span wraps onto the next line, out of lint's sight")
        for m in re.finditer(r"\]\(([^)#\s]+)", line):
            if not m.group(1).startswith("http") and not ((ROOT / f).parent / m.group(1)).exists():
                fails.append(f"LINK {f}:{i} {m.group(1)}")


def front():
    text = (ROOT / "SKILL.md").read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    keys = dict(re.findall(r"^([a-z]+): *(.*)$", m.group(1), re.M)) if m else {}
    name = keys.get("name", "").strip('"')
    if name != ROOT.name:
        fails.append(f"FRONT SKILL.md name is {name!r}, its folder {ROOT.name!r} "
                     "(a Raycast projection? see tests/README.md)")
    for k in ("description", "compatibility"):
        if k not in keys:
            fails.append(f"FRONT SKILL.md frontmatter has no {k}")


def rules(f, text, n_src, n_leaves, n_groups):
    for i, s in sentences(text):
        if re.search(r"\bstatus\b", s) and re.search(r"refus", s, re.I) \
                and not re.search(r"bare|status server", s, re.I):
            fails.append(f"R1 {f}:{i} 'status refused' without 'bare': {s[:90]}")
        if re.search(r"at once|immediately", s) and "settled" in s and not re.search(r"match", s):
            fails.append(f"R2 {f}:{i} 'settled returns at once' without the --until condition: {s[:90]}")
        m = re.search(r"\b(two|three|four|five|six|\d+) (?:read )?sources\b", s)
        if m and NUM.get(m.group(1), int(m.group(1)) if m.group(1).isdigit() else 0) != n_src:
            fails.append(f"R4 {f}:{i} says {m.group(1)} sources, help has {n_src}: {s[:90]}")
        m = re.search(r"(~?)(\d+) (?:leaf )?commands", s)
        if m and abs(int(m.group(2)) - n_leaves) > (3 if m.group(1) else 0):
            fails.append(f"R5 {f}:{i} says {m.group(0)}, completion tree has {n_leaves} leaves")
        m = re.search(r"\b(\d+) groups", s)
        if m and int(m.group(1)) != n_groups:
            fails.append(f"R5 {f}:{i} says {m.group(0)}, completion tree has {n_groups}")
        if "`timeout`" in s and "deliver" in s and not re.search(r"may or may not|whether", s, re.I):
            fails.append(f"R6 {f}:{i} delivery after `timeout` stated as certain: {s[:90]}")
        if "leaves its transcript" in s and re.search(r"laude", s) and "fullscreen" not in s:
            fails.append(f"R8 {f}:{i} claude's transcript in scrollback without the fullscreen condition: {s[:90]}")
        if "turn ended" in s and re.search(r"completion_seq|Compare it", s) and "Herdr" not in s:
            fails.append(f"R9 {f}:{i} `completion_seq` taken as the work's end, not Herdr's count: {s[:90]}")
    paras = {}
    for i, s in sentences(text):
        paras[i] = paras.get(i, "") + " " + s
    for i, p in paras.items():
        if "grill" in p and "`blocked`" in p and "prose" not in p:
            fails.append(f"R7 {f}:{i} grilling's questions said to arrive as a `blocked` dialog")
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"MARK_\$\?|MARK_\[0-9\]", line) and "nonce" not in line.lower():
            fails.append(f"R3 {f}:{i} reusable marker without a per-run nonce")


def trace(text):
    cases = re.findall(r"^\| (T\d+) \|", section(text, "Cases"), re.M)
    rows = re.findall(r"^\| (T\d+) \| ([^|]+?) \| (.+?) \|\s*$", section(text, "Trace"), re.M)
    traced = {r[0] for r in rows}
    for case in cases:
        if case not in traced:
            fails.append(f"TRACE {case} has no Trace line")
    for case, f, phrase in rows:
        path = ROOT / f
        if case not in cases:
            fails.append(f"TRACE {case} is not in the Cases table")
        elif f not in FILES or not path.is_file():
            fails.append(f"TRACE {case} {f}: not a skill file")
        elif flat(phrase) not in flat(path.read_text()):
            fails.append(f"TRACE {case} {f}: phrase gone: {phrase}")
    return len(cases), len(rows)


def main():
    node, flags, values = build_tree()
    roots = set(node[()])
    leaves = [p for p in node if p and not node[p] and p[0] != "completions"]
    groups = [p for p in node[()] if p != "completions"]
    if "--tree" in sys.argv:
        want = set(sys.argv[sys.argv.index("--tree") + 1:])
        for p in sorted(leaves):
            if not want or p[0] in want:
                vals = "; ".join(f"{f}={'|'.join(sorted(v))}" for (q, f), v in values.items() if q == p)
                print(" ".join(p), " ".join(sorted(flags.get(p, {"(not probed)"}))), vals)
        print(f"{len(groups)} groups, {len(leaves)} leaf commands")
        return 0
    n_src = len(values.get((("agent", "read"), "--source"), ()))
    mentioned, text_all, code_words = set(), "", set()
    for f in FILES:
        text = (ROOT / f).read_text()
        text_all += text
        code_words |= drift(f, text, node, flags, values, roots, mentioned)
        rules(f, text, n_src, len(leaves), len(groups))
        hygiene(f, text)
    n_cases = n_rows = 0
    if (ROOT / README).is_file():
        readme = (ROOT / README).read_text()
        drift(README, readme, node, flags, values, roots, set())
        hygiene(README, readme)
        n_cases, n_rows = trace(readme)
    else:
        fails.append(f"TRACE {README} is missing")
    for sub in node[("agent",)]:
        if ("agent", sub) not in mentioned:
            fails.append(f"COVER agent {sub} is never shown in a code span")
    for p in (("agent", "read"), ("pane", "read"), ("pane", "wait-output")):
        for v in sorted(values.get((p, "--source"), ())):
            if v not in code_words:
                fails.append(f"COVER {' '.join(p)} --source {v} never appears in code")
    for p in sorted(mentioned):
        unused = sorted(fl for fl in flags.get(p, set()) - GLOBAL - {"--json"} if fl not in text_all)
        if p and not node.get(p) and unused:
            warns.append(f"FLAGS {' '.join(p)}: not named anywhere: {' '.join(unused)}")
    front()
    n = len((ROOT / "SKILL.md").read_text().splitlines())
    if n >= 500:
        fails.append(f"SIZE SKILL.md has {n} lines (limit 500)")
    for w in warns:
        print("WARN", w)
    for x in fails:
        print("FAIL", x)
    print(f"{len(groups)} groups, {len(leaves)} leaves, {len(mentioned)} paths shown, "
          f"{n_cases} cases, {n_rows} trace lines, SKILL.md {n} lines: "
          f"{len(fails)} FAIL, {len(warns)} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
