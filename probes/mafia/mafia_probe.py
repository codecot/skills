#!/usr/bin/env python3
"""A probe, not a product: can local models play Mafia at all?

Before building the room loop (specs/2026-08-03-personas-and-rooms.md) it is
worth knowing whether the participants can hold a role, lie for several rounds
and vote for a reason. One file, ollama only, no VoiceBridge integration and no
paid calls — if the answer is "no", better to learn it now than after the
channels, the fuses and the referee are written.

    python3 tools/mafia_probe.py [--players 6] [--model qwen3:14b] [--seed 1]
                                 [--budget-usd 0.50] [--max-calls 200]

The referee here is the same shape the spec asks for — view / apply / over —
deliberately, so that what survives can move into the real loop.

Every call goes through the ledger (tools/runlog.py): tokens, seconds and price
per thinking act, and a stop cock that refuses the next call rather than
reporting the overrun afterwards. A local run costs nothing but still records
the token traffic, which is what makes `--what-if claude-opus-5` able to answer
"and what would this have cost paid" from measurement instead of arithmetic.
"""
import argparse, json, random, re, sys, time, urllib.request

from runlog import Ledger, BudgetExceeded

OLLAMA = "http://127.0.0.1:11434/api/chat"

RULES = """Ты играешь в мафию. Правила:
- Ночью мафия выбирает жертву. Днём все обсуждают и голосуют, кого казнить.
- Мафия побеждает, когда её становится не меньше, чем мирных.
- Мирные побеждают, когда казнены все мафиози.
Говори коротко — две-три фразы, как живой человек за столом. Не пересказывай
правила, не объясняй, что ты ИИ. Обращайся к игрокам по именам."""


def ask(led, model, system, user, timeout=600, **meta):
    """One thinking act, priced. The ledger's veto comes first, then the call."""
    led.check(meta.get("phase", ""))
    # think=False: qwen3 reasons out loud by default, which triples the time
    # per turn for a game where the reasoning is not the artefact. A table of
    # six players times four rounds is what makes this matter.
    body = {"model": model, "stream": False, "think": False,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"temperature": 0.8, "num_predict": 220}}
    rq = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(),
                                headers={"content-type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        d = json.load(r)
    dt = time.time() - t0
    raw = d.get("message", {}).get("content", "")
    # local models like to think out loud in <think> blocks; count what was
    # thought before discarding it — with think=True that is where the money
    # goes on a paid provider, so the column has to exist from the start
    thought = "".join(re.findall(r"<think>(.*?)</think>", raw, flags=re.S))
    txt = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    # ollama reports real counts; no estimating from characters
    led.record(model=model, seconds=dt,
               tokens_in=d.get("prompt_eval_count", 0),
               tokens_out=d.get("eval_count", 0),
               thinking_tokens=len(thought) // 4,
               prompt=user, text=txt,
               **meta)
    return txt, dt


# Dispositions for the `agenda` arm: does giving every seat its own bias make
# the room argue? This is the hypothesis that a room of differently-primed
# agents should naturally hold different lines.
#
# Note that several of these are anti-conformist *by construction* — distrusting
# whoever repeats others, refusing to move under pressure. That is deliberate:
# it makes this a generous test rather than a fair one. If the table still
# converges when a third of it has been explicitly told not to follow the
# crowd, then prompt-level differentiation is not the missing ingredient, and
# the finding is much harder to argue with.
#
# None of these carry game information — no hints about roles, no facts. A
# disposition only changes how the same evidence is weighed, which is exactly
# what a persona is supposed to do.
AGENDAS = [
    "Ты не доверяешь тем, кто высказывается первым.",
    "Ты считаешь, что молчуны опаснее крикунов.",
    "Ты заступаешься за того, на кого набросились всей толпой.",
    "Тебя раздражают общие рассуждения, ты требуешь конкретики.",
    "Ты доверяешь тем, кто честно признаёт свои сомнения.",
    "Ты подозреваешь тех, кто повторяет чужие слова.",
    "Ты считаешь, что громче всех обвиняет обычно виноватый.",
    "Ты не меняешь мнение под давлением большинства.",
]


class Game:
    """State, rules and the ledger — in code, never in a model (spec §6a)."""

    def __init__(self, names, n_mafia, rng, variant="base"):
        self.names = names
        self.rng = rng
        self.variant = variant
        # `private`: each seat sees only a short tail of the table talk, to
        # test whether the shared transcript is what drowns the persona.
        self.window = 6 if variant == "private" else 24
        # `agenda`: every seat gets a different disposition, assigned by seat
        # position rather than drawn.
        #
        # Deterministic on purpose. Drawing them from `rng` would consume the
        # same stream that assigns roles and picks the detective's checks, so
        # the identical seed would produce a different game in this arm than in
        # the others — and the arms could then only be compared in aggregate.
        # Fixed assignment keeps every seed a matched pair across all variants,
        # which is worth far more than randomising a label. Roles are still
        # drawn, so disposition and role stay uncorrelated across seeds.
        self.agenda = {}
        if variant == "agenda":
            self.agenda = {n: AGENDAS[i % len(AGENDAS)]
                           for i, n in enumerate(sorted(names))}
        self.mafia = set(rng.sample(names, n_mafia))
        self.detective = rng.choice([n for n in names if n not in self.mafia])
        self.alive = set(names)
        self.public = []          # [(round, who, text)]
        self.conclave = []        # mafia-only channel
        self.facts = {}           # name -> [private facts from the referee]
        self.ledger = []
        self.round = 0

    def role(self, n):
        if n in self.mafia:
            return "мафия"
        return "шериф" if n == self.detective else "мирный"

    # --- view(role, state, talk): what this participant is shown
    def view(self, who):
        lines = [f"Игроки в живых: {', '.join(sorted(self.alive))}.",
                 f"Ты — {who}. Твоя роль: {self.role(who)}."]
        if who in self.agenda:
            # placed before the transcript on purpose: if it worked only at the
            # very end we would be measuring recency, not disposition
            lines.append("Твой характер: " + self.agenda[who])
        if self.variant == "survival" and who not in self.mafia:
            # The payoff, not the personality. A town seat that is paid to
            # survive rather than to be right has an objective that competes
            # with its neighbours' — which is the one thing a disposition
            # cannot manufacture. Everything else about the game is unchanged.
            lines.append(
                "Тебе платят за то, что ты доживёшь до конца, а не за то, что "
                "ты угадаешь мафию. Быть правым необязательно — важно не "
                "попасть под казнь.")
        if who in self.mafia:
            partners = sorted(self.mafia & self.alive - {who})
            lines.append("Твои подельники: " +
                         (", ".join(partners) if partners else "никого не осталось"))
            if self.conclave:
                lines.append("Ночной сговор:\n" + "\n".join(
                    f"  {w}: {t}" for _, w, t in self.conclave[-6:]))
        for f in self.facts.get(who, []):
            lines.append("Ты знаешь: " + f)
        if self.public:
            lines.append("Разговор за столом:\n" + "\n".join(
                f"  [{r}] {w}: {t}" for r, w, t in self.public[-self.window:]))
        return "\n".join(lines)

    # --- over(state)
    def over(self):
        m = len(self.mafia & self.alive)
        t = len(self.alive) - m
        if m == 0:
            return "мирные"
        if m >= t:
            return "мафия"
        return None


def parse_move(txt, candidates, marker):
    """A move must be STRUCTURED, not read out of prose.

    The first version of this probe took "the last name mentioned" and was
    wrong on the first night: the model opened by echoing the list of living
    players, so the heuristic picked the last name of that list instead of the
    victim it had actually named. The spec says a move is validated by the
    referee (§6a); cutting that corner cost one wrong killing. Now only a
    dedicated final line counts, and anything else is a refusal to move.
    """
    m = re.search(marker + r"\s*:?\s*([A-Za-zА-Яа-яЁё]+)", txt)
    if m:
        for c in candidates:
            if c.lower() == m.group(1).lower():
                return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", type=int, default=6)
    ap.add_argument("--model", default="qwen3:14b")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-rounds", type=int, default=6)
    # the stop cock: whichever cap is hit first ends the run cleanly, with the
    # partial ledger printed rather than lost
    ap.add_argument("--budget-usd", type=float, default=None)
    ap.add_argument("--max-calls", type=int, default=400)
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--tag", default="", help="what this run is testing")
    ap.add_argument("--variant", default="base",
                    choices=["base", "private", "agenda", "survival"],
                    help="base: as measured; private: short transcript window; "
                         "agenda: a different disposition per seat; "
                         "survival: town is paid to last, not to be right")
    ap.add_argument("--what-if", default="claude-opus-5",
                    help="re-price the measured traffic on this model")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    pool = ["Аня", "Борис", "Вера", "Глеб", "Дина", "Егор", "Жанна", "Захар"]
    names = pool[:a.players]
    # balance: two mafia need at least six seats, or the first night already
    # brings parity and the game ends before anyone has spoken
    n_mafia = 2 if a.players >= 6 else 1
    g = Game(names, n_mafia, rng, variant=a.variant)
    stats = {"votes": 0, "herd": 0, "mafia_hit_own": 0, "unparsed": 0}
    led = Ledger("mafia", budget_usd=a.budget_usd, max_calls=a.max_calls,
                 max_seconds=a.max_seconds, tag=a.tag)
    led.note(kind="setup", players=names, mafia=sorted(g.mafia),
             detective=g.detective, model=a.model, seed=a.seed,
             variant=a.variant, window=g.window, agenda=g.agenda)

    print(f"состав: {', '.join(names)}")
    print(f"мафия: {', '.join(sorted(g.mafia))} · шериф: {g.detective}")
    print(f"журнал: {led.path}\n")

    try:
        play(a, g, led, stats, rng)
    except BudgetExceeded as e:
        # not an error: the brake did its job. Say which cap and how far it got.
        print(f"\n⏹ стоп-кран: {e}")
        led.note(kind="stopped", reason=str(e), round=g.round)

    won = g.over() or "никто (не доиграно)"
    led.close(winner=won, rounds=g.round, **stats)

    print("\n" + "=" * 52)
    print(f"победа: {won}, раундов: {g.round}")
    print(led.report(group="phase"))
    print(f"голосов распознано: {stats['votes']}, не разобрано: {stats['unparsed']}")
    if stats["votes"]:
        print(f"стадность (голос как у первого бюллетеня): "
              f"{100*stats['herd']/stats['votes']:.0f}%")
        print(f"мафия голосовала за своих: {stats['mafia_hit_own']} раз")
    if a.what_if:
        print(f"эта же партия на {a.what_if}: ${led.what_if(a.what_if):.4f}")


def play(a, g, led, stats, rng):
    while g.round < a.max_rounds and not g.over():
        g.round += 1
        # ground truth for the analyser: who was on the table when this round
        # opened. Without it, "mentioned an already-dead player" and every
        # per-round rate has no denominator.
        led.note(kind="round_open", round=g.round, alive=sorted(g.alive))
        print(f"─── раунд {g.round} " + "─" * 40)

        # night: the mafia channel picks a victim; the detective checks someone
        killers = sorted(g.mafia & g.alive)
        if killers:
            speaker = killers[g.round % len(killers)]
            targets = sorted(g.alive - g.mafia)
            txt, dt = ask(led, a.model, RULES,
                          g.view(speaker) +
                          f"\n\nНочь. Выбери жертву из: {', '.join(targets)}. "
                          "Одна фраза — кого и почему. Последней строкой ровно: "
                          "ЖЕРТВА: <имя>",
                          phase="night", who=speaker, role=g.role(speaker),
                          round=g.round)
            victim = parse_move(txt, targets, "ЖЕРТВА")
            if victim is None:
                stats["unparsed"] += 1
                victim = rng.choice(targets)
            g.conclave.append((g.round, speaker, txt))
            print(f"  [ночь] {speaker}: {txt[:110]}")
        else:
            victim = None

        if g.detective in g.alive:
            suspect = rng.choice(sorted(g.alive - {g.detective}))
            g.facts.setdefault(g.detective, []).append(
                f"ты проверил {suspect} — он {'мафия' if suspect in g.mafia else 'мирный'}")

        if victim:
            g.alive.discard(victim)
            g.ledger.append(("night_kill", g.round, victim))
            led.note(kind="night_kill", round=g.round, who=victim,
                     role=g.role(victim))
            print(f"  [утро] убит {victim}")
        if g.over():
            break

        # day: the floor rotates each round (spec §4)
        order = sorted(g.alive)
        start = g.round % len(order)
        order = order[start:] + order[:start]
        # Talk first, ballots after — and in secret.
        #
        # The first run folded the vote into the speech, and 67% of votes simply
        # repeated the previous speaker: the first person to name someone was
        # handing everyone else a filled-in ballot. The detective announced a
        # true "Борис is mafia" and then voted for someone else in the same
        # breath. Speaking and voting are different moves and must be separated;
        # nobody sees a vote until all are cast.
        for who in order:
            txt, dt = ask(led, a.model, RULES,
                          g.view(who) +
                          "\n\nДень, обсуждение. Скажи 2-3 фразы: кого подозреваешь "
                          "и почему. Голосовать будешь отдельно, имя пока не называй "
                          "как окончательное.",
                          phase="talk", who=who, role=g.role(who), round=g.round)
            g.public.append((g.round, who, txt))
            print(f"  {who} ({g.role(who)}): {txt[:110]}")

        votes, first_named = {}, None
        for who in order:
            others = [n for n in order if n != who]
            txt, dt = ask(led, a.model, RULES,
                          g.view(who) +
                          "\n\nГолосование, тайное — никто не видит чужих бюллетеней. "
                          "Одна строка, ровно: ГОЛОС: <имя> — "
                          f"из: {', '.join(others)}",
                          phase="ballot", who=who, role=g.role(who), round=g.round)
            v = parse_move(txt, others, "ГОЛОС")
            if v is None:
                # 9 ballots of 13 came back without the marker line. A local
                # model asked for prose and a format in one breath gives prose.
                # One retry that asks for nothing but the name recovers almost
                # all of them; a real implementation uses a response schema
                # where the provider supports one.
                txt2, dt2 = ask(led, a.model, "Ответь одним словом.",
                                f"Кого из этих ты казнишь: {', '.join(others)}? "
                                "Ответ — только имя, без пояснений.",
                                phase="retry", who=who, role=g.role(who),
                                round=g.round)
                stats["retries"] = stats.get("retries", 0) + 1
                for c in others:
                    if c.lower() in txt2.lower():
                        v = c
                        break
            if v is None:
                stats["unparsed"] += 1
            else:
                votes[who] = v
                stats["votes"] += 1
                if first_named is None:
                    first_named = v
                elif v == first_named:
                    stats["herd"] += 1     # matched the first ballot cast
                if who in g.mafia and v in g.mafia:
                    stats["mafia_hit_own"] += 1
            # the ballot is the one clean accusation signal in the game — no
            # NLP, no judge, no interpretation. Recorded as ground truth.
            led.note(kind="ballot", round=g.round, who=who, role=g.role(who),
                     vote=v, parsed=v is not None)
            print(f"      бюллетень {who}: {v}")

        if votes:
            tally = {}
            for v in votes.values():
                tally[v] = tally.get(v, 0) + 1
            top = max(tally.values())
            picked = sorted(n for n, c in tally.items() if c == top)
            out = picked[0] if len(picked) == 1 else rng.choice(picked)
            g.alive.discard(out)
            g.ledger.append(("vote_out", g.round, out, dict(tally)))
            led.note(kind="vote_out", round=g.round, who=out,
                     role=g.role(out), tally=tally)
            print(f"  [итог] казнён {out} ({g.role(out)}), голоса {tally}")


if __name__ == "__main__":
    main()
