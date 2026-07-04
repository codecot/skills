# cycle-closer

> Close the loop between what a goal claims and what the code contains:
> extract the goal's declared features (its Δ list), then reconcile each
> against the actual tree — covered / missing / inconclusive, with a real
> `path:line` behind every "covered".

**Version:** v1
**Lineage:** extracted from Factory's goal-coverage contour, 2026-07 — the
quality-layer's "closes the loop" audit that reconciles a goal document's
declared deltas against the code's actual status, with an anti-hallucination
rule: no evidence, no "covered". Extracted verbatim with identifiers
generalized.
**Use with:** Claude Code / Codex / Cursor / any agent with read access to a
clone of the project at its default branch.
**Strength:** MUST — every "covered" cites a `path:line` you actually
opened; when in doubt return "inconclusive", NEVER a confident "missing";
no invented paths or line numbers. SHOULD — the 40-feature cap and the JSON
output shape; resize and reshape to your pipeline.

## Prompt

```
You are auditing whether the features described by a GOAL ("<goal-slug>")
are actually implemented in the CODE you have been dropped into (the current
working directory is a read-only clone of the project at its default branch).

Work in two steps:
1. EXTRACT a bounded list of concrete features / requirements the GOAL text
   claims (Why-now, Concept, the Roadmap / Δ list, scope). Aim for 40
   or fewer — each a single, checkable capability, not a vague theme.
2. For EACH feature, inspect the code (Read / Grep / Glob) and decide:
   - "covered": the feature is present in the code. You MUST set `evidence`
     to a real `path:line` you actually opened (a done spec or PR# is also
     acceptable). Cite the most load-bearing location.
   - "missing": nothing in the code implements it.
   - "inconclusive": you could not confirm presence or absence with
     confidence (cross-cutting feature, partial evidence, ran out of leads).

Rules:
- A goal feature often spans <subsystem> ↔ <subsystem> ↔ <subsystem>. A one-file glance is
  NOT enough. When in doubt, return "inconclusive" — NEVER a confident
  "missing". A false "missing" wastes effort on redundant work.
- Every `covered` MUST cite a path that exists in this clone. Do not invent
  paths or line numbers — open the file first.
- `reasoning`: one or two contestable sentences per feature.
- `evidence` is null for "missing" (and may be null for "inconclusive").

GOAL text (goal.md):
"""
<goal text (goal.md)>
"""

Return JSON { "features": [ {feature, status, evidence, reasoning} ] }.
```

## Notes & known limits

- "Why-now, Concept, the Roadmap / Δ list" are the section names of
  Factory's goal-document template. Map them to whatever shape your goal /
  epic / milestone docs have — the method (extract claims, then ground each
  one) is what transfers.
- In the source system a deterministic verifier ran AFTER the model: any
  "covered" verdict citing a path that didn't exist in the clone was
  downgraded to "inconclusive" with a note, and a "covered" with no evidence
  at all was downgraded up front. That check is code, not prompt — if you
  can, re-implement it; it catches exactly the hallucinations the prompt
  alone can't prevent.
- The asymmetry is deliberate: a false "missing" triggers redundant work, a
  false "covered" hides a gap — so uncertainty must land in "inconclusive",
  and "covered" carries the evidence burden.
- Deliberately NOT a code review and NOT a per-spec acceptance audit. Its
  sibling in the same system (a per-spec "completion analyst") walks ONE
  spec's acceptance criteria with a DONE / NOT_DONE verdict; this card
  audits a whole goal's breadth instead of one spec's depth.
- Bound the goal text you paste (the source system capped it at ~40k chars)
  and keep the feature list ≤ 40 — one pass stays cheap and the output stays
  readable.

## Changelog

- v1 (2026-07) — extracted from Factory's goal-coverage contour
  (quality-layer Δ9); identifiers generalized, no other changes.
