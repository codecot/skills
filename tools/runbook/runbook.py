#!/usr/bin/env python3
"""runbook.py - living document engine.

A runbook is a plain markdown file. Headings are steps. Fenced blocks carry
roles: check (probe state), do (make it true), undo (take it back), ask (input).
The engine keeps state between runs, honours critical gates, and can verify
independent steps in any order.

Stdlib only, Python 3.8+. See FORMAT.md.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

VERSION = "0.1"

ROLES = {"check", "do", "undo", "ask"}
SHELL_LANGS = {"sh", "bash", "zsh", "shell"}

PASS = "pass"
FAIL = "fail"
BLOCKED = "blocked"
SKIPPED = "skipped"
UNKNOWN = "unknown"

MARKS = {PASS: "ok  ", FAIL: "FAIL", BLOCKED: "----", SKIPPED: "skip", UNKNOWN: " ?  "}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
ATTR_RE = re.compile(r"\{([^{}]*)\}\s*$")


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "step"


def parse_tokens(info: str):
    """Split an info string / attribute list into flags and key=value pairs."""
    flags: List[str] = []
    attrs: Dict[str, str] = {}
    ident: Optional[str] = None
    for tok in info.split():
        tok = tok.strip()
        if not tok:
            continue
        if tok.startswith("#"):
            ident = tok[1:]
        elif "=" in tok:
            k, v = tok.split("=", 1)
            attrs[k.strip()] = v.strip().strip('"').strip("'")
        else:
            flags.append(tok)
    return ident, flags, attrs


@dataclass
class Block:
    role: str
    lang: str
    body: str
    attrs: Dict[str, str] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    line: int = 0


def expand(value: str) -> str:
    """A leading ~ in an input means the home directory, as a reader expects."""
    if value.startswith("~/") or value == "~":
        return os.path.expanduser(value)
    return value


@dataclass
class Ask:
    name: str
    prompt: str
    secret: bool = False
    persist: bool = True
    default: str = ""


@dataclass
class Step:
    id: str
    title: str
    level: int
    line: int
    flags: List[str] = field(default_factory=list)
    attrs: Dict[str, str] = field(default_factory=dict)
    blocks: List[Block] = field(default_factory=list)

    @property
    def critical(self) -> bool:
        return "critical" in self.flags

    @property
    def needs(self) -> List[str]:
        raw = self.attrs.get("needs", "")
        return [s for s in re.split(r"[,\s]+", raw) if s]

    def of_role(self, role: str) -> List[Block]:
        return [b for b in self.blocks if b.role == role]

    @property
    def asks(self) -> List[Ask]:
        out: List[Ask] = []
        for b in self.of_role("ask"):
            out.extend(parse_asks(b))
        return out


def parse_asks(block: Block) -> List[Ask]:
    asks: List[Ask] = []
    for raw in block.body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        name = parts[0]
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            continue
        prompt = parts[1] if len(parts) > 1 else name
        ask = Ask(name=name, prompt=prompt)
        for mod in parts[2:]:
            if mod == "secret":
                ask.secret = True
                ask.persist = False
            elif mod == "persist":
                ask.persist = True
            elif mod.startswith("default="):
                ask.default = mod.split("=", 1)[1]
        asks.append(ask)
    return asks


@dataclass
class Runbook:
    path: Path
    title: str
    steps: List[Step]
    doc_blocks: List[Block]

    def step(self, sid: str) -> Optional[Step]:
        for s in self.steps:
            if s.id == sid:
                return s
        return None

    @property
    def global_asks(self) -> List[Ask]:
        out: List[Ask] = []
        for b in self.doc_blocks:
            if b.role == "ask":
                out.extend(parse_asks(b))
        return out


def parse(path: Path) -> Runbook:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = path.stem
    steps: List[Step] = []
    doc_blocks: List[Block] = []
    seen_ids: Dict[str, int] = {}
    i = 0
    step_level: Optional[int] = None

    while i < len(lines):
        line = lines[i]
        fence = FENCE_RE.match(line)
        if fence:
            indent, marker, info = fence.group(1), fence.group(2), fence.group(3)
            body: List[str] = []
            i += 1
            while i < len(lines):
                close = FENCE_RE.match(lines[i])
                if close and close.group(2)[0] == marker[0] and len(close.group(2)) >= len(marker) and not close.group(3).strip():
                    i += 1
                    break
                body.append(lines[i])
                i += 1
            block = make_block(info, "\n".join(body), i)
            if block is not None:
                (steps[-1].blocks if steps else doc_blocks).append(block)
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            ident, flags, attrs = None, [], {}
            m = ATTR_RE.search(text)
            if m:
                ident, flags, attrs = parse_tokens(m.group(1))
                text = text[: m.start()].strip()
            if level == 1 and not steps and step_level is None:
                title = text
                i += 1
                continue
            if step_level is None:
                step_level = level
            if level > step_level:
                # deeper headings are prose inside the current step
                i += 1
                continue
            sid = ident or slug(text)
            if sid in seen_ids:
                seen_ids[sid] += 1
                sid = "%s-%d" % (sid, seen_ids[sid])
            else:
                seen_ids[sid] = 1
            steps.append(Step(id=sid, title=text, level=level, line=i + 1, flags=flags, attrs=attrs))
            i += 1
            continue
        i += 1

    return Runbook(path=path, title=title, steps=steps, doc_blocks=doc_blocks)


def make_block(info: str, body: str, line: int) -> Optional[Block]:
    ident, flags, attrs = parse_tokens(info)
    role = None
    lang = ""
    rest: List[str] = []
    for f in flags:
        if role is None and f in ROLES:
            role = f
        elif not lang and (f in SHELL_LANGS or f in {"python", "python3"}):
            lang = f
        else:
            rest.append(f)
    if role is None:
        if lang in SHELL_LANGS and "step" in rest:
            role = "do"
        else:
            return None  # documentation block, not executable
    if not lang:
        lang = "python3" if role != "ask" and "python" in rest else "bash"
    return Block(role=role, lang=lang, body=body, attrs=attrs, flags=rest, line=line)


class State:
    def __init__(self, path: Path):
        self.path = path
        self.data: Dict = {"version": VERSION, "steps": {}, "vars": {}}
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data.update(loaded)
                    self.data.setdefault("steps", {})
                    self.data.setdefault("vars", {})
            except (ValueError, OSError):
                pass

    def status(self, sid: str) -> str:
        return self.data["steps"].get(sid, {}).get("status", UNKNOWN)

    def record(self, sid: str, status: str, exit_code: Optional[int] = None, note: str = "",
               output: str = "") -> None:
        entry = self.data["steps"].setdefault(sid, {})
        entry["status"] = status
        entry["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        if exit_code is not None:
            entry["exit"] = exit_code
        if note:
            entry["note"] = note
        if status == FAIL and output:
            entry["output"] = output
        else:
            entry.pop("output", None)
        self.save()

    def set_var(self, name: str, value: str, persist: bool) -> None:
        if persist:
            self.data["vars"][name] = value
        else:
            self.data["vars"].pop(name, None)
            self.data.setdefault("unstored", [])
            if name not in self.data["unstored"]:
                self.data["unstored"].append(name)
        self.save()

    def save(self) -> None:
        self.data["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)


class Console:
    def __init__(self, color: Optional[bool] = None, verbose: bool = False):
        self.color = sys.stdout.isatty() if color is None else color
        self.verbose = verbose
        self.secrets: List[str] = []

    def mask(self, text: str) -> str:
        for s in self.secrets:
            if s:
                text = text.replace(s, "***")
        return text

    def paint(self, text: str, code: str) -> str:
        if not self.color:
            return text
        return "\033[%sm%s\033[0m" % (code, text)

    def mark(self, status: str) -> str:
        codes = {PASS: "32", FAIL: "31", BLOCKED: "90", SKIPPED: "33", UNKNOWN: "90"}
        return self.paint(MARKS[status], codes.get(status, "0"))

    def say(self, text: str = "") -> None:
        print(self.mask(text))

    def head(self, text: str) -> None:
        self.say("\n" + self.paint(text, "1"))

    def output(self, text: str, limit: int = 20) -> None:
        text = text.rstrip()
        if not text:
            return
        rows = text.splitlines()
        if not self.verbose and len(rows) > limit:
            rows = ["... (%d lines trimmed)" % (len(rows) - limit)] + rows[-limit:]
        for row in rows:
            self.say("      " + row)


class Engine:
    def __init__(self, book: Runbook, state: State, con: Console, env_extra: Dict[str, str],
                 interactive: bool = True, timeout: int = 600):
        self.book = book
        self.state = state
        self.con = con
        self.vars: Dict[str, str] = dict(state.data.get("vars", {}))
        self.vars.update(env_extra)
        self.interactive = interactive
        self.timeout = timeout
        self.last_exit: Optional[int] = None
        self.last_output: str = ""

    # ---- execution primitives -------------------------------------------------
    def shell_for(self, block: Block) -> List[str]:
        want = block.attrs.get("shell", block.lang)
        if want in {"python", "python3"}:
            return [sys.executable, "-c", block.body]
        path = shutil.which(want) or shutil.which("bash") or "/bin/sh"
        return [path, "-c", block.body]

    def run_block(self, block: Block) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env.update({k: str(v) for k, v in self.vars.items()})
        cwd = block.attrs.get("cwd")
        workdir = Path(os.path.expanduser(cwd)) if cwd else self.book.path.parent
        timeout = int(block.attrs.get("timeout", self.timeout))
        try:
            return subprocess.run(
                self.shell_for(block), env=env, cwd=str(workdir), timeout=timeout,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
        except subprocess.TimeoutExpired as exc:
            out = exc.output or ""
            if isinstance(out, bytes):
                out = out.decode("utf-8", "replace")
            return subprocess.CompletedProcess(args=[], returncode=124,
                                               stdout=out + "\n[timeout after %ds]" % timeout)

    def ok_codes(self, block: Block) -> List[int]:
        raw = block.attrs.get("ok", "0")
        return [int(x) for x in re.split(r"[,\s]+", raw) if x.strip().lstrip("-").isdigit()]

    def exec_role(self, step: Step, role: str) -> Optional[bool]:
        blocks = step.of_role(role)
        if not blocks:
            return None
        for block in blocks:
            proc = self.run_block(block)
            good = proc.returncode in self.ok_codes(block)
            self.last_exit = proc.returncode
            self.last_output = "\n".join(self.con.mask(proc.stdout).rstrip().splitlines()[-10:])
            capture = block.attrs.get("capture")
            if capture and good:
                self.vars[capture] = proc.stdout.strip()
                self.state.set_var(capture, self.vars[capture], True)
            show = self.con.verbose or block.role != "check"
            if show and (not good or self.con.verbose):
                self.con.output(proc.stdout)
                if not good:
                    self.con.say("      exit %d" % proc.returncode)
            if not good:
                return False
        return True

    # ---- inputs ---------------------------------------------------------------
    def collect(self, asks: List[Ask]) -> bool:
        for ask in asks:
            if ask.name in self.vars and self.vars[ask.name] != "":
                if ask.secret:
                    self.con.secrets.append(self.vars[ask.name])
                continue
            from_env = os.environ.get(ask.name)
            if from_env:
                self.vars[ask.name] = expand(from_env)
            elif self.interactive:
                label = "  %s" % ask.prompt
                if ask.default:
                    label += " [%s]" % ask.default
                label += ": "
                try:
                    value = getpass.getpass(label) if ask.secret else input(label)
                except EOFError:
                    value = ""
                self.vars[ask.name] = value.strip() or ask.default
            else:
                self.vars[ask.name] = ask.default
            self.vars[ask.name] = expand(self.vars[ask.name])
            if not self.vars[ask.name]:
                self.con.say("  missing input %s" % ask.name)
                return False
            if ask.secret:
                self.con.secrets.append(self.vars[ask.name])
            self.state.set_var(ask.name, self.vars[ask.name], ask.persist)
        return True

    # ---- step level -----------------------------------------------------------
    def remember(self, step: Step, status: str, note: str = "") -> str:
        """Write a step result to state together with the exit code and output tail."""
        self.state.record(step.id, status, exit_code=self.last_exit, note=note,
                          output=self.last_output)
        return status

    def blocked_by(self, step: Step) -> List[str]:
        return [n for n in step.needs if self.state.status(n) != PASS]

    def check(self, step: Step) -> str:
        blocks = step.of_role("check")
        if not blocks:
            return self.state.status(step.id)
        self.last_exit, self.last_output = None, ""
        if not self.collect(step.asks):
            return FAIL
        ok = self.exec_role(step, "check")
        return PASS if ok else FAIL

    def fix(self, step: Step) -> str:
        self.last_exit, self.last_output = None, ""
        if not self.collect(step.asks):
            return self.remember(step, FAIL, "missing input")
        done = self.exec_role(step, "do")
        if done is None:
            return self.remember(step, FAIL, "no do block")
        if not done:
            return self.remember(step, FAIL, "do failed")
        return self.remember(step, self.check(step), "after do")

    def undo(self, step: Step) -> Optional[bool]:
        result = self.exec_role(step, "undo")
        if result:
            self.state.record(step.id, UNKNOWN, note="undone")
        return result


# ---------------------------------------------------------------------------
# commands


def report(book: Runbook, state: State, con: Console) -> None:
    con.head("%s  (%s)" % (book.title, book.path.name))
    for n, step in enumerate(book.steps, 1):
        status = state.status(step.id)
        tag = " [critical]" if step.critical else ""
        con.say("  %s  %2d. %s%s" % (con.mark(status), n, step.title, tag))
        entry = state.data["steps"].get(step.id, {})
        if status in (FAIL, BLOCKED):
            detail = entry.get("note", "")
            if entry.get("output"):
                detail = ("%s: %s" % (detail, entry["output"].splitlines()[-1])) if detail else entry["output"].splitlines()[-1]
            if detail:
                con.say("        %s" % detail)
    counts: Dict[str, int] = {}
    for step in book.steps:
        s = state.status(step.id)
        counts[s] = counts.get(s, 0) + 1
    con.say("\n  " + ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())))


def ensure_inputs(eng: Engine, book: Runbook, con: Console) -> None:
    """Поля, объявленные до первого шага, нужны любой команде: без них проверки
    получают пустую переменную и врут про состояние машины."""
    if book.global_asks and not eng.collect(book.global_asks):
        con.say("  (не хватает значений для всего документа, проверки пойдут как есть)")


def cmd_status(book: Runbook, state: State, con: Console, args) -> int:
    eng = Engine(book, state, con, parse_sets(args.set), interactive=False)
    ensure_inputs(eng, book, con)
    failed_critical = False
    for step in book.steps:
        if not step.of_role("check"):
            state.record(step.id, state.status(step.id))
            continue
        blocked = eng.blocked_by(step)
        status = BLOCKED if blocked else eng.check(step)
        note = "blocked by %s" % ",".join(blocked) if blocked else ("check failed" if status == FAIL else "checked")
        eng.remember(step, status, note)
        if status == FAIL and step.critical:
            failed_critical = True
    report(book, state, con)
    if args.json:
        print(json.dumps(as_json(book, state), indent=2, ensure_ascii=False))
    if failed_critical:
        return 2
    return 1 if any(state.status(s.id) == FAIL for s in book.steps) else 0


def cmd_run(book: Runbook, state: State, con: Console, args) -> int:
    eng = Engine(book, state, con, parse_sets(args.set), interactive=not args.yes)
    if book.global_asks:
        con.head("Inputs")
        if not eng.collect(book.global_asks):
            return 3

    gate_stop: Optional[Step] = None
    only = set(args.only or [])

    for n, step in enumerate(book.steps, 1):
        if only and step.id not in only:
            continue
        con.head("%2d. %s%s" % (n, step.title, "  [critical]" if step.critical else ""))
        blocked = eng.blocked_by(step)
        if blocked:
            eng.remember(step, BLOCKED, "needs " + ",".join(blocked))
            con.say("  %s waiting on: %s" % (con.mark(BLOCKED), ", ".join(blocked)))
            continue
        status = eng.check(step)
        if status == PASS:
            eng.remember(step, PASS, "already true")
            con.say("  %s already true" % con.mark(PASS))
            continue
        if not step.of_role("do"):
            eng.remember(step, FAIL, "manual step")
            con.say("  %s needs a human, no do block" % con.mark(FAIL))
        else:
            if args.no_fix:
                eng.remember(step, FAIL, "fix skipped")
                con.say("  %s red, fix skipped" % con.mark(FAIL))
            else:
                if not args.yes and eng.interactive:
                    answer = ask_line("  red. run the fix? [Y/n/q] ").lower()
                    if answer.startswith("q"):
                        con.say("  stopped by you")
                        return 2
                    if answer.startswith("n"):
                        eng.remember(step, SKIPPED, "skipped by you")
                        continue
                con.say("  fixing ...")
                status = eng.fix(step)
                con.say("  %s %s" % (con.mark(status), "green after fix" if status == PASS else "still red"))
        if state.status(step.id) != PASS and step.critical:
            gate_stop = step
            break

    if gate_stop is not None:
        con.head("Gate: %s is critical and red. Stopping here." % gate_stop.title)
        con.say("  Auditing independent steps below the gate, read only.")
        for step in book.steps[book.steps.index(gate_stop) + 1:]:
            if gate_stop.id in step.needs:
                eng.remember(step, BLOCKED, "needs " + gate_stop.id)
                continue
            if step.of_role("check"):
                status = eng.check(step)
                eng.remember(step, status, "audit")
                con.say("  %s %s" % (con.mark(status), step.title))

    report(book, state, con)
    if gate_stop is not None:
        return 2
    return 1 if any(state.status(s.id) == FAIL for s in book.steps) else 0


def cmd_step(book: Runbook, state: State, con: Console, args) -> int:
    step = book.step(args.id)
    if step is None:
        con.say("no step %r. known ids: %s" % (args.id, ", ".join(s.id for s in book.steps)))
        return 3
    eng = Engine(book, state, con, parse_sets(args.set), interactive=not args.yes)
    ensure_inputs(eng, book, con)
    con.head(step.title)
    if args.undo:
        result = eng.undo(step)
        if result is None:
            con.say("  no undo block")
            return 3
        con.say("  %s" % ("undone" if result else "undo failed"))
        return 0 if result else 1
    if args.fix:
        status = eng.fix(step)
    else:
        status = eng.check(step)
        eng.remember(step, status, "check failed" if status == FAIL else "checked")
    con.say("  %s %s" % (con.mark(status), status))
    return 0 if status == PASS else 1


def cmd_teardown(book: Runbook, state: State, con: Console, args) -> int:
    eng = Engine(book, state, con, parse_sets(args.set), interactive=not args.yes)
    ensure_inputs(eng, book, con)
    failures = 0
    for step in reversed(book.steps):
        if not step.of_role("undo"):
            continue
        con.head("undo: %s" % step.title)
        if not args.yes and ask_line("  run undo? [Y/n] ").lower().startswith("n"):
            con.say("  left alone")
            continue
        if eng.undo(step):
            con.say("  done")
        else:
            failures += 1
            con.say("  undo failed")
    return 1 if failures else 0


def cmd_plan(book: Runbook, state: State, con: Console, args) -> int:
    if args.json:
        print(json.dumps(as_json(book, state), indent=2, ensure_ascii=False))
        return 0
    con.head("%s  (%d steps)" % (book.title, len(book.steps)))
    for n, step in enumerate(book.steps, 1):
        roles = ",".join(sorted({b.role for b in step.blocks})) or "prose"
        bits = [roles]
        if step.critical:
            bits.append("critical")
        if step.needs:
            bits.append("needs " + ",".join(step.needs))
        con.say("  %2d. %-40s %s  #%s" % (n, step.title, "; ".join(bits), step.id))
    return 0


def cmd_vars(book: Runbook, state: State, con: Console, args) -> int:
    con.head("vars in %s" % state.path.name)
    for k, v in sorted(state.data.get("vars", {}).items()):
        con.say("  %s = %s" % (k, v))
    for k in state.data.get("unstored", []):
        con.say("  %s = <not stored, secret>" % k)
    return 0


def as_json(book: Runbook, state: State) -> Dict:
    return {
        "runbook": str(book.path),
        "title": book.title,
        "engine": VERSION,
        "steps": [
            {
                "id": s.id,
                "title": s.title,
                "line": s.line,
                "critical": s.critical,
                "needs": s.needs,
                "roles": sorted({b.role for b in s.blocks}),
                "asks": [a.name for a in s.asks],
                "status": state.status(s.id),
                "state": state.data["steps"].get(s.id, {}),
            }
            for s in book.steps
        ],
        "inputs": [a.name for a in book.global_asks],
    }


def parse_sets(pairs: Optional[List[str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in pairs or []:
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v
    return out


def ask_line(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="runbook", description="run a markdown runbook as a living document")
    p.add_argument("--version", action="version", version="runbook %s" % VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("file", type=Path)
        sp.add_argument("--state", type=Path, default=None, help="state file (default: <file>.state.json)")
        sp.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
        sp.add_argument("--verbose", "-v", action="store_true")
        sp.add_argument("--no-color", action="store_true")
        return sp

    s = common(sub.add_parser("status", help="run every check, change nothing"))
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    r = common(sub.add_parser("run", help="walk the steps, fix what is red"))
    r.add_argument("--yes", "-y", action="store_true", help="no questions, fix automatically")
    r.add_argument("--no-fix", action="store_true", help="check only, never run do blocks")
    r.add_argument("--only", action="append", help="limit to these step ids")
    r.set_defaults(func=cmd_run)

    st = common(sub.add_parser("step", help="work on one step"))
    st.add_argument("id")
    st.add_argument("--fix", action="store_true")
    st.add_argument("--undo", action="store_true")
    st.add_argument("--yes", "-y", action="store_true")
    st.set_defaults(func=cmd_step)

    t = common(sub.add_parser("teardown", help="run undo blocks bottom to top"))
    t.add_argument("--yes", "-y", action="store_true")
    t.set_defaults(func=cmd_teardown)

    pl = common(sub.add_parser("plan", help="show the parsed structure"))
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(func=cmd_plan)

    v = common(sub.add_parser("vars", help="show saved inputs"))
    v.set_defaults(func=cmd_vars)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.file.expanduser()
    if not path.exists():
        print("no such runbook: %s" % path, file=sys.stderr)
        return 3
    book = parse(path)
    if not book.steps:
        print("no steps found in %s (steps are markdown headings)" % path, file=sys.stderr)
        return 3
    state_path = args.state or path.with_suffix(path.suffix + ".state.json")
    state = State(state_path)
    con = Console(color=False if args.no_color else None, verbose=args.verbose)
    return args.func(book, state, con, args)


if __name__ == "__main__":
    sys.exit(main())
