# ai-usage-audit

> Find out how someone actually works with Copilot Chat, from their own local
> history, before advising them how to use less of it: where the requests go,
> which sessions loop, which prompts start without a plan.

**Version:** v1
**Lineage:** written when a colleague's Copilot usage ran about three times over
the team's quota and the request was "help him optimise". Advice without seeing
the work is guessing, so the order became: count first, read the most expensive
sessions second, advise third. Counting is done by a script, not a model, so the
audit itself costs almost nothing. The "do not suggest a weaker model" rule came
from the first draft of the advice: trading result quality for request count is
not an optimisation.
**Use with:** GitHub Copilot in VS Code (Agent mode) for the reading part; the
counting is `tools/chat-usage` (Python 3.8+, standard library). Everything stays
on the machine where the history lives.
**Strength:** "the person runs it on their own machine and reads the findings
first", "numbers from the script, not from the model" and "no weaker model" are
MUST. The thresholds (5 sessions, 4-prompt loops, 5,000-character pastes) are
SHOULD.

## Procedure

1. Run the counter on the machine where VS Code is used:
   ```
   python tools/chat-usage/chat_usage.py            # finds the VS Code user folder
   python tools/chat-usage/chat_usage.py --root "<VS Code User folder>"
   ```
   Output: `chat-usage-out/requests.csv` and `chat-usage-out/summary.md` — the
   history span, requests per quarter, month and day, by model, mode and
   project, the longest sessions, retry loops and huge pastes.
2. Read the "What the files contain" block first. If model or timestamp
   coverage is low, the split by model or month is not trustworthy; say so
   instead of filling the gap.
3. Compare the total with the billing figure. Far fewer requests in the history
   than on the bill means the usage is elsewhere (the GitHub coding agent,
   another IDE, another machine) — that is a finding, not a failure.
4. Paste the prompt below into Copilot Chat (Agent mode) with `summary.md`
   attached. The person reads `findings.md` first and decides what to share.

## Prompt

```
Attached is summary.md, a count of my own Copilot Chat history made by a script (requests.csv is next to it).
Read-only: do not modify or delete anything outside the chat-usage-out folder.

1. In three bullets with numbers: where most of my requests went (period, project, model, mode).
2. Open requests.csv and, for the 5 sessions with the most requests, read only the prompts (not the responses). For each: what the task was, why it took so many rounds, and what would have finished it in fewer. Typical causes to check: no plan or spec written before starting; the agent not told how to build and test; whole logs pasted instead of the last 100 lines; one chat carried across unrelated tasks; retrying after two failed rounds instead of stopping to rethink.
3. Look at the retry loops listed in summary.md: what was failing, and was a human check missing between rounds?
4. One paragraph: the single habit change that would save the most rounds without lowering the quality of the result. Do not suggest switching to a weaker model.

Write it to chat-usage-out/findings.md. No secrets, tokens, customer data or code in it; quote at most 150 characters of any prompt.
```

## Notes & known limits

- Chat requests are not billing units: model multipliers, inline completions and
  the GitHub coding agent are not in these files.
- The request fields (`modelId`, `modeInfo`, `timestamp`) follow the VS Code
  chat session format and are tested on synthetic files; formats change between
  versions. On a first real run, check the coverage block; a field at 0% means
  the name moved — open one session file and patch `request_rows`.
- Not a performance review. It shows where requests went, not how good the work
  was.

## Changelog

- v1 (2026-10) — written for a quota-overrun conversation; initial form.
