#!/usr/bin/env python3
"""Tally the CCAR-F trainer result by exam domain.

Run it after taking the trainer (it reads the trainer's state, changes nothing):

    python3 ccar-f-score.py

Each step's domain is in its title ("Qn - Domain"); this groups pass/fail by
domain so you can see which area to review. 43/60 is the pass range.
"""
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RUNBOOK = os.path.join(HERE, "..", "runbook.py")
BOOK = os.path.join(HERE, "ccar-f-trainer.md")


def main() -> int:
    proc = subprocess.run(
        [sys.executable, RUNBOOK, "plan", BOOK, "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "failed to read runbook plan\n")
        return 1
    data = json.loads(proc.stdout)
    ok, total = Counter(), Counter()
    for step in data["steps"]:
        domain = step["title"].split(" - ", 1)[1].split(" (")[0]
        total[domain] += 1
        if step.get("status") == "pass":
            ok[domain] += 1
    print("Score by domain:")
    for domain in sorted(total):
        print("  %-34s %d/%d" % (domain, ok[domain], total[domain]))
    got, n = sum(ok.values()), sum(total.values())
    verdict = "pass range" if got >= 43 else "below 43/60 - keep practising"
    print("  %-34s %d/%d   (%s)" % ("TOTAL", got, n, verdict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
