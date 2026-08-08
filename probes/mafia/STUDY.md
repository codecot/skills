# Why a room of models agrees with itself: a measured study

Status: **in progress**, 03.08.2026. Base and three ablation arms complete;
coalitions and recruitment not started. This document is the record of the
whole line of work, written so it can be picked up cold.

This study grew out of a private tool's "rooms" feature (several models in one
conversation); the tools in this folder are the complete, self-contained
instrument — referee, null model, and statistics.

---

## 1. Where this started, and how it turned into a game

The room feature (see the companion spec) was meant to put several models —
possibly from several providers — into one conversation: a committee, a design
review, a panel. The expectation behind it, stated plainly so it can be judged
later:

> Give each seat its own persona and its own brief, and each voice will push
> its own line. The room will argue, and the argument will be worth reading.

It does not. Rooms converge: seats paraphrase each other, the second speaker
agrees with the first, and by the third turn there is one position wearing
several names. That is the failure this study exists to characterise.

Mafia was chosen as the instrument, not the subject. It is the smallest game
that contains everything a room needs — asymmetric information, a reason to
misrepresent, a decision with consequences, and a ground truth the referee
knows and the participants do not. Crucially it makes disagreement *scoreable*:
in a committee you cannot tell a bad consensus from a good one; in Mafia you
can, because someone is lying and the referee knows who.

So the question moved from "does the room feel alive" to something answerable:
**does the table's agreement carry any information, or is it agreement for its
own sake?**

## 2. Apparatus

Four files under `tools/`, all local, no paid calls anywhere (§7).

| file | what it is |
|---|---|
| `mafia_probe.py` | the game. Referee in code — `view(who)` / move validation / `over()`. Four room variants (§5). |
| `runlog.py` | the ledger. One JSONL line per model call: phase, seat, role, round, prompt, response, tokens, seconds, price. Budget/call/time caps that **refuse before the call**. |
| `mafia_null.py` | the control. The identical ruleset played by dice, 20 000 games, reporting the *same statistics* as the real scorer. |
| `mafia_stats.py` | the scorer. Reads the logs after the fact; role-conditioned metrics, bootstrap intervals, permutation and paired tests. |

Run:

```sh
python3 tools/mafia_probe.py --players 7 --seed 201 --variant base
python3 tools/mafia_null.py  --games 20000 --players 7
python3 tools/mafia_stats.py --base-only          # or --compare
```

Data lives in `~/vb_runs/*.jsonl` — personal telemetry, outside the repository,
like the personas and the audio library. Present size: 206 games, 9.2 MB.

### Design decisions worth keeping

**The referee is code.** State, roles, legality and the ledger never live
inside a model. A move is a structured object the referee validates, never a
sentence the referee interprets — see §6, where the first version of this cost
us a wrongly killed player.

**Metrics live downstream of the log.** The scorer reads stored text and can be
rewritten and re-run for free. This is not tidiness; three of our metrics
turned out to measure the wrong thing (§6), and without stored text each
correction would have cost a fresh run.

**Arms are paired by seed.** Every variant replays the identical role
assignment and the identical detective checks, so each game has a twin in every
other arm and the test is on the differences. Disposition assignment is
deliberately deterministic rather than drawn, so that it does not consume the
random stream and break the pairing.

## 3. The control, and why it is the point

No number here means anything without knowing what the same number looks like
when nobody is thinking. The null model plays the same rules with random
voters. At 7 seats, 2 mafia:

| statistic | chance |
|---|---|
| ballots on the round's modal target | 58.4% |
| vote concentration | 42.4% |
| executions landing on a mafioso | 31.0% |
| detective votes a mafioso she knows | 21.9% |
| mafia voting for its own team | 5.2% |
| **mafia win rate** | **92.1%** |

That last row matters for reading everything else: the ruleset is lopsided, so
winning or losing carries almost no signal. "Did the town ever execute a
mafioso" is the honest outcome measure, not "who won".

The control earns its keep immediately. Our first headline — "separating the
vote from the speech cut herding from 67% to 25–33%" — describes a number that
sits **inside the null's 90% interval**. The defensible claim is not that
herding fell to 25–33%; it is that the bandwagon was eliminated, down to
chance. Same fact, very different sentence.

## 4. What the base arm shows

89 games, 7 seats, 2 mafia + detective, qwen3:14b, all local.

### Agreement is concentrated where it is pathological

| role | ballots on the modal target | 95% CI | n |
|---|---|---|---|
| **townsperson** | **79.0%** | 75–82 | 427 |
| mafia | 68.4% | 62–75 | 245 |
| detective | 65.8% | 55–75 | 105 |
| *chance* | *58.4%* | | |

Vote concentration 69.6% (CI 67–72) against a chance level of 42.4%.

The town — the only seats with no private information and no reason to differ —
is the only group clearly above chance. The mafia and the detective, who both
hold something the others do not, sit near it. **Conformity appears exactly
where it is a defect and is absent where it would have been skill.**

This is the central result. It also reframes the phenomenon: unanimity among
identically-informed, identically-paid agents is not a failure of intelligence.
It is the correct response to a room where there is nothing to disagree about.

### Private information works; that is what makes the rest damning

The detective votes a mafioso she has been shown **84% of the time (37/44)
against a chance level of 22%**. This is the largest effect in the study. The
channel is not broken. Information given by the referee reaches the seat that
should have it and changes what that seat does.

So the convergence is not "models can't". It is a property of the room.

### The mafia does not play like mafia

- Votes for its **own team 14.7%** of the time (chance 5.2%) — nearly three
  times chance. It follows the crowd onto its own partner.
- Opens a new name on 37% of its speaking turns, the town on 38% — it does not
  keep its head down.
- Aggression per turn 0.79 vs the town's 0.83, **not distinguishable** (p=0.59).
- Says one thing and votes another on 18% of turns; the town does it on 15%.
  The gap between word and ballot — where a human table's play lives — is the
  same for the deceiver as for the honest player. It is noise, not tactic.

### The detective does not manage her risk, and is not punished for it

She names her checked mafioso out loud in **66% of the chances she has**. And
it costs her nothing measurable: removed the next round 23% of the time after
speaking up, 33% after staying quiet (p=0.70, and underpowered either way).

A competent mafia kills a revealed detective every time. This one does not
react to the single most important public statement in the game.

### Outcomes

Executions land on a mafioso 43% of the time against 31% by chance; the mafia
wins 81% of games against 92% by chance. The town is better than dice, but not
by much, and the gap is much smaller than the detective's 84%-vs-22% would lead
you to expect. Good information enters the room and mostly fails to convert.

## 5. Three interventions that changed nothing

Each arm is 7 seats, paired against base on identical seeds.

| arm | what changed | Δ town conformity | 95% CI | p | n pairs |
|---|---|---|---|---|---|
| `private` | transcript window 24 → 6 messages | −2.8 pts | −13 … +7 | 0.61 | 20 |
| `agenda` | a different disposition per seat | −1.1 pts | −12 … +9 | 0.84 | 20 |
| `survival` | town told it is paid to last, not to be right | −2.7 pts | −8 … +2 | 0.31 | 76 |

**`private`** tested whether the shared transcript simply drowns the persona by
volume and recency. It does not appear to.

**`agenda`** tested the founding expectation from §1 directly. It was made a
*generous* test on purpose: several dispositions are anti-conformist by
construction ("you distrust whoever repeats others", "you do not change your
mind under pressure"). The table converged anyway.

**`survival`** was meant to break the symmetry of objectives, and at n=20 it
looked like it did — −7.0 points, with the mafia's win rate dropping from 95%
to 80%. At n=76 the effect was −2.7 points, p=0.31, and the win-rate difference
−4.7 points, p=0.65. **The first reading was noise**, exactly the regression an
underpowered first look invites.

Note what `survival` actually was: a *stated* payoff in the prompt. The referee
still scored the game the same way; nothing in the mechanics paid for surviving.
So it belongs with the other two — it was another prompt-level intervention
wearing a mechanism's clothes.

### The thesis the data supports

Three things changed in the prompt: nothing moved. Two things changed in the
mechanics — a private fact issued by the referee, and a secret ballot as a
separate move — and both moved everything.

> **Change the mechanics and behaviour changes. Change the prompt and it does
> not.** Divergence in a room is not requested from the model; it is built into
> the rules.

Stated as a bound rather than a slogan: at these sample sizes an effect larger
than ±7 points (survival) or ±15 points (the other two) would have been
detected. Smaller effects are not excluded. The claim is that prompt-level
differentiation produces no *large* effect — not that it produces none.

## 6. Everything we got wrong, and how

This section is the most reusable part of the study. Five errors, all caught
before publication, four of them in our own instruments.

1. **A move parsed out of prose killed the wrong player.** The first probe took
   "the last name mentioned" as the victim; the model opened by echoing the
   list of living players. Fixed with a required marker line — after which 9 of
   13 ballots came back with no marker at all, because a local model asked for
   prose and a format in one breath returns prose. One retry asking for nothing
   but a name recovers them.

2. **Herding was measured against the first ballot cast.** In a round where
   four of five voted together but the first voter was the outlier, this
   reported 0%. Replaced by the modal-vote share.

3. **Corpses in the denominator manufactured a significant result.** The alive
   roster was recorded at round open, i.e. *before* the night kill, so the
   night's victim counted as a player who "accused nobody and was removed" —
   their aggression is zero by construction. This produced "the passive get
   killed" at p=0.000. With the day roster it is p=0.14. The finding was an
   artefact of the dead.

4. **"48% of mentions name a dead player" was meaningless.** Naming the night's
   victim is the single most legitimate topic at the table. Split properly:
   39.9% of mentions are of removed players, but only **7.8%** are of players
   dead longer than a round — and even that is a hint, not proof, because a
   mention count cannot tell reminiscence from suspicion.

5. **Two findings did not survive their own sample growing.**
   - "They hit back when named" — 0.82 vs 0.57 at p=0.030 on 33 games; 0.78 vs
     0.74 at p=0.55 on 89. Gone.
   - The `survival` arm, above.

   Both were read as signal at n≈20–30 by the same person who had already run
   the power calculation showing n=20 has **28% power**. Under-powered first
   looks are not weak evidence; they are a coin flip that produces a number.

6. **One anecdote we had promoted to a finding.** The companion spec records
   that the detective announced "Борис is mafia" and the mafia killed her the
   next night. It happened. As a pattern it does not exist (§4). One memorable
   game is not a result.

Standing rules that came out of this: state the chance level next to every
number; report a null as an interval and a minimum detectable effect, never as
"no effect"; size the run *before* reading the direction.

## 7. Constraints held throughout

- **Local only.** The single network address in any of the four tools is
  `http://127.0.0.1:11434/api/chat`. ollama listens on loopback, not `0.0.0.0`.
- **One model:** `qwen3:14b`, digest `bdbd181c33f2ed1b`, 14.8B Q4_K_M — all
  4 400 calls of it.
- **Zero paid calls**, verified from the ledger: `$0.000000`. The paid-model
  prices in `runlog.py` exist only to re-price measured token traffic
  arithmetically (`--what-if claude-opus-5`); they never dial out.
- **Total:** 4 400 calls, 2.17M input / 123k output tokens, 6.4 hours of model
  time, no money.

For reference, the same traffic on a frontier model would be roughly $0.15 per
seven-seat game, and would run in about the same wall-clock time — the
bottleneck is the number of sequential turns, not the speed of any one of them.
Secret ballots parallelise; speeches do not.

## 8. Open, and what to do next

The mechanics below come from how *The Traitors* actually runs, and they are
ranked by expected effect on the measured defect. All are referee-side, which
is where §5 says the lever is.

1. **Coalition talk — private sub-channels.** Today there are exactly two
   channels: everyone-sees-everything, plus the mafia's conclave. A real table
   negotiates in twos and threes before the vote. This destroys the symmetry of
   information among townsfolk *by construction*, which §4 identifies as the
   cause of their conformity. This is the next experiment. Cost: roughly
   doubles the calls per round.
2. **Recruitment, with join-or-die.** Puts an individual payoff in the referee
   rather than in the prompt, and stops the game ending at exposure. This is
   the real version of what `survival` only claimed.
3. **Morning as a signal.** Nobody died ⇒ somebody was recruited. The absence
   of an event becomes public information the table can reason from.
4. **Speech/ballot divergence** needs no mechanism — it is already legal and
   the models simply do not use it (§4). It stays a metric.

Also open: the echo itself is still only characterised, not solved; the
ruleset's 92%-by-chance mafia win rate should be rebalanced before outcomes are
used as evidence; and every result here is one model, one game, one language.

## 9. On publishing this

The intended output is an article — LinkedIn plus a personal site — told as
what it is: a builder's account, not a paper.

What is defensible:

- the practical finding of §5, stated as the bound and not the slogan;
- the null model as a cheap instrument most multi-agent demonstrations skip,
  and what happened to our own headline when we ran it;
- §6 in full. The errors are the most transferable part, and admitting them is
  what makes the rest credible.

What is **not** ours to claim: the phenomenon is partly known. Before claiming
novelty, check *Degeneration-of-Thought* in multi-agent debate, conformity and
sycophancy in LLM discussion, the Werewolf/Avalon LLM literature, and
*Hoodwinked*. "We measured this and here is what a room needs" is honest;
"we discovered this" is not.

External validity is one model, one game, one language, one ruleset. Say so.
