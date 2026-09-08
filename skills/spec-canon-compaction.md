# spec-canon-compaction

> Turn a pile of specification files into one living canon per subsystem —
> "what is true now" — with every claim traced to a spec or a test, a list of
> contradictions for a human, and the specs themselves left untouched as the
> ledger. For codebases where reading the specs has become a token bill.

**Version:** v1
**Lineage:** extracted from a factory that accumulated 470+ spec documents in
five months (2026-09) and a client team's own note that "we have so many spec
files that reading them is a huge load of tokens" and their planned
"fundamental specs wiki" was "not completed yet". The method: history stays,
a canon is built above it, and every merge must patch the canon.
**Use with:** any agent with repo access. Pairs with `recon-system-map`
(run first if the codebase is unknown) and `recon-principle-audit` (the
canon is what an audit should cite).
**Strength:** RULES are MUST. Section shape of the canon is SHOULD — keep it
if you have no house style.

## Prompt

```
You are compacting the specifications of one subsystem into a CANON: a
single living document that states what is true about the subsystem NOW.
The spec files are history and must not be edited or deleted. Work in
passes; after each pass STOP, hand me the artifact, and wait.

RULES (non-negotiable)
- Every sentence in the canon cites its source: a spec file (path, and the
  section or line), a test (path), or code (path:line). A sentence with no
  source is not written.
- Later beats earlier: when two specs disagree, the later merged one wins
  UNLESS a test or code shows the earlier is what runs — then record a
  CONTRADICTION and do not choose.
- Prose is not truth: a spec's claim that something "is" or "will be" built
  is intent until a test or code path confirms it. Mark unconfirmed claims
  INTENDED, not TRUE.
- Read-only on specs and code. You write exactly two files: the canon and
  the contradiction list.
- No names of people, clients, or internal hostnames in the artifacts.

PASS 1 — Inventory
List every spec touching this subsystem: path, date, status, size, one-line
summary, and which other specs it references or supersedes. Flag drafts,
superseded specs, and "finalize"/"close" specs that only restate others.
Output: SPEC-INVENTORY.md with a count and total size in bytes — the number
this work exists to shrink.

PASS 2 — Extract claims
From each non-superseded spec, extract every checkable claim about the
subsystem as one line: the claim, its source, and its status (TRUE if a
test or code confirms; INTENDED if only stated; STALE if code shows
otherwise). Group by topic, not by spec.
Output: CLAIMS.md.

PASS 3 — Build the canon
Write CANON-<subsystem>.md with these sections, each a list of sourced
sentences: Purpose · Interfaces (what enters, what leaves) · Invariants
(what must always hold) · Gates (what is refused and where) · Data (what is
stored, where, for how long) · Operations (how it runs, timers, limits) ·
Known limits · Open questions. Only TRUE claims go into the body; INTENDED
claims go into a final "Intended, not yet true" section with their spec.
Keep it under 2,000 words; if it cannot fit, the subsystem is two.
Output: CANON-<subsystem>.md.

PASS 4 — Contradictions and absorption
List every place where specs disagree with each other or with code, as:
claim A (source) vs claim B (source) → which one runs today (evidence) →
question for the owner. Then list the specs that are now FULLY absorbed by
the canon (every claim of theirs appears, sourced) — candidates for the
archive folder, to be moved by a human, never by you.
Output: CONTRADICTIONS.md and an "absorbed" list at its end.

FINALE — numbers
Before: N specs, B bytes. After: 1 canon, b bytes; M contradictions open;
K specs fully absorbed. State what a new session must now read to work on
this subsystem: the canon alone, or the canon plus which specs.

RULE FOR WHAT COMES NEXT (write it at the top of the canon)
"A change to this subsystem enters as a spec written as a DELTA against
this canon, naming the section it changes. Merging that spec must update
this file in the same pull request. A spec that cannot name the canon
section it changes is a note, not a spec."
```

## Notes & known limits

- It compacts one subsystem at a time by design. Running it on a whole
  repository produces a canon nobody reads; if PASS 3 cannot fit 2,000
  words, split.
- INTENDED vs TRUE depends on tests and code being reachable. On a specs-only
  repository everything is INTENDED; say so in the finale rather than
  promoting claims.
- The contradiction list is the valuable output, not the canon. A canon with
  zero contradictions from 50 specs is a sign PASS 4 was skipped.
- It does not decide what to archive; it nominates. Moving specs is a human
  commit with a reason.
- The "delta against the canon" rule at the end is what stops the pile from
  growing back. Without a gate enforcing it (see `recon-principle-audit`:
  prose is not mechanism), it is a wish.

## Changelog

- v1 (2026-09) — extracted from a spec-driven factory (471 specs) and a
  client team's stated pain; the "later beats earlier unless code says
  otherwise" rule came from a week in which three specs described the same
  gate and none of them was built.
