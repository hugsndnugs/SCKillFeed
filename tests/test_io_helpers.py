import csv
import os
from datetime import datetime

from lib import io_helpers


def test_resolve_auto_log_path_tmpdir(tmp_path, monkeypatch):
    # When called with a relative path the function returns an absolute path.
    # The implementation prefers the project layout; here we assert it's
    # absolute and that the tail path matches the requested relative path
    monkeypatch.chdir(tmp_path)
    resolved = io_helpers.resolve_auto_log_path("logs/test.csv")
    assert os.path.isabs(resolved)
    # normalize both sides to avoid mixed separators across platforms
    assert os.path.normpath(resolved).endswith(
        os.path.normpath(os.path.join("logs", "test.csv"))
    )


def test_append_kill_to_csv_creates_header_and_row(tmp_path):
    csv_path = tmp_path / "kills.csv"
    data = {
        # pass a datetime object to ensure both object and string paths work
        "timestamp": datetime.utcnow(),
        "killer": "Alice",
        "victim": "Bob",
        "weapon": "Laser",
    }

    # first append should create file and header
    io_helpers.append_kill_to_csv(str(csv_path), data)
    assert csv_path.exists()

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["killer"] == "Alice"

    # second append should add another row
    data2 = data.copy()
    data2["killer"] = "Carol"
    io_helpers.append_kill_to_csv(str(csv_path), data2)
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[1]["killer"] == "Carol"
