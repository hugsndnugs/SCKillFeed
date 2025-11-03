# Lifetime Statistics Tab - Implementation Plan

## Overview
Add a new "Lifetime Statistics" tab that aggregates and displays comprehensive statistics from all historical kill data stored in the automatic CSV log file.

## Current State Analysis

### Existing Features
1. **Real-time Statistics Tab**: Shows current session statistics (kills, deaths, K/D ratio, streaks, weapons used, recent activity)
2. **Automatic CSV Logging**: All kill events are automatically logged to `kill_log.csv` (configurable path via `config["user"]["auto_log_csv"]`)
3. **CSV Structure**: Each row contains: `timestamp`, `killer`, `victim`, `weapon`
4. **Statistics Tracked**:
   - Total kills/deaths
   - Current streaks (kill/death)
   - Maximum streaks (kill/death)
   - Weapons used (Counter)
   - Weapons against (Counter)
   - Victims (Counter)
   - Killers (Counter)

### Key Observations
- Statistics reset on app restart (stored in memory only)
- CSV file persists all historical data
- Need to read and aggregate CSV data for lifetime stats
- CSV path resolved via `resolve_auto_log_path()`

## Proposed Lifetime Statistics Tab Features

### Section 1: Core Lifetime Metrics (Top Cards)
Display large, prominent cards showing:
1. **Total Lifetime Kills** - Aggregated from all CSV entries where player is killer
2. **Total Lifetime Deaths** - Aggregated from all CSV entries where player is victim
3. **Lifetime K/D Ratio** - Calculated from lifetime kills/deaths
4. **Total Sessions Tracked** - Estimate based on time gaps or unique days
5. **First Kill Date** - Earliest timestamp in CSV
6. **Last Kill Date** - Most recent timestamp in CSV
7. **Total Play Time** - Estimated from first to last kill (or session-based)

### Section 2: Weapon Statistics (Expandable)
1. **Most Used Weapon** - Weapon with highest kill count
2. **Most Effective Weapon** - Weapon with highest K/D when used
3. **Favorite Weapon** - Most frequently used weapon
4. **Weapons Mastery Table** - Sortable table showing:
   - Weapon name
   - Total kills with weapon
   - Deaths by weapon
   - K/D ratio
   - Usage percentage
   - First use date
   - Last use date

### Section 3: Player vs Player Statistics
1. **Most Killed Player** - Top victim count
2. **Nemesis** - Player who killed you most
3. **Top Rivals Table** - Sortable table showing:
   - Player name
   - Times killed by them
   - Times killed them
   - Head-to-head K/D
   - Last encounter date

### Section 4: Performance Trends
1. **Kills by Day/Week/Month** - Time-based grouping charts
2. **Best Day** - Day with most kills
3. **Best Week** - Week with most kills
4. **Best Month** - Month with most kills
5. **Kill Rate Over Time** - Kills per hour/day over time
6. **Performance Graph** - Visual chart showing kill trends

### Section 5: Streak Statistics
1. **Lifetime Max Kill Streak** - Highest kill streak ever achieved
2. **Lifetime Max Death Streak** - Highest death streak ever
3. **Average Kill Streak** - Mean kill streak length
4. **Streak History** - Table of notable streaks

### Section 6: Advanced Metrics
1. **Kills per Session Average** - Average kills per gaming session
2. **Most Active Day of Week** - Day with most kills
3. **Most Active Time of Day** - Hour range with most activity
4. **Survival Rate** - Percentage of encounters survived
5. **Suicide Count** - Total self-inflicted deaths
6. **First Blood Count** - Kills within first minute of sessions

### Section 7: Timeline & History
1. **Activity Timeline** - Visual timeline of all kills/deaths
2. **Milestones** - Auto-detected milestones (100 kills, 1000 kills, etc.)
3. **Recent History Table** - Last 50 events (similar to current tab but more comprehensive)

## Technical Implementation Details

### New Files to Create
1. **`lib/lifetime_stats.py`** - Core logic for reading CSV and calculating lifetime statistics
   - `load_lifetime_data(csv_path, player_name) -> dict`
   - `calculate_lifetime_stats(kill_data) -> dict`
   - `get_weapon_stats(kill_data, player_name) -> dict`
   - `get_pvp_stats(kill_data, player_name) -> dict`
   - `get_time_trends(kill_data) -> dict`
   - `get_streaks_history(kill_data, player_name) -> list`

2. **`lib/ui_helpers.py`** - Add `create_lifetime_stats_tab(gui)` function
   - Similar structure to `create_statistics_tab()`
   - Use ttk.Frame, ttk.LabelFrame for organization
   - Use ttk.Treeview for sortable tables
   - Use tk.Canvas for charts/graphs (or matplotlib if available)

### Modified Files
1. **`sc_kill_feed_gui.py`**
   - Add import for lifetime_stats helpers
   - Add call to `create_lifetime_stats_tab(self)` in `setup_ui()`
   - Add method `update_lifetime_statistics_display()` 
   - Add method `refresh_lifetime_stats()` - reloads from CSV
   - Add refresh button on lifetime tab

2. **`constants.py`**
   - Add `TAB_LIFETIME_STATS = "📊 Lifetime Stats"`
   - Add any new UI constants needed

### Data Loading Strategy
1. **On Tab Open**: Load CSV data when user clicks the Lifetime Stats tab
2. **Refresh Button**: Manual refresh to reload from CSV
3. **Auto-refresh**: Option to auto-refresh every N minutes (configurable)
4. **Caching**: Cache loaded data in memory, invalidate on refresh

### CSV Reading Considerations
- Handle missing CSV file gracefully (show empty state)
- Handle malformed CSV entries (skip and log)
- Handle large CSV files efficiently (streaming/chunked reading)
- Parse timestamps correctly (ISO format from CSV)
- Filter by player name to get player-specific stats
- Calculate all metrics efficiently (avoid repeated CSV reads)

### UI Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ Lifetime Statistics Tab                                  │
├─────────────────────────────────────────────────────────┤
│ [Refresh Stats] [Export Lifetime Report]                │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │Lifetime  │ │Lifetime  │ │Lifetime  │ │Total     │   │
│ │Kills     │ │Deaths    │ │K/D Ratio │ │Sessions  │   │
│ │  1,234   │ │   567    │ │   2.18   │ │   42     │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│ ⚔️ Weapon Statistics                                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Most Used: F8 Lightning (234 kills)                 │ │
│ │ Most Effective: P4-AR (K/D: 3.45)                  │ │
│ └─────────────────────────────────────────────────────┘ │
│ [Weapon Mastery Table - Sortable]                       │
├─────────────────────────────────────────────────────────┤
│ 👥 Player vs Player                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Most Killed: PlayerX (45 times)                     │ │
│ │ Nemesis: PlayerY (killed you 23 times)              │ │
│ └─────────────────────────────────────────────────────┘ │
│ [Top Rivals Table - Sortable]                           │
├─────────────────────────────────────────────────────────┤
│ 📈 Performance Trends                                    │
│ [Charts/Graphs: Kills over time, Best days, etc.]      │
├─────────────────────────────────────────────────────────┤
│ 🔥 Streak Statistics                                     │
│ [Max streaks, Average streaks, Streak history]          │
├─────────────────────────────────────────────────────────┤
│ 📅 Timeline & Milestones                                 │
│ [Activity timeline, Milestones table]                   │
└─────────────────────────────────────────────────────────┘
```

### Performance Considerations
- Lazy loading: Only load CSV when tab is accessed
- Progressive rendering: Show core stats first, then load detailed tables
- Caching: Cache parsed CSV data in memory
- Large file handling: For CSVs > 10MB, use streaming/chunked processing
- Background processing: Load data in background thread to avoid UI freeze

### Error Handling
- CSV file not found: Show friendly message with path info
- Corrupted CSV entries: Skip and log warnings
- Empty CSV: Show empty state with message
- Permission errors: Show error message
- Large files: Show progress indicator

### Configuration Options
Add to config file:
- `lifetime_stats_auto_refresh`: Enable/disable auto-refresh
- `lifetime_stats_refresh_interval`: Minutes between auto-refresh
- `lifetime_stats_csv_path`: Override CSV path (defaults to auto_log_csv)

## Implementation Phases

### Phase 1: Core Infrastructure
1. Create `lib/lifetime_stats.py` with basic CSV reading
2. Add `create_lifetime_stats_tab()` stub to `ui_helpers.py`
3. Add tab to main GUI
4. Implement basic CSV loading and error handling

### Phase 2: Core Statistics
1. Implement lifetime kills/deaths calculation
2. Implement lifetime K/D ratio
3. Display in top cards section
4. Add refresh functionality

### Phase 3: Weapon Statistics
1. Calculate weapon usage statistics
2. Implement weapon mastery table
3. Add sorting to table

### Phase 4: PvP Statistics
1. Calculate player vs player statistics
2. Implement rivals table
3. Calculate head-to-head records

### Phase 5: Trends & Advanced Metrics
1. Implement time-based grouping (day/week/month)
2. Calculate streaks history
3. Add basic charts/visualizations
4. Implement milestone detection

### Phase 6: Polish & Optimization
1. Add loading indicators
2. Optimize CSV reading for large files
3. Add caching mechanism
4. Improve UI layout and styling
5. Add export functionality for lifetime report

## Additional Features (Future Enhancements)
1. **Export Lifetime Report**: Export all lifetime stats to JSON/PDF
2. **Compare Sessions**: Compare stats between time periods
3. **Achievement System**: Track and display achievements
4. **Import History**: Import stats from old/external CSV files
5. **Statistics Filters**: Filter lifetime stats by date range
6. **Charts Library**: Use matplotlib or similar for better visualizations

## Testing Considerations
1. Test with empty CSV file
2. Test with missing CSV file
3. Test with corrupted CSV entries
4. Test with very large CSV files (100k+ entries)
5. Test with single session data
6. Test with multi-year data
7. Test refresh functionality
8. Test with invalid player names
9. Test concurrent access (monitoring while viewing lifetime stats)

## User Experience Goals
1. **Fast Loading**: Tab should load within 2-3 seconds for typical CSV sizes
2. **Clear Information**: Stats should be easy to understand at a glance
3. **Comprehensive**: Show all relevant lifetime metrics
4. **Interactive**: Sortable tables, refreshable data
5. **Visual**: Charts and graphs where helpful
6. **Responsive**: Handle large datasets without freezing UI

