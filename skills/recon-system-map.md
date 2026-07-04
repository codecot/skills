# recon-system-map

> Build a precise mental model of an unfamiliar production codebase — a
> reconnaissance MAP, not a tutorial. Read-only, evidence-bound, honest about
> unknowns.

**Version:** v1
**Lineage:** extracted from onboarding myself into a large enterprise
data/analytics codebase (2026-07). Designed to be safe to run on a project you
don't own yet: strictly read-only, every claim traceable, output is an artifact
you can hand to the team.
**Use with:** any agent with repo access (Claude Code, Codex, Copilot chat).
**Strength:** the RULES block is MUST. Pass order is SHOULD (reorder passes to
fit the system; for a data-heavy system keep the data pass early).

## Prompt

```
You are helping me build a precise mental model of an unfamiliar production
codebase. I need a reconnaissance MAP of this system, not a tutorial. Work in
PASSES; after each pass STOP, hand me the artifact for that pass, and wait
before going deeper.

RULES (non-negotiable)
- Evidence-bound: every claim about the system must point to concrete
  files/paths/symbols (path:line where possible). No plausible-sounding
  generalities.
- Honest unknowns: where the code doesn't let you determine something, write
  UNKNOWN and list what would confirm it. Never guess silently.
- Read-only: exploration only. Do not modify, refactor, or "fix" anything.
- Breadth first: a shallow full map before any deep dive.

PASS 1 — Inventory & topology
- Top-level structure: modules / packages / services — one line of purpose
  each, with path.
- The stack as ACTUALLY used (frameworks, versions from lockfiles/configs —
  not from README claims).
- How it runs: local start, CI, deployment entry (scripts/configs, with paths).
Output: SYSTEM-MAP.md, section 1.

PASS 2 — Entry points & control flow
- Every externally-triggered entry point: HTTP routes/APIs, scheduled jobs,
  queue/event consumers, CLI commands, UI roots. For each: path, trigger,
  one-line purpose, what it calls into.
- The 3–5 MAIN ARTERIES: the most important request/data paths traced end to
  end, file by file.
Output: section 2 + a text diagram of the arteries.

PASS 3 — Data layer
- Where data actually lives: every database / store / warehouse referenced in
  config or code; the schemas/models with defining files.
- The data flow: ingestion → storage → transformation → serving — which code
  owns each stage.
- Core domain entities + a GLOSSARY: term → meaning → defining file.
Output: section 3 + glossary.

PASS 4 — Seams & risks
- Configuration & environments; how secrets are handled.
- Test coverage reality: what is actually tested vs not (evidence, not vibes).
- The scary parts: god-files, implicit coupling, suspected dead code — each
  with evidence.
Output: section 4.

FINALE — a 10-line executive summary of "how this system actually works",
plus the TOP-5 questions that only a human teammate can answer (intent,
history, design politics — things the code cannot tell you).
```

## Notes & known limits

- NOT for making changes — it deliberately forbids them. Pair with a separate
  change-scoped session once the map exists.
- On multi-service monorepos, run per service; Pass 1 sprawls otherwise.
- The TOP-5-questions finale doubles as a legitimate conversation-starter with
  the team that owns the system.

## Changelog

- v1 (2026-07) — extracted from a real enterprise onboarding; staged passes,
  evidence rule, UNKNOWN contract.
