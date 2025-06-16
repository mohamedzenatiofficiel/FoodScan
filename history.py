import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path("history.json")


def load_history(file_path=HISTORY_FILE):
    """Load history entries from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def append_history(barcode, name, nutriscore, date=None, file_path=HISTORY_FILE):
    """Append a new scan entry to the history file."""
    history = load_history(file_path)
    entry = {
        "barcode": barcode,
        "name": name,
        "nutriscore": nutriscore,
        "date": date or datetime.now().isoformat(timespec="seconds"),
    }
    history.append(entry)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

