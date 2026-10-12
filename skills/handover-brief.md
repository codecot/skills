# handover-brief

> Produce a spoken-English description of a system you work on — what it does,
> which screens and reports it has, which measures it shows, how data flows and
> fails — in categories only, with every identifier replaced by a bracketed
> category. For onboarding a new teammate, handing a project over, or
> explaining your own system to a stakeholder outside the team.

**Version:** v1
**Lineage:** written after being asked, out loud, "what does your platform
actually report and which measures does it use?" about a system I had led for
two years — and finding that the names were in the code, not in my mouth.
The categories-not-identifiers rule comes from the same engagement: the agent
that reads the repo can see everything, and the text it writes has to be safe
to carry out of the room. The "spoken, not documentation" rule comes from
rehearsal: a paragraph you cannot say in one breath is not a brief.
**Use with:** GitHub Copilot in VS Code with the repository open, Claude Code,
Codex — any agent with read access to the codebase. Read the output on the
machine where the repository lives before it goes anywhere else.
**Strength:** the RULES block is MUST. The six sections and the ~400-word
length are SHOULD; drop a section the system does not have, never add an
identifier to fill one.

## Prompt

```
I am handing this system over to a teammate who has never seen it. I need a
plain-English brief I can say out loud in a few minutes, not documentation.
Read the repository first. Then write about 400 words, in six sections:

1. What the system is, in two sentences. Who uses it every day and for which
   decision.
2. The screens and reports. One line each: what the user sees and which
   question it answers. Group them by purpose (for example: positions and
   exposure, performance against a reference, risk measures, attribution,
   data quality, administration — use the groups this system actually has).
3. The measures. Every metric the system computes or displays. For each: the
   plain name, what it means in one line, and whether it is computed here or
   taken from a data source.
4. The data flow. Where data comes from (by type of source, not by vendor
   name), how often it arrives, where it is processed, where it lands, and
   how it is checked before a user sees it.
5. What happens when data is missing, late or wrong. Who notices, how, and
   what the user sees meanwhile.
6. Ownership. Which parts are owned by the engineering side and which by the
   domain specialists (analysts, quants, operators) — as the code and the
   configuration show it, not as a job title would.

RULES (non-negotiable)
- Categories, not identifiers. Do not write: product, portfolio, strategy,
  fund or account names; tickers or codes; client, company or vendor names;
  internal service, repository, table, model or dashboard names; people's
  names; environment names; URLs; any number read from data or configuration.
- Where an identifier would normally appear, write the category in square
  brackets: [equity fund], [market data vendor], [risk engine], [reporting
  database].
- Spoken English. Short sentences, one idea each. If a sentence cannot be
  said in one breath, split it.
- Say UNKNOWN where the code does not show the answer (for example who is
  paged when a feed fails, if there is no alerting code). Do not infer from
  comments or README claims; mark those as "the README says".
- Read-only. Do not modify anything.

After the six sections, add a ten-line list: the questions this brief cannot
answer from the code and a human teammate must — history, intent, who decided
what and why.
```

## Review before the text leaves the machine

Read the output where the repository lives. Then:

- Every proper name gone? Search the text for capitalised words that are not
  sentence starts or category words.
- Every number gone except counts of sections and the like?
- Brackets wherever an identifier used to be? If one is missing, add it by
  hand; if a line cannot survive without the identifier, drop the line.
- The UNKNOWN list present? A brief with no unknowns was written from the
  README, not from the code.

## Notes & known limits

- Not a system map. For paths, entry points and arteries use
  `recon-system-map`; this skill is the thing you say after that map exists.
- Not a contribution report. It describes the system, not your part in it
  beyond section 6; for "what did I deliver" use `contribution-report`.
- The agent cannot judge what counts as confidential in your organisation.
  The rules remove the obvious classes (names, codes, numbers); the human
  review pass is part of the skill, not optional.
- Measures the system displays but computes elsewhere are easy to misattribute.
  Section 3 asks for "computed here or taken from a source" for that reason;
  check it against the data-flow section.
- Spoken English from a model still drifts into documentation English after a
  few paragraphs. Read it aloud once; shorten what you stumble on.

## Changelog

- v1 (2026-10) — extracted from a handover rehearsal on a long-running
  analytics platform; initial form.
