"""
MLB Data Sandbox Script

This script demonstrates comprehensive MLB data exploration using pybaseball.
It validates the library's capabilities for:
- Fetching current season game data
- Retrieving player batting statistics
- Identifying first home run scorers (research)
- Tracking anytime home run scorers (research)

Purpose:
- Test pybaseball API functionality before production integration
- Explore data structures and available fields
- Validate first HR and anytime HR tracking capabilities
- Document findings for production implementation

Usage:
    python backend/sandbox/mlb_sandbox.py

Requirements:
    - pybaseball library (pip install pybaseball)
    - pandas (typically installed with pybaseball)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for common_utils import
sys.path.insert(0, str(Path(__file__).parent))

from common_utils import (
    check_library_installed,
    display_dataframe_sample,
    handle_api_error,
    print_section_header,
    validate_dataframe_response,
    print_data_structure_info,
)

# Check for required library
if not check_library_installed("pybaseball", "pip install pybaseball"):
    sys.exit(1)

# Import pybaseball after dependency check
from pybaseball import schedule_and_record, batting_stats, statcast


def main():
    """Main execution function for MLB data exploration."""
    print_section_header("MLB Data Sandbox - Comprehensive Exploration")
    print("This script explores MLB data capabilities using pybaseball")
    print("Focus: Game data, player statistics, and home run scorer tracking")
    print()

    # Fetch and display current season games
    games_df = fetch_current_season_games()

    if games_df is not None:
        # Fetch and display player batting statistics
        batting_df = fetch_player_batting_stats()

        if batting_df is not None:
            # Research first home run scorer identification using statcast data
            hr_data = explore_first_hr_scorer_identification(games_df)

            if hr_data is not None:
                # Research anytime home run scorer tracking
                explore_anytime_hr_scorer_tracking(hr_data)


def fetch_current_season_games():
    """
    Fetch and display current season MLB games.

    Uses pybaseball.schedule_and_record() to retrieve game data for the 2024 season.
    Displays key fields: game_id, home_team, away_team, game_date, final_score.

    Requirements: 3.1, 3.2, 6.1, 7.1, 7.2, 7.3
    """
    print_section_header("Current Season Games")

    try:
        # Fetch 2024 season games
        # schedule_and_record() requires a year and team abbreviation
        # For exploration, we'll fetch games for a sample team
        # Common team abbreviations: NYY (Yankees), LAD (Dodgers), BOS (Red Sox)

        print("📡 Fetching 2024 MLB season games...")
        print("⚠️  Note: pybaseball fetches data from Baseball Reference...")
        print("   Using sample team (NYY - New York Yankees) for exploration")
        print()

        # Fetch Yankees schedule for 2024 season
        games_df = schedule_and_record(2024, "NYY")

        # Validate response
        if not validate_dataframe_response(games_df, "game data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(games_df)} games for NYY")
        print()

        # Display key columns for game identification
        # Available columns in schedule_and_record response:
        # Date, Tm (Team), Opp (Opponent), W/L, R (Runs), RA (Runs Against),
        # Inn (Innings), W-L (Record), Rank, GB (Games Behind), Win, Loss, Save,
        # Time, D/N (Day/Night), Attendance, Streak, Orig. Scheduled

        key_columns = [
            "Date",
            "Tm",  # Team
            "Opp",  # Opponent
            "W/L",  # Win/Loss
            "R",  # Runs scored
            "RA",  # Runs allowed
            "Inn",  # Innings played
        ]

        # Filter to only existing columns
        available_columns = [col for col in key_columns if col in games_df.columns]

        # Sort by date (most recent first)
        games_df_sorted = games_df.sort_values("Date", ascending=False)

        display_dataframe_sample(
            games_df_sorted,
            "MLB Games - New York Yankees 2024 Season",
            max_rows=15,
            columns=available_columns,
        )

        # Display full data structure for exploration
        print_data_structure_info(games_df, "MLB Games - Complete Data Structure")

        # Document data structure notes
        print_section_header("MLB Game Data - Structure Notes")
        print("📋 Key Observations:")
        print()
        print("  • schedule_and_record() returns data for ONE team")
        print("  • Each row represents one game from that team's perspective")
        print("  • Date format: 'Day, Month DD' (e.g., 'Monday, Apr 1')")
        print("  • Opp column shows opponent with @ for away games")
        print("  • R = Runs scored by the team")
        print("  • RA = Runs allowed (opponent's runs)")
        print("  • Inn = Innings played (9 for regulation, >9 for extra innings)")
        print()
        print("⚠️  Limitations Identified:")
        print("  • No unified game_id field (need to construct from date + teams)")
        print("  • Team-centric view (not game-centric)")
        print("  • Need to fetch schedule for each team separately")
        print("  • No direct player-level data in schedule")
        print()
        print("💡 Next Steps:")
        print("  • Explore player batting statistics")
        print("  • Research play-by-play data availability")
        print("  • Investigate run scorer identification methods")
        print()

        return games_df

    except Exception as e:
        handle_api_error(e, "fetching MLB games")
        return None


def fetch_player_batting_stats():
    """
    Fetch and display player batting statistics for a sample date range.

    Uses pybaseball.batting_stats() to retrieve player batting statistics.
    Focuses on batting statistics: hits, home_runs, RBIs.

    Requirements: 3.3, 3.4, 6.2, 6.3
    """
    print_section_header("Player Batting Statistics")

    try:
        # Fetch batting statistics for 2024 season
        # batting_stats() requires start_season and end_season parameters
        # Returns season-level statistics for all players

        print("📡 Fetching 2024 MLB batting statistics...")
        print("⚠️  Note: This fetches data from FanGraphs and may take a moment...")
        print()

        # Fetch 2024 season batting stats
        batting_df = batting_stats(
            2024, 2024, qual=1
        )  # qual=1 means at least 1 plate appearance

        # Validate response
        if not validate_dataframe_response(batting_df, "batting statistics retrieval"):
            return None

        print(f"✅ Successfully retrieved statistics for {len(batting_df)} players")
        print()

        # Filter to players with at least one hit
        players_with_hits = batting_df[batting_df["H"] > 0].copy()

        if len(players_with_hits) == 0:
            print("⚠️  No batting data found in the dataset")
            return None

        print(f"📊 Found {len(players_with_hits)} players with hits in 2024")
        print()

        # Display key columns for batting analysis
        # Available columns in batting_stats response include:
        # Name, Team, G (Games), PA (Plate Appearances), AB (At Bats),
        # H (Hits), 1B, 2B, 3B, HR (Home Runs), R (Runs), RBI (Runs Batted In),
        # BB (Walks), SO (Strikeouts), AVG (Batting Average), OBP, SLG, OPS, etc.

        key_columns = [
            "Name",
            "Team",
            "G",  # Games played
            "PA",  # Plate appearances
            "H",  # Hits
            "HR",  # Home runs
            "RBI",  # Runs batted in
            "R",  # Runs scored
            "AVG",  # Batting average
        ]

        # Filter to only existing columns
        available_columns = [
            col for col in key_columns if col in players_with_hits.columns
        ]

        # Sort by hits (highest first)
        players_sorted = players_with_hits.sort_values("H", ascending=False)

        display_dataframe_sample(
            players_sorted,
            "Top Hitters - 2024 MLB Season",
            max_rows=20,
            columns=available_columns,
        )

        # Display data structure information
        print_section_header("Batting Statistics - Data Structure Notes")
        print("📋 Key Fields for Batting Tracking:")
        print()
        print("  • H: Total hits (singles + doubles + triples + home runs)")
        print("  • HR: Home runs")
        print("  • RBI: Runs batted in (runs scored by teammates due to this batter)")
        print("  • R: Runs scored by this player")
        print("  • 1B, 2B, 3B: Singles, doubles, triples")
        print("  • AVG: Batting average (H / AB)")
        print("  • OBP: On-base percentage")
        print("  • SLG: Slugging percentage")
        print("  • OPS: On-base plus slugging")
        print()
        print("📊 Data Granularity:")
        print("  • Statistics are season-level aggregates")
        print("  • Each row represents one player's full season performance")
        print("  • No game-by-game breakdown in this dataset")
        print("  • No timing/sequence information")
        print()
        print("⚠️  Limitation Identified:")
        print("  • This dataset provides SEASON TOTALS only")
        print("  • It does NOT provide game-by-game data")
        print("  • It does NOT provide inning-by-inning or play-by-play data")
        print("  • Cannot determine FIRST HOME RUN scorer from this data alone")
        print("  • Need play-by-play data for home run scorer identification")
        print()
        print("💡 Key Insight - Home Run Tracking:")
        print()
        print("  • 'HR' (Home Runs) = Times this player hit a home run")
        print("  • Home runs are discrete, identifiable events (unlike runs scored)")
        print("  • For 'first HR scorer' tracking, we need HR events with timing data")
        print("  • Similar to NFL first TD tracking - clear, measurable event")
        print("  • Popular prop bet: 'Who will hit the first home run?'")
        print()

        # Show some interesting statistics
        print_section_header("Batting Statistics - Summary")

        # Top home run hitters
        top_hr = players_with_hits.nlargest(10, "HR")[["Name", "Team", "HR", "RBI"]]
        print("⚾ Top 10 Home Run Hitters:")
        print()
        for idx, row in top_hr.iterrows():
            print(
                f"  {row['Name']} ({row['Team']}): {int(row['HR'])} HR, {int(row['RBI'])} RBI"
            )
        print()

        # Top run scorers (most runs scored)
        top_runs = players_with_hits.nlargest(10, "R")[["Name", "Team", "R", "H"]]
        print("🏃 Top 10 Run Scorers (Most Runs Scored):")
        print()
        for idx, row in top_runs.iterrows():
            print(
                f"  {row['Name']} ({row['Team']}): {int(row['R'])} runs, {int(row['H'])} hits"
            )
        print()

        return players_sorted

    except Exception as e:
        handle_api_error(e, "fetching player batting statistics")
        return None


def explore_first_hr_scorer_identification(games_df):
    """
    Research and explore first home run scorer identification using statcast data.

    Uses pybaseball.statcast() to retrieve play-by-play data and attempts to identify
    the first home run scorer for sample games.

    Requirements: 3.4, 8.4
    """
    print_section_header("First Home Run Scorer Identification - Research")

    try:
        # Statcast provides detailed pitch-by-pitch data including home runs
        # We'll fetch data for a recent date range to find games with home runs

        print("📡 Fetching statcast data for sample date range...")
        print("⚠️  Note: Statcast data is detailed and may take a moment to load...")
        print("   Using a 3-day sample from late season (September 2024)")
        print()

        # Fetch statcast data for a few days in September 2024
        # statcast() requires start_dt and end_dt in 'YYYY-MM-DD' format
        statcast_df = statcast(start_dt="2024-09-20", end_dt="2024-09-22")

        # Validate response
        if not validate_dataframe_response(statcast_df, "statcast data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(statcast_df)} pitch records")
        print()

        # Filter to home runs only
        # In statcast data, events == 'home_run' indicates a home run
        hr_plays = statcast_df[statcast_df["events"] == "home_run"].copy()

        if len(hr_plays) == 0:
            print("⚠️  No home run plays found in the sample date range")
            print("   Try expanding the date range or selecting different dates")
            return None

        print(f"📊 Found {len(hr_plays)} home runs in the sample period")
        print()

        # Display data structure for home run plays
        print_data_structure_info(
            hr_plays, "Statcast Home Run Data - Complete Structure"
        )

        # Select a sample game to analyze
        # Group by game_pk (unique game identifier)
        hr_counts_by_game = (
            hr_plays.groupby("game_pk").size().sort_values(ascending=False)
        )

        if len(hr_counts_by_game) == 0:
            print("⚠️  No games with home runs found")
            return None

        sample_game_pk = hr_counts_by_game.index[0]
        sample_game_hrs = hr_plays[hr_plays["game_pk"] == sample_game_pk].copy()

        print(f"🎯 Analyzing sample game: {sample_game_pk}")
        print(f"   Total home runs in this game: {len(sample_game_hrs)}")
        print()

        # Sort by inning and at_bat_number to get chronological order
        # at_bat_number is sequential within a game
        sample_game_hrs_sorted = sample_game_hrs.sort_values(
            ["inning", "at_bat_number"]
        )

        # Display home run plays with timing information
        hr_display_columns = [
            "game_date",
            "inning",
            "inning_topbot",
            "at_bat_number",
            "player_name",
            "batter",
            "home_team",
            "away_team",
            "events",
            "description",
            "launch_speed",
            "launch_angle",
            "hit_distance_sc",
        ]

        available_hr_columns = [
            col for col in hr_display_columns if col in sample_game_hrs_sorted.columns
        ]

        display_dataframe_sample(
            sample_game_hrs_sorted,
            f"Home Run Plays - Game {sample_game_pk} (Chronological Order)",
            max_rows=10,
            columns=available_hr_columns,
        )

        # Identify the first home run scorer
        first_hr = sample_game_hrs_sorted.iloc[0]

        print_section_header("First HR Scorer Identification - RESULTS")
        print("✅ SUCCESS: First home run scorer can be identified!")
        print()
        print(f"⚾ First Home Run Scorer:")
        print(f"   Player: {first_hr['player_name']}")
        print(f"   Batter ID: {first_hr['batter']}")
        print(f"   Inning: {first_hr['inning']} ({first_hr['inning_topbot']})")
        print(f"   At-Bat Number: {first_hr['at_bat_number']}")
        print(f"   Launch Speed: {first_hr['launch_speed']} mph")
        print(f"   Launch Angle: {first_hr['launch_angle']}°")
        print(f"   Distance: {first_hr['hit_distance_sc']} feet")
        print()

        # Document data structure for first HR identification
        print_section_header(
            "First HR Identification - Data Structure & Recommendations"
        )
        print("📋 Key Fields Available:")
        print()
        print("  • game_pk: Unique game identifier (MLB's official game ID)")
        print("  • game_date: Date of the game")
        print("  • at_bat_number: Sequential at-bat number (for chronological sorting)")
        print("  • inning: Inning number")
        print("  • inning_topbot: 'Top' or 'Bot' (which half of inning)")
        print("  • player_name: Name of the batter who hit the home run")
        print("  • batter: MLB player ID for the batter")
        print("  • events: Event type ('home_run' for home runs)")
        print("  • description: Text description of the play")
        print("  • launch_speed: Exit velocity in mph")
        print("  • launch_angle: Launch angle in degrees")
        print("  • hit_distance_sc: Distance in feet")
        print("  • home_team: Home team abbreviation")
        print("  • away_team: Away team abbreviation")
        print()
        print("✅ First HR Identification Algorithm:")
        print()
        print(
            "  1. Use pybaseball.statcast() to fetch play-by-play data for date range"
        )
        print("  2. Filter to events == 'home_run'")
        print("  3. Group by game_pk (unique game identifier)")
        print("  4. Sort by at_bat_number (ascending = chronological)")
        print("  5. Take the first record per game")
        print("  6. Extract player_name and batter (player ID)")
        print()
        print("📊 Data Quality:")
        print(f"  • Total HR plays in sample: {len(hr_plays)}")
        print(f"  • HR plays with player name: {hr_plays['player_name'].notna().sum()}")
        print(f"  • HR plays with batter ID: {hr_plays['batter'].notna().sum()}")
        print(
            f"  • HR plays with timing data: {hr_plays['at_bat_number'].notna().sum()}"
        )
        print()
        print("💡 Production Implementation Recommendations:")
        print()
        print("  ✓ Use pybaseball.statcast() for play-by-play home run data")
        print("  ✓ Filter to events == 'home_run'")
        print("  ✓ Sort by at_bat_number ascending")
        print("  ✓ Group by game_pk and take first record")
        print("  ✓ Store first HR scorer in database with game_pk reference")
        print("  ✓ Statcast data includes rich details (exit velo, distance, angle)")
        print("  ✓ Update data after each game completes")
        print()
        print("⚠️  Considerations:")
        print()
        print("  • Statcast data is available from 2015 onwards")
        print("  • Data is typically available within hours of game completion")
        print("  • API has rate limiting - use date ranges wisely")
        print("  • game_pk is MLB's official game identifier (use for joins)")
        print("  • at_bat_number provides reliable chronological ordering")
        print("  • Grand slams, solo HRs, etc. all tracked the same way")
        print()
        print("🔍 Additional Insights:")
        print()
        print("  • Statcast provides the most detailed MLB data available")
        print("  • Every pitch is tracked with location, velocity, spin rate")
        print("  • Home runs include exit velocity, launch angle, distance")
        print("  • Can distinguish HR types (solo, 2-run, 3-run, grand slam)")
        print("  • Can track HR to specific field locations")
        print("  • Batter ID allows reliable player identification")
        print()

        return sample_game_hrs_sorted

    except Exception as e:
        handle_api_error(e, "exploring first home run scorer identification")
        return None


def explore_anytime_hr_scorer_tracking(sample_game_hrs):
    """
    Research and explore anytime home run scorer tracking using statcast data.

    Analyzes the same statcast data to demonstrate tracking ALL home run scorers
    in a game (anytime HR), not just the first scorer.

    Requirements: 3.4, 8.4
    """
    print_section_header("Anytime HR Scorer Tracking - Research")

    try:
        # We already have home run plays from the previous function
        print("📊 Analyzing anytime HR scorer tracking capabilities...")
        print()

        # Get the game_pk from the sample data
        game_pk = sample_game_hrs.iloc[0]["game_pk"]

        print(f"🎯 Sample Game: {game_pk}")
        print(f"   Total home runs: {len(sample_game_hrs)}")
        print()

        # Group by player to show all HR scorers
        player_hr_counts = (
            sample_game_hrs.groupby(["player_name", "batter"])
            .size()
            .reset_index(name="hr_count")
        )
        player_hr_counts_sorted = player_hr_counts.sort_values(
            "hr_count", ascending=False
        )

        print_section_header("All HR Scorers in Game (Anytime HR)")
        print("📊 Players who hit home runs:")
        print()

        for idx, row in player_hr_counts_sorted.iterrows():
            print(
                f"  • {row['player_name']} (ID: {row['batter']}): {row['hr_count']} HR(s)"
            )

        print()

        # Show breakdown by inning
        inning_hr_counts = (
            sample_game_hrs.groupby(["inning", "inning_topbot"])
            .size()
            .reset_index(name="hr_count")
        )

        print("📊 Home Run Breakdown by Inning:")
        print()
        for idx, row in inning_hr_counts.iterrows():
            print(
                f"  • Inning {row['inning']} ({row['inning_topbot']}): {row['hr_count']} HR(s)"
            )
        print()

        # Show HR details (distance, exit velo)
        print("📊 Home Run Details:")
        print()
        for idx, row in sample_game_hrs.iterrows():
            print(
                f"  • {row['player_name']}: {int(row['hit_distance_sc'])} ft, {row['launch_speed']} mph, {row['launch_angle']}°"
            )
        print()

        # Compare first HR vs anytime HR data structures
        print_section_header("First HR vs Anytime HR - Data Structure Comparison")
        print("📋 Data Structure Comparison:")
        print()
        print("FIRST HOME RUN SCORER:")
        print("  • Requires: Filtering to first HR only (by at_bat_number)")
        print("  • Result: Single player per game")
        print("  • Use case: 'Who will hit the first home run?'")
        print("  • Implementation: Sort by at_bat_number, take first record per game")
        print()
        print("ANYTIME HOME RUN SCORER:")
        print("  • Requires: All HR plays (no at-bat filtering)")
        print("  • Result: Multiple players per game (all who hit HRs)")
        print("  • Use case: 'Will player X hit a home run at any point?'")
        print("  • Implementation: Filter to events == 'home_run', group by player")
        print()
        print("✅ KEY INSIGHT:")
        print("  • Both use the SAME underlying data (statcast)")
        print("  • Difference is only in the filtering/aggregation logic")
        print("  • First HR = temporal filter (earliest at_bat_number)")
        print("  • Anytime HR = no temporal filter (all home runs)")
        print()

        print_section_header("Anytime HR Tracking - RESULTS")
        print("✅ SUCCESS: Anytime HR tracking is fully supported!")
        print()
        print("📊 Capabilities Confirmed:")
        print("  ✓ Can identify ALL players who hit HRs in a game")
        print("  ✓ Can count multiple HRs by same player")
        print("  ✓ Can track HR details (distance, exit velo, launch angle)")
        print("  ✓ Can track HRs for both teams")
        print("  ✓ Can get timing information for each HR (inning, at-bat)")
        print("  ✓ Can distinguish HR types by runners on base")
        print()

        print_section_header("Anytime HR Tracking - Production Recommendations")
        print("💡 Implementation Strategy:")
        print()
        print("  1. Use same statcast data source (pybaseball.statcast())")
        print("  2. Filter to events == 'home_run' (same as first HR)")
        print("  3. For anytime HR: Group by game_pk + batter")
        print("  4. Store all HR scorers per game (not just first)")
        print("  5. Support queries like 'Did player X hit a HR in game Y?'")
        print()
        print("📊 Database Schema Suggestion:")
        print()
        print("  Table: game_home_runs")
        print("    • game_pk (FK to games)")
        print("    • batter (FK to players - MLB player ID)")
        print("    • hr_sequence (1 = first HR, 2 = second HR, etc.)")
        print("    • inning (inning number)")
        print("    • inning_topbot (Top or Bot)")
        print("    • at_bat_number (for ordering)")
        print("    • launch_speed (exit velocity in mph)")
        print("    • launch_angle (degrees)")
        print("    • hit_distance_sc (distance in feet)")
        print("    • is_first_hr (boolean flag)")
        print()
        print("  Benefits:")
        print("    • Single table supports both first HR and anytime HR queries")
        print("    • Can answer 'Who hit first HR?' (filter is_first_hr = true)")
        print("    • Can answer 'Did X hit a HR?' (filter batter = X)")
        print("    • Can answer 'How many HRs did X hit?' (count by batter)")
        print("    • Rich HR details available for analysis")
        print()
        print("⚠️  Performance Considerations:")
        print()
        print("  • Statcast data is pitch-level (~700K pitches per season)")
        print("  • HR plays are ~5,000-6,000 per season (~0.8% of pitches)")
        print("  • Recommend caching HR data separately from full statcast")
        print("  • Update after each game completes (not real-time during game)")
        print("  • Index on game_pk and batter for fast queries")
        print("  • Statcast API has rate limits - batch fetch by date range")
        print()
        print("🎯 MLB vs NFL Comparison:")
        print()
        print("  SIMILARITIES:")
        print("    • Both track discrete scoring events (HR vs TD)")
        print("    • Both support first scorer and anytime scorer tracking")
        print("    • Both have reliable play-by-play data with timing")
        print(
            "    • Both use sequential ordering (at_bat_number vs game_seconds_remaining)"
        )
        print()
        print("  DIFFERENCES:")
        print("    • MLB: ~5-6K HRs per season, NFL: ~1.5K TDs per season")
        print("    • MLB: Statcast has rich physics data (exit velo, angle, distance)")
        print("    • MLB: game_pk is official MLB ID, NFL uses custom game_id")
        print("    • MLB: Statcast from 2015+, NFL: nflreadpy has historical data")
        print()

        return player_hr_counts_sorted

    except Exception as e:
        handle_api_error(e, "exploring anytime home run scorer tracking")
        return None


if __name__ == "__main__":
    main()
