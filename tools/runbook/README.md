# runbook — a setup document that checks itself

**Version:** v1
**Lineage:** written for a real problem: a step-by-step access-setup instruction
handed to a team, where "I did step 4" is a claim nobody can verify. Same theme as
the rest of this repo — evidence over assertion — applied to documents instead of
prompts.
**Runs with:** Python 3.8+, standard library only. Nothing to install.

A runbook is an ordinary markdown file. It reads like an instruction because it is
one. The engine looks at two things: headings are steps, and fenced blocks carry a
role.

| Role | The question it answers |
|---|---|
| `check` | is this already true? By contract it changes nothing |
| `do` | make it true |
| `undo` | take it back |
| `ask` | what does this need from the human? |

```markdown
## Node 20 is installed {#node critical}

```check
node --version | grep -q '^v20'
```

```do
nvm install 20
```
```

Full format: [FORMAT.md](FORMAT.md). Examples: [examples/](examples/).

## Commands

```sh
python3 runbook.py status  setup.md          # probe every step, change nothing
python3 runbook.py run     setup.md          # ask, check, fix what is red, respect gates
python3 runbook.py run     setup.md --yes    # no questions, for a second machine or CI
python3 runbook.py step    setup.md node --fix
python3 runbook.py teardown setup.md         # undo blocks, bottom to top
python3 runbook.py plan    setup.md --json   # structure and state for another front end
```

Exit codes: `0` all green, `1` something red, `2` a critical gate stopped the walk,
`3` bad usage.

## What it does that a shell script cannot

- **A step has a state, not a place in a sequence.** It is green because the machine
  says so, not because a line ran once on a Tuesday.
- **A `do` block that lies cannot turn a step green.** The check is re-run after the
  fix, and the check has the last word.
- **Critical gates.** A red gate stops the walk, then every step below it that does
  not depend on it is still probed read-only. One run tells you everything that is
  wrong, not just the first thing.
- **Steps with no `do` block are human steps.** "Ask IT for access" is a legitimate
  step: it goes red, the report says who has to move, and the walk continues.
- **Inputs live in the document.** Tokens and URLs are asked once. Values marked
  `secret` are never echoed, never written to the state file, and are masked in
  output.
- **It cleans up after itself.** `teardown` walks the undo blocks in reverse.
- **It is still a document.** No notebook format, no new file type. A reader who
  never heard of this tool reads it and follows it by hand.

State lives next to the file in `<name>.md.state.json`: per step a status, the last
exit code, the tail of failing output while it is red, plus captured values.

## Why a terminal and not a web UI

The runbook has to work on a machine where nothing is set up yet, which is the whole
point of a setup document. So the engine must not need a server, a browser, an
editor extension or a package install before step one. Python 3 is already there;
node is often the thing the runbook is about to install.

The decision stays open: `plan --json` and the state file are the entire model as
data. A web page or a TUI is a front end over that, not a rewrite.

## Tests

```sh
python3 tests/test_runbook.py
```

25 tests, no network, no installs: parsing, gates, dependency blocking, state across
runs, captured variables, secret handling, timeouts, teardown order.

## Known limits

- Not on `PATH` yet: it runs as `python3 runbook.py`, not `runbook`.
- Secrets are re-asked on every run by design. No keyring integration.
- Inside a walk you cannot go back a step; you rerun it with `step --fix`.
- A document cannot include another document, so very large setups stay one file.
- Shell blocks assume a POSIX shell. Windows is untested.
