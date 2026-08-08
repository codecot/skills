#!/usr/bin/env python3
"""A ledger for experiments: every model call, what it cost, and a stop cock.

An experiment that cannot say what it spent is not an experiment, it is an
anecdote. This records one line per call — who asked, in which phase, how many
tokens each way, how long, how much — so that a run can be priced afterwards
and two runs can be compared. The same ledger takes local calls (price zero,
seconds real) and paid ones, because the point of the Mafia probe is exactly
that comparison.

The stop cock is the other half. `check()` is called BEFORE a call, not after,
and raises rather than warns — a budget that only reports the overrun is a
receipt, not a brake.

    led = Ledger("mafia", budget_usd=0.50, max_calls=200)
    led.check()                       # raises BudgetExceeded, no call is made
    led.record(model="qwen3:14b", phase="talk", who="Аня",
               tokens_in=812, tokens_out=96, seconds=6.1)
    print(led.report())

Lines go to ~/vb_runs/<run-id>.jsonl — personal telemetry, like the personas
and the audio library, never into the repository.
"""
import json, os, pathlib, time

RUN_ROOT = pathlib.Path(os.environ.get("VB_RUNS", pathlib.Path.home() / "vb_runs"))

# USD per million tokens, (input, output). Local models bill in electricity and
# patience, which the ledger tracks as seconds instead.
#
# Checked against the published rates on 2026-08-03. Anything not listed here is
# recorded at zero and flagged in the report, so an unknown model shows up as a
# hole in the accounting rather than as a silent free lunch.
PRICES = {
    "claude-fable-5":    (10.00, 50.00),
    "claude-opus-5":     (5.00, 25.00),
    "claude-opus-4-8":   (5.00, 25.00),
    "claude-sonnet-5":   (3.00, 15.00),   # intro 2.00/10.00 through 2026-08-31
    "claude-haiku-4-5":  (1.00, 5.00),
    "gpt-oss:20b":       (0.0, 0.0),
    "qwen3:14b":         (0.0, 0.0),
    "llama3.2":          (0.0, 0.0),
}

# Cache multipliers on the input rate (Anthropic): a read is a tenth, a write a
# quarter more than the plain rate. Carried here so the room loop can turn
# caching on later without the ledger having to be rewritten.
CACHE_READ = 0.10
CACHE_WRITE = 1.25


class BudgetExceeded(RuntimeError):
    """The stop cock. Raised before a call, never after."""


def price(model, tokens_in=0, tokens_out=0, cache_read=0, cache_write=0):
    """USD for one call. Unknown model -> 0.0, and the report says so."""
    rate = PRICES.get(model)
    if rate is None:
        return 0.0
    pin, pout = rate
    usd = tokens_in * pin + tokens_out * pout
    usd += cache_read * pin * CACHE_READ + cache_write * pin * CACHE_WRITE
    return usd / 1_000_000


class Ledger:
    def __init__(self, name, budget_usd=None, max_calls=None, max_seconds=None,
                 run_id=None, tag="", root=RUN_ROOT):
        self.name = name
        self.budget_usd = budget_usd
        self.max_calls = max_calls
        self.max_seconds = max_seconds
        self.tag = tag
        self.run_id = run_id or f"{name}-{time.strftime('%Y%m%d-%H%M%S')}"
        self.calls = []
        self.unknown_models = set()
        self.started = time.time()
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / f"{self.run_id}.jsonl"
        self._write({"type": "run_start", "run": self.run_id, "name": name,
                     "tag": tag, "ts": time.time(),
                     "budget_usd": budget_usd, "max_calls": max_calls,
                     "max_seconds": max_seconds})

    # --- accounting
    def _write(self, obj):
        with self.path.open("a") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    @property
    def spent(self):
        return sum(c["usd"] for c in self.calls)

    @property
    def seconds(self):
        return sum(c["seconds"] for c in self.calls)

    def check(self, note=""):
        """Call this before spending. Raises instead of warning — on purpose."""
        if self.max_calls is not None and len(self.calls) >= self.max_calls:
            raise BudgetExceeded(
                f"call cap reached: {len(self.calls)}/{self.max_calls}" +
                (f" ({note})" if note else ""))
        if self.budget_usd is not None and self.spent >= self.budget_usd:
            raise BudgetExceeded(
                f"budget reached: ${self.spent:.4f}/${self.budget_usd:.2f}" +
                (f" ({note})" if note else ""))
        if self.max_seconds is not None and self.seconds >= self.max_seconds:
            raise BudgetExceeded(
                f"time cap reached: {self.seconds:.0f}s/{self.max_seconds:.0f}s" +
                (f" ({note})" if note else ""))

    def record(self, model, seconds, tokens_in=0, tokens_out=0,
               cache_read=0, cache_write=0, thinking_tokens=0,
               prompt=None, text=None, **meta):
        """One thinking act: what it was, what it cost, whether it landed.

        `meta` is free-form and is what makes a run answerable afterwards —
        phase, seat, role, round, whether the move parsed. Record the failures
        too; a retry that costs money is part of the price of the design.

        `prompt` and `text` are the exchange itself, and they are the reason a
        metric can be *changed after the run*. The first version of this ledger
        stored counts only, and the first metric we wrote turned out to measure
        the wrong thing — with no text there was nothing to re-score, and three
        games of local compute were lost. Numbers can be recomputed from text;
        text cannot be recovered from numbers.
        """
        if model not in PRICES:
            self.unknown_models.add(model)
        usd = price(model, tokens_in, tokens_out, cache_read, cache_write)
        row = {"type": "call", "ts": time.time(), "model": model,
               "seconds": round(seconds, 3), "tokens_in": tokens_in,
               "tokens_out": tokens_out, "cache_read": cache_read,
               "cache_write": cache_write, "thinking_tokens": thinking_tokens,
               "usd": usd, **meta}
        if text is not None:
            row["text"] = text
        if prompt is not None:
            row["prompt"] = prompt
        self.calls.append(row)
        self._write(row)
        return row

    def note(self, **fields):
        """A non-call event worth keeping next to the calls — a kill, a verdict."""
        self._write({"type": "event", "ts": time.time(), **fields})

    # --- reading back
    def by(self, key):
        out = {}
        for c in self.calls:
            k = c.get(key, "?")
            g = out.setdefault(k, {"calls": 0, "usd": 0.0, "seconds": 0.0,
                                   "tokens_in": 0, "tokens_out": 0})
            g["calls"] += 1
            g["usd"] += c["usd"]
            g["seconds"] += c["seconds"]
            g["tokens_in"] += c["tokens_in"]
            g["tokens_out"] += c["tokens_out"]
        return out

    def close(self, **outcome):
        self._write({"type": "run_end", "ts": time.time(),
                     "calls": len(self.calls), "usd": self.spent,
                     "seconds": self.seconds, "wall": time.time() - self.started,
                     **outcome})

    def report(self, group="phase"):
        if not self.calls:
            return f"{self.run_id}: no calls recorded"
        n = len(self.calls)
        tin = sum(c["tokens_in"] for c in self.calls)
        tout = sum(c["tokens_out"] for c in self.calls)
        wall = time.time() - self.started
        lines = [f"── ledger {self.run_id}" + (f" [{self.tag}]" if self.tag else ""),
                 f"   calls {n}  ·  in {tin:,} tok  ·  out {tout:,} tok",
                 f"   model time {self.seconds:.0f}s ({self.seconds/n:.1f}s per call)"
                 f"  ·  wall {wall:.0f}s",
                 f"   spent ${self.spent:.4f}" +
                 (f" of ${self.budget_usd:.2f}" if self.budget_usd else "")]
        groups = self.by(group)
        if len(groups) > 1:
            lines.append(f"   by {group}:")
            for k, g in sorted(groups.items(), key=lambda kv: -kv[1]["usd"]):
                lines.append(f"     {k:<12} {g['calls']:>3} calls  "
                             f"{g['seconds']:>6.0f}s  ${g['usd']:.4f}")
        if self.unknown_models:
            lines.append("   ! no price for: " + ", ".join(sorted(self.unknown_models))
                         + " — counted as free, add it to PRICES")
        lines.append(f"   {self.path}")
        return "\n".join(lines)

    # --- what would this run have cost elsewhere
    def what_if(self, model):
        """Re-price the same token traffic on another model.

        The whole reason the Mafia probe ran locally was to find out whether it
        was worth paying for. This answers that from measured tokens rather than
        from a guess.
        """
        tin = sum(c["tokens_in"] for c in self.calls)
        tout = sum(c["tokens_out"] for c in self.calls)
        return price(model, tin, tout)


def replay(path):
    """Read a run back. `python3 tools/runlog.py ~/vb_runs/<id>.jsonl`"""
    rows = [json.loads(l) for l in pathlib.Path(path).read_text().splitlines() if l]
    calls = [r for r in rows if r.get("type") == "call"]
    if not calls:
        print("no calls in", path)
        return
    tin = sum(c["tokens_in"] for c in calls)
    tout = sum(c["tokens_out"] for c in calls)
    usd = sum(c["usd"] for c in calls)
    secs = sum(c["seconds"] for c in calls)
    print(f"{pathlib.Path(path).stem}: {len(calls)} calls, "
          f"{tin:,} in / {tout:,} out, {secs:.0f}s, ${usd:.4f}")
    print("\nsame traffic priced elsewhere:")
    for m in ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"):
        print(f"  {m:<18} ${price(m, tin, tout):.4f}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        replay(sys.argv[1])
    else:
        runs = sorted(RUN_ROOT.glob("*.jsonl")) if RUN_ROOT.exists() else []
        if not runs:
            print(f"no runs under {RUN_ROOT}")
        for p in runs[-20:]:
            print(p)
