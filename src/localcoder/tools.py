import shlex, subprocess
from pathlib import Path
from langchain_core.tools import tool
from localcoder import config
from localcoder.docs import DOCS_TOOLS

SKIP = {".git", ".venv", "__pycache__", "node_modules"}
ALLOWED_CMDS = {"pytest", "python", "uv", "ruff", "git"}

def _safe(path: str) -> Path:
    p = (config.WORKSPACE / path).resolve()
    if not p.is_relative_to(config.WORKSPACE):
        raise ValueError(f"Path escapes workspace: {path}")
    return p

@tool
def list_files(folder: str = ".") -> str:
    """List files under a workspace folder (relative path)."""
    root = _safe(folder)
    out = [str(p.relative_to(config.WORKSPACE)) for p in root.rglob("*")
           if p.is_file() and not SKIP & set(p.parts)]
    return "\n".join(sorted(out)[:300]) or "(empty)"

@tool
def read_file(path: str) -> str:
    """Read a workspace file. Returns numbered lines."""
    lines = _safe(path).read_text(encoding="utf-8").splitlines()
    return "\n".join(f"{i+1:4} | {l}" for i, l in enumerate(lines))

@tool
def search_code(query: str) -> str:
    """Find lines containing `query` across workspace files."""
    hits = []
    for p in config.WORKSPACE.rglob("*.*"):
        if SKIP & set(p.parts) or not p.is_file():
            continue
        try:
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if query in line:
                    hits.append(f"{p.relative_to(config.WORKSPACE)}:{n}: {line.strip()}")
        except UnicodeDecodeError:
            continue
        if len(hits) >= 50:
            break
    return "\n".join(hits) or "No matches."

@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a workspace file with `content`."""
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {path}"

@tool
def edit_file(path: str, old: str, new: str) -> str:
    """Replace the single exact occurrence of `old` with `new` in a file."""
    p = _safe(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        return f"ERROR: snippet found {count} times; it must match exactly once."
    p.write_text(text.replace(old, new), encoding="utf-8")
    return f"Edited {path}"

@tool
def run_command(command: str) -> str:
    """Run an allowlisted command (pytest, python, uv, ruff, git) in the workspace."""
    args = shlex.split(command)
    if not args or args[0] not in ALLOWED_CMDS:
        return f"ERROR: '{args[0] if args else ''}' is not allowed."
    try:
        r = subprocess.run(args, cwd=config.WORKSPACE, capture_output=True,
                           text=True, timeout=config.COMMAND_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out."
    return f"exit={r.returncode}\n{(r.stdout + r.stderr)[-4000:]}"

SAFE_TOOLS = [list_files, read_file, search_code] + DOCS_TOOLS
GATED_TOOLS = [write_file, edit_file, run_command]
ALL_TOOLS = SAFE_TOOLS + GATED_TOOLS
GATED_NAMES = {t.name for t in GATED_TOOLS}