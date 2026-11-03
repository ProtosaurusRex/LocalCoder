import sys, time, json
from langchain_core.tools import tool
from localcoder.llm import get_llm
from localcoder.tools import ALL_TOOLS

@tool
def read_file(path: str) -> str:
    """Read a text file from the workspace."""
    return ""

PROMPT = "Open src/app.py and tell me what the main function does."
TRIALS = 10

for model in sys.argv[1:]:
    llm = get_llm(model).bind_tools(ALL_TOOLS)
    called, valid, secs = 0, 0, []
    for _ in range(TRIALS):
        t0 = time.perf_counter()
        msg = llm.invoke(PROMPT)
        if not msg.tool_calls: print(model, repr(msg.content[:200]))
        secs.append(time.perf_counter() - t0)
        if msg.tool_calls:
            called += 1
            if msg.tool_calls[0]["args"].get("path", "").endswith("app.py"):
                valid += 1
    print(json.dumps({"model": model, "tool_call_rate": called / TRIALS,
                      "valid_args": valid / TRIALS,
                      "avg_s": round(sum(secs) / TRIALS, 2)}))