# The runbook format

A runbook is an ordinary markdown file. It stays readable on GitHub, in an
editor, in a chat window. The engine only looks at two things: headings and
fenced code blocks.

## Steps are headings

The first `#` heading is the document title. Every heading after that starts a
step; deeper headings inside a step are prose.

```markdown
## Node 20 is installed {#node critical}
```

In the braces, all optional:

| Token | Meaning |
|---|---|
| `#node` | step id, used by `needs`, `step` and the state file. Default: a slug of the title |
| `critical` | a gate. If this step ends red the walk stops |
| `needs=node,git` | do not touch this step until those ids are green |

## Blocks are roles

The word after the opening fence says what a block is for. Anything without a
role word is documentation and is never executed, so sample output and JSON
snippets are safe to paste.

| Role | Question it answers | Run by |
|---|---|---|
| `check` | is this already true? | every command, never mutates by contract |
| `do` | make it true | `run`, `step --fix` |
| `undo` | take it back | `teardown`, `step --undo` |
| `ask` | what does the engine need from the human? | before the other blocks of that step |

````markdown
```check
node --version | grep -q '^v20'
```

```do
nvm install 20
```

```undo
nvm uninstall 20
```
````

A check passes on exit code 0. The language is `bash` unless you say otherwise;
`sh`, `zsh` and `python` also work.

Block attributes:

| Attribute | Meaning |
|---|---|
| `capture=NODE_V` | stdout of this block becomes that variable, saved for later runs |
| `timeout=30` | seconds before the block is killed and reported as exit 124 |
| `ok=0,3` | exit codes that count as success |
| `shell=zsh` | run with something other than bash |
| `cwd=~/Projects/app` | working directory. Default: the folder the runbook lives in |

## Inputs

An `ask` block lists what the engine needs. One line per value, pipe separated:
name, prompt, then modifiers.

````markdown
```ask
GITHUB_TOKEN | Personal access token | secret
REGISTRY | Registry url | default=https://registry.npmjs.org
```
````

Values become environment variables for every block, so `$GITHUB_TOKEN` works
in the shell with no templating of its own. A leading `~/` is expanded to the
home directory. An `ask` block before the first step asks once for the whole
document.

`secret` means two things: the prompt does not echo, and the value is never
written to the state file. Secret values are masked in everything the engine
prints. A value already in the real environment is taken from there and not
asked for.

## State

Next to `setup.md` the engine keeps `setup.md.state.json`: per step a status,
a timestamp, the last exit code and, while a step is red, the tail of its
output. Plus captured and non-secret input values.

Statuses: `pass`, `fail`, `blocked` (something in `needs` is not green),
`skipped` (you said no), `unknown` (never checked).

Because state lives in a file and checks are cheap, order does not bind you:
`status` re-probes every step and tells you the truth about the machine right
now, whatever happened in earlier sessions.

## Two rules that make a runbook trustworthy

**A check must not change anything.** It answers a question. `status` runs
nothing but checks, which is what makes it safe to run at any moment.

**A do block must be safe to run twice.** The engine re-runs the check after
the do block, and a step only goes green when the check says so, not when the
do block exits 0. This is the Ansible contract in a document a person reads.
