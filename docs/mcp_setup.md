# Using LocalCoder as an MCP server (optional)

LocalCoder ships an MCP server so any MCP client (Claude Desktop, Claude Code, MCP Inspector) can use its workspace tools. This is optional: the main way to use LocalCoder is the `localcoder` CLI.

## Tools exposed

| Tool | What it does |
| --- | --- |
| `list_files` | List files in the workspace |
| `read_file` | Read a workspace file with line numbers |
| `search_code` | Plain-text search across the workspace |
| `ask_localcoder` | Hand a read-only question to the local Ollama agent; any write it attempts is auto-rejected |
| `edit_file` | Only when `LOCALCODER_MCP_WRITE=1` is set: replace one exact snippet in a file |

Writes are off by default. The client already asks before calling tools, but a second process editing files is easy to get wrong, so it's opt-in.

**Speed note:** `ask_localcoder` runs the full local agent, which takes about 15 seconds per step with `qwen3:4b` on a 4 GB GPU. On modest hardware, the three read tools are the useful part; on a bigger GPU, `ask_localcoder` lets a hosted model delegate repo exploration to a free local one.

## Try it with MCP Inspector

```powershell
uv run mcp dev src/localcoder/mcp_server.py
```

## Register with Claude Desktop

Add this to `claude_desktop_config.json`, replacing the path with where you cloned the repo, then restart Claude Desktop:

```json
{
  "mcpServers": {
    "localcoder": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\ProtobrainComplex", "run", "localcoder-mcp"]
    }
  }
}
```

To enable `edit_file`, add `"env": {"LOCALCODER_MCP_WRITE": "1"}` to that entry.

## Register with Claude Code

```bash
claude mcp add localcoder -- uv --directory /path/to/ProtobrainComplex run localcoder-mcp
```

Ollama must be running for `ask_localcoder`; the three read tools work without it.
