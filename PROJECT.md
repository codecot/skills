# PROJECT

## 1. What this project does
A small, curated library of versioned prompts ("skills") and agent definitions for coding agents, built around one theme: verification over vibes. It also ships a few stdlib-only Python tools that carry the same theme into code — a self-checking markdown runbook engine, a local Copilot Chat usage counter, and a multi-agent "Mafia" measurement probe.

## 2. Main technologies
- Markdown — skills, agent definitions, docs (the bulk of the repo).
- Python 3 (3.8+ for `tools/`, 3.10+ for `probes/mafia`), standard library only; tests use `unittest`.
- No package manager, no framework, no build step.

## 3. Project structure
- `skills/` — single-purpose prompt cards to paste into any capable agent; `TEMPLATE.md` is the card format.
- `agents/` — fuller agent/subagent definitions (roles with contracts).
- `tools/runbook/` — `runbook.py`, a markdown setup document whose steps verify themselves; `FORMAT.md`, `examples/`, `tests/`.
- `tools/chat-usage/` — `chat_usage.py`, counts local VS Code Copilot Chat history for the `ai-usage-audit` skill; `tests/`.
- `probes/mafia/` — game referee, random-voter null, statistics and cost ledger for a multi-agent conformity study (`STUDY.md`).

## 4. How to run locally
```sh
git clone git@github.com:codecot/skills.git && cd skills
# nothing to install
python3 tools/runbook/tests/test_runbook.py
python3 tools/chat-usage/tests/test_chat_usage.py
python3 tools/runbook/runbook.py status tools/runbook/examples/demo-workspace.md
python3 tools/chat-usage/chat_usage.py --out /tmp/chat-usage-out
cd probes/mafia && python3 mafia_null.py   # mafia_probe.py also needs a local Ollama
```

## 5. How to deploy
There is no deploy. The repository is consumed by reading or copying files from GitHub; there is no CI, package or hosted service.

## 6. Key external dependencies
- Ollama on `http://127.0.0.1:11434/api/chat` — only for `probes/mafia/mafia_probe.py`.
- VS Code / Copilot Chat session files on local disk — read by `tools/chat-usage`.
- No databases, no paid APIs.
