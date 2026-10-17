# chat-usage — count your own Copilot Chat history, locally

**Runs with:** Python 3.8+, standard library only. Nothing to install, nothing leaves the machine.
**Used by:** the `skills/ai-usage-audit.md` skill.

VS Code keeps Copilot Chat sessions on disk, per workspace: `workspaceStorage/<id>/chatSessions/*.json` (snapshots) and `*.jsonl` (journals), plus `globalStorage/emptyWindowChatSessions/` for chats with no folder open. This tool reads them and writes:

- `requests.csv` — one row per request: date, time, project, session, mode, model, prompt and response length, tool calls, whether it looks like a retry, and the first N characters of the prompt (secrets redacted; `--prompt-chars 0` keeps none);
- `summary.md` — the history span, requests per quarter, month and top days, by model, mode and project, the 15 longest sessions, retry loops (4+ consecutive retry-like prompts or huge pastes) and pastes over 5,000 characters.

```
python chat_usage.py                      # Code, Code - Insiders and VSCodium user folders
python chat_usage.py --root PATH          # a VS Code "User" folder or any folder of session files
python chat_usage.py --out DIR --prompt-chars 0
python tests/test_chat_usage.py
```

The summary says how many requests carried a timestamp, a model and a mode, and how many journal entries could not be applied. Low coverage is reported, not guessed around.
