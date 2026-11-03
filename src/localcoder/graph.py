from typing import Annotated, Literal, TypedDict
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from localcoder import config
from localcoder.llm import get_llm
from localcoder.prompts import SYSTEM_PROMPT
from localcoder.tools import ALL_TOOLS, GATED_NAMES
from langchain_core.messages import ToolMessage
from langgraph.types import Command, interrupt

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    steps: int

llm = get_llm().bind_tools(ALL_TOOLS)

def agent(state: AgentState):
    steps = state.get("steps", 0)
    if steps >= config.MAX_STEPS:
        return {"messages": [AIMessage(f"Stopped: hit the {config.MAX_STEPS}-step limit.")]}
    reply = llm.invoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
    return {"messages": [reply], "steps": steps + 1}

def route(state: AgentState) -> str:
    calls = getattr(state["messages"][-1], "tool_calls", None)
    if not calls:
        return END
    return "approve" if any(c["name"] in GATED_NAMES for c in calls) else "tools"

def approve(state: AgentState) -> Command[Literal["tools", "agent"]]:
    calls = state["messages"][-1].tool_calls
    decision = interrupt({
        "tool_calls": [{"name": c["name"], "args": c["args"]} for c in calls]
    })
    if decision.get("approved"):
        return Command(goto="tools")
    feedback = decision.get("feedback") or "Rejected by reviewer."
    rejected = [
        ToolMessage(content=f"REJECTED: {feedback}", tool_call_id=c["id"], name=c["name"])
        for c in calls
    ]
    return Command(goto="agent", update={"messages": rejected})

def build_graph(checkpointer=None):
    g = StateGraph(AgentState)
    g.add_node("agent", agent)
    g.add_node("approve", approve)
    g.add_node("tools", ToolNode(ALL_TOOLS, handle_tool_errors=True))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, ["tools", "approve", END])
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=checkpointer)