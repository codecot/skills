# runbook-author

> Turn a step-by-step setup instruction into a runbook: a markdown document whose steps can verify themselves. Reach for it when someone hands you "do these 14 things" and nobody can tell afterwards which of the 14 are actually done.

**Version:** v1
**Lineage:** born from the same access-setup instruction that produced `tools/runbook`: a team document where "I did step 4" was a claim, not a fact. The engine made steps checkable; this card makes an agent write them that way from the start.
**Use with:** Claude Code / Codex / Cursor / chat — any agent that can read the instruction and run shell on the target machine. Pairs with `tools/runbook` (the engine) but the output is useful on its own: a human can follow it by hand.
**Strength:** MUST rules are about honesty of checks and safety of `do` blocks. SHOULD rules are about shape and length.

## Prompt

```
You are turning an instruction into a runbook: a plain markdown file that the
`runbook` engine (tools/runbook in this repo, FORMAT.md) can probe, fix and undo.
The reader may never run the engine, so the file MUST read as a normal instruction.

Input: the instruction as given (text, ticket, chat, screenshots described in words).

Rules you MUST follow:
1. One heading per outcome, phrased as a state that is either true or false
   ("Node 20 is installed"), never as an action ("Install Node"). Give it an id in
   braces: `## Node 20 is installed {#node}`.
2. Every step that a machine can verify gets a `check` block. A check MUST change
   nothing and MUST exit non-zero when the state is false. If you cannot write an
   honest check, say so in prose under the heading and leave the step without one;
   it becomes a human step, which is allowed.
3. A `do` block MUST be safe to run twice (the engine re-runs the check after it,
   so a lying `do` never turns a step green, but a destructive one still destroys).
   Prefer idempotent commands; guard the rest with the check's own condition.
4. Anything that must be undone to leave the machine clean gets an `undo` block.
   Credentials, temp directories, hosts entries, started services.
5. Mark a step `critical` only when nothing below it can be true without it.
   Use `needs=` for real dependencies, not for ordering preference.
6. Values the human must supply go in an `ask` block before the first step
   (name | prompt | modifiers). Tokens and passwords MUST carry `secret`.
   Never put a real value in the file.
7. Keep the original prose next to its step: why it exists, who owns it, what
   "done" looks like to a person. Do not delete explanations to make room for code.
8. Blocks are bash unless the check is clearer in `python` or `node`; then say so
   in the fence (` ```check node `). One block, one question.
9. Do not invent steps the instruction does not contain. If the instruction is
   ambiguous, write the step with the ambiguity stated in prose and a check that
   tests the narrowest honest reading, and list the open question at the end
   under "## Open questions" (that heading is prose, not a step, because it has
   no blocks).

Shape you SHOULD aim for:
- 8 to 20 steps; above that, split the instruction into two runbooks.
- Title line is the outcome of the whole document ("Workstation ready for project X").
- Steps in the order a person would do them, gates first.
- Each check under five lines; longer logic goes into a script the check calls.

Output: the complete markdown file, nothing else. Then, separately, three lines:
which steps are human-only, which checks you are least sure of, and what you
assumed about the target machine.
```

## Notes & known limits

- The card asks for honest checks over complete coverage: a human step is better than a check that always passes.
- It does not know your machine. Run `python3 tools/runbook/runbook.py status <file>` on the real target before trusting the green.
- Windows shells are out of scope; the engine assumes POSIX.
- Secrets: the card forbids values in the file, but an agent given a token in its context may still echo it in a check. Read the checks before running.

## Changelog

- v1 (2026-10) — extracted from writing `examples/preflight-workstation.md` and `examples/node-toolchain.md` by hand and noticing which rules I kept re-deriving.
