#!/usr/bin/env python3
"""Tests for chat-usage. Stdlib unittest, synthetic session files only."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chat_usage as cu  # noqa: E402

DAY1 = 1760000000000  # 2025-10-09 UTC
DAY = 86400000


def req(text, ts, model="claude-opus-5-5", mode="agent", tools=0):
    return {
        "message": {"text": text},
        "timestamp": ts,
        "modelId": model,
        "modeInfo": {"kind": mode},
        "response": [{"kind": "markdownContent", "value": {"value": "ok"}}]
        + [{"kind": "toolInvocationSerialized"} for _ in range(tools)],
    }


def make_user_dir(tmp: Path) -> Path:
    ws = tmp / "User" / "workspaceStorage" / "abc"
    (ws / "chatSessions").mkdir(parents=True)
    (ws / "workspace.json").write_text(json.dumps({"folder": "file:///home/me/proj-a"}))
    snap = {"sessionId": "s1", "creationDate": DAY1, "requests": [
        req("fix the build", DAY1, tools=3),
        req("still failing", DAY1 + 60000),
        req("same error", DAY1 + 120000),
        req("try again", DAY1 + 180000),
        req("x" * 6000, DAY1 + 240000),
        req("write a commit message", DAY1 + 100 * DAY, model="gpt-5", mode="ask"),
    ]}
    (ws / "chatSessions" / "s1.json").write_text(json.dumps(snap))
    empty = tmp / "User" / "globalStorage" / "emptyWindowChatSessions"
    empty.mkdir(parents=True)
    journal = [
        {"kind": 0, "v": {"sessionId": "s2", "creationDate": DAY1 + DAY, "requests": []}},
        {"kind": 2, "k": ["requests"], "v": [req("explain module api token=abc123", DAY1 + DAY)]},
        {"kind": 1, "k": ["requests", 0, "modelId"], "v": "claude-sonnet-5-5"},
        {"kind": 9, "k": ["whatever"], "v": 1},
    ]
    (empty / "s2.jsonl").write_text("\n".join(json.dumps(e) for e in journal))
    return tmp / "User"


class ChatUsageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.user = make_user_dir(self.tmp)
        self.out = self.tmp / "out"
        self.assertEqual(cu.main(["--root", str(self.user), "--out", str(self.out)]), 0)
        self.summary = (self.out / "summary.md").read_text()
        self.csv = (self.out / "requests.csv").read_text()

    def test_reads_both_formats_and_projects(self):
        self.assertIn("7 requests in 2 sessions, from 2 session files", self.summary)
        self.assertIn("| proj-a | 6 |", self.summary)
        self.assertIn("| (no folder) | 1 |", self.summary)

    def test_journal_set_and_unknown_kind_counted(self):
        self.assertIn("claude-sonnet-5-5", self.csv)
        self.assertIn("journal entries that could not be applied: 1", self.summary)

    def test_history_span_month_and_quarter(self):
        self.assertIn("first request: 2025-10-09; last request: 2026-01-17", self.summary)
        self.assertIn("| 2025-Q4 | 6 |", self.summary)
        self.assertIn("| 2026-Q1 | 1 |", self.summary)
        self.assertIn("| 2026-01 | 1 |", self.summary)

    def test_loop_and_paste_detected(self):
        self.assertIn("- 1 loops, 4 requests inside them", self.summary)
        self.assertIn("1 prompts over 5000 characters", self.summary)

    def test_secrets_redacted_and_tools_counted(self):
        self.assertNotIn("abc123", self.csv)
        self.assertIn("[redacted]", self.csv)
        self.assertIn(",3,", self.csv)

    def test_prompt_chars_zero_keeps_no_text(self):
        out = self.tmp / "out0"
        cu.main(["--root", str(self.user), "--out", str(out), "--prompt-chars", "0"])
        self.assertNotIn("fix the build", (out / "requests.csv").read_text())


if __name__ == "__main__":
    unittest.main()
