import os

from localcoder import config


def get_llm(model: str | None = None):
    """Return the chat model. Local Ollama by default; set LLM_PROVIDER=anthropic to swap."""
    if os.getenv("LLM_PROVIDER", "ollama") == "anthropic":
        from langchain_anthropic import ChatAnthropic  # uv add langchain-anthropic
        return ChatAnthropic(model=model or os.environ["ANTHROPIC_MODEL"], temperature=0)

    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=model or config.MODEL,
        base_url=config.BASE_URL,
        temperature=0,
        num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),  # 8192 fits a 4 GB GPU
        reasoning=os.getenv("OLLAMA_REASONING", "true") != "false",
    )
