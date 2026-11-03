import argparse, uuid
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from localcoder.graph import build_graph

console = Console()

def preview(call: dict) -> None:
    name, args = call["name"], call["args"]
    if name == "edit_file":
        body = f"--- {args['path']}\n- " + args["old"].replace("\n", "\n- ") \
             + "\n+ " + args["new"].replace("\n", "\n+ ")
        console.print(Panel(Syntax(body, "diff"), title="edit_file"))
    elif name == "write_file":
        console.print(Panel(Syntax(args["content"], "python", line_numbers=True),
                            title=f"write_file → {args['path']}"))
    else:
        console.print(Panel(args.get("command", str(args)), title=name))

def ask() -> dict:
    ans = console.input("[bold]Approve? \\[y]es / \\[n]o / or type feedback: [/]").strip()
    if ans.lower() in {"y", "yes", ""}:
        return {"approved": True}
    return {"approved": False, "feedback": None if ans.lower() in {"n", "no"} else ans}

def run_turn(app, payload, cfg) -> None:
    while True:
        paused = None
        for chunk in app.stream(payload, cfg, stream_mode="updates"):
            if "__interrupt__" in chunk:
                paused = chunk["__interrupt__"][0].value
                continue
            for node, update in chunk.items():
                for msg in (update or {}).get("messages", []):
                    for c in getattr(msg, "tool_calls", []) or []:
                        console.print(f"[cyan]→ {c['name']}[/] {c['args'].get('path', '')}")
                    if node == "agent" and msg.content and not getattr(msg, "tool_calls", None):
                        console.print(Panel(msg.content, title="LocalCoder"))
        if not paused:
            return
        for call in paused["tool_calls"]:
            preview(call)
        payload = Command(resume=ask())

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--thread", default=None, help="resume an earlier session")
    thread = p.parse_args().thread or uuid.uuid4().hex[:8]
    cfg = {"configurable": {"thread_id": thread}, "recursion_limit": 100}
    with SqliteSaver.from_conn_string("checkpoints.db") as saver:
        app = build_graph(saver)
        console.print(f"[dim]thread {thread} · type 'exit' to quit[/]")
        while (task := console.input("[bold green]you> [/]").strip()) != "exit":
            if task:
                run_turn(app, {"messages": [("user", task)]}, cfg)