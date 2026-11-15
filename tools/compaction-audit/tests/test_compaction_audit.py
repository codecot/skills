#!/usr/bin/env python3
"""Tests for compaction-audit. Stdlib unittest, synthetic transcripts only."""
import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compaction_audit as ca  # noqa: E402

T0 = datetime.datetime(2026, 11, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)


def ts(minutes):
    return (T0 + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def dump(obj):
    """Claude Code writes compact JSON, one object per line."""
    return json.dumps(obj, separators=(",", ":"))


def msg(kind, minutes, text="hello", sidechain=False):
    return dump({"parentUuid": None, "isSidechain": sidechain, "type": kind,
                 "message": {"role": kind, "content": text}, "timestamp": ts(minutes)})


def big_user(minutes):
    """A tool-result line too large to parse: type near the start, timestamp near the end."""
    return dump({"parentUuid": None, "isSidechain": False, "type": "user",
                 "message": {"role": "user", "content": "x" * 30000}, "timestamp": ts(minutes)})


def big_assistant(minutes):
    """Assistant lines carry the type near the end, after the message body."""
    return dump({"parentUuid": None, "isSidechain": False,
                 "message": {"role": "assistant", "content": "y" * 30000},
                 "type": "assistant", "timestamp": ts(minutes)})


def boundary(minutes, trigger, pre, post=None):
    meta = {"trigger": trigger, "preTokens": pre}
    if post is not None:
        meta["postTokens"] = post
    return dump({"parentUuid": None, "type": "system", "subtype": "compact_boundary",
                 "compactMetadata": meta, "timestamp": ts(minutes)})


def write(tmp, lines, name="aaaaaaaa-1111.jsonl"):
    p = Path(tmp) / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


class AuditTest(unittest.TestCase):
    def test_idle_and_manual_compactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, [
                msg("user", 0), msg("assistant", 1),
                boundary(57, "auto", 250000, 30000),          # 56 minutes after the last message
                msg("user", 60), msg("assistant", 61),
                boundary(64, "manual", 800000, 20000),        # 3 minutes after the last message
            ])
            rows = ca.audit(p)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["trigger"], "auto")
        self.assertEqual(rows[0]["pre_tokens"], 250000)
        self.assertEqual(rows[0]["post_tokens"], 30000)
        self.assertEqual(rows[0]["idle_min"], 56.0)
        self.assertEqual(rows[1]["trigger"], "manual")
        self.assertEqual(rows[1]["idle_min"], 3.0)
        self.assertEqual(rows[0]["session"], "aaaaaaaa")

    def test_large_lines_and_sidechains(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, [
                msg("user", 0),
                big_user(10),                                  # counts: last activity at minute 10
                msg("assistant", 40, sidechain=True),          # a subagent line does not count
                boundary(66, "auto", 300000),
                big_assistant(70),
                boundary(126, "auto", 210000),
            ])
            rows = ca.audit(p)
        self.assertEqual([r["idle_min"] for r in rows], [56.0, 56.0])
        self.assertIsNone(rows[0]["post_tokens"])

    def test_since_filter_and_other_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, [
                dump({"type": "mode", "mode": "normal"}),         # bookkeeping lines carry no time
                msg("user", 0), boundary(56, "auto", 220000),
                msg("user", 60 * 48), boundary(60 * 48 + 56, "auto", 230000),
                "not json at all",
            ])
            all_rows = ca.audit(p)
            late = ca.audit(p, since=(T0 + datetime.timedelta(days=2)).date())
        self.assertEqual(len(all_rows), 2)
        self.assertEqual(len(late), 1)
        self.assertEqual(late[0]["pre_tokens"], 230000)
        self.assertEqual(late[0]["idle_min"], 56.0)

    def test_spaced_json_is_read_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            big = json.dumps({"parentUuid": None, "type": "user",
                              "message": {"role": "user", "content": "x" * 30000}, "timestamp": ts(10)})
            p = write(tmp, [msg("user", 0), big, boundary(66, "auto", 300000)])
            self.assertEqual(ca.audit(p)[0]["idle_min"], 56.0)

    def test_no_compactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, [msg("user", 0), msg("assistant", 1)])
            self.assertEqual(ca.audit(p), [])


if __name__ == "__main__":
    unittest.main()
