import pytest
from localcoder.tools import read_file, edit_file

def test_escape_blocked():
    with pytest.raises(ValueError):
        read_file.invoke({"path": "../pyproject.toml"})

def test_edit_requires_unique_match(tmp_path, monkeypatch):
    from localcoder import config
    monkeypatch.setattr(config, "WORKSPACE", tmp_path)
    (tmp_path / "a.py").write_text("x = 1\nx = 1\n")
    assert "2 times" in edit_file.invoke({"path": "a.py", "old": "x = 1", "new": "x = 2"})