from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from localcoder import graph as G

def test_reject_routes_back(monkeypatch):
    calls = iter([
        AIMessage("", tool_calls=[{"name": "write_file", "args": {"path": "x.py", "content": ""}, "id": "1"}]),
        AIMessage("OK, I won't write it."),
    ])
    monkeypatch.setattr(G, "llm", type("L", (), {"invoke": lambda self, m: next(calls)})())
    app = G.build_graph(InMemorySaver())
    cfg = {"configurable": {"thread_id": "t1"}}
    first = app.invoke({"messages": [("user", "make x.py")]}, cfg)
    assert "__interrupt__" in first
    final = app.invoke(Command(resume={"approved": False, "feedback": "no"}), cfg)
    assert "REJECTED" in final["messages"][-2].content