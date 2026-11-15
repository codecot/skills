# PROJECT.md — codecot/skills

## 1. What this project does

A small, curated library of prompts ("skills") and agent definitions built around one theme: verification over vibes. It is mostly markdown you paste into any capable agent. Alongside the markdown are a few standard-library Python tools: `runbook`, a setup document that checks itself; `chat-usage`, which counts your local Copilot Chat history; `compaction-audit`, which reports when Claude Code compacted your sessions; and `mafia`, a probe that measures conformity in multi-agent LLM rooms.

## 2. Main technologies

- **Markdown**: skills, agent definitions, runbook documents, study write-ups.
- **Python 3**, standard library only, with no third-party packages and no packaging/dependency file:
  - `tools/runbook`, `tools/chat-usage` and `tools/compaction-audit`: Python 3.8+.
  - `probes/mafia`: Python 3.10+.
- **unittest** (stdlib) for tests.
- **Node.js**: optional. `runbook` uses it only to execute `node` blocks inside a runbook.
- No web framework, no build step.

## 3. Project structure

- `skills/`: single-purpose, versioned prompt cards (`TEMPLATE.md` plus one file per skill).
- `agents/`: fuller agent/subagent role definitions with contracts (spec-writer, snapshot-reviewer, cycle-closer, and others).
- `tools/runbook/`: `runbook.py` engine, `FORMAT.md` spec, `examples/`, `tests/`.
- `tools/chat-usage/`: `chat_usage.py` (reads VS Code Copilot Chat session files, writes `requests.csv` and `summary.md`), `tests/`.
- `tools/compaction-audit/`: `compaction_audit.py` (reads Claude Code session transcripts, reports every compaction with its trigger, tokens before and after, and idle time), `tests/`.
- `probes/mafia/`: multi-agent conformity probe (`mafia_probe.py`), random-voter null model (`mafia_null.py`), statistics (`mafia_stats.py`), cost ledger (`runlog.py`), and `STUDY.md`.

## 4. How to run locally

```sh
git clone git@github.com:codecot/skills.git
cd skills
# nothing to install: Python 3.8+ standard library only

# tests
python3 tools/runbook/tests/test_runbook.py
python3 tools/chat-usage/tests/test_chat_usage.py
python3 tools/compaction-audit/tests/test_compaction_audit.py

# runbook: probe a document (writes <file>.md.state.json next to it)
python3 tools/runbook/runbook.py status tools/runbook/examples/demo-workspace.md

# chat-usage: count your own VS Code Copilot Chat history
python3 tools/chat-usage/chat_usage.py --out chat-usage-out

# compaction-audit: when and why Claude Code compacted your sessions
python3 tools/compaction-audit/compaction_audit.py --rows

# mafia probe (needs Python 3.10+ and a local Ollama on 127.0.0.1:11434)
cd probes/mafia
python3 mafia_null.py
python3 mafia_probe.py --games 20
python3 mafia_stats.py
```

Skills and agents need no running: open the markdown file and paste it into an agent.

## 5. How to deploy

There is no deploy. The repository is the deliverable: people read it on GitHub or clone it and run the tools locally. It has no CI, no hosting, and no package publishing.

## 6. Key external dependencies

- **Ollama** (local HTTP API at `http://127.0.0.1:11434/api/chat`): used only by `probes/mafia/mafia_probe.py`. The study used the model `qwen3:14b`.
- **VS Code / Copilot Chat local storage** (`workspaceStorage/*/chatSessions`, `globalStorage/emptyWindowChatSessions`): read-only input for `tools/chat-usage`.
- **Claude Code local transcripts** (`~/.claude/projects/**/*.jsonl`): read-only input for `tools/compaction-audit`.
- **Local filesystem**: `runbook` keeps state in `<name>.md.state.json`. The mafia ledger writes runs to `$VB_RUNS` (default `~/vb_runs`).
- No databases, no paid APIs, no network calls beyond local Ollama.
