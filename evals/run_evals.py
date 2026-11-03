"""Run every task in evals/tasks/ through the agent and score it by pytest.

Usage: uv run python evals/run_evals.py qwen3:4b [llama3.2 ...]
Each task is copied to a temp folder, writes are auto-approved inside that
sandbox, and the task passes if `pytest -q` exits 0 afterwards.
"""
import json, shutil, subprocess, sys, tempfile, time, uuid
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from localcoder import config, graph as G
from localcoder.llm import get_llm
from localcoder.tools import ALL_TOOLS

TASKS = sorted(p for p in Path("evals/tasks").iterdir() if p.is_dir())


TRACE_DIR = Path("evals/traces")


def save_trace(task_name: str, messages) -> None:
    """Write each step (tool calls, truncated tool output, final answer) for debugging failures."""
    model = G.llm.bound.model if hasattr(G.llm, "bound") else "model"
    folder = TRACE_DIR / model.replace(":", "_")
    folder.mkdir(parents=True, exist_ok=True)
    steps = [{"type": m.type,
              "tool_calls": [{"name": c["name"], "args": c["args"]} for c in getattr(m, "tool_calls", None) or []],
              "content": str(m.content)[:1500]} for m in messages]
    (folder / f"{task_name}.json").write_text(json.dumps(steps, indent=2))


def run_task(task: Path) -> dict:
    work = Path(tempfile.mkdtemp())
    shutil.copytree(task, work, dirs_exist_ok=True)
    config.WORKSPACE = work                      # tools read this at call time
    app = G.build_graph(InMemorySaver())
    cfg = {"configurable": {"thread_id": uuid.uuid4().hex}, "recursion_limit": 100}
    prompt = json.loads((task / "task.json").read_text())["prompt"]
    t0 = time.perf_counter()
    out = app.invoke({"messages": [("user", prompt)]}, cfg)
    while "__interrupt__" in out:                # auto-approve inside the sandbox
        out = app.invoke(Command(resume={"approved": True}), cfg)
    passed = subprocess.run(["pytest", "-q"], cwd=work, capture_output=True).returncode == 0
    errors = sum("ERROR" in str(m.content) for m in out["messages"] if m.type == "tool")
    save_trace(task.name, out["messages"])
    return {"task": task.name, "passed": passed, "steps": out.get("steps", 0),
            "tool_errors": errors, "seconds": round(time.perf_counter() - t0, 1)}


if __name__ == "__main__":
    for model in sys.argv[1:]:
        G.llm = get_llm(model).bind_tools(ALL_TOOLS)
        rows = []
        for t in TASKS:
            row = run_task(t)
            rows.append(row)
            print(f"  {model} {row['task']}: {'PASS' if row['passed'] else 'FAIL'} "
                  f"({row['steps']} steps, {row['seconds']}s)")
        rate = sum(r["passed"] for r in rows) / len(rows)
        Path(f"evals/results_{model.replace(':', '_')}.json").write_text(json.dumps(rows, indent=2))
        print(f"{model}: {rate:.0%} pass, avg {sum(r['steps'] for r in rows) / len(rows):.1f} steps")
