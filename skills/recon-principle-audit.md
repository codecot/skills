# recon-principle-audit

> Audit an unfamiliar codebase against a stated set of engineering principles:
> for each principle, find where it is ENFORCED by mechanism, where it is only
> STATED in prose, where it is ABSENT, and where the code CONTRADICTS it.
> Evidence-bound, read-only, honest about unknowns. The question it answers is
> not "how does this system work" but "does this system hold the same beliefs
> I do — and can it prove it".

**Version:** v1
**Lineage:** extracted from evaluating an enterprise agent/automation platform
(2026-09) against the operator's own SDLC principles before proposing how the
two could meet. Grew out of a lesson learned the same week on the operator's
own factory: a rule everyone believed was enforced turned out to live only in a
markdown file — the mechanism did not exist. "Documented" and "enforced" had
been confused for months. This audit exists so that confusion is impossible.
**Use with:** any agent with repo access (Claude Code, Codex, Copilot chat).
Pairs with `recon-system-map` — run that first if no map exists.
**Strength:** RULES and the four-way classification are MUST. The default
principle list is SHOULD — replace it with your own; the method does not care
which principles, only that each is testable.

## Prompt

```
You are auditing an unfamiliar codebase against a set of engineering
principles. I want to know, for each principle, whether this system HOLDS it —
and whether it can PROVE it. Work in passes; after each pass STOP, hand me the
artifact, and wait.

RULES (non-negotiable)
- Evidence-bound: every finding points to concrete files/paths/symbols
  (path:line where possible). No plausible-sounding generalities.
- Prose is not mechanism. A README, a policy doc, a comment, a system prompt
  or a CLAUDE.md that says "we always X" is evidence of INTENT, never of
  ENFORCEMENT. Only code, configuration, CI, a gate, a test or a schema that
  makes X impossible to skip counts as enforcement.
- Four-way classification, one per principle, no fifth option:
    ENFORCED     — a mechanism makes the principle hard to violate (cite it)
    STATED       — the principle appears in prose only (cite where)
    ABSENT       — neither mechanism nor prose (say what you searched)
    CONTRADICTED — the code does the opposite (cite it; this outranks STATED)
- Honest unknowns: if you cannot determine it, write UNKNOWN and list exactly
  what would confirm it. Never guess silently.
- Read-only. Explore; do not modify, refactor or "fix" anything.
- No names of people, clients, or internal hostnames in the artifact.

PASS 0 — Make the principles testable
Take the principle list below (or the one I give you). Rewrite each as a
claim that a mechanism could enforce, and name the kind of evidence that
would prove it (a gate, a CI job, a schema constraint, a refusal path, a
journal row). A principle that cannot be made testable is marked
UNTESTABLE and set aside — say why.
Output: PRINCIPLES.md — the testable list.

PASS 1 — Map, if none exists
If there is no SYSTEM-MAP.md for this codebase, run the inventory and
entry-point passes of recon-system-map first. Do not audit a system you have
not mapped.

PASS 2 — Hunt each principle
For each testable principle, in order:
  a. Search for the MECHANISM: gates, validators, middleware, CI steps,
     schema constraints, permission checks, refusal paths. Cite each hit.
  b. Search for the PROSE: docs, prompts, comments, policies. Cite each hit.
  c. Search for the CONTRADICTION: code paths that bypass, disable, or do the
     opposite (feature flags that skip the gate, admin overrides, "temporary"
     exceptions, catch-and-continue). Cite each hit.
  d. Classify. If both a mechanism and a bypass exist, the classification is
     CONTRADICTED and the bypass is the finding.
Output: AUDIT.md — one section per principle: classification, evidence,
what was searched, and the single most important file.

PASS 3 — The seams
For every principle not ENFORCED: the smallest change that would enforce it,
named as a mechanism (not "add a policy"), with the file it would live in
and what it would refuse. Estimate honestly: one line / one file / one
subsystem / a redesign.
Output: SEAMS.md.

FINALE — the verdict table and the questions
A table: principle → classification → one-line evidence → seam size.
Then a 10-line summary answering: does this system hold the same beliefs, and
where does it only say it does. Then the TOP-5 questions only the system's
authors can answer — history, intent, why a bypass exists — things the code
cannot tell you.

DEFAULT PRINCIPLE LIST (replace with your own)
 1. Work enters only as a reviewed, merged specification — not as a ticket,
    a chat message, or a prompt.
 2. Work runs on infrastructure that does not depend on a person's laptop
    being open.
 3. Generated changes are reviewed by a model from a different vendor than
    the one that produced them, before any human sees them.
 4. A human is the only gate, and stands at merge, deploy and publish — not
    inside the generation loop.
 5. Policy is enforced outside the model: a rule the model could forget is
    also a rule the system cannot skip.
 6. The system can refuse its operator: an unsourced claim, an unknown
    caller, an out-of-scope write is rejected with a reason, not accepted
    with a warning.
 7. Every published number carries its source and the command to recount it.
 8. Every run leaves a journal row: cost, duration, outcome, what was refused.
 9. Running units of work are named and addressable; identity does not
    change with the transport that reaches them.
10. Secrets never enter a transcript or a log; credentials are held by a
    broker, not by the agent.
11. A living canon states what is true now; history is kept but is not the
    source of truth.
12. Anything that deletes, publishes, or spends money is idempotent and
    replayable from the journal.
```

## Notes & known limits

- It measures beliefs-as-mechanism, not quality. A system can ENFORCE every
  principle and still be badly built; the audit will not say so. Pair with a
  review skill for that.
- CONTRADICTED is deliberately harsh: one admin bypass flips a principle from
  ENFORCED to CONTRADICTED. That is the point — a gate with a back door is not
  a gate — but expect pushback from authors; the artifact must cite the exact
  bypass so the discussion is about a file, not a feeling.
- Prose search has false negatives: principles stated in a wiki, a ticket
  system, or a Slack channel are invisible to a repo-only pass. Mark UNKNOWN
  and ask.
- The default list encodes one operator's SDLC. Swap it. The value is the
  four-way classification and the "prose is not mechanism" rule, not the
  particular principles.
- Not for: comparing two systems to each other (run it twice and diff), or
  estimating effort beyond the one-line/file/subsystem/redesign scale.

## Changelog

- v1 (2026-09) — extracted from an enterprise platform evaluation; the
  "prose is not mechanism" rule was learned the hard way on the author's own
  factory the same week (a spec-creation gate believed to exist was found to
  be a paragraph in a markdown file).
