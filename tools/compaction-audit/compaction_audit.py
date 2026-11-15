#!/usr/bin/env python3
"""Audit context compactions in Claude Code session transcripts.

Reads the JSONL transcripts Claude Code keeps under ~/.claude/projects and
reports, for every compaction: when it happened, what triggered it, how many
tokens were in context before and after, and how long the session had been
idle. Nothing from the conversations themselves is printed.

    python3 compaction_audit.py                  # every transcript on this machine
    python3 compaction_audit.py FILE.jsonl ...   # specific transcripts
    python3 compaction_audit.py --since 2026-11-01 --csv out.csv

Standard library only. Read-only.
"""
import argparse
import csv
import datetime
import glob
import json
import os
import statistics
import sys


def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def message_time(line):
    """Timestamp of a user or assistant line, or None for any other line.

    Small lines are parsed. Large ones (tool output, images) are only scanned:
    the line type sits near one end and a timestamp near the other, and any
    timestamp inside such a line is within seconds of the line's own.
    """
    if len(line) < 20000:
        try:
            d = json.loads(line)
        except ValueError:
            return None
        if d.get("type") in ("user", "assistant") and not d.get("isSidechain"):
            return parse_ts(d.get("timestamp") or "")
        return None
    head = line[:300].replace('": "', '":"')
    tail = line[-800:].replace('": "', '":"')
    if '"type":"user"' in head or '"type":"assistant"' in tail:
        i = tail.rfind('"timestamp":"')
        if i < 0:
            i = head.rfind('"timestamp":"')
            tail = head
        if i >= 0:
            j = tail.find('"', i + 13)
            return parse_ts(tail[i + 13:j]) if j > 0 else None
    return None


def audit(path, since=None):
    rows, prev = [], None
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if '"compactMetadata"' in line:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                meta = d.get("compactMetadata") or {}
                ts = parse_ts(d.get("timestamp") or "")
                if ts is None or (since and ts.date() < since):
                    prev = ts or prev
                    continue
                gap = (ts - prev).total_seconds() / 60 if prev else None
                rows.append({
                    "session": os.path.basename(path)[:8],
                    "time": ts.strftime("%Y-%m-%d %H:%M"),
                    "trigger": meta.get("trigger") or "?",
                    "pre_tokens": meta.get("preTokens"),
                    "post_tokens": meta.get("postTokens") or meta.get("postCompactTokens"),
                    "idle_min": round(gap, 1) if gap is not None else None,
                })
                prev = ts
                continue
            ts = message_time(line)
            if ts:
                prev = ts
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*", help="transcript files (default: all under ~/.claude/projects)")
    ap.add_argument("--since", help="only compactions on or after this date, YYYY-MM-DD")
    ap.add_argument("--csv", help="also write every row to this CSV file")
    ap.add_argument("--rows", action="store_true", help="print every compaction, not only the summary")
    a = ap.parse_args()
    since = datetime.date.fromisoformat(a.since) if a.since else None
    paths = a.paths or [p for p in glob.glob(os.path.expanduser("~/.claude/projects/**/*.jsonl"), recursive=True)
                        if "/subagents/" not in p]
    rows = []
    for p in paths:
        try:
            rows += audit(p, since)
        except OSError as e:
            print(f"skip {p}: {e}", file=sys.stderr)
    rows.sort(key=lambda r: r["time"])
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["session"])
            w.writeheader()
            w.writerows(rows)
    if a.rows:
        print(f"{'time':16}  {'session':8}  {'trigger':7}  {'before':>8}  {'after':>7}  {'idle min':>8}")
        for r in rows:
            print(f"{r['time']:16}  {r['session']:8}  {r['trigger']:7}  {r['pre_tokens'] or 0:>8}  "
                  f"{r['post_tokens'] or 0:>7}  {r['idle_min'] if r['idle_min'] is not None else '':>8}")
        print()
    n = len(rows)
    print(f"transcripts read: {len(paths)}   compactions: {n}")
    if not n:
        return
    auto = [r for r in rows if r["trigger"] == "auto"]
    pre = [r["pre_tokens"] for r in rows if r["pre_tokens"]]
    post = [r["post_tokens"] for r in rows if r["post_tokens"]]
    idle = [r for r in auto if r["idle_min"] is not None and 50 <= r["idle_min"] <= 65]
    print(f"automatic: {len(auto)}   manual: {n - len(auto)}")
    if pre:
        print(f"tokens before: min {min(pre):,}  median {int(statistics.median(pre)):,}  max {max(pre):,}")
    if post:
        print(f"tokens after:  min {min(post):,}  median {int(statistics.median(post)):,}  max {max(post):,}")
    print(f"automatic compactions that fired 50-65 minutes after the last message: {len(idle)} of {len(auto)}")
    if idle:
        ip = [r["pre_tokens"] for r in idle if r["pre_tokens"]]
        print(f"  context at those moments: min {min(ip):,}  median {int(statistics.median(ip)):,}  max {max(ip):,}")


if __name__ == "__main__":
    main()
