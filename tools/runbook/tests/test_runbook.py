#!/usr/bin/env python3
"""Tests for the runbook engine. Stdlib unittest, no network, no installs."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runbook as rb  # noqa: E402


def write(tmp: Path, name: str, text: str) -> Path:
    p = tmp / name
    p.write_text(text, encoding="utf-8")
    return p


def run(args):
    return rb.main(args)


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_headings_become_steps_and_title_is_h1(self):
        f = write(self.tmp, "a.md", """# My setup

intro prose

## First thing {#first critical}

```check
true
```

### a sub heading is prose

## Second thing {needs=first}

```bash do
true
```
""")
        book = rb.parse(f)
        self.assertEqual(book.title, "My setup")
        self.assertEqual([s.id for s in book.steps], ["first", "second-thing"])
        self.assertTrue(book.steps[0].critical)
        self.assertEqual(book.steps[1].needs, ["first"])
        self.assertEqual(book.steps[1].of_role("do")[0].body.strip(), "true")

    def test_documentation_blocks_are_not_executable(self):
        f = write(self.tmp, "b.md", """## Step

```json
{"not": "a command"}
```

```
plain sample output
```
""")
        book = rb.parse(f)
        self.assertEqual(book.steps[0].blocks, [])

    def test_ask_block_parsing(self):
        f = write(self.tmp, "c.md", """## Creds

```ask
TOKEN | Personal token | secret
REGISTRY | Registry url | default=https://example.com
```
""")
        asks = rb.parse(f).steps[0].asks
        self.assertEqual([a.name for a in asks], ["TOKEN", "REGISTRY"])
        self.assertTrue(asks[0].secret)
        self.assertFalse(asks[0].persist)
        self.assertEqual(asks[1].default, "https://example.com")

    def test_duplicate_ids_are_disambiguated(self):
        f = write(self.tmp, "d.md", "## Same\n\n## Same\n")
        self.assertEqual([s.id for s in rb.parse(f).steps], ["same", "same-2"])


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def state_of(self, f: Path):
        return json.loads(f.with_suffix(f.suffix + ".state.json").read_text())

    def test_check_only_run_reports_green_and_red(self):
        f = write(self.tmp, "s.md", """## Green

```check
true
```

## Red

```check
false
```
""")
        code = run(["status", str(f), "--no-color"])
        st = self.state_of(f)
        self.assertEqual(st["steps"]["green"]["status"], "pass")
        self.assertEqual(st["steps"]["red"]["status"], "fail")
        self.assertEqual(code, 1)

    def test_status_never_runs_do_blocks(self):
        flag = self.tmp / "touched"
        f = write(self.tmp, "s2.md", """## Thing

```check
false
```

```do
touch %s
```
""" % flag)
        run(["status", str(f), "--no-color"])
        self.assertFalse(flag.exists())

    def test_do_makes_check_pass(self):
        flag = self.tmp / "made"
        f = write(self.tmp, "r.md", """## Make the file

```check
test -f %s
```

```do
touch %s
```
""" % (flag, flag))
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertTrue(flag.exists())
        self.assertEqual(code, 0)
        self.assertEqual(self.state_of(f)["steps"]["make-the-file"]["status"], "pass")

    def test_do_that_does_not_satisfy_check_is_red(self):
        f = write(self.tmp, "r2.md", """## Lies

```check
false
```

```do
true
```
""")
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 1)
        self.assertEqual(self.state_of(f)["steps"]["lies"]["status"], "fail")

    def test_critical_gate_stops_but_audits_independent_steps(self):
        f = write(self.tmp, "g.md", """## Gate {critical}

```check
false
```

## Dependent {needs=gate}

```check
true
```

## Independent

```check
true
```
""")
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 2)
        st = self.state_of(f)["steps"]
        self.assertEqual(st["gate"]["status"], "fail")
        self.assertEqual(st["dependent"]["status"], "blocked")
        self.assertEqual(st["independent"]["status"], "pass")

    def test_non_critical_red_does_not_stop_the_walk(self):
        f = write(self.tmp, "n.md", """## Soft

```check
false
```

## Later

```check
true
```
""")
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 1)
        self.assertEqual(self.state_of(f)["steps"]["later"]["status"], "pass")

    def test_inputs_reach_the_shell_and_secrets_are_not_stored(self):
        out = self.tmp / "out.txt"
        f = write(self.tmp, "i.md", """## Uses input

```ask
NAME | Your name
PW | Password | secret
```

```check
test -f %s
```

```do
printf '%%s' "$NAME" > %s
```
""" % (out, out))
        code = run(["run", str(f), "--yes", "--no-color", "--set", "NAME=ada", "--set", "PW=hunter2"])
        self.assertEqual(code, 0)
        self.assertEqual(out.read_text(), "ada")
        st = self.state_of(f)
        self.assertNotIn("PW", json.dumps(st))

    def test_missing_required_input_fails_the_step(self):
        f = write(self.tmp, "m.md", """## Needs token

```ask
TOKEN | Token | secret
```

```check
false
```

```do
true
```
""")
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 1)
        self.assertEqual(self.state_of(f)["steps"]["needs-token"]["note"], "missing input")

    def test_capture_stores_a_variable_for_later_steps(self):
        f = write(self.tmp, "cap.md", """## Read version {#ver}

```check capture=TOOL_V
printf 'v9.9'
```

## Use it {needs=ver}

```check
test "$TOOL_V" = v9.9
```
""")
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 0)
        self.assertEqual(self.state_of(f)["vars"]["TOOL_V"], "v9.9")

    def test_state_persists_between_invocations(self):
        flag = self.tmp / "keep"
        f = write(self.tmp, "p.md", """## Keep

```check
test -f %s
```

```do
touch %s
```
""" % (flag, flag))
        run(["run", str(f), "--yes", "--no-color"])
        run(["status", str(f), "--no-color"])
        self.assertEqual(self.state_of(f)["steps"]["keep"]["status"], "pass")

    def test_teardown_runs_undo_in_reverse_order(self):
        log = self.tmp / "log.txt"
        f = write(self.tmp, "t.md", """## One

```undo
echo one >> %s
```

## Two

```undo
echo two >> %s
```
""" % (log, log))
        code = run(["teardown", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 0)
        self.assertEqual(log.read_text().split(), ["two", "one"])

    def test_step_command_targets_one_step(self):
        f = write(self.tmp, "one.md", """## Alpha

```check
true
```

## Beta

```check
false
```
""")
        self.assertEqual(run(["step", str(f), "alpha", "--no-color"]), 0)
        self.assertEqual(run(["step", str(f), "beta", "--no-color"]), 1)
        self.assertEqual(run(["step", str(f), "nope", "--no-color"]), 3)

    def test_manual_step_without_do_is_red_not_a_crash(self):
        f = write(self.tmp, "man.md", """## Ask IT for access

```check
false
```
""")
        code = run(["run", str(f), "--yes", "--no-color"])
        self.assertEqual(code, 1)
        self.assertEqual(self.state_of(f)["steps"]["ask-it-for-access"]["note"], "manual step")

    def test_timeout_is_reported_not_hung(self):
        f = write(self.tmp, "to.md", """## Slow

```check timeout=1
sleep 5
```
""")
        code = run(["status", str(f), "--no-color"])
        self.assertEqual(code, 1)
        self.assertEqual(self.state_of(f)["steps"]["slow"]["exit"], 124)

    def test_tilde_in_an_input_means_the_home_directory(self):
        f = write(self.tmp, "tilde.md", """## Home path

```ask
TARGET | Where | default=~/nowhere-really
```

```check
case "$TARGET" in "$HOME"/*) exit 0 ;; *) exit 1 ;; esac
```
""")
        self.assertEqual(run(["run", str(f), "--yes", "--no-color"]), 0)

    def test_failing_check_output_is_kept_in_state_for_the_report(self):
        f = write(self.tmp, "out.md", """## Noisy

```check
echo "permission denied, ask IT" >&2
exit 7
```
""")
        run(["status", str(f), "--no-color"])
        entry = self.state_of(f)["steps"]["noisy"]
        self.assertEqual(entry["exit"], 7)
        self.assertIn("ask IT", entry["output"])

    def test_document_level_inputs_reach_every_command(self):
        f = write(self.tmp, "glob.md", """# Doc

```ask
LIMIT | How many | default=7
```

## Uses the document input

```check
test "$LIMIT" = 7
```
""")
        self.assertEqual(run(["status", str(f), "--no-color"]), 0)
        self.assertEqual(run(["step", str(f), "uses-the-document-input", "--no-color", "--yes"]), 0)

    def test_ok_codes_allow_nonzero_success(self):
        f = write(self.tmp, "ok.md", """## Tolerant

```check ok=0,3
exit 3
```
""")
        self.assertEqual(run(["status", str(f), "--no-color"]), 0)

    def test_json_plan_is_machine_readable(self):
        f = write(self.tmp, "j.md", """## A {#a critical}

```check
true
```
""")
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            run(["plan", str(f), "--json", "--no-color"])
        data = json.loads(buf.getvalue())
        self.assertEqual(data["steps"][0]["id"], "a")
        self.assertTrue(data["steps"][0]["critical"])

    def test_python_blocks_run_too(self):
        f = write(self.tmp, "py.md", """## Python check

```python check
import sys; sys.exit(0)
```
""")
        self.assertEqual(run(["status", str(f), "--no-color"]), 0)

    def test_missing_file_and_empty_runbook_are_usage_errors(self):
        self.assertEqual(run(["status", str(self.tmp / "nope.md"), "--no-color"]), 3)
        empty = write(self.tmp, "e.md", "just prose, no headings\n")
        self.assertEqual(run(["status", str(empty), "--no-color"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
