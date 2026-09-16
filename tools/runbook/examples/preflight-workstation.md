# Preflight: is this machine ready to work?

Read-only. Every block here is a `check`, so `runbook status` answers the question
without touching anything. Run it before a long build, a render, or handing a
machine to someone else.

```ask
MIN_FREE_GB | How many GB free do you need on the work disk | default=20
```

## Disk has room {#disk critical}

A build that dies at 98% wastes more time than this whole file.

```check
free=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc '0-9')
test "$free" -ge "$MIN_FREE_GB"
```

## Memory is not already eaten {#memory}

```check
avail=$(awk '/MemAvailable/ {print int($2/1024/1024)}' /proc/meminfo)
echo "available: ${avail} GB"
test "$avail" -ge 2
```

## Core tools are installed {#tools critical}

```check
for t in git curl python3; do
  command -v "$t" >/dev/null || { echo "missing: $t"; exit 1; }
done
```

## Python version is recorded {#python needs=tools}

Whatever a check prints on stdout can be captured and reused by later steps
and by the next run.

```check capture=PY_V
python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])'
```

## Git knows who you are {#identity needs=tools}

A machine that commits as `root@localhost` is a machine someone will have to
clean up after. No `do` block on purpose: this is a decision, not a task.

```check
git config --get user.email | grep -q '@'
```

## The network is actually up {#network}

DNS and routing fail in different ways; this checks both at once.

```check timeout=10
curl -fsS -m 8 -o /dev/null https://github.com
```

## GPU driver answers {#gpu}

Non-critical: plenty of work needs no GPU. Red here just means "not today".

```check timeout=15 capture=GPU_NAME
nvidia-smi --query-gpu=name --format=csv,noheader
```
