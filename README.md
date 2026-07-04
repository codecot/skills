# Skills — prompts & agents from a working software factory

A small, curated library of prompts, skills, and agent setups I actually use —
extracted from a self-referential spec-to-code engine (Factory) and daily
applied-AI work. Built in the open.

**This is not a mega-collection.** The excellent broad libraries already exist.
This one is narrow and opinionated, with one theme: **verification over vibes.**
Skills here are built around evidence, honest uncertainty, and keeping human
judgement in the loop:

- reviews that must point to files, not impressions
- recon that says `UNKNOWN` instead of guessing
- RAG that abstains instead of inventing
- critics that argue with reasons, and never hold veto

## Structure

- `skills/` — single-purpose prompts you paste into any capable agent
  (Claude Code, Codex, Cursor, a chat). Each is a versioned card with
  provenance: where it came from, what it's for, its known limits.
- `agents/` — fuller agent/subagent definitions (roles with contracts).
  Currently: `spec-writer`, `snapshot-reviewer`, `cycle-closer` — ported from Factory's contours (sanitized) —
  and `spec-drafter`, `memory-snapshot-reviewer`, `cycle-close-verifier` — ported from the operator-side subagents used alongside Factory (sanitized).

## Why versioned cards

Every skill carries its lineage — which real work produced it and what changed
between versions. A prompt you can't trace is a prompt you can't trust or fix.
(The same rule my factory applies to its own generated code.)

## Status

Early. Skills are added as they graduate from daily use — not scraped, not
generated in bulk. If something here is wrong or has a sharper form, open an
issue: adversarial review is the point.

— Volodymyr Pasichnyk · [codecot.com](https://codecot.com)
