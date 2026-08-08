#!/usr/bin/env python3
"""Score recorded games — from the text, after the fact, by role.

Two corrections to how the probe measured itself, both forced by things we got
wrong:

**Conformity has to be conditional on role.** The probe reported one number for
the whole table. But if the mafia's best play is to keep its head down and back
whichever line is already forming, then a conforming mafioso is playing well
and a conforming townsperson is the failure. A single number adds those up and
cancels the finding. Town agreement is degeneration; mafia agreement is skill.

**Metrics belong downstream of the log, not inside the loop.** The first metric
this project wrote — agreement with the first ballot cast — measured the wrong
thing, and there was no stored text to re-score. Everything here reads
~/vb_runs/*.jsonl and can be rewritten and re-run for free.

    python3 tools/mafia_stats.py                 # every run
    python3 tools/mafia_stats.py ~/vb_runs/mafia-2026*.jsonl

What is measured, and what each measure is honestly worth:

  ballots        — clean. A vote is an accusation with no interpretation.
  mentions       — a proxy for attention, NOT for accusation. Naming someone
                   may be an attack or a defence; separating the two needs a
                   judge, and a judge needs validating. Reported as visibility.
  initiative     — who first put a name on the table in a round, versus who
                   joined a name already in play. This is the closest thing to
                   'aggression' that survives without a judge.
"""
import glob, json, pathlib, random, re, statistics, sys

RUNS = pathlib.Path.home() / "vb_runs"

# Chance level, from tools/mafia_null.py at 20 000 games per seat count. These
# are the identical statistics computed here, on dice instead of models — not
# approximations of them. Regenerate if the ruleset changes:
#     python3 tools/mafia_null.py --games 20000 --players 7
NULL = {
    7: {"crowd": .584, "conc": .424, "self": .052, "det": .219, "mafia_win": .921,
        "exec": .310},
    8: {"crowd": .600, "conc": .438, "self": .050, "det": .261, "mafia_win": .777,
        "exec": .316},
}


def perm_test(a, b, trials=20000, seed=0):
    """Difference of means, with a p-value that assumes nothing about shape.

    Counting metrics on a dozen games are small, skewed and bounded — a t-test
    would be borrowing assumptions we have not earned. Shuffling the labels
    costs nothing and answers the only question that matters: could this gap
    have come out of the same pot by luck?
    """
    if not a or not b:
        return float("nan"), float("nan")
    obs = statistics.fmean(a) - statistics.fmean(b)
    pool, na = list(a) + list(b), len(a)
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        rng.shuffle(pool)
        d = statistics.fmean(pool[:na]) - statistics.fmean(pool[na:])
        if abs(d) >= abs(obs):
            hits += 1
    return obs, (hits + 1) / (trials + 1)


def boot_ci(xs, trials=5000, seed=0):
    """95% interval by resampling — the honest width of a small sample."""
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(xs, k=len(xs)))
                   for _ in range(trials))
    return means[int(0.025 * trials)], means[int(0.975 * trials)]


def split(pairs):
    """[(value, flag)] -> (values where flag, values where not)"""
    return [v for v, f in pairs if f], [v for v, f in pairs if not f]


def forms(name):
    """Russian case forms, so 'Бориса' and 'Борису' count as Boris.

    Matching on a stem would be worse than useless here: 'Вера' → 'Вер' also
    matches 'верю' and 'неверно', which are among the commonest words at a
    Mafia table. Explicit endings, anchored on word boundaries.
    """
    if name.endswith("а"):
        s = name[:-1]
        return [s + e for e in ("а", "ы", "е", "у", "ой", "ою")]
    if name.endswith("я"):
        s = name[:-1]
        return [s + e for e in ("я", "и", "е", "ю", "ей", "ею")]
    return [name + e for e in ("", "а", "у", "ом", "е")]


def mentions(text, names):
    """Which of `names` this text refers to."""
    out = set()
    low = text.lower()
    for n in names:
        for f in forms(n):
            if re.search(r"\b" + re.escape(f.lower()) + r"\b", low):
                out.add(n)
                break
    return out


def load(path):
    rows = [json.loads(l) for l in pathlib.Path(path).read_text().splitlines() if l]
    g = {"path": path, "calls": [], "notes": [], "setup": None}
    for r in rows:
        if r.get("type") == "call":
            g["calls"].append(r)
        elif r.get("type") == "event":
            g["notes"].append(r)
            if r.get("kind") == "setup":
                g["setup"] = r
        elif r.get("type") == "run_end":
            g["end"] = r
    return g


def score(g):
    """One game -> a dict of measurements. Returns None if the log is unusable."""
    su = g["setup"]
    if not su or not g["calls"]:
        return None
    # runs recorded before the ledger stored text and ground truth cannot be
    # scored by these metrics — skip them rather than let them dilute the
    # numbers with silent zeroes
    if not any(n.get("kind") == "ballot" for n in g["notes"]):
        return None
    mafia = set(su["mafia"])
    det = su["detective"]
    everyone = set(su["players"])

    def role(n):
        return "мафия" if n in mafia else ("шериф" if n == det else "мирный")

    alive_at = {n["round"]: set(n["alive"])
                for n in g["notes"] if n.get("kind") == "round_open"}
    # `round_open` is written before the night, so the night's victim is listed
    # as alive but never gets a turn. Counting them as a player who "accused
    # nobody and was removed" is an artefact of the corpse, not a behaviour —
    # and it was strong enough to invert the first reading of whether accusers
    # get killed. Every talk-phase measurement uses the day roster instead.
    night_of = {}
    for n in g["notes"]:
        if n.get("kind") == "night_kill":
            night_of.setdefault(n["round"], set()).add(n["who"])
    day_alive = {r: v - night_of.get(r, set()) for r, v in alive_at.items()}
    ballots = [n for n in g["notes"] if n.get("kind") == "ballot" and n.get("vote")]
    kills = [n for n in g["notes"] if n.get("kind") in ("night_kill", "vote_out")]

    m = {"path": g["path"], "rounds": max(alive_at or {0: None}),
         "seats": len(everyone), "variant": su.get("variant", "base"),
         "seed": su.get("seed"),
         "winner": g.get("end", {}).get("winner", "?"),
         "usd": g.get("end", {}).get("usd", 0.0),
         "seconds": g.get("end", {}).get("seconds", 0.0)}

    # --- conformity, conditional on role -----------------------------------
    # For each round: did this ballot go to the round's modal target? Voting
    # with the crowd is what we want to separate by role.
    with_crowd = {"мафия": [0, 0], "мирный": [0, 0], "шериф": [0, 0]}
    conc = []
    for rnd in sorted({b["round"] for b in ballots}):
        rb = [b for b in ballots if b["round"] == rnd]
        tally = {}
        for b in rb:
            tally[b["vote"]] = tally.get(b["vote"], 0) + 1
        modal = max(tally.values())
        top = {n for n, c in tally.items() if c == modal}
        conc.append(modal / len(rb))
        for b in rb:
            r = b["role"]
            with_crowd[r][1] += 1
            if b["vote"] in top:
                with_crowd[r][0] += 1
    m["concentration"] = statistics.fmean(conc) if conc else None
    for r, (hit, tot) in with_crowd.items():
        m[f"crowd_{r}"] = hit / tot if tot else None
        m[f"n_{r}"] = tot

    # --- did the town ever hit a mafioso? ----------------------------------
    # Under random play the mafia wins 92% of the time, so win/loss carries
    # almost no signal. "Was a mafioso ever executed" does.
    outs = [n for n in kills if n["kind"] == "vote_out"]
    m["executions"] = len(outs)
    m["mafia_executed"] = sum(1 for n in outs if n["who"] in mafia)

    # --- mafia voting for its own ------------------------------------------
    mb = [b for b in ballots if b["role"] == "мафия"]
    m["mafia_self_vote"] = (sum(1 for b in mb if b["vote"] in mafia) / len(mb)
                            if mb else None)

    # --- did the detective act on what she knew? ---------------------------
    # The referee handed her the fact; the only question is whether the vote
    # followed it. Reconstructed from her own prompt, which named the fact.
    had = used = 0
    for b in ballots:
        if b["who"] != det:
            continue
        pr = next((c["prompt"] for c in g["calls"]
                   if c.get("phase") == "ballot" and c.get("who") == det
                   and c.get("round") == b["round"] and "prompt" in c), "")
        known = {n for n in mafia
                 if re.search(r"проверил " + n + r" — он мафия", pr)}
        known &= day_alive.get(b["round"], everyone)   # ballots are cast by day
        if known:
            had += 1
            if b["vote"] in known:
                used += 1
    m["det_had"] = had
    m["det_used"] = used

    # --- visibility and initiative, from the talk text ---------------------
    # Aggression proxy: how many living others a speaker names. Visibility:
    # how often a player is named by others. Both are attention, not polarity.
    talk = [c for c in g["calls"] if c.get("phase") == "talk" and "text" in c]
    named_by, names_others, first_namer, joined = {}, {}, 0, 0
    dead_mentions = tot_mentions = stale_mentions = 0
    for rnd in sorted({c["round"] for c in talk}):
        alive = day_alive.get(rnd, everyone)
        on_table = set()
        for c in sorted((c for c in talk if c["round"] == rnd),
                        key=lambda c: c["ts"]):
            who = c["who"]
            said = mentions(c["text"], everyone - {who})
            tot_mentions += len(said)
            # Naming a dead player is not by itself an error — the night's
            # victim is the single most legitimate topic at the table ("they
            # killed Боря, so he was dangerous to them"). Only a player who
            # died in an EARLIER round is stale, and even that is a hint rather
            # than proof, because the count cannot tell reminiscence from
            # suspicion. Reported split; never as one number.
            dead_mentions += len(said - alive)
            fresh_dead = night_of.get(rnd, set()) | {
                n["who"] for n in kills
                if n["kind"] == "vote_out" and n["round"] == rnd - 1}
            stale_mentions += len(said - alive - fresh_dead)
            live = said & alive
            names_others[who] = names_others.get(who, 0) + len(live)
            for t in live:
                named_by[t] = named_by.get(t, 0) + 1
            fresh = live - on_table
            if fresh and not on_table:
                first_namer += 1
            elif live and not fresh:
                joined += 1        # said only names already in play
            on_table |= live
    m["mentions_total"] = tot_mentions
    m["mentions_of_dead"] = dead_mentions
    m["mentions_stale"] = stale_mentions
    m["initiated"] = first_namer
    m["joined_existing"] = joined
    m["talk_turns"] = len(talk)

    # aggression by role, per turn
    for r in ("мафия", "мирный", "шериф"):
        seats = [n for n in everyone if role(n) == r]
        turns = [c for c in talk if role(c["who"]) == r]
        m[f"aggr_{r}"] = (sum(names_others.get(n, 0) for n in seats) / len(turns)
                          if turns else None)

    # --- who initiates, by role --------------------------------------------
    # The claim under test: a mafioso should avoid putting the first name on
    # the table and instead back a line that is already forming. Split the
    # initiative count by role or the question cannot be answered.
    init_by, join_by = {}, {}
    for rnd in sorted({c["round"] for c in talk}):
        alive = day_alive.get(rnd, everyone)
        on_table = set()
        for c in sorted((c for c in talk if c["round"] == rnd),
                        key=lambda c: c["ts"]):
            live = mentions(c["text"], everyone - {c["who"]}) & alive
            r = role(c["who"])
            if live - on_table:
                init_by[r] = init_by.get(r, 0) + 1
            elif live:
                join_by[r] = join_by.get(r, 0) + 1
            on_table |= live
    m["init_by"] = init_by
    m["join_by"] = join_by

    # --- two different hypotheses, deliberately kept apart ------------------
    # (a) VISIBILITY: being talked about precedes removal. This is close to
    #     tautological — the table discusses whom to execute and then executes
    #     whoever it discussed — so it is reported as a sanity check, not a
    #     finding.
    # (b) AGGRESSION: doing the accusing gets you removed LATER. That is the
    #     real claim, it is not tautological, and it needs the next round to
    #     test — "потом играет против тебя". Measured at both horizons so the
    #     difference between them is visible.
    vis_pairs, aggr_now, aggr_next = [], [], []
    counter, decay = [], []
    rounds = sorted(alive_at)
    vis_by_round = {}
    for i, rnd in enumerate(rounds):
        alive = day_alive[rnd]          # only players who lived to speak
        vis, aggr = {}, {}
        # speech order inside the round matters: a player named by an earlier
        # speaker can hit back on their own turn, and that is precisely the
        # behaviour under test
        seq = sorted((c for c in talk if c["round"] == rnd), key=lambda c: c["ts"])
        named_so_far = {}
        for c in seq:
            who = c["who"]
            under_fire = named_so_far.get(who, 0) > 0
            live = mentions(c["text"], alive - {who})
            aggr[who] = aggr.get(who, 0) + len(live)
            counter.append((len(live), under_fire))
            for t in live:
                vis[t] = vis.get(t, 0) + 1
                named_so_far[t] = named_so_far.get(t, 0) + 1
        vis_by_round[rnd] = vis
        # the only removal a day-alive player can suffer this round is the vote
        gone_now = {n["who"] for n in kills
                    if n["round"] == rnd and n["kind"] == "vote_out"}
        gone_next = {n["who"] for n in kills if n["round"] == rnd + 1}
        survived = alive - gone_now
        for p in alive:
            vis_pairs.append((vis.get(p, 0), p in gone_now))
            aggr_now.append((aggr.get(p, 0), p in gone_now))
        # only players who lived through this round can be killed in the next,
        # and only if there IS a next round on record
        if i + 1 < len(rounds):
            nxt = rounds[i + 1]
            for p in survived:
                aggr_next.append((aggr.get(p, 0), p in gone_next))
            # does hitting back buy you quiet? For everyone who came under fire
            # this round and lived, compare the pressure on them next round,
            # split by whether they answered aggressively.
            nvis = vis_by_round.get(nxt, {})
            for p in survived:
                if vis.get(p, 0) > 0 and p in day_alive.get(nxt, set()):
                    decay.append((nvis.get(p, 0) - vis[p], aggr.get(p, 0) > 0))
    m["vis_pairs"] = vis_pairs
    m["aggr_now"] = aggr_now
    m["aggr_next"] = aggr_next
    m["counter"] = counter
    m["decay"] = decay

    # --- do they say one thing and vote another? ---------------------------
    # At a real table the ballot is not obliged to match the speech, and the
    # gap is where the play lives — you talk up one suspect and quietly vote
    # someone else. We store speech and ballot as separate records, so this
    # costs nothing to ask of games already played.
    #
    # A player who names nobody is not concealing anything, they simply made
    # no public commitment; that is a third category, not a divergence.
    say_vote = {"мафия": [0, 0, 0], "мирный": [0, 0, 0], "шериф": [0, 0, 0]}
    for b in ballots:
        c = next((c for c in talk if c["round"] == b["round"]
                  and c["who"] == b["who"]), None)
        if not c:
            continue
        named = mentions(c["text"], day_alive.get(b["round"], everyone) - {b["who"]})
        r = b["role"]
        if not named:
            say_vote[r][2] += 1                      # silent
        elif b["vote"] in named:
            say_vote[r][0] += 1                      # voted what they said
        else:
            say_vote[r][1] += 1                      # voted someone else
    m["say_vote"] = say_vote

    # --- the sheriff's dilemma ---------------------------------------------
    # Holding a fact and announcing it are different decisions. Coming out
    # identifies you to the people you just accused, and they move at night.
    # Measured: how often she says it out loud, and what it costs her.
    reveal, reveal_cost = [], []
    for rnd in sorted(day_alive):
        if det not in day_alive[rnd]:
            continue
        pr = next((c["prompt"] for c in g["calls"]
                   if c.get("phase") == "ballot" and c.get("who") == det
                   and c.get("round") == rnd and "prompt" in c), "")
        known = {n for n in mafia
                 if re.search(r"проверил " + n + r" — он мафия", pr)} & day_alive[rnd]
        if not known:
            continue
        c = next((c for c in talk if c["round"] == rnd and c["who"] == det), None)
        if not c:
            continue
        said = bool(mentions(c["text"], known))
        reveal.append(said)
        gone_next = {n["who"] for n in kills if n["round"] == rnd + 1}
        if rnd + 1 in day_alive or gone_next:
            reveal_cost.append((float(det in gone_next), said))
    m["reveal"] = reveal
    m["reveal_cost"] = reveal_cost
    return m


def rate(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else float("nan")


def paired(a, b, trials=20000, seed=0):
    """Same seed, two arms — test the differences, not the two piles.

    Every arm replays the identical role assignment and the identical detective
    checks, so a game in one arm has a twin in the other. Comparing the piles
    throws that away and pays for it in noise; comparing the differences keeps
    it. The null here is that a difference is as likely to point one way as the
    other, so the shuffle flips signs rather than reassigning labels.
    """
    keys = sorted(set(a) & set(b))
    d = [a[k] - b[k] for k in keys if a[k] is not None and b[k] is not None]
    if len(d) < 3:
        return float("nan"), float("nan"), 0
    obs = statistics.fmean(d)
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        s = statistics.fmean(x if rng.random() < .5 else -x for x in d)
        if abs(s) >= abs(obs):
            hits += 1
    return obs, (hits + 1) / (trials + 1), len(d)


def compare(games):
    """Arm against arm, on the metrics the thesis actually rests on."""
    arms = {}
    for g in games:
        arms.setdefault(g["variant"], []).append(g)
    if len(arms) < 2:
        print("only one arm present — nothing to compare")
        return
    order = [v for v in ("base", "private", "agenda", "survival") if v in arms]
    order += [v for v in arms if v not in order]

    print("\n═══ ARMS ═══")
    print("  does any of this change how much the room agrees with itself?\n")
    hdr = f"  {'arm':<10} {'n':>3} {'town conf':>10} {'concentr':>9} " \
          f"{'mafia win':>10} {'aggr M−T':>9} {'dead ment':>10}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for v in order:
        gs = arms[v]
        tc = rate([g["crowd_мирный"] for g in gs if g.get("crowd_мирный") is not None])
        cc = rate([g["concentration"] for g in gs if g["concentration"] is not None])
        mw = sum(1 for g in gs if g["winner"] == "мафия") / len(gs)
        am = rate([g["aggr_мафия"] for g in gs if g.get("aggr_мафия") is not None])
        at = rate([g["aggr_мирный"] for g in gs if g.get("aggr_мирный") is not None])
        dm = sum(g["mentions_of_dead"] for g in gs) / max(1, sum(g["mentions_total"] for g in gs))
        print(f"  {v:<10} {len(gs):>3} {100*tc:>9.1f}% {100*cc:>8.1f}% "
              f"{100*mw:>9.0f}% {am-at:>+9.2f} {100*dm:>9.1f}%")

    if "base" not in arms:
        return
    print("\n  paired against base, same seeds (town conformity):")
    print("  a null result is only worth reading next to what the sample COULD")
    print("  have detected — an interval, never a bare 'no effect'")
    base = {g["seed"]: g["crowd_мирный"] for g in arms["base"]}
    for v in order:
        if v == "base":
            continue
        arm = {g["seed"]: g["crowd_мирный"] for g in arms[v]}
        d, p, n = paired(arm, base)
        if n < 3:
            print(f"    {v:<10} too few matched seeds ({n})")
            continue
        keys = sorted(set(arm) & set(base))
        diffs = [arm[k] - base[k] for k in keys
                 if arm[k] is not None and base[k] is not None]
        lo, hi = boot_ci(diffs)
        # smallest true effect this many pairs would catch 80% of the time,
        # from the observed spread — the honest ceiling on a negative
        sd = statistics.stdev(diffs) if len(diffs) > 1 else float("nan")
        mde = 2.8 * sd / (len(diffs) ** 0.5)
        if p < 0.05:
            verdict = "← moves it"
        else:
            verdict = f"← undetectable below ±{100*mde:.0f} pts at this n"
        print(f"    {v:<10} {100*d:+6.1f} pts  (95% CI {100*lo:+.0f} to {100*hi:+.0f})"
              f"  p = {p:.3f}  n={n}  {verdict}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    paths = args or sorted(glob.glob(str(RUNS / "mafia-*.jsonl")))
    games = [s for s in (score(load(p)) for p in paths) if s]
    if not games:
        print("no scorable runs — is ~/vb_runs populated?")
        return
    if "--compare" in flags:
        compare(games)
        return
    if "--base-only" in flags:
        games = [g for g in games if g["variant"] == "base"]
    n = len(games)
    seats = statistics.mode(g["seats"] for g in games)
    nul = NULL.get(seats, NULL[7])
    print(f"═══ {n} games scored from the logs ({seats} seats) ═══\n")

    print("CONFORMITY, BY ROLE  (share of ballots cast for the round's modal target)")
    print("  the whole point: town agreeing is degeneration, mafia agreeing is skill")
    for r in ("мирный", "шериф", "мафия"):
        vals = [g[f"crowd_{r}"] for g in games if g.get(f"crowd_{r}") is not None]
        tot = sum(g.get(f"n_{r}") or 0 for g in games)
        if vals:
            lo, hi = boot_ci(vals)
            print(f"    {r:<8} {100*rate(vals):5.1f}%   (95% CI {100*lo:.0f}–{100*hi:.0f}%,"
                  f" {tot} ballots)")
    print(f"    chance level for all of them: {100*nul['crowd']:.1f}%")
    cvals = [g["concentration"] for g in games if g["concentration"] is not None]
    lo, hi = boot_ci(cvals)
    print(f"    concentration {100*rate(cvals):.1f}% (95% CI {100*lo:.0f}–{100*hi:.0f}%)"
          f"   · chance {100*nul['conc']:.1f}%")

    print("\nTOWN EFFECTIVENESS")
    ex = sum(g["executions"] for g in games)
    mx = sum(g["mafia_executed"] for g in games)
    print(f"    executions {ex}, of which mafia {mx}  →  {100*mx/max(1,ex):.0f}% hit rate"
          f"   · chance {100*nul['exec']:.0f}%")
    print(f"    games where town ever executed a mafioso: "
          f"{sum(1 for g in games if g['mafia_executed'])}/{n}")
    wins = [g["winner"] for g in games]
    print(f"    mafia won {wins.count('мафия')}/{n} ({100*wins.count('мафия')/n:.0f}%)"
          f"   · chance {100*nul['mafia_win']:.0f}%")

    print("\nINFORMATION USE")
    had = sum(g["det_had"] for g in games)
    used = sum(g["det_used"] for g in games)
    print(f"    detective held a live 'X is mafia' fact on {had} ballots, "
          f"voted it {used} times" + (f"  ({100*used/had:.0f}%)" if had else ""))
    print(f"    chance {100*nul['det']:.0f}%")
    svals = [g["mafia_self_vote"] for g in games if g["mafia_self_vote"] is not None]
    lo, hi = boot_ci(svals)
    print(f"    mafia voted for its own team {100*rate(svals):.1f}% "
          f"(95% CI {100*lo:.0f}–{100*hi:.0f}%)   · chance {100*nul['self']:.1f}%")

    print("\nDOES THE MAFIA HIDE?  (initiative vs backing a line already in play)")
    print("  the claim: a mafioso should avoid naming first and ride the obvious line")
    for r in ("мирный", "шериф", "мафия"):
        ini = sum(g["init_by"].get(r, 0) for g in games)
        joi = sum(g["join_by"].get(r, 0) for g in games)
        tot = ini + joi
        if tot:
            print(f"    {r:<8} opened {ini:>3}  ·  joined {joi:>3}  →  "
                  f"{100*ini/tot:4.0f}% of its speaking turns opened a new name")
    print("    aggression per talk turn (living others named):")
    for r in ("мирный", "шериф", "мафия"):
        vals = [g[f"aggr_{r}"] for g in games if g.get(f"aggr_{r}") is not None]
        lo, hi = boot_ci(vals)
        print(f"      {r:<8} {rate(vals):.2f}   (95% CI {lo:.2f}–{hi:.2f})")
    tv = [g["aggr_мафия"] for g in games if g.get("aggr_мафия") is not None]
    cv = [g["aggr_мирный"] for g in games if g.get("aggr_мирный") is not None]
    d, p = perm_test(tv, cv)
    print(f"    mafia minus town: {d:+.2f}  ·  p = {p:.3f}"
          f"   {'← distinguishable' if p < 0.05 else '← not distinguishable'}")

    print("\nTALKING ABOUT THE DEAD")
    tm = sum(g["mentions_total"] for g in games)
    dm = sum(g["mentions_of_dead"] for g in games)
    sm = sum(g["mentions_stale"] for g in games)
    print(f"    named someone already removed: {dm}/{tm} ({100*dm/max(1,tm):.1f}%)")
    print(f"      of those, freshly killed — a legitimate topic: {dm-sm}")
    print(f"      dead for more than a round — stale: {sm} "
          f"({100*sm/max(1,tm):.1f}% of all mentions)")

    print("\nSANITY CHECK: being talked about precedes removal")
    print("  near-tautological — the table discusses whom to execute, then does it")
    k, l = split([p for g in games for p in g["vis_pairs"]])
    d, p = perm_test(k, l)
    print(f"    mentioned, removed that round: {rate(k):.2f} (n={len(k)})   "
          f"survived: {rate(l):.2f} (n={len(l)})   diff {d:+.2f}, p = {p:.3f}")

    print("\nSAYING ONE THING AND VOTING ANOTHER")
    print("  at a real table the ballot need not match the speech — that gap is the play")
    for r in ("мирный", "шериф", "мафия"):
        same = sum(g["say_vote"][r][0] for g in games)
        diff = sum(g["say_vote"][r][1] for g in games)
        mute = sum(g["say_vote"][r][2] for g in games)
        spoke = same + diff
        if spoke:
            print(f"    {r:<8} voted what they said {same:>3}  ·  voted someone else "
                  f"{diff:>3}  →  {100*diff/spoke:4.0f}% divergence"
                  f"   (named nobody: {mute})")

    print("\nTHE SHERIFF'S DILEMMA  (holding a fact vs announcing it)")
    rv = [x for g in games for x in g["reveal"]]
    if rv:
        print(f"    named her checked mafioso out loud: {sum(rv)}/{len(rv)} "
              f"({100*sum(rv)/len(rv):.0f}% of the chances she had)")
    k, l = split([p for g in games for p in g["reveal_cost"]])
    if k and l:
        d, p = perm_test(k, l)
        print(f"    removed next round after speaking up: {100*rate(k):.0f}% (n={len(k)})")
        print(f"    after staying quiet:                  {100*rate(l):.0f}% (n={len(l)})"
              f"   diff {100*d:+.0f} pts, p = {p:.3f}")

    print("\nDO THEY HIT BACK?  (aggression on your turn, given you were just named)")
    print("  the observed human tactic: come under suspicion, escalate hard")
    k, l = split([p for g in games for p in g["counter"]])
    if k and l:
        d, p = perm_test(k, l)
        print(f"    named before your turn: {rate(k):.2f} names back (n={len(k)})")
        print(f"    not named:              {rate(l):.2f} (n={len(l)})   "
              f"diff {d:+.2f}, p = {p:.3f}")

    print("\nDOES HITTING BACK BUY QUIET?  (change in pressure the following round)")
    print("  the other half: people stop pressing whoever fights back")
    k, l = split([p for g in games for p in g["decay"]])
    if k and l:
        d, p = perm_test(k, l)
        print(f"    answered aggressively: pressure {rate(k):+.2f} next round (n={len(k)})")
        print(f"    stayed quiet:          pressure {rate(l):+.2f} (n={len(l)})   "
              f"diff {d:+.2f}, p = {p:.3f}")

    print("\nHYPOTHESIS: doing the accusing gets you killed — LATER")
    print("  this one is not tautological, and the horizon is the whole point")
    for label, key in (("same round", "aggr_now"), ("next round", "aggr_next")):
        k, l = split([p for g in games for p in g[key]])
        if not k or not l:
            continue
        d, p = perm_test(k, l)
        verdict = "← real on this sample" if p < 0.05 else "← noise on this sample"
        print(f"    {label:<11} accused {rate(k):.2f} before being removed "
              f"(n={len(k)})  ·  {rate(l):.2f} if not (n={len(l)})   "
              f"diff {d:+.2f}, p = {p:.3f}  {verdict}")

    usd = sum(g["usd"] for g in games)
    secs = sum(g["seconds"] for g in games)
    print(f"\ncost of all of it: ${usd:.4f}, {secs/60:.0f} min of model time")


if __name__ == "__main__":
    main()
