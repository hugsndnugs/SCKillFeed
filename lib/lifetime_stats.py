"""Lifetime statistics calculation from CSV log files.

This module provides functions to read historical kill data from CSV files
and calculate comprehensive lifetime statistics.
"""

import csv
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def load_lifetime_data(csv_path: str, player_name: str) -> List[Dict]:
    """Load kill data from CSV file, filtering for player-specific events.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        csv_path: Path to the CSV file containing kill logs
        player_name: Player name to filter events for (case-insensitive)

=======
=======
>>>>>>> Stashed changes
    
    Args:
        csv_path: Path to the CSV file containing kill logs
        player_name: Player name to filter events for (case-insensitive)
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        List of kill event dictionaries with keys: timestamp, killer, victim, weapon
        Empty list if file doesn't exist or is empty
    """
    kill_data = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not csv_path or not player_name:
        logger.debug("Missing csv_path or player_name for lifetime stats")
        return kill_data

=======
=======
>>>>>>> Stashed changes
    
    if not csv_path or not player_name:
        logger.debug("Missing csv_path or player_name for lifetime stats")
        return kill_data
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    try:
        if not os.path.exists(csv_path):
            logger.debug(f"CSV file not found: {csv_path}")
            return kill_data
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        player_name_lower = player_name.lower()

        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            # Validate CSV has required columns
            required_columns = ["timestamp", "killer", "victim", "weapon"]
            if not all(col in reader.fieldnames for col in required_columns):
                logger.warning(
                    f"CSV missing required columns. Found: {reader.fieldnames}"
                )
                return kill_data

=======
=======
>>>>>>> Stashed changes
        
        player_name_lower = player_name.lower()
        
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            
            # Validate CSV has required columns
            required_columns = ["timestamp", "killer", "victim", "weapon"]
            if not all(col in reader.fieldnames for col in required_columns):
                logger.warning(f"CSV missing required columns. Found: {reader.fieldnames}")
                return kill_data
            
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            for row_idx, row in enumerate(reader, start=2):  # Start at 2 (header + 1)
                try:
                    # Get raw values
                    killer = row.get("killer", "").strip()
                    victim = row.get("victim", "").strip()
                    weapon = row.get("weapon", "").strip()
<<<<<<< Updated upstream
<<<<<<< Updated upstream

                    # Skip rows with "unknown" values (case-insensitive)
                    if (
                        killer.lower() == "unknown"
                        or victim.lower() == "unknown"
                        or weapon.lower() == "unknown"
                    ):
                        continue

                    # Skip rows where player is not involved
                    killer_lower = killer.lower()
                    victim_lower = victim.lower()

                    if player_name_lower not in (killer_lower, victim_lower):
                        continue

=======
=======
>>>>>>> Stashed changes
                    
                    # Skip rows with "unknown" values (case-insensitive)
                    if killer.lower() == "unknown" or victim.lower() == "unknown" or weapon.lower() == "unknown":
                        continue
                    
                    # Skip rows where player is not involved
                    killer_lower = killer.lower()
                    victim_lower = victim.lower()
                    
                    if player_name_lower not in (killer_lower, victim_lower):
                        continue
                    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    # Parse timestamp
                    timestamp_str = row.get("timestamp", "")
                    try:
                        # Try ISO format first
                        if "T" in timestamp_str:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                        else:
                            # Try other common formats
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )
                    except (ValueError, AttributeError):
                        # If parsing fails, skip this row but log a warning
                        logger.debug(
                            f"Skipping row {row_idx}: invalid timestamp '{timestamp_str}'"
                        )
                        continue

                    kill_data.append(
                        {
                            "timestamp": timestamp,
                            "killer": killer,
                            "victim": victim,
                            "weapon": weapon,
                        }
                    )

                except Exception as e:
                    logger.debug(f"Error parsing CSV row {row_idx}: {e}", exc_info=True)
                    continue

        logger.info(f"Loaded {len(kill_data)} kill events from {csv_path}")
        return kill_data

=======
=======
>>>>>>> Stashed changes
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        else:
                            # Try other common formats
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except (ValueError, AttributeError):
                        # If parsing fails, skip this row but log a warning
                        logger.debug(f"Skipping row {row_idx}: invalid timestamp '{timestamp_str}'")
                        continue
                    
                    kill_data.append({
                        "timestamp": timestamp,
                        "killer": killer,
                        "victim": victim,
                        "weapon": weapon,
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing CSV row {row_idx}: {e}", exc_info=True)
                    continue
        
        logger.info(f"Loaded {len(kill_data)} kill events from {csv_path}")
        return kill_data
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    except PermissionError:
        logger.error(f"Permission denied reading CSV file: {csv_path}")
        return kill_data
    except Exception as e:
        logger.error(f"Error loading lifetime data from {csv_path}: {e}", exc_info=True)
        return kill_data


def calculate_lifetime_stats(kill_data: List[Dict], player_name: str) -> Dict:
    """Calculate comprehensive lifetime statistics from kill data.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering (case-insensitive)

=======
=======
>>>>>>> Stashed changes
    
    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering (case-insensitive)
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        Dictionary containing all lifetime statistics
    """
    stats = {
        "total_kills": 0,
        "total_deaths": 0,
        "lifetime_kd_ratio": 0.0,
        "total_sessions": 0,
        "first_kill_date": None,
        "last_kill_date": None,
        "total_play_time_hours": 0.0,
        "suicide_count": 0,
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not kill_data:
        return stats

=======
=======
>>>>>>> Stashed changes
    
    if not kill_data:
        return stats
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    player_name_lower = player_name.lower()
    timestamps = []
    session_starts = []
    last_timestamp = None
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
    weapons_used = Counter()
    weapons_against = Counter()
    victims = Counter()
    killers = Counter()
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
    for event in kill_data:
        killer = event.get("killer", "")
        victim = event.get("victim", "")
        weapon = event.get("weapon", "")
        timestamp = event.get("timestamp")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        if not isinstance(timestamp, datetime):
            continue

        timestamps.append(timestamp)

=======
=======
>>>>>>> Stashed changes
        
        if not isinstance(timestamp, datetime):
            continue
        
        timestamps.append(timestamp)
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # Track session starts (events more than 2 hours apart)
        if last_timestamp:
            time_diff = (timestamp - last_timestamp).total_seconds() / 3600
            if time_diff > 2.0:  # 2 hour gap = new session
                session_starts.append(timestamp)
        else:
            session_starts.append(timestamp)
        last_timestamp = timestamp
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        killer_lower = killer.lower()
        victim_lower = victim.lower()

=======
=======
>>>>>>> Stashed changes
        
        killer_lower = killer.lower()
        victim_lower = victim.lower()
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # Handle suicides
        if killer_lower == victim_lower:
            if killer_lower == player_name_lower:
                stats["total_deaths"] += 1
                stats["suicide_count"] += 1
                # Only count non-unknown weapons
                if weapon.lower() != "unknown":
                    weapons_against[weapon] += 1
            continue
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        # Skip unknown values in statistics
        weapon_lower = weapon.lower()

=======
=======
>>>>>>> Stashed changes
        
        # Skip unknown values in statistics
        weapon_lower = weapon.lower()
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # Player kills
        if killer_lower == player_name_lower:
            stats["total_kills"] += 1
            # Only count non-unknown weapons and victims
            if weapon_lower != "unknown":
                weapons_used[weapon] += 1
            if victim_lower != "unknown":
                victims[victim] += 1
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
=======
        
>>>>>>> Stashed changes
        # Player deaths
        if victim_lower == player_name_lower:
            stats["total_deaths"] += 1
            # Only count non-unknown weapons and killers
            if weapon_lower != "unknown":
                weapons_against[weapon] += 1
            if killer_lower != "unknown":
                killers[killer] += 1
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
    # Calculate derived stats
    if stats["total_deaths"] > 0:
        stats["lifetime_kd_ratio"] = stats["total_kills"] / stats["total_deaths"]
    elif stats["total_kills"] > 0:
        stats["lifetime_kd_ratio"] = float(stats["total_kills"])
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if timestamps:
        stats["first_kill_date"] = min(timestamps)
        stats["last_kill_date"] = max(timestamps)
        time_span = (
            stats["last_kill_date"] - stats["first_kill_date"]
        ).total_seconds() / 3600
        stats["total_play_time_hours"] = max(0, time_span)

    # Estimate sessions (session starts + 1 for first session)
    stats["total_sessions"] = len(session_starts)

=======
=======
>>>>>>> Stashed changes
    
    if timestamps:
        stats["first_kill_date"] = min(timestamps)
        stats["last_kill_date"] = max(timestamps)
        time_span = (stats["last_kill_date"] - stats["first_kill_date"]).total_seconds() / 3600
        stats["total_play_time_hours"] = max(0, time_span)
    
    # Estimate sessions (session starts + 1 for first session)
    stats["total_sessions"] = len(session_starts)
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # Add counters to stats
    stats["weapons_used"] = weapons_used
    stats["weapons_against"] = weapons_against
    stats["victims"] = victims
    stats["killers"] = killers
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
    return stats


def get_weapon_stats(kill_data: List[Dict], player_name: str) -> Dict:
    """Calculate detailed weapon statistics.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering

=======
=======
>>>>>>> Stashed changes
    
    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        Dictionary with weapon statistics including mastery table
    """
    weapon_stats = {
        "most_used": ("", 0),
        "most_effective": ("", 0.0),
        "mastery_table": [],
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not kill_data:
        return weapon_stats

    player_name_lower = player_name.lower()

=======
=======
>>>>>>> Stashed changes
    
    if not kill_data:
        return weapon_stats
    
    player_name_lower = player_name.lower()
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # Track kills and deaths per weapon
    weapon_kills = Counter()
    weapon_deaths = Counter()
    weapon_first_use = {}
    weapon_last_use = {}
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
    for event in kill_data:
        killer = event.get("killer", "").lower()
        victim = event.get("victim", "").lower()
        weapon = event.get("weapon", "")
        timestamp = event.get("timestamp")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        # Skip unknown weapons
        if weapon.lower() == "unknown":
            continue

=======
=======
>>>>>>> Stashed changes
        
        # Skip unknown weapons
        if weapon.lower() == "unknown":
            continue
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        if killer == player_name_lower and killer != victim:
            weapon_kills[weapon] += 1
            if weapon not in weapon_first_use:
                weapon_first_use[weapon] = timestamp
            weapon_last_use[weapon] = timestamp
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        if victim == player_name_lower and killer != victim:
            weapon_deaths[weapon] += 1

    # Find most used weapon
    if weapon_kills:
        weapon_stats["most_used"] = weapon_kills.most_common(1)[0]

=======
=======
>>>>>>> Stashed changes
        
        if victim == player_name_lower and killer != victim:
            weapon_deaths[weapon] += 1
    
    # Find most used weapon
    if weapon_kills:
        weapon_stats["most_used"] = weapon_kills.most_common(1)[0]
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # Calculate K/D for each weapon and find most effective
    weapon_kd = {}
    for weapon in set(list(weapon_kills.keys()) + list(weapon_deaths.keys())):
        kills = weapon_kills.get(weapon, 0)
        deaths = weapon_deaths.get(weapon, 0)
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
=======
        
>>>>>>> Stashed changes
        if deaths > 0:
            kd = kills / deaths
        elif kills > 0:
            kd = float(kills)
        else:
            kd = 0.0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        weapon_kd[weapon] = kd

        if kd > weapon_stats["most_effective"][1]:
            weapon_stats["most_effective"] = (weapon, kd)

    # Build mastery table
    total_kills = sum(weapon_kills.values())
    mastery_list = []

=======
=======
>>>>>>> Stashed changes
        
        weapon_kd[weapon] = kd
        
        if kd > weapon_stats["most_effective"][1]:
            weapon_stats["most_effective"] = (weapon, kd)
    
    # Build mastery table
    total_kills = sum(weapon_kills.values())
    mastery_list = []
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for weapon in set(list(weapon_kills.keys()) + list(weapon_deaths.keys())):
        kills = weapon_kills.get(weapon, 0)
        deaths = weapon_deaths.get(weapon, 0)
        kd = weapon_kd.get(weapon, 0.0)
        usage_pct = (kills / total_kills * 100) if total_kills > 0 else 0.0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        mastery_list.append(
            {
                "weapon": weapon,
                "kills": kills,
                "deaths": deaths,
                "kd_ratio": kd,
                "usage_percentage": usage_pct,
                "first_use": weapon_first_use.get(weapon),
                "last_use": weapon_last_use.get(weapon),
            }
        )

    # Sort by kills descending
    mastery_list.sort(key=lambda x: x["kills"], reverse=True)
    weapon_stats["mastery_table"] = mastery_list

=======
=======
>>>>>>> Stashed changes
        
        mastery_list.append({
            "weapon": weapon,
            "kills": kills,
            "deaths": deaths,
            "kd_ratio": kd,
            "usage_percentage": usage_pct,
            "first_use": weapon_first_use.get(weapon),
            "last_use": weapon_last_use.get(weapon),
        })
    
    # Sort by kills descending
    mastery_list.sort(key=lambda x: x["kills"], reverse=True)
    weapon_stats["mastery_table"] = mastery_list
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    return weapon_stats


def get_pvp_stats(kill_data: List[Dict], player_name: str) -> Dict:
    """Calculate player vs player statistics.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering

=======
=======
>>>>>>> Stashed changes
    
    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        Dictionary with PvP statistics
    """
    pvp_stats = {
        "most_killed": ("", 0),
        "nemesis": ("", 0),
        "rivals_table": [],
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not kill_data:
        return pvp_stats

    player_name_lower = player_name.lower()

=======
=======
>>>>>>> Stashed changes
    
    if not kill_data:
        return pvp_stats
    
    player_name_lower = player_name.lower()
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # Track encounters with each player
    player_kills = Counter()  # How many times you killed them
    player_deaths = Counter()  # How many times they killed you
    last_encounter = {}
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
=======
    
>>>>>>> Stashed changes
    for event in kill_data:
        killer = event.get("killer", "").lower()
        victim = event.get("victim", "").lower()
        timestamp = event.get("timestamp")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        # Skip unknown players
        if killer == "unknown" or victim == "unknown":
            continue

        # Skip suicides
        if killer == victim:
            continue

=======
=======
>>>>>>> Stashed changes
        
        # Skip unknown players
        if killer == "unknown" or victim == "unknown":
            continue
        
        # Skip suicides
        if killer == victim:
            continue
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # You killed someone
        if killer == player_name_lower:
            player_kills[victim] += 1
            last_encounter[victim] = timestamp
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
=======
        
>>>>>>> Stashed changes
        # Someone killed you
        if victim == player_name_lower:
            player_deaths[killer] += 1
            last_encounter[killer] = timestamp
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    # Find most killed player
    if player_kills:
        pvp_stats["most_killed"] = player_kills.most_common(1)[0]

    # Find nemesis (player who killed you most)
    if player_deaths:
        pvp_stats["nemesis"] = player_deaths.most_common(1)[0]

    # Build rivals table
    all_players = set(list(player_kills.keys()) + list(player_deaths.keys()))
    rivals_list = []

    for player in all_players:
        kills = player_kills.get(player, 0)
        deaths = player_deaths.get(player, 0)

=======
=======
>>>>>>> Stashed changes
    
    # Find most killed player
    if player_kills:
        pvp_stats["most_killed"] = player_kills.most_common(1)[0]
    
    # Find nemesis (player who killed you most)
    if player_deaths:
        pvp_stats["nemesis"] = player_deaths.most_common(1)[0]
    
    # Build rivals table
    all_players = set(list(player_kills.keys()) + list(player_deaths.keys()))
    rivals_list = []
    
    for player in all_players:
        kills = player_kills.get(player, 0)
        deaths = player_deaths.get(player, 0)
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # Calculate head-to-head K/D
        if deaths > 0:
            h2h_kd = kills / deaths
        elif kills > 0:
            h2h_kd = float(kills)
        else:
            h2h_kd = 0.0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        rivals_list.append(
            {
                "player": player,
                "killed_them": kills,
                "killed_by_them": deaths,
                "head_to_head_kd": h2h_kd,
                "last_encounter": last_encounter.get(player),
            }
        )

    # Sort by total encounters
    rivals_list.sort(key=lambda x: x["killed_them"] + x["killed_by_them"], reverse=True)
    pvp_stats["rivals_table"] = rivals_list

=======
=======
>>>>>>> Stashed changes
        
        rivals_list.append({
            "player": player,
            "killed_them": kills,
            "killed_by_them": deaths,
            "head_to_head_kd": h2h_kd,
            "last_encounter": last_encounter.get(player),
        })
    
    # Sort by total encounters
    rivals_list.sort(key=lambda x: x["killed_them"] + x["killed_by_them"], reverse=True)
    pvp_stats["rivals_table"] = rivals_list
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    return pvp_stats


def get_time_trends(kill_data: List[Dict], player_name: str) -> Dict:
    """Calculate time-based trends and statistics.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering

=======
=======
>>>>>>> Stashed changes
    
    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        Dictionary with time-based trends
    """
    trends = {
        "kills_by_day": {},
        "kills_by_week": {},
        "kills_by_month": {},
        "best_day": None,
        "best_week": None,
        "best_month": None,
        "kills_by_hour": Counter(),
        "kills_by_day_of_week": Counter(),
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not kill_data:
        return trends

    player_name_lower = player_name.lower()

=======
=======
>>>>>>> Stashed changes
    
    if not kill_data:
        return trends
    
    player_name_lower = player_name.lower()
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for event in kill_data:
        killer = event.get("killer", "").lower()
        victim = event.get("victim", "").lower()
        weapon = event.get("weapon", "")
        timestamp = event.get("timestamp")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        if not isinstance(timestamp, datetime):
            continue

        # Skip unknown values
        if killer == "unknown" or victim == "unknown" or weapon.lower() == "unknown":
            continue

        # Only count player kills (not deaths) for trends
        if killer != player_name_lower or killer == victim:
            continue

        # Group by day
        day_key = timestamp.strftime("%Y-%m-%d")
        trends["kills_by_day"][day_key] = trends["kills_by_day"].get(day_key, 0) + 1

        # Group by week (ISO week)
        week_key = f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
        trends["kills_by_week"][week_key] = trends["kills_by_week"].get(week_key, 0) + 1

        # Group by month
        month_key = timestamp.strftime("%Y-%m")
        trends["kills_by_month"][month_key] = (
            trends["kills_by_month"].get(month_key, 0) + 1
        )

        # Group by hour
        trends["kills_by_hour"][timestamp.hour] += 1

        # Group by day of week (0=Monday, 6=Sunday)
        trends["kills_by_day_of_week"][timestamp.weekday()] += 1

=======
=======
>>>>>>> Stashed changes
        
        if not isinstance(timestamp, datetime):
            continue
        
        # Skip unknown values
        if killer == "unknown" or victim == "unknown" or weapon.lower() == "unknown":
            continue
        
        # Only count player kills (not deaths) for trends
        if killer != player_name_lower or killer == victim:
            continue
        
        # Group by day
        day_key = timestamp.strftime("%Y-%m-%d")
        trends["kills_by_day"][day_key] = trends["kills_by_day"].get(day_key, 0) + 1
        
        # Group by week (ISO week)
        week_key = f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
        trends["kills_by_week"][week_key] = trends["kills_by_week"].get(week_key, 0) + 1
        
        # Group by month
        month_key = timestamp.strftime("%Y-%m")
        trends["kills_by_month"][month_key] = trends["kills_by_month"].get(month_key, 0) + 1
        
        # Group by hour
        trends["kills_by_hour"][timestamp.hour] += 1
        
        # Group by day of week (0=Monday, 6=Sunday)
        trends["kills_by_day_of_week"][timestamp.weekday()] += 1
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # Find best periods
    if trends["kills_by_day"]:
        best_day_key = max(trends["kills_by_day"].items(), key=lambda x: x[1])
        trends["best_day"] = {"date": best_day_key[0], "kills": best_day_key[1]}
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if trends["kills_by_week"]:
        best_week_key = max(trends["kills_by_week"].items(), key=lambda x: x[1])
        trends["best_week"] = {"period": best_week_key[0], "kills": best_week_key[1]}

    if trends["kills_by_month"]:
        best_month_key = max(trends["kills_by_month"].items(), key=lambda x: x[1])
        trends["best_month"] = {"period": best_month_key[0], "kills": best_month_key[1]}

=======
=======
>>>>>>> Stashed changes
    
    if trends["kills_by_week"]:
        best_week_key = max(trends["kills_by_week"].items(), key=lambda x: x[1])
        trends["best_week"] = {"period": best_week_key[0], "kills": best_week_key[1]}
    
    if trends["kills_by_month"]:
        best_month_key = max(trends["kills_by_month"].items(), key=lambda x: x[1])
        trends["best_month"] = {"period": best_month_key[0], "kills": best_month_key[1]}
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    return trends


def get_streaks_history(kill_data: List[Dict], player_name: str) -> Dict:
    """Calculate streak statistics and history.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering

=======
=======
>>>>>>> Stashed changes
    
    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        Dictionary with streak statistics
    """
    streaks = {
        "max_kill_streak": 0,
        "max_death_streak": 0,
        "current_kill_streak": 0,
        "current_death_streak": 0,
        "streak_history": [],
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not kill_data:
        return streaks

    # Sort by timestamp
    sorted_data = sorted(kill_data, key=lambda x: x.get("timestamp", datetime.min))

=======
=======
>>>>>>> Stashed changes
    
    if not kill_data:
        return streaks
    
    # Sort by timestamp
    sorted_data = sorted(kill_data, key=lambda x: x.get("timestamp", datetime.min))
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    player_name_lower = player_name.lower()
    current_kill_streak = 0
    current_death_streak = 0
    max_kill_streak = 0
    max_death_streak = 0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    streak_start = None
    streak_type = None

=======
=======
>>>>>>> Stashed changes
    
    streak_start = None
    streak_type = None
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for event in sorted_data:
        killer = event.get("killer", "").lower()
        victim = event.get("victim", "").lower()
        timestamp = event.get("timestamp")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        # Skip unknown players
        if killer == "unknown" or victim == "unknown":
            continue

        # Skip suicides
        if killer == victim:
            continue

        is_kill = killer == player_name_lower
        is_death = victim == player_name_lower

        if is_kill:
            # Start new kill streak if we were on death streak
            if streak_type == "death" and current_death_streak > 0:
                streaks["streak_history"].append(
                    {
                        "type": "death",
                        "length": current_death_streak,
                        "start": streak_start,
                        "end": timestamp,
                    }
                )
                current_death_streak = 0

=======
=======
>>>>>>> Stashed changes
        
        # Skip unknown players
        if killer == "unknown" or victim == "unknown":
            continue
        
        # Skip suicides
        if killer == victim:
            continue
        
        is_kill = killer == player_name_lower
        is_death = victim == player_name_lower
        
        if is_kill:
            # Start new kill streak if we were on death streak
            if streak_type == "death" and current_death_streak > 0:
                streaks["streak_history"].append({
                    "type": "death",
                    "length": current_death_streak,
                    "start": streak_start,
                    "end": timestamp,
                })
                current_death_streak = 0
            
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            # Start new kill streak if needed
            if streak_type != "kill":
                streak_start = timestamp
                streak_type = "kill"
                current_kill_streak = 0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

            current_kill_streak += 1
            max_kill_streak = max(max_kill_streak, current_kill_streak)

        elif is_death:
            # End kill streak if there was one
            if streak_type == "kill" and current_kill_streak > 0:
                streaks["streak_history"].append(
                    {
                        "type": "kill",
                        "length": current_kill_streak,
                        "start": streak_start,
                        "end": timestamp,
                    }
                )
                current_kill_streak = 0

=======
=======
>>>>>>> Stashed changes
            
            current_kill_streak += 1
            max_kill_streak = max(max_kill_streak, current_kill_streak)
        
        elif is_death:
            # End kill streak if there was one
            if streak_type == "kill" and current_kill_streak > 0:
                streaks["streak_history"].append({
                    "type": "kill",
                    "length": current_kill_streak,
                    "start": streak_start,
                    "end": timestamp,
                })
                current_kill_streak = 0
            
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            # Start new death streak if needed
            if streak_type != "death":
                streak_start = timestamp
                streak_type = "death"
                current_death_streak = 0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

            current_death_streak += 1
            max_death_streak = max(max_death_streak, current_death_streak)

=======
=======
>>>>>>> Stashed changes
            
            current_death_streak += 1
            max_death_streak = max(max_death_streak, current_death_streak)
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    streaks["max_kill_streak"] = max_kill_streak
    streaks["max_death_streak"] = max_death_streak
    streaks["current_kill_streak"] = current_kill_streak
    streaks["current_death_streak"] = current_death_streak
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    # Calculate average kill streak from streak history
    kill_streaks = [
        s["length"] for s in streaks["streak_history"] if s["type"] == "kill"
    ]
=======
    
    # Calculate average kill streak from streak history
    kill_streaks = [s["length"] for s in streaks["streak_history"] if s["type"] == "kill"]
>>>>>>> Stashed changes
=======
    
    # Calculate average kill streak from streak history
    kill_streaks = [s["length"] for s in streaks["streak_history"] if s["type"] == "kill"]
>>>>>>> Stashed changes
    if kill_streaks:
        streaks["average_kill_streak"] = sum(kill_streaks) / len(kill_streaks)
    else:
        streaks["average_kill_streak"] = 0.0
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    # Sort streak history by length (descending) and limit to top 20
    streaks["streak_history"].sort(key=lambda x: x["length"], reverse=True)
    streaks["streak_history"] = streaks["streak_history"][:20]

=======
=======
>>>>>>> Stashed changes
    
    # Sort streak history by length (descending) and limit to top 20
    streaks["streak_history"].sort(key=lambda x: x["length"], reverse=True)
    streaks["streak_history"] = streaks["streak_history"][:20]
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    return streaks


def detect_milestones(kill_data: List[Dict], player_name: str) -> List[Dict]:
    """Detect milestone achievements (kill count milestones).
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering

=======
=======
>>>>>>> Stashed changes
    
    Args:
        kill_data: List of kill event dictionaries
        player_name: Player name for filtering
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    Returns:
        List of milestone dictionaries with keys: milestone, timestamp, kill_count
    """
    milestones = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    if not kill_data:
        return milestones

    # Define milestone thresholds
    milestone_thresholds = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

    player_name_lower = player_name.lower()

    # Sort by timestamp to track kill count progression
    sorted_data = sorted(kill_data, key=lambda x: x.get("timestamp", datetime.min))

    kill_count = 0
    milestone_index = 0

=======
=======
>>>>>>> Stashed changes
    
    if not kill_data:
        return milestones
    
    # Define milestone thresholds
    milestone_thresholds = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
    
    player_name_lower = player_name.lower()
    
    # Sort by timestamp to track kill count progression
    sorted_data = sorted(kill_data, key=lambda x: x.get("timestamp", datetime.min))
    
    kill_count = 0
    milestone_index = 0
    
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for event in sorted_data:
        killer = event.get("killer", "").lower()
        victim = event.get("victim", "").lower()
        timestamp = event.get("timestamp")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        # Skip unknown players
        if killer == "unknown" or victim == "unknown":
            continue

        # Skip suicides
        if killer == victim:
            continue

        # Count player kills
        if killer == player_name_lower:
            kill_count += 1

            # Check if we've reached the next milestone
            while milestone_index < len(milestone_thresholds):
                threshold = milestone_thresholds[milestone_index]

                if kill_count >= threshold:
                    milestones.append(
                        {
                            "milestone": f"{threshold:,} Kills",
                            "timestamp": timestamp,
                            "kill_count": kill_count,
                        }
                    )
                    milestone_index += 1
                else:
                    break

    return milestones
=======
=======
>>>>>>> Stashed changes
        
        # Skip unknown players
        if killer == "unknown" or victim == "unknown":
            continue
        
        # Skip suicides
        if killer == victim:
            continue
        
        # Count player kills
        if killer == player_name_lower:
            kill_count += 1
            
            # Check if we've reached the next milestone
            while milestone_index < len(milestone_thresholds):
                threshold = milestone_thresholds[milestone_index]
                
                if kill_count >= threshold:
                    milestones.append({
                        "milestone": f"{threshold:,} Kills",
                        "timestamp": timestamp,
                        "kill_count": kill_count,
                    })
                    milestone_index += 1
                else:
                    break
    
    return milestones

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
