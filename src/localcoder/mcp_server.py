import os, uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from mcp.server.mcpserver import MCPServer   # mcp 2.x; FastMCP was renamed
from localcoder import docs as D
from localcoder import tools as T
from localcoder.graph import build_graph

mcp = MCPServer(name="localcoder")
ALLOW_WRITE = os.getenv("LOCALCODER_MCP_WRITE") == "1"

@mcp.tool()
def list_files(folder: str = ".") -> str:
    """List files in the LocalCoder workspace."""
    return T.list_files.invoke({"folder": folder})

@mcp.tool()
def read_file(path: str) -> str:
    """Read a workspace file with line numbers."""
    return T.read_file.invoke({"path": path})

@mcp.tool()
def search_code(query: str) -> str:
    """Search workspace files for a string."""
    return T.search_code.invoke({"query": query})

@mcp.tool()
def ask_localcoder(question: str) -> str:
    """Ask the local Ollama agent a read-only question about the workspace code."""
    app = build_graph(InMemorySaver())
    cfg = {"configurable": {"thread_id": uuid.uuid4().hex}, "recursion_limit": 100}
    result = app.invoke({"messages": [("user", question)]}, cfg)
    while "__interrupt__" in result:   # auto-reject any write in read-only mode
        result = app.invoke(Command(resume={"approved": False,
                     "feedback": "Read-only mode: answer without changing files."}), cfg)
    return result["messages"][-1].content

@mcp.tool()
def list_doc_sources() -> str:
    """List the configured documentation sources."""
    return D.list_doc_sources.invoke({})


@mcp.tool()
def search_docs(source: str, query: str) -> str:
    """Search one documentation source's index for matching pages."""
    return D.search_docs.invoke({"source": source, "query": query})


@mcp.tool()
def fetch_doc(url: str, start: int = 0) -> str:
    """Read a documentation page (allowed domains only), in chunks."""
    return D.fetch_doc.invoke({"url": url, "start": start})


if ALLOW_WRITE:
    @mcp.tool()
    def edit_file(path: str, old: str, new: str) -> str:
        """Replace one exact snippet in a workspace file."""
        return T.edit_file.invoke({"path": path, "old": old, "new": new})

def main() -> None:
    mcp.run()   # stdio transport