# wide-change-playbook

> Turn a bundled "modernization" diff — formatter + dependency bumps + cleanup
> in one PR — into a sequence of independently verifiable changes, before it
> becomes an unattributable incident.

**Version:** v1
**Lineage:** distilled from a career's worth of watching the same movie:
a wide "refurbishing" PR lands, checks are green, deploy breaks — and the
question "which of the forty changes did it?" has no answer, because the unit
of change stopped matching the unit of verification. The playbook encodes the
counter-discipline: every slice declares its verification before it lands.
Sibling of `grill-my-spec` (that one interrogates intent; this one
interrogates a change plan).
**Use with:** any capable agent, as a review lens over a proposed plan OR an
existing bundled diff/PR.
**Strength:** the MUST rules (one concern per change; verification declared
before landing; no-op proven mechanically) are non-negotiable. Slice
granularity and landing order are SHOULD — tune to the system.

## Prompt

```
You are reviewing a proposed WIDE CHANGE: formatter adoption, dependency
upgrades, framework bump, mass refactor — possibly several bundled together.
Your job is to slice it into changes whose unit of change EQUALS the unit of
verification, and to produce a landing plan.

Rules (MUST):
- One concern per change. Formatting, dependency upgrades, refactors, and
  behavior changes never travel in the same commit/PR.
- Every slice declares, BEFORE landing: (a) what it changes, (b) how it is
  verified — mechanical proof preferred: AST/bytecode equality for
  format-only changes; clean-environment install + import/smoke test for
  dependency changes (no inheritance from any host machine); golden tests
  for behavior-preserving refactors; (c) its blast radius; (d) its rollback
  story — what a revert takes with it.
- "No-op" is proven, never asserted. A formatting slice ships with its
  mechanical no-op proof and is listed in .git-blame-ignore-revs so blame
  and bisect stay readable across it.
- Dependency slices carry a lockfile diff and pass a hermetic install gate;
  upgrades of unrelated packages do not share a slice.
- Landing order minimizes coupled risk: no-op slices in quiet windows,
  risky slices when owners are awake, never on a Friday evening.
- Anything that cannot be sliced into a verifiable unit is flagged
  UNSLICEABLE with the reason stated — never silently bundled.

Output:
1. Numbered landing plan: slice → verification method → rollback story.
2. Risk table: slice, failure mode it could cause, how it would be noticed.
3. Review questions for the author — anything the diff/plan does not answer.
4. If this is an EXISTING PR under review: a ready-to-post review comment —
   bounded-gate style: acknowledge the valid core first and offer it a fast
   separate path; request the slicing with the criteria stated upfront
   (finite, explicit, the same for everyone); no retroactive demands, no
   tone. The comment should be one a reasonable author can only agree with.

The change to review:
<paste the plan, diff summary, or PR description here>
```

## Notes & known limits

- NOT a code review: it reviews the SHAPE of a change, not its content.
  Run content review per slice afterwards — that's the point.
- Primary daily use is the REVIEWER seat: a bundled PR lands on you, you run
  this lens, you post output #4. The slicing plan is the reasoning; the
  comment is the deliverable.
- The playbook trades one big review for several small ones. That is not
  overhead; the big review was an illusion (nobody meaningfully reviews a
  forty-concern diff), the small ones are real.
- Agent-era note: generation is cheap now, so wide plausible diffs have
  become cheap to produce — which makes this discipline more load-bearing,
  not less. Gates over habits: where possible, encode the hermetic install
  check and the format-no-op check in CI rather than in people.

## Changelog

- v1 (2026-08) — initial form: unit-of-change = unit-of-verification law,
  mechanical no-op proofs, hermetic dependency gate, landing-order rules.
