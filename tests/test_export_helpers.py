import csv
import json

from lib import export_helpers


def sample_kills():
    return [
        {
            "timestamp": "2020-01-01T00:00:00",
            "killer": "A",
            "victim": "B",
            "weapon": "X",
        },
        {
            "timestamp": "2020-01-01T00:01:00",
            "killer": "C",
            "victim": "D",
            "weapon": "Y",
        },
    ]


def test_export_csv_writes_file(tmp_path):
    kills = sample_kills()
    out = tmp_path / "out.csv"
    export_helpers.export_csv(kills, str(out))
    assert out.exists()
    with open(out, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["killer"] == "A"


def test_export_json_writes_file(tmp_path):
    kills = sample_kills()
    stats = {"total_kills": 2}
    out = tmp_path / "out.json"
    export_helpers.export_json(kills, stats, "Player1", str(out))
    assert out.exists()
    with open(out, encoding="utf-8") as fh:
        payload = json.load(fh)
    # export_helpers uses 'player_name' and 'statistics' keys
    assert payload["player_name"] == "Player1"
    assert payload["statistics"]["total_kills"] == 2
