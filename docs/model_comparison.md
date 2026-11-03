# Model comparison

Hardware: laptop RTX 3050, 4 GB VRAM. All models served by Ollama.
**Chosen model: `qwen3:4b`.**

## Round 1: single tool (`read_file` only), 10 trials each

| Model | Tool-call rate | Valid args | Avg s/reply |
| --- | --- | --- | --- |
| `llama3.2` (3B) | 1.0 | 1.0 | 3.08 |
| `qwen2.5-coder:3b` | 0.0 | 0.0 | 1.07 |
| `qwen2.5-coder:7b` | 0.0 | 0.0 | 2.92 |

`qwen2.5-coder:14b` was dropped first: it ran out of GPU memory on the 4 GB card.

The Qwen coder models scored zero on structured tool calls. They are known to write tool calls as JSON in the reply text instead of Ollama's `tool_calls` field, so the agent never sees a call.

## Round 2: llama3.2 vs qwen3:4b, 10 trials each

| Model | Tool-call rate | Valid args | Avg s/reply |
| --- | --- | --- | --- |
| `llama3.2` (3B) | 1.0 | 1.0 | 1.85 |
| `qwen3:4b` | 1.0 | 1.0 | 14.57 |

A tie on accuracy; qwen3:4b is about 8x slower because it reasons before answering (thinking mode is on by default).

## Tie-breaker: the real agent (Step 3 checkpoint)

Task: "What does calc.py do? Is there a bug?" with all six tools available. `calc.py` defines `add(a, b)` as `return a - b`.

**llama3.2: fail.** Called `run_command("python calc.py")`, which prints nothing (`exit=0`), never read the file, and invented an answer:

```text
human | What does calc.py do? Is there a bug?
ai    | run_command {'command': 'python calc.py'}
tool  | exit=0
ai    | The calc.py script calculates the sum of all numbers in a list. There doesn't appear to be a bug in the script.
```

In an earlier run without the read-first prompt rule, it wrote tool calls as text and claimed tests passed that did not exist.

**qwen3:4b: pass.** Followed the system prompt's explore order exactly:

```text
human | What does calc.py do? Is there a bug?
ai    | list_files {'folder': '.'}
tool  | calc.py
ai    | read_file {'path': 'calc.py'}
tool  |    1 | def add(a, b):
      |    2 |     return a - b
ai    | calc.py defines a function called `add` that returns `a - b` (subtraction) instead of `a + b` (addition). This is a bug because the function name implies addition but performs subtraction.
```

## Takeaways

- A single-tool benchmark overstates small models. With the full toolset, picking the *right* tool is the hard part.
- Reasoning beat code specialization: the general qwen3:4b outperformed the code-tuned Qwen models, which could not emit structured tool calls.
- Trade-off accepted: about 15 s per step for correct, grounded answers. Revisit `reasoning=False` during the Step 7 evals.

## Eval suite: qwen3:4b, thinking on vs off

Five fixture tasks (`evals/tasks/`), each a small repo with a failing test; a task passes if `pytest -q` exits 0 after the agent finishes. Writes auto-approved inside a temp sandbox.

| Task | Thinking on | Thinking off |
| --- | --- | --- |
| 01_off_by_one | PASS, 5 steps, 253 s | PASS, 5 steps, 262 s |
| 02_empty_input | PASS, 5 steps, 321 s | PASS, 5 steps, 217 s |
| 03_rename_across_files | PASS, 7 steps, 294 s | PASS, 7 steps, 695 s |
| 04_add_feature | PASS, 6 steps, 579 s | PASS, 8 steps, 934 s |
| 05_parse_dates | PASS, 5 steps, 155 s | PASS, 5 steps, 175 s |
| **Total** | **5/5, 5.6 avg steps, 26.7 min** | **5/5, 6.0 avg steps, 38.1 min** |

Raw rows: `evals/results_qwen3_4b_thinking.json`, `evals/results_qwen3_4b_no_thinking.json`.

- Turning thinking off did not make the agent faster. It took more steps on the two multi-step tasks and ~40% longer overall, so thinking stays on.
- Most of the time per step is the model re-reading a growing conversation on a 4 GB laptop GPU, not reasoning tokens.
- One run per setting and five easy tasks: the 100% scores show the harness works, not where the model's ceiling is. Harder tasks are the next step.

## Eval suite: documentation research before every change

After adding documentation tools, the system prompt was changed to require a docs lookup (search, then read the page in 4,000-character chunks) before writing any code.

| Task | Thinking on, no research | Research before every change |
| --- | --- | --- |
| 01_off_by_one | PASS, 5 steps, 253 s | PASS, 7 steps, 516 s |
| 02_empty_input | PASS, 5 steps, 321 s | PASS, 6 steps, 234 s |
| 03_rename_across_files | PASS, 7 steps, 294 s | **FAIL**, 6 steps, 978 s |
| 04_add_feature | PASS, 6 steps, 579 s | **FAIL**, 8 steps, 2151 s |
| 05_parse_dates | PASS, 5 steps, 155 s | PASS, 5 steps, 371 s |
| **Total** | **5/5, 26.7 min** | **3/5, 70.8 min** |

Raw rows: `evals/results_qwen3_4b_research_every_task.json`.

- Both failures are the multi-step tasks, where the conversation grows longest. With an 8k context on a 4 GB GPU, the added doc pages overflow the window and Ollama drops the oldest messages, including the system prompt and the task.
- Task 03 never needed docs at all: it's a broken import between two of the repo's own files.
- Fix applied: research only before code that calls library APIs, doc chunks cut to 2,000 characters, and per-task traces saved to `evals/traces/` so failures can be diagnosed.
