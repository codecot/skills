"""Tests for prose_stamps.py: every phrase category fires, a clean text passes.

    python3 skills/prose-check/scripts/test_prose_stamps.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "prose_stamps.py")

SAMPLES = {
    "fake_contrast": "This tool is not just a linter but a whole new way of working with code.",
    "drama": "The release was a game-changer for the team and the whole company.",
    "empty_analysis": "The team shipped the change on Monday, highlighting its focus on speed.",
    "vague_claim": "Testing plays a crucial role in every project we have ever shipped.",
    "fake_authority": "Experts agree that small pull requests are easier to review well.",
    "chat_filler": "Great question, and the answer depends on the size of the team.",
    "llm_vocab": "We will delve into the details of the review process next week.",
}

CLEAN = (
    "The reviewer found 41 issues in March. We fixed 30 of them in the next "
    "round and closed the rest with a reason written in the pull request."
)


def run(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(text + "\n")
        path = fh.name
    try:
        res = subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    return res.returncode, res.stdout


class ProseStampsTest(unittest.TestCase):
    def test_catalogue_covers_samples(self):
        with open(os.path.join(HERE, "prose_stamps.json"), encoding="utf-8") as fh:
            cats = {k for k in json.load(fh) if not k.startswith("_")}
        self.assertEqual(cats, set(SAMPLES))

    def test_each_category_fires(self):
        for cat, text in SAMPLES.items():
            with self.subTest(cat=cat):
                code, out = run(text)
                self.assertIn(cat, out)
                if cat != "llm_vocab":  # llm_vocab is a hint, not a HIT
                    self.assertEqual(code, 1, out)

    def test_clean_text_passes(self):
        code, out = run(CLEAN)
        self.assertEqual(code, 0, out)
        self.assertIn("0 HIT", out)

    def test_staccato_is_a_hit(self):
        code, out = run("We ship. We test. We learn. We repeat it all again tomorrow morning.")
        self.assertIn("staccato", out)
        self.assertEqual(code, 1, out)


if __name__ == "__main__":
    unittest.main()
