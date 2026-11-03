import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
WORKSPACE = Path(os.getenv("WORKSPACE_ROOT", "./workspace")).resolve()
MAX_STEPS = int(os.getenv("MAX_STEPS", "25"))
COMMAND_TIMEOUT_S = int(os.getenv("COMMAND_TIMEOUT_S", "60"))
WORKSPACE.mkdir(parents=True, exist_ok=True)
DOC_SOURCES = Path(os.getenv("DOC_SOURCES", "doc_sources.json")).resolve()
DOCS_MAX_CHARS = int(os.getenv("DOCS_MAX_CHARS", "2000"))
