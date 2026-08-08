# mafia — a measuring instrument for multi-agent rooms

Put several LLM "seats" in one conversation and they converge: by the third
turn there is one position wearing several names. Before building around that
observation, measure it. This folder is the complete instrument from a study
of 89 scored games: **conformity concentrates exactly where it is pathological
(79% vs 58.4% chance for seats with no private information), and three
prompt-level interventions moved nothing while two mechanical ones moved
everything.**

Full write-up with all numbers, confidence intervals, and an honest error log:
[STUDY.md](STUDY.md).

## The discipline this encodes

1. **Write the dice version first.** `mafia_null.py` plays the identical
   ruleset with random voters (20,000 games). Every number from the real runs
   is read against that chance level — the null killed this study's first
   headline before anyone else could.
2. **The referee is code.** State, roles, and legality never live inside a
   model; a move is a structured object the referee validates
   (`mafia_probe.py`).
3. **An experiment that cannot say what it spent is an anecdote.**
   `runlog.py` is a ledger with a stop cock: every call priced, budget checked
   *before* the call, `BudgetExceeded` raised rather than warned.
4. **Size the run before reading the direction.** n=20 at 28% power is a coin
   flip that produces a number; the study's own early findings died when the
   sample grew (`mafia_stats.py` carries the power and bootstrap machinery).

## Files

| file | role |
|---|---|
| `mafia_probe.py` | the game: referee, seats, ledger integration; local model via Ollama |
| `mafia_null.py` | the dice control: same rules, random voters, chance levels |
| `mafia_stats.py` | paired-arm statistics: bootstrap CIs, permutation tests, power |
| `runlog.py` | the ledger: per-call cost, budget stop cock, what-if repricing |
| `STUDY.md` | the full measured study, including everything it got wrong |

## Running

Needs Python 3.10+ and a local [Ollama](https://ollama.com) with a mid-size
model (the study used `qwen3:14b`); no paid APIs required — the whole study
cost $0.00 and 6.4 hours of desktop compute.

```sh
python3 mafia_null.py            # chance levels first — always first
python3 mafia_probe.py --games 20
python3 mafia_stats.py runs/
```

Provenance: extracted from a working personal multi-agent lab, 2026-08.
License: same as the repository.
