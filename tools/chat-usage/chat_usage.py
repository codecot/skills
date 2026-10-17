#!/usr/bin/env python3
"""chat-usage: count your own VS Code Copilot Chat history, locally.

Reads the chat session files VS Code keeps on disk and writes a request table
and a summary: how far back the history goes, requests per month, quarter and
day, by model, mode and project, the longest sessions, retry loops and huge
pastes. Counting is done here, not by a model, so the numbers are cheap and
repeatable. Standard library only; nothing leaves the machine.

Usage:
    python chat_usage.py                 # find VS Code data, write ./chat-usage-out/
    python chat_usage.py --root PATH     # a VS Code "User" folder, or any folder of session files
    python chat_usage.py --out DIR --prompt-chars 0
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

RETRY_WORDS = re.compile(
    r"\b(still|again|same (error|issue|problem)|not work|doesn'?t work|didn'?t work|failing|fails|failed|retry|try again)\b",
    re.I,
)
SECRET_LIKE = re.compile(
    r"(?i)(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+"
    r"|(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+|https?://[^\s/]+:[^\s@]+@\S+)"
)
TOOL_KINDS = {"toolInvocation", "toolInvocationSerialized"}
LONG_PASTE = 5000
SHORT_PROMPT = 200


def default_roots() -> list[Path]:
    home = Path.home()
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    names = ["Code", "Code - Insiders", "VSCodium"]
    return [base / n / "User" for n in names if (base / n / "User").is_dir()]


def session_files(root: Path) -> list[tuple[Path, str]]:
    """(file, project) pairs. Project comes from workspace.json next to chatSessions."""
    out = []
    for f in sorted(root.rglob("*.json*")):
        if f.suffix not in (".json", ".jsonl") or f.parent.name not in ("chatSessions", "emptyWindowChatSessions"):
            continue
        project = "(no folder)"
        ws = f.parent.parent / "workspace.json"
        if ws.is_file():
            try:
                w = json.loads(ws.read_text(encoding="utf-8"))
                uri = w.get("folder") or w.get("workspace") or ""
                project = uri.rstrip("/").split("/")[-1] or project
            except (OSError, ValueError):
                pass
        out.append((f, project))
    return out


def _set(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def _get(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def load_session(path: Path) -> tuple[dict | None, int]:
    """A session dict, plus the number of journal entries that could not be applied.

    .json is a snapshot. .jsonl is a journal: kind 0 carries the initial state,
    kind 1 sets the value at path k, kind 2 appends v (a list) to the array at k.
    Unknown kinds and paths that do not resolve are counted, not guessed."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            return json.loads(text), 0
        except ValueError:
            return None, 1
    state, skipped = None, 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            kind, k, v = e.get("kind"), e.get("k") or [], e.get("v")
            if kind == 0:
                state = v
            elif kind == 1 and state is not None and k:
                _set(state, k, v)
            elif kind == 2 and state is not None and k:
                target = _get(state, k)
                target.extend(v if isinstance(v, list) else [v])
            else:
                skipped += 1
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            skipped += 1
    return state, skipped


def _text_len(parts) -> int:
    n = 0
    for p in parts or []:
        if isinstance(p, dict):
            v = p.get("value")
            if isinstance(v, str):
                n += len(v)
            elif isinstance(v, dict) and isinstance(v.get("value"), str):
                n += len(v["value"])
    return n


def request_rows(session: dict, project: str, file: Path, prompt_chars: int) -> list[dict]:
    rows = []
    created = session.get("creationDate")
    sid = session.get("sessionId") or file.stem
    for i, r in enumerate(session.get("requests") or []):
        if not isinstance(r, dict):
            continue
        msg = r.get("message") or {}
        prompt = msg.get("text") if isinstance(msg, dict) else str(msg)
        prompt = prompt or ""
        ts = r.get("timestamp") or created
        meta = (r.get("result") or {}).get("metadata") or {}
        agent = r.get("agent") or {}
        mode = (r.get("modeInfo") or {}).get("kind") or agent.get("id") or ""
        model = r.get("modelId") or meta.get("modelId") or meta.get("model") or ""
        response = r.get("response") or []
        tools = sum(1 for p in response if isinstance(p, dict) and p.get("kind") in TOOL_KINDS)
        when = datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if isinstance(ts, (int, float)) else None
        head = SECRET_LIKE.sub("[redacted]", prompt[:prompt_chars]).replace("\n", " ") if prompt_chars else ""
        rows.append({
            "date": when.strftime("%Y-%m-%d") if when else "",
            "time": when.strftime("%H:%M") if when else "",
            "project": project,
            "session": sid,
            "index": i,
            "mode": mode,
            "model": model,
            "prompt_chars": len(prompt),
            "response_chars": _text_len(response),
            "tool_calls": tools,
            "canceled": bool(r.get("isCanceled")),
            "retry_like": bool(len(prompt) < SHORT_PROMPT and RETRY_WORDS.search(prompt)),
            "prompt_head": head,
        })
    return rows


def quarter(date: str) -> str:
    y, m = date[:4], int(date[5:7])
    return f"{y}-Q{(m - 1) // 3 + 1}"


def loops(rows: list[dict], min_run: int = 4) -> list[tuple[str, str, str, int]]:
    """Runs of >= min_run consecutive retry-like or pasted-error prompts in one session."""
    found = []
    by_session = defaultdict(list)
    for r in rows:
        by_session[r["session"]].append(r)
    for sid, rs in by_session.items():
        run = 0
        for r in rs + [None]:
            hit = r is not None and (r["retry_like"] or r["prompt_chars"] > LONG_PASTE)
            if hit:
                run += 1
                continue
            if run >= min_run:
                found.append((sid, rs[0]["project"], rs[0]["date"], run))
            run = 0
    return sorted(found, key=lambda x: -x[3])


def table(title: str, counter, head=("", "requests"), limit=None) -> str:
    items = counter.most_common(limit) if limit else sorted(counter.items())
    lines = [f"## {title}", "", f"| {head[0]} | {head[1]} |", "|---|---|"]
    lines += [f"| {k or '(unknown)'} | {v} |" for k, v in items]
    return "\n".join(lines) + "\n"


def summary(rows: list[dict], files: int, skipped: int) -> str:
    dated = [r for r in rows if r["date"]]
    sessions = {r["session"] for r in rows}
    out = ["# Copilot Chat usage — local history", ""]
    if dated:
        first, last = min(r["date"] for r in dated), max(r["date"] for r in dated)
        span = (datetime.fromisoformat(last) - datetime.fromisoformat(first)).days + 1
        active = len({r["date"] for r in dated})
        out += [
            "## History span", "",
            f"- first request: {first}; last request: {last}; {span} days, {active} of them with requests",
            f"- {len(rows)} requests in {len(sessions)} sessions, from {files} session files",
            "",
        ]
    else:
        out += [f"- {len(rows)} requests, {files} session files, no timestamps found", ""]
    n = max(len(rows), 1)
    cov = lambda key: round(100 * sum(1 for r in rows if r[key]) / n)  # noqa: E731
    out += [
        "## What the files contain", "",
        f"- requests with a timestamp: {cov('date')}%; with a model id: {cov('model')}%; with a mode: {cov('mode')}%",
        f"- journal entries that could not be applied: {skipped}",
        "- these are chat requests, not billing units: model multipliers, inline completions and the",
        "  GitHub coding agent are not in these files",
        "",
    ]
    out.append(table("Requests per quarter", Counter(quarter(r["date"]) for r in dated), ("quarter", "requests")))
    out.append(table("Requests per month", Counter(r["date"][:7] for r in dated), ("month", "requests")))
    out.append(table("Top 10 days", Counter(r["date"] for r in dated), ("day", "requests"), 10))
    out.append(table("By model", Counter(r["model"] for r in rows), ("model", "requests"), 20))
    out.append(table("By mode", Counter(r["mode"] for r in rows), ("mode", "requests"), 20))
    out.append(table("By project", Counter(r["project"] for r in rows), ("project", "requests"), 20))
    per_session = Counter(r["session"] for r in rows)
    first_of = {}
    for r in rows:
        first_of.setdefault(r["session"], r)
    out += ["## 15 longest sessions", "", "| requests | project | date | first prompt |", "|---|---|---|---|"]
    for sid, k in per_session.most_common(15):
        f = first_of[sid]
        out.append(f"| {k} | {f['project']} | {f['date']} | {f['prompt_head'].replace('|', '/')} |")
    out.append("")
    lp = loops(rows)
    out += ["## Retry loops (4+ consecutive retry-like prompts or huge pastes)", "",
            f"- {len(lp)} loops, {sum(x[3] for x in lp)} requests inside them", ""]
    out += [f"- {k} in a row — {p}, {d}, session {s}" for s, p, d, k in lp[:15]]
    big = [r for r in rows if r["prompt_chars"] > LONG_PASTE]
    out += ["", "## Huge pastes", "", f"- {len(big)} prompts over {LONG_PASTE} characters, "
            f"in {len({r['session'] for r in big})} sessions", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", action="append", type=Path, help="VS Code User folder or a folder of session files")
    ap.add_argument("--out", type=Path, default=Path("chat-usage-out"))
    ap.add_argument("--prompt-chars", type=int, default=150, help="prompt characters kept for the longest-sessions table (0 = none)")
    a = ap.parse_args(argv)
    roots = a.root or default_roots()
    if not roots:
        print("No VS Code user folder found; pass --root.", file=sys.stderr)
        return 2
    rows, files, skipped = [], 0, 0
    for root in roots:
        for f, project in session_files(root):
            session, bad = load_session(f)
            files += 1
            skipped += bad
            if session:
                rows += request_rows(session, project, f, a.prompt_chars)
    rows.sort(key=lambda r: (r["date"], r["time"], r["session"], r["index"]))
    a.out.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["date"]
    with open(a.out / "requests.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (a.out / "summary.md").write_text(summary(rows, files, skipped), encoding="utf-8")
    print(f"{files} session files, {len(rows)} requests -> {a.out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
