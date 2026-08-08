#!/usr/bin/env python3
"""The control condition: the same table, played by dice.

Every number the probe reports is meaningless until we know what the same
number looks like when nobody is thinking. "Herding dropped to 25–33%" sounds
like an improvement; with five candidates on the ballot, pure chance produces
about 25% agreement. So that headline may be describing a table of coin flips.

This plays the identical ruleset with random voters — same referee, same
rotation, same tie-breaks, no model — and reports the distribution each metric
takes under the null. Any claim about the models has to beat this, with a
margin wider than the spread.

    python3 tools/mafia_null.py --games 5000 --players 7

It also implements the metric the probe should have used. `herd_first` counts
ballots matching the FIRST one cast, which reports 0% for a round where four of
five voted together but the first voter was the outlier — that happened in a
real run. `concentration` — the modal vote's share — measures the bandwagon
regardless of who spoke first.
"""
import argparse, random, statistics

from mafia_probe import Game


def one_game(names, n_mafia, rng, max_rounds=6):
    """The probe's flow with the models removed and dice in their place."""
    g = Game(names, n_mafia, rng)
    m = {"ballots": 0, "herd_first": 0, "conc": [], "crowd": [], "mafia_self": 0,
         "det_had_fact": 0, "det_used_fact": 0}

    while g.round < max_rounds and not g.over():
        g.round += 1
        killers = sorted(g.mafia & g.alive)
        if killers:
            victim = rng.choice(sorted(g.alive - g.mafia))
            g.alive.discard(victim)
        if g.over():
            break

        # the detective checks someone at random — as in the probe, which means
        # her usefulness is partly luck and has to be counted as such
        known_mafia = set()
        if g.detective in g.alive:
            suspect = rng.choice(sorted(g.alive - {g.detective}))
            if suspect in g.mafia:
                g.facts.setdefault(g.detective, []).append(suspect)
        known_mafia = {s for s in g.facts.get(g.detective, []) if s in g.alive}

        order = sorted(g.alive)
        order = order[g.round % len(order):] + order[:g.round % len(order)]

        votes, first = {}, None
        for who in order:
            others = [n for n in order if n != who]
            if not others:
                continue
            v = rng.choice(others)          # <- the null: no reasoning at all
            votes[who] = v
            m["ballots"] += 1
            if first is None:
                first = v
            elif v == first:
                m["herd_first"] += 1
            if who in g.mafia and v in g.mafia:
                m["mafia_self"] += 1
            if who == g.detective and known_mafia:
                m["det_had_fact"] += 1
                if v in known_mafia:
                    m["det_used_fact"] += 1

        if votes:
            tally = {}
            for v in votes.values():
                tally[v] = tally.get(v, 0) + 1
            m["conc"].append(max(tally.values()) / len(votes))
            top = max(tally.values())
            # the same statistic mafia_stats computes on real games — share of
            # ballots landing on the round's modal target. A comparator has to
            # be the identical measurement or it is decoration.
            winners = {n for n, c in tally.items() if c == top}
            m.setdefault("crowd", []).append(
                sum(1 for v in votes.values() if v in winners) / len(votes))
            picked = sorted(n for n, c in tally.items() if c == top)
            out = picked[0] if len(picked) == 1 else rng.choice(picked)
            # what share of executions land on a mafioso when nobody reasons.
            # This is the only honest yardstick for "the town is good at this",
            # because the mafia's share of the living rises as townsfolk are
            # removed — a hit rate has to be read against that drift, not
            # against the opening ratio.
            m.setdefault("exec", []).append(out in g.mafia)
            g.alive.discard(out)

    m["winner"] = g.over() or "none"
    m["rounds"] = g.round
    return m


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=5000)
    ap.add_argument("--players", type=int, default=7)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    pool = ["Аня", "Борис", "Вера", "Глеб", "Дина", "Егор", "Жанна", "Захар"]
    names = pool[:a.players]
    n_mafia = 2 if a.players >= 6 else 1
    rng = random.Random(a.seed)

    herd, conc, wins, rounds, selfvote, det = [], [], [], [], [], []
    crowd, execs = [], []
    for _ in range(a.games):
        m = one_game(names, n_mafia, rng)
        if m["ballots"]:
            herd.append(m["herd_first"] / m["ballots"])
            selfvote.append(m["mafia_self"] / m["ballots"])
        conc += m["conc"]
        crowd += m["crowd"]
        execs += m.get("exec", [])
        wins.append(m["winner"])
        rounds.append(m["rounds"])
        if m["det_had_fact"]:
            det.append(m["det_used_fact"] / m["det_had_fact"])

    n = a.games
    print(f"null model · {n} games · {a.players} seats, {n_mafia} mafia\n")
    print("Every claim about the models must clear these, by more than the spread.\n")

    def row(label, xs, unit="%"):
        if not xs:
            print(f"  {label:<34} n/a")
            return
        mean = statistics.fmean(xs)
        lo, hi = pct(xs, 0.05), pct(xs, 0.95)
        k = 100 if unit == "%" else 1
        print(f"  {label:<34} {mean*k:6.1f}{unit}   "
              f"(90% of games: {lo*k:.0f}–{hi*k:.0f}{unit})")

    row("executions landing on a mafioso", [float(x) for x in execs])
    row("herd vs first ballot", herd)
    row("ballots on the modal target", crowd)
    row("vote concentration (modal share)", conc)
    row("mafia voting for own team", selfvote)
    row("detective votes a known mafioso", det)
    print(f"  {'mafia win rate':<34} "
          f"{100*wins.count('мафия')/n:6.1f}%")
    print(f"  {'median rounds':<34} {statistics.median(rounds):6.1f}")

    print("\nreading it:")
    print("  · herd ≈ 1/(seats−1) by construction — a measured 25–33% is at chance.")
    print("  · a detective who votes her own fact at the chance rate is not using it.")
    print("  · mafia win rate here is the ruleset's balance, not anyone's skill.")


if __name__ == "__main__":
    main()
