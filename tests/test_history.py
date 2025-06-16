import os
tempfile = __import__("tempfile")

from history import load_history, append_history


def test_load_history_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "history.json")
        assert load_history(path) == []


def test_append_history_adds_entry():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "history.json")
        append_history("123", "Test", "a", "2024-01-01T00:00:00", path)
        data = load_history(path)
        assert len(data) == 1
        entry = data[0]
        assert entry["barcode"] == "123"
        assert entry["name"] == "Test"
        assert entry["nutriscore"] == "a"
        assert entry["date"] == "2024-01-01T00:00:00"
