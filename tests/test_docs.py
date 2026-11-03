"""Offline tests for the documentation tools (no network calls)."""
import json

import pytest

from localcoder import config, docs


@pytest.fixture
def demo_source(tmp_path, monkeypatch):
    path = tmp_path / "doc_sources.json"
    path.write_text(json.dumps({"sources": [{
        "name": "demo", "description": "Demo docs",
        "index": "https://demo.dev/llms.txt", "domains": ["demo.dev"],
    }]}))
    monkeypatch.setattr(config, "DOC_SOURCES", path)


def test_domain_allowlist(demo_source):
    assert docs._allowed("https://demo.dev/page.md")
    assert docs._allowed("https://api.demo.dev/page.md")
    assert not docs._allowed("https://evil.com/demo.dev")
    assert not docs._allowed("https://notdemo.dev/page.md")


def test_search_filters_and_ranks(demo_source, monkeypatch):
    index = ("# Demo\n"
             "- [Interrupts](https://demo.dev/interrupts.md)\n"
             "- [Streaming](https://demo.dev/streaming.md)\n"
             "- [GRAPH\\_RECURSION\\_LIMIT](https://demo.dev/errors/GRAPH\\_RECURSION\\_LIMIT.md)\n"
             "- [Interrupt elsewhere](https://evil.com/interrupts.md)\n")
    monkeypatch.setattr(docs, "_get", lambda url: (url, "text/plain", index))
    out = docs.search_docs.invoke({"source": "demo", "query": "interrupt"})
    assert "https://demo.dev/interrupts.md" in out
    assert "streaming" not in out and "evil.com" not in out
    out = docs.search_docs.invoke({"source": "demo", "query": "recursion"})
    assert "GRAPH_RECURSION_LIMIT.md" in out          # markdown escapes removed


def test_unknown_source(demo_source):
    assert docs.search_docs.invoke({"source": "nope", "query": "x"}).startswith("ERROR")


def test_fetch_blocks_other_domains(demo_source):
    assert docs.fetch_doc.invoke({"url": "https://evil.com/page"}).startswith("ERROR")


def test_fetch_chunks_long_pages(demo_source, monkeypatch):
    monkeypatch.setattr(config, "DOCS_MAX_CHARS", 100)
    monkeypatch.setattr(docs, "_get", lambda url: (url, "text/markdown", "a" * 250))
    first = docs.fetch_doc.invoke({"url": "https://demo.dev/long.md"})
    assert "start=100" in first
    last = docs.fetch_doc.invoke({"url": "https://demo.dev/long.md", "start": 200})
    assert "more chars" not in last


def test_html_index(demo_source, monkeypatch):
    html = ('<html><body><nav><a href="/skip">Nav</a></nav><div role="main">'
            '<a href="library/datetime.html">datetime</a>'
            '<a href="https://evil.com/x">evil</a></div></body></html>')
    monkeypatch.setattr(docs, "_get", lambda url: ("https://demo.dev/3/index.html", "text/html", html))
    out = docs.search_docs.invoke({"source": "demo", "query": "datetime"})
    assert "https://demo.dev/3/library/datetime.html" in out
