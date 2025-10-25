"""Export helpers for CSV and JSON exports."""

import csv
import json
from datetime import datetime


def export_csv(kills_data, file_path):
    """Write kills_data (iterable of dicts) to CSV file_path."""
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "killer", "victim", "weapon"])
        for kill in kills_data:
            writer.writerow(
                [
                    (
                        kill["timestamp"].isoformat()
                        if hasattr(kill["timestamp"], "isoformat")
                        else str(kill["timestamp"])
                    ),
                    kill.get("killer", ""),
                    kill.get("victim", ""),
                    kill.get("weapon", ""),
                ]
            )


def export_json(kills_data, stats, player_name, file_path):
    """Export kills_data and stats to a JSON file."""
    data = {
        "player_name": player_name,
        "export_time": datetime.now().isoformat(),
        "statistics": {
            "total_kills": stats.get("total_kills", 0),
            "total_deaths": stats.get("total_deaths", 0),
            "kill_death_ratio": stats.get("total_kills", 0)
            / max(stats.get("total_deaths", 0), 1),
            "max_kill_streak": stats.get("max_kill_streak", 0),
            "max_death_streak": stats.get("max_death_streak", 0),
        },
        "kill_events": [
            {
                "timestamp": (
                    kill["timestamp"].isoformat()
                    if hasattr(kill["timestamp"], "isoformat")
                    else str(kill["timestamp"])
                ),
                "killer": kill.get("killer", ""),
                "victim": kill.get("victim", ""),
                "weapon": kill.get("weapon", ""),
            }
            for kill in kills_data
        ],
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
