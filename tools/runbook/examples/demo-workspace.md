# Demo: prepare a workspace

Safe to run anywhere. Everything happens under `~/.cache/runbook-demo`,
and `teardown` removes it again. Read it as a normal document; the engine
reads the same text as a program.

```ask
WORKSPACE | Where to put the demo workspace | default=~/.cache/runbook-demo
```

## Shell tools are present {#tools critical}

Nothing below works without `git` and `curl`. This step is a gate: if it is
red, the walk stops here.

```check
command -v git >/dev/null && command -v curl >/dev/null
```

## Python version is recorded {#python}

A check can also harvest a value. Whatever this block prints on stdout is
stored as `PY_V` and is visible to every later step and to the next run.

```check capture=PY_V
python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])'
```

## The workspace exists {#workspace needs=tools}

```check
test -d "$WORKSPACE"
```

```do
mkdir -p "$WORKSPACE"
```

```undo
rm -rf "$WORKSPACE"
```

## Config file is written {#config needs=workspace}

The check proves the end state, the do block reaches it. Run the runbook
twice and this step reports green the second time without doing anything.

```check
grep -q "python = $PY_V" "$WORKSPACE/config.ini" 2>/dev/null
```

```do
printf '[demo]\npython = %s\n' "$PY_V" > "$WORKSPACE/config.ini"
```

```undo
rm -f "$WORKSPACE/config.ini"
```

## Someone in IT has to do this one {#manual}

A step with no `do` block is a human step. It goes red and, because it is not
critical, the walk continues past it and the report says what is left for you.

```check
test -f "$WORKSPACE/approved-by-it.txt"
```
