---
name: prose-check
description: "Use before any text goes public (a post, an article, a letter to a recruiter or a manager): three passes in order, meaning first, then LLM stamps with a scanner that gates on hits, then facts. Returns the text, its claim in one line, what was cut and what is unverified."
---

# prose-check

> Three passes over a text before it goes public: is there a claim, does it
> read like a model wrote it, can every fact be sourced. Meaning comes first,
> because polishing a sentence you are about to delete is wasted work.

**Version:** v1
**Lineage:** the gate I run on my own posts and letters since 2026-11-13. The
stamp scanner started from Wikipedia's "Signs of AI writing" and grew with the
stamps I kept finding in drafts; the meaning pass came from drafts that passed
the scanner clean and still said nothing.
**Use with:** Claude Code (the scanner runs from `scripts/`); in a chat, paste
the passes and run the scanner yourself.
**Strength:** the order of the passes and "fix every HIT" are MUST. The output
format is SHOULD.

## Pass 1. Meaning

Done by reading, before any tool.

1. **Where is the claim.** Say in one sentence what the text actually claims.
   Find that sentence in the draft. If it is not in the first two sentences,
   move it there. If you can't state it, there is no text yet: go back to the
   author for the thought, don't polish.
2. **"So what?" per sentence.** A sentence stays only if it adds one of: a
   fact, an example, a number, a step of reasoning, an action for the reader.
   A sentence that only sets the mood, repeats its neighbour in other words or
   sounds clever goes.
3. **One idea.** A post carries one idea. The second good idea is the next
   post.
4. **Whose is it.** The text needs something only its author could have
   written: their case, their number, their decision. A general truth with no
   example of theirs gets cut or gets an example.

Don't, in this pass:
- force exactly three arguments; there are as many as there are;
- remove the author's own words and images for being "wrong"; fix the tone,
  keep the content;
- add a moral or an aphorism at the end to round it off.

## Pass 2. Stamps

```
python3 scripts/prose_stamps.py [--skip REGEX] FILE
```

Blocks are split on lines that are exactly `---`; `#` headings are skipped.
Fix every HIT, look at every hint. Exit code 1 on any HIT, so it can gate a
pipeline. A signature line the author always uses will show as a
`short_closer` hint; that is expected.

What the scanner does not see, check by eye: contrast pairs without a marker
("X is cheap. Y is scarce."), "not X but Y" framings, two-sentence staccato.

## Pass 3. Facts

- Every number and date has a source you can name. No source, no number.
- Describe systems as they are now. Something proposed but not built is not
  written in the present tense.
- No names of employers, clients, recruiters or agencies unless the author
  asked for them.
- Days and times from the clock, not from memory.

## What to hand back

1. The finished text, whole, ready to copy.
2. One line: the claim of the text, as you understood it.
3. "Cut": what pass 1 removed, so the author can bring back what was theirs.
   If nothing was cut, say so.
4. What is unverified (a number without a source, a doubt about tone), up
   front, not after being asked.
