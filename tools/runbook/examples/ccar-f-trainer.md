# CCAR-F Trainer

A self-checking practice exam for Claude Certified Architect - Foundations, in
runbook form. Each step is one question: you answer via `ask`, the `check`
compares your answer to a hashed key (the plaintext answer is not in the file),
and on a miss the `do` block prints the rationale. The domain is in each heading,
so misses can be tallied per domain.

Weighted to the official domains: Agentic Architecture & Orchestration (27%),
Claude Code Configuration & Workflows (20%), Prompt Engineering & Structured
Output (20%), Tool Design & MCP Integration (18%), Context Management &
Reliability (15%). Pass mark ~ 720/1000 (~72%), so target >= 43/60.

Run it:

```sh
python3 ../runbook.py run    ccar-f-trainer.md   # ask each question, check your answer
python3 ../runbook.py status ccar-f-trainer.md   # re-probe, change nothing
python3 ccar-f-score.py                          # tally your result by exam domain
```

Answers for `Select TWO` questions are two letters, any order, e.g. `AB`.

The correct answer is stored as a SHA-256 hash in each `check`, not in plain
text, so scanning the file does not hand you the key; a miss reveals the
rationale (and the right letter) through the `do` block. To retake from scratch,
delete the state file: `rm ccar-f-trainer.md.state.json`.

## Q1 - Agentic {#q1}

```ask
Q1 | A job extracts data from 10k invoices nightly, fixed schema, no decisions needed. Best design?  A) an agent loop per invoice  /  B) multi-agent with a planner  /  C) single-shot structured output in a batch job  /  D) a reflection loop
```

```check
printf '%s' "${Q1:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Fixed schema, no decisions -> simplest path; batch for volume/cost. Agents/planner/reflection are overkill.'
exit 1
```

## Q2 - Prompt Engineering {#q2}

```ask
Q2 | You need the model to always return JSON matching a fixed schema. Most reliable mechanism?  A) ask nicely for JSON in the prompt  /  B) lower temperature only  /  C) add "return only JSON" and hope  /  D) use tool use / structured output with the schema
```

```check
printf '%s' "${Q2:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Schema-enforced structured output cannot return an invalid shape; asking nicely is not reliable.'
exit 1
```

## Q3 - Claude Code {#q3}

```ask
Q3 | Where do persistent project-specific instructions the agent should always load belong?  A) CLAUDE.md  /  B) a settings.json env var  /  C) the clipboard  /  D) a code comment
```

```check
printf '%s' "${Q3:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: CLAUDE.md is the persistent project memory the agent always loads.'
exit 1
```

## Q4 - Tool Design & MCP {#q4}

```ask
Q4 | A tool description is vague ("does stuff with data"). Likely consequence?  A) the tool errors  /  B) no effect, only the name matters  /  C) the model misuses or under-uses the tool  /  D) faster calls
```

```check
printf '%s' "${Q4:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: The model chooses tools from their descriptions; vague -> misuse/under-use.'
exit 1
```

## Q5 - Context Management {#q5}

```ask
Q5 | Each turn of a long chat re-sends a large static style guide before dynamic content. Cheapest fix preserving quality?  A) switch to a smaller model  /  B) prompt caching with the static guide as a stable prefix  /  C) delete the guide  /  D) summarize every message
```

```check
printf '%s' "${Q5:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: A static prefix -> prompt caching cuts cost/latency without losing content.'
exit 1
```

## Q6 - Agentic {#q6}

```ask
Q6 | An agent must research an unfamiliar topic across sources, where the next query depends on findings. Architecture?  A) batch classification  /  B) a fixed two-step chain  /  C) single-shot prompt  /  D) an agentic loop with a web-search tool and model-driven control flow
```

```check
printf '%s' "${Q6:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Next step depends on findings -> a model-driven loop with a tool. That is agentic.'
exit 1
```

## Q7 - Agentic (Select TWO) {#q7}

```ask
Q7 | Genuine risks of an UNBOUNDED agent loop? (Select TWO)  Pick TWO (e.g. AB).  A) the schema becomes invalid  /  B) guaranteed higher accuracy  /  C) runaway cost  /  D) infinite / no-progress loops
```

```check
printf '%s' "${Q7:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^90ec58127ec472ffb7e3f90c3ee320f8bb1dc6bc64a48143e6d91f7d9a6de236' && exit 0
echo 'why: Unbounded loops burn cost and can spin with no progress; they do not guarantee accuracy.'
exit 1
```

## Q8 - Prompt Engineering {#q8}

```ask
Q8 | You want the model to reason before committing to a final label in structured output. Best field ordering?  A) confidence, label, reasoning  /  B) reasoning, then label  /  C) order does not matter  /  D) label, then reasoning
```

```check
printf '%s' "${Q8:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Reasoning must come before the committed label (think, then answer).'
exit 1
```

## Q9 - Tool Design & MCP {#q9}

```ask
Q9 | In MCP, which primitive is read-only context the client pulls in (not an action)?  A) Resource  /  B) Sampling  /  C) Tool  /  D) Prompt
```

```check
printf '%s' "${Q9:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Resources = read-only context; Tools = actions; Prompts = templates.'
exit 1
```

## Q10 - Claude Code {#q10}

```ask
Q10 | You want a shell command to run automatically after every file edit in Claude Code. What do you configure?  A) an MCP server  /  B) a slash command  /  C) a hook in settings.json  /  D) a CLAUDE.md note
```

```check
printf '%s' "${Q10:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: "After every edit, run X" = a hook in settings.json (the harness runs it, not the model).'
exit 1
```

## Q11 - Context Management {#q11}

```ask
Q11 | A classifier's self-reported confidence is uncalibrated. How do you make a confidence threshold trustworthy?  A) treat the model's number as a probability  /  B) raise temperature  /  C) calibrate the threshold against a labeled gold set by measuring real accuracy at each level  /  D) route everything to a human
```

```check
printf '%s' "${Q11:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Self-reported confidence is only usable after calibration against a gold set.'
exit 1
```

## Q12 - Agentic {#q12}

```ask
Q12 | What best distinguishes an "agentic" system from a "workflow"?  A) agentic uses more tokens  /  B) in agentic the model decides control flow dynamically; a workflow's steps are pre-scripted  /  C) workflows cannot use tools  /  D) agentic always uses multiple models
```

```check
printf '%s' "${Q12:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Agentic = model controls flow dynamically; workflow = developer scripts the steps.'
exit 1
```

## Q13 - Prompt Engineering (Select TWO) {#q13}

```ask
Q13 | Effective ways to reduce hallucinated facts via prompting? (Select TWO)  Pick TWO (e.g. AB).  A) remove the system prompt  /  B) let the model abstain / say "I do not know" when unsure  /  C) increase max_tokens  /  D) provide source material and ask it to ground answers and cite
```

```check
printf '%s' "${Q13:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^24349c8054862cb8cbd4d857d096943e21434041ea744799074e2e28e753c14c' && exit 0
echo 'why: Abstention + grounding/citation reduce hallucination; more tokens / no system prompt do not.'
exit 1
```

## Q14 - Tool Design & MCP {#q14}

```ask
Q14 | Designing a refund tool for a customer agent. Safest design?  A) let the model pass raw SQL  /  B) no params, infer everything  /  C) one free-text "action" param  /  D) structured params (order_id, amount) plus server-side authorization and limits
```

```check
printf '%s' "${Q14:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Structured params + server-side authz/limits; never free-text/SQL or blind inference.'
exit 1
```

## Q15 - Claude Code {#q15}

```ask
Q15 | What does a Claude Code subagent give you?  A) automatic deployment  /  B) a separate context/agent to delegate a scoped task, keeping its tool output out of the main context  /  C) a faster model  /  D) a GUI
```

```check
printf '%s' "${Q15:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Subagent = delegated scoped context, keeps its tool output out of the main thread.'
exit 1
```

## Q16 - Agentic {#q16}

```ask
Q16 | An agent finishes when it stops requesting tools and returns a final answer. Which stop_reason signals "keep looping"?  A) max_tokens  /  B) tool_use  /  C) end_turn  /  D) stop_sequence
```

```check
printf '%s' "${Q16:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: tool_use = it wants to act -> loop; end_turn = done.'
exit 1
```

## Q17 - Context Management {#q17}

```ask
Q17 | Strongest reason to prefer RAG over stuffing everything into a long context window?  A) retrieving only relevant chunks cuts cost/latency and avoids degradation on huge inputs  /  B) RAG removes the need for evals  /  C) RAG is always more accurate  /  D) long context never works
```

```check
printf '%s' "${Q17:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Retrieve only relevant chunks -> cheaper, faster, avoids long-context degradation.'
exit 1
```

## Q18 - Prompt Engineering {#q18}

```ask
Q18 | Prefilling the assistant turn with a brace is a technique to...  A) increase temperature  /  B) cache the prompt  /  C) nudge the model to start a JSON object / constrain format  /  D) end the conversation
```

```check
printf '%s' "${Q18:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Prefilling a brace constrains the model to start a JSON object.'
exit 1
```

## Q19 - Agentic {#q19}

```ask
Q19 | A support agent can issue refunds. Best place for a human-approval gate?  A) never, trust the model  /  B) after the refund is already sent  /  C) on every message  /  D) on the irreversible/high-impact action (refund above a threshold)
```

```check
printf '%s' "${Q19:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Gate the irreversible/high-impact action, not every message, and not after the fact.'
exit 1
```

## Q20 - Tool Design & MCP {#q20}

```ask
Q20 | Your MCP tool returns a 5MB blob on every call, bloating context. Better design?  A) call the tool more often  /  B) increase the context window  /  C) return a summary/handle and let the agent fetch detail only if needed  /  D) always return the full blob
```

```check
printf '%s' "${Q20:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Return a handle/summary; fetch detail on demand to protect context.'
exit 1
```

## Q21 - Claude Code {#q21}

```ask
Q21 | Which file controls tool-permission rules and env for a Claude Code project?  A) package.json  /  B) .gitignore  /  C) settings.json / settings.local.json  /  D) CLAUDE.md
```

```check
printf '%s' "${Q21:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: settings.json / settings.local.json holds permissions and env.'
exit 1
```

## Q22 - Prompt Engineering (Select TWO) {#q22}

```ask
Q22 | Good uses of XML tags in a Claude prompt? (Select TWO)  Pick TWO (e.g. AB).  A) encrypting the prompt  /  B) marking where examples start/end  /  C) delimiting sections (context, instructions)  /  D) reducing token cost to zero
```

```check
printf '%s' "${Q22:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^768921a22b8e190c2cfafeb0688f0d58a5f76ee4c7fb369758a208c7ba5e9acb' && exit 0
echo 'why: XML tags delimit sections and examples; they do not encrypt or zero-cost.'
exit 1
```

## Q23 - Agentic {#q23}

```ask
Q23 | Multi-agent orchestration is MOST justified when:  A) the task is a simple lookup  /  B) latency must be minimal  /  C) subtasks are genuinely independent/parallelizable or need distinct specialized roles  /  D) you want to save tokens
```

```check
printf '%s' "${Q23:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Multi-agent pays off for independent/parallel or specialized subtasks, not simple/low-latency work.'
exit 1
```

## Q24 - Context Management {#q24}

```ask
Q24 | "Context rot" in long agent sessions refers to:  A) accumulated, stale, or contradictory context degrading quality over many turns  /  B) the model file corrupting  /  C) rising token prices  /  D) a network error
```

```check
printf '%s' "${Q24:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Context rot = stale/contradictory accumulated context degrading quality.'
exit 1
```

## Q25 - Tool Design & MCP {#q25}

```ask
Q25 | When should a capability be a tool vs. handled in the prompt?  A) never use tools  /  B) a tool when it must act on the world or fetch fresh/external data; prompt-only when the model can reason it out  /  C) only for math  /  D) always a tool
```

```check
printf '%s' "${Q25:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Tool when it must act or fetch fresh/external data; otherwise prompt-only.'
exit 1
```

## Q26 - Prompt Engineering {#q26}

```ask
Q26 | Inconsistent output formats across calls. Besides structured output, which helps most?  A) removing instructions  /  B) raising temperature  /  C) a few-shot example showing the exact desired format  /  D) longer max_tokens
```

```check
printf '%s' "${Q26:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: A few-shot example of the exact format is the strongest extra lever.'
exit 1
```

## Q27 - Agentic {#q27}

```ask
Q27 | An agent repeatedly calls the same failing tool with the same args. Best reliability pattern?  A) increase temperature each retry  /  B) let it keep trying forever  /  C) remove all tools  /  D) detect no-progress / repeated identical calls, cap retries, change strategy
```

```check
printf '%s' "${Q27:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Detect no-progress, cap retries, change strategy - do not loop forever.'
exit 1
```

## Q28 - Claude Code {#q28}

```ask
Q28 | Slash commands in Claude Code are:  A) git hooks  /  B) reusable prompt/command templates you invoke by name  /  C) keyboard shortcuts only  /  D) MCP servers
```

```check
printf '%s' "${Q28:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Slash commands = reusable prompt/command templates invoked by name.'
exit 1
```

## Q29 - Context Management {#q29}

```ask
Q29 | Prompt caching gives a cost/latency benefit only when:  A) temperature is 0  /  B) you use a small model  /  C) the cached prefix is identical and appears at the start, before variable content  /  D) the cached content changes every request
```

```check
printf '%s' "${Q29:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Cache helps only with an identical prefix placed before variable content.'
exit 1
```

## Q30 - Agentic (Select TWO) {#q30}

```ask
Q30 | Signs a task should be single-shot, not agentic? (Select TWO)  Pick TWO (e.g. AB).  A) steps are known and fixed in advance  /  B) each run must dynamically re-plan  /  C) no external actions/tools are needed to decide the answer  /  D) it requires open-ended multi-step investigation
```

```check
printf '%s' "${Q30:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^472e73d796e20aa8ff9059e6316f218e0322548f661ec4dc267507ed66317404' && exit 0
echo 'why: Known fixed steps and no external action needed -> single-shot. The others argue for an agent.'
exit 1
```

## Q31 - Tool Design & MCP {#q31}

```ask
Q31 | A well-designed tool description should primarily:  A) clearly state what the tool does, when to use it, and what each parameter means  /  B) list the implementation code  /  C) hide the parameters  /  D) be as short as possible
```

```check
printf '%s' "${Q31:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Description must convey what/when/parameters - not be minimal or hide params.'
exit 1
```

## Q32 - Prompt Engineering {#q32}

```ask
Q32 | To make the model follow a persona/role consistently, you should:  A) repeat it only in every user message  /  B) put the role instruction in the system prompt  /  C) prefill the user turn  /  D) use a higher temperature
```

```check
printf '%s' "${Q32:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Role belongs in the system prompt for consistent behavior.'
exit 1
```

## Q33 - Agentic {#q33}

```ask
Q33 | Three subagents review a diff for bugs, security, and performance in parallel, then findings merge. This is:  A) impossible  /  B) parallel multi-agent fan-out with an aggregation step  /  C) a workflow with no agents  /  D) a single-shot call
```

```check
printf '%s' "${Q33:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Parallel fan-out of specialized subagents + aggregation.'
exit 1
```

## Q34 - Claude Code {#q34}

```ask
Q34 | The Claude Agent SDK is for:  A) fine-tuning models  /  B) building your own agents programmatically with the same harness primitives  /  C) hosting websites  /  D) running Claude Code only interactively
```

```check
printf '%s' "${Q34:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Agent SDK = build your own agents with the same harness primitives.'
exit 1
```

## Q35 - Context Management {#q35}

```ask
Q35 | A conversation approaches the context-window limit mid-task. Best strategy?  A) crash  /  B) switch providers  /  C) delete the system prompt  /  D) summarize/compact earlier turns while preserving key state, then continue
```

```check
printf '%s' "${Q35:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Compact/summarize earlier turns, preserve key state, continue.'
exit 1
```

## Q36 - Tool Design & MCP (Select TWO) {#q36}

```ask
Q36 | Security practices for tools an agent can call? (Select TWO)  Pick TWO (e.g. AB).  A) pass secrets in the tool description  /  B) least-privilege: expose only needed actions, with limits  /  C) trust all model-provided arguments  /  D) server-side authorization/validation of every call
```

```check
printf '%s' "${Q36:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^24349c8054862cb8cbd4d857d096943e21434041ea744799074e2e28e753c14c' && exit 0
echo 'why: Server-side validation + least privilege; never trust all args or expose secrets.'
exit 1
```

## Q37 - Prompt Engineering {#q37}

```ask
Q37 | Setting stop_sequences is used to:  A) make the model stop generating at a defined marker  /  B) cache the prompt  /  C) add tools  /  D) increase creativity
```

```check
printf '%s' "${Q37:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: stop_sequences halt generation at a defined marker.'
exit 1
```

## Q38 - Agentic {#q38}

```ask
Q38 | In a plan-then-execute agent, the "plan" step mainly helps by:  A) guaranteeing correctness  /  B) reducing token cost to zero  /  C) decomposing an open-ended goal into steps before acting, improving coherence on complex tasks  /  D) replacing the need for tools
```

```check
printf '%s' "${Q38:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Planning decomposes an open-ended goal -> better coherence on complex tasks.'
exit 1
```

## Q39 - Claude Code {#q39}

```ask
Q39 | You want Claude Code to NOT read a large generated folder. Best approach?  A) delete the folder  /  B) configure ignore/permissions so the agent does not pull it into context  /  C) rename CLAUDE.md  /  D) lower temperature
```

```check
printf '%s' "${Q39:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Use ignore/permissions so the folder never enters context.'
exit 1
```

## Q40 - Prompt Engineering {#q40}

```ask
Q40 | Chain-of-thought (think step by step) most helps on:  A) simple lookups  /  B) formatting tasks  /  C) reducing latency  /  D) multi-step reasoning / complex problems
```

```check
printf '%s' "${Q40:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: CoT helps multi-step reasoning, not lookups/formatting/latency.'
exit 1
```

## Q41 - Tool Design & MCP {#q41}

```ask
Q41 | An agent needs to READ inventory and PLACE an order. Good MCP modeling?  A) both as one free-text tool  /  B) place orders via a resource  /  C) inventory as a resource/read tool, order placement as an action tool with validation  /  D) neither; put it in the prompt
```

```check
printf '%s' "${Q41:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Read = resource/read tool; act (order) = action tool with validation.'
exit 1
```

## Q42 - Agentic {#q42}

```ask
Q42 | Reflection (the model critiquing its own output and retrying) adds the most value when:  A) latency is the only concern  /  B) the task is trivial classification  /  C) never  /  D) output quality is checkable and errors are common (e.g., testable code)
```

```check
printf '%s' "${Q42:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Reflection pays when quality is checkable and errors are common.'
exit 1
```

## Q43 - Context Management (Select TWO) {#q43}

```ask
Q43 | Ways to keep a long agent run reliable? (Select TWO)  Pick TWO (e.g. AB).  A) periodic summarization/compaction of history  /  B) externalize durable state (files/DB) instead of relying only on in-context memory  /  C) append everything forever with no management  /  D) never use tools
```

```check
printf '%s' "${Q43:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^38164fbd17603d73f696b8b4d72664d735bb6a7c88577687fd2ae33fd6964153' && exit 0
echo 'why: Durable external state + periodic compaction keep long runs reliable.'
exit 1
```

## Q44 - Prompt Engineering {#q44}

```ask
Q44 | You want deterministic, repeatable classification outputs. Temperature should be:  A) irrelevant  /  B) negative  /  C) high (0.9+)  /  D) low / 0
```

```check
printf '%s' "${Q44:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Low/0 temperature -> deterministic, repeatable classification.'
exit 1
```

## Q45 - Agentic {#q45}

```ask
Q45 | Deterministic math validation in an invoice agent should be done by:  A) prompt caching  /  B) deterministic code, not the LLM  /  C) a second LLM  /  D) the LLM doing arithmetic in its head
```

```check
printf '%s' "${Q45:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Arithmetic -> deterministic code, never the LLM'"'"'s head.'
exit 1
```

## Q46 - Claude Code {#q46}

```ask
Q46 | MCP servers in Claude Code let you:  A) change the model weights  /  B) replace settings.json  /  C) speed up the CPU  /  D) connect the agent to external tools/data/services via a standard protocol
```

```check
printf '%s' "${Q46:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: MCP connects the agent to external tools/data via a standard protocol.'
exit 1
```

## Q47 - Tool Design & MCP {#q47}

```ask
Q47 | A tool parameter should be an enum rather than free text when:  A) the model is small  /  B) you always want maximum flexibility  /  C) the valid values are a known, fixed set (prevents invalid inputs)  /  D) never
```

```check
printf '%s' "${Q47:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Enum when values are a known fixed set - prevents invalid inputs.'
exit 1
```

## Q48 - Prompt Engineering (Select TWO) {#q48}

```ask
Q48 | Signs your prompt is over-constrained and hurting quality? (Select TWO)  Pick TWO (e.g. AB).  A) so many rules the model ignores some  /  B) one well-chosen example  /  C) contradictory instructions the model cannot satisfy  /  D) a single clear instruction
```

```check
printf '%s' "${Q48:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^472e73d796e20aa8ff9059e6316f218e0322548f661ec4dc267507ed66317404' && exit 0
echo 'why: Contradictions and rule overload are over-constraint symptoms; clarity/an example are good.'
exit 1
```

## Q49 - Agentic {#q49}

```ask
Q49 | Human-in-the-loop is MOST important for agent actions that are:  A) irreversible or high-impact (payments, deletes, sends)  /  B) cached  /  C) fast  /  D) read-only
```

```check
printf '%s' "${Q49:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: HITL matters most for irreversible/high-impact actions.'
exit 1
```

## Q50 - Context Management {#q50}

```ask
Q50 | The "lost in the middle" effect means:  A) tools fail mid-call  /  B) caching breaks  /  C) models ignore the system prompt  /  D) info in the middle of a very long context is attended to less reliably than the start/end
```

```check
printf '%s' "${Q50:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Lost in the middle = weaker attention to mid-context info vs. start/end.'
exit 1
```

## Q51 - Claude Code {#q51}

```ask
Q51 | Best practice for secrets (API keys) in a Claude Code project?  A) keep in environment/.env, never commit, never print  /  B) put in the system prompt  /  C) hardcode in CLAUDE.md  /  D) share in the PR description
```

```check
printf '%s' "${Q51:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Secrets live in env/.env; never commit, print, or embed in prompts/PRs.'
exit 1
```

## Q52 - Agentic {#q52}

```ask
Q52 | An orchestrator with a task queue and runners routing PRs through dev/fix cycles with a human merge gate is:  A) pure RAG  /  B) single-shot prompting  /  C) fine-tuning  /  D) a structured agentic pipeline with model-driven work and a human gate
```

```check
printf '%s' "${Q52:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^3f39d5c348e5b79d06e842c114e6cc571583bbf44e4b0ebfda1a01ec05745d43' && exit 0
echo 'why: Queue + runners + human merge gate = a structured agentic pipeline.'
exit 1
```

## Q53 - Tool Design & MCP {#q53}

```ask
Q53 | If two tools have overlapping, ambiguous descriptions, the likely failure is:  A) faster execution  /  B) lower cost  /  C) the model picks the wrong tool  /  D) better accuracy
```

```check
printf '%s' "${Q53:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Ambiguous overlapping descriptions -> wrong-tool selection.'
exit 1
```

## Q54 - Prompt Engineering {#q54}

```ask
Q54 | To steer a long structured response's format precisely, combine structured output with:  A) removing the schema  /  B) a clear schema + one concrete example of the desired shape  /  C) no system prompt  /  D) higher temperature
```

```check
printf '%s' "${Q54:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: Schema + one concrete example pins the output shape.'
exit 1
```

## Q55 - Agentic (Select TWO) {#q55}

```ask
Q55 | Valid stopping conditions for an agent loop? (Select TWO)  Pick TWO (e.g. AB).  A) the token price changes  /  B) model returns a final answer with no tool calls  /  C) the screen turns blue  /  D) a max-step / budget cap is reached
```

```check
printf '%s' "${Q55:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^24349c8054862cb8cbd4d857d096943e21434041ea744799074e2e28e753c14c' && exit 0
echo 'why: A final answer with no tool calls, or a budget/step cap - both valid stops.'
exit 1
```

## Q56 - Context Management {#q56}

```ask
Q56 | Idempotency matters in agent tool calls because:  A) retries after failures should not cause duplicate side effects (e.g., double charges)  /  B) it makes outputs creative  /  C) it caches prompts  /  D) it lowers temperature
```

```check
printf '%s' "${Q56:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Idempotency prevents duplicate side effects on retries (e.g., double charge).'
exit 1
```

## Q57 - Tool Design & MCP {#q57}

```ask
Q57 | A good MCP prompt primitive is:  A) a reusable, parameterized prompt template the server exposes to clients  /  B) an action that mutates data  /  C) a place to store secrets  /  D) the model's weights
```

```check
printf '%s' "${Q57:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: MCP prompt = reusable parameterized template the server exposes.'
exit 1
```

## Q58 - Prompt Engineering {#q58}

```ask
Q58 | The model must extract 8 fields but some may be missing in the source. Best schema design?  A) force the model to guess missing ones  /  B) drop structured output  /  C) allow nullable/optional fields and an explicit "not found" value  /  D) require all 8 always
```

```check
printf '%s' "${Q58:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^6b23c0d5f35d1b11f9b683f0b0a617355deb11277d91ae091d399c655b87940d' && exit 0
echo 'why: Optional/nullable fields + explicit "not found" beats forcing guesses.'
exit 1
```

## Q59 - Agentic {#q59}

```ask
Q59 | Using a cheap model for bulk and an expensive model only for hard cases is:  A) a cost-aware cascade/routing pattern matching spend to difficulty  /  B) not possible  /  C) fine-tuning  /  D) wasteful
```

```check
printf '%s' "${Q59:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd' && exit 0
echo 'why: Cheap-bulk + expensive-hard = cost-aware cascade/routing.'
exit 1
```

## Q60 - Context Management {#q60}

```ask
Q60 | The best single evidence that a prompt/config change actually improved quality is:  A) it feels better  /  B) it scores higher on a fixed eval set vs. the baseline  /  C) fewer tokens used  /  D) the model says so
```

```check
printf '%s' "${Q60:-}" | tr 'a-z' 'A-Z' | tr -cd 'A-Z' | fold -w1 | sort | tr -d '\n' | sha256sum | grep -qi '^df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c' && exit 0
echo 'why: A higher score on a fixed eval vs. baseline is the real evidence.'
exit 1
```
