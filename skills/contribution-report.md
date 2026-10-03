# contribution-report

> Build a factual "my contribution to the project" report from your own git
> history — one quarter at a time, then one merge pass — when you leave a
> project or have to account for a long period.

**Version:** v1
**Lineage:** written on the way out of a two-year enterprise engagement, when
"what did you actually deliver?" had to be answered from the record rather
than from memory. The quarter-by-quarter split comes from the first attempt:
two years of commits in one prompt produced adjectives; one quarter at a time
produced work items with file paths. The "write UNCLEAR, don't guess" rule is
the same one the factory applies to its reviewers.
**Use with:** GitHub Copilot in VS Code (any capable model), Claude Code, Codex,
or a chat — the input is a text export of `git log`, so no agent needs repo
access. Everything stays on the machine where the repositories live.
**Strength:** "facts from the log only" and "UNCLEAR over guessing" are MUST.
The quarter window, the 4–8 item count and the output length are SHOULD.

## Procedure

1. Export your own commits per quarter, per repository, into a scratch folder
   (never committed):
   ```
   git log --author="<your name>" --no-merges --since=YYYY-MM-01 --until=YYYY-MM-01 \
     --date=short --pretty=format:"%h %ad %s" --stat > contrib/<quarter>_<repo>.txt
   ```
   No terminal? GitHub → Pull requests → `is:pr author:@me merged:YYYY-MM-DD..YYYY-MM-DD`
   and paste the titles into the same file. Check the author spelling first:
   `git log --format=%an | sort -u`.
2. One chat per quarter with Prompt A and the file attached → `contrib/<quarter>_summary.md`.
3. One chat for the whole period with Prompt B and every summary attached → the report.
4. The sections "what only I know" and "open items" are written by you, not by the model.

## Prompt A — one quarter

```
You are summarising my own commits on a software project. Input: a git log of
my commits for one quarter, with changed files (attached).
- Group the commits into 4–8 work items by feature or area, not by file.
- For each item: a name a product manager would recognise; what changed for the
  user or the team; the main files or modules; rough size (commits, files).
- Then list separately: (a) test automation and CI/CD, (b) infrastructure or
  tooling, (c) fixes with no feature.
- Facts from the log only. Where a commit message is unclear, write UNCLEAR
  rather than guess.
Output: English, one page, ending with a table: commits, files touched, work items.
```

## Prompt B — the whole period

```
Attached are quarterly summaries of my commits on one project over the whole
period. Write "My contribution to the project":
1. A timeline table: quarter → the two or three main deliveries.
2. The five largest threads of work across the period, one paragraph each:
   what it is, why it mattered, what state it is in now.
3. "What runs because of this work": automation that runs unattended, feature
   flags, standards, tooling — with where each lives.
4. Counts for the whole period: commits, files, work items, quarters.
Facts only, no adjectives, English, two to three pages. Where quarters
disagree or a thread is unclear, say so.
```

## Notes & known limits

- Not a performance review and not a CV: it reports what the log shows, which
  undercounts review, mentoring and design work that left no commits. Add
  those by hand, labelled as such.
- Squash merges hide authorship inside a PR; use the PR search variant for
  repositories that squash.
- Commit messages written in a hurry produce UNCLEAR items; that is the
  honest result, not a prompt failure.
- Client code and logs must not leave the client machine; only the finished
  report is handed over, there.

## Changelog

- v1 (2026-10) — extracted from a two-year handover; initial form.
