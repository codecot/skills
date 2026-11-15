# compaction-audit — see when Claude Code compacted your sessions, and why

**Runs with:** Python 3.8+, standard library only. Nothing to install, nothing leaves the machine.

A read-only script that shows when Claude Code compacted your sessions, what triggered each compaction, how much context there was before and after, and how long the session had been idle.

It reads the session transcripts Claude Code keeps under `~/.claude/projects`. It prints numbers and timestamps only. Nothing from the conversations themselves is printed.

## Run

```bash
python3 compaction_audit.py                      # every transcript on this machine
python3 compaction_audit.py --rows               # one line per compaction
python3 compaction_audit.py --since 2026-11-01   # recent ones only
python3 compaction_audit.py path/to/session.jsonl --rows --csv out.csv
python3 tests/test_compaction_audit.py
```

## What it reports

```
time              session   trigger    before    after  idle min
2026-11-14 21:26  a1b2c3d4  auto       636464    45773      56.8
2026-11-14 23:20  a1b2c3d4  auto       293426    41284      55.9
2026-11-15 13:17  a1b2c3d4  auto       356527    40742      56.3

transcripts read: 573   compactions: 214
automatic: 172   manual: 42
tokens before: min 16,929  median 274,798  max 1,001,023
tokens after:  min 7,932  median 20,286  max 173,469
automatic compactions that fired 50-65 minutes after the last message: 152 of 172
```

`idle min` is the time between the last user or assistant message and the compaction. A value near 56 means the compaction was started by the idle timer, whatever the size of the context.

## Why the idle column matters

Claude Code compacts a conversation in two situations. One is a full context window. The other is idle compaction: a conversation above 200,000 tokens that has had no request for about an hour is replaced by a summary shortly before the prompt cache expires. On a model with a one-million-token window the two look nothing alike in this report: a full window compacts near 967,000 tokens, an idle one anywhere from 200,000 up.

Two settings in `~/.claude/settings.json` control what this script measures:

```json
{
  "idleCompaction": false,
  "cleanupPeriodDays": 3650
}
```

`idleCompaction` turns the idle timer off. `cleanupPeriodDays` is how long transcripts are kept; the default is 30 days, after which a session you have not used is deleted, and this script can no longer see it.

## Limits

- The transcript format is not documented and may change between Claude Code versions.
- The idle gap is measured from the transcript, so it is as accurate as the timestamps in it.
- Subagent transcripts are skipped.
