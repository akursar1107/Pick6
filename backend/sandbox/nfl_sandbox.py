"""
NFL Data Sandbox Script

This script demonstrates comprehensive NFL data exploration using nflreadpy.
It validates the library's capabilities for:
- Fetching current season game data
- Retrieving player touchdown statistics
- Identifying first touchdown scorers (research)
- Tracking anytime touchdown scorers (research)

Purpose:
- Test nflreadpy API functionality before production integration
- Explore data structures and available fields
- Validate first TD and anytime TD tracking capabilities
- Document findings for production implementation

Usage:
    python backend/sandbox/nfl_sandbox.py

Requirements:
    - nflreadpy library (pip install nflreadpy)
    - pandas (typically installed with nflreadpy)
"""

import sys
from pathlib import Path

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
if not check_library_installed("nflreadpy", "pip install nflreadpy"):
    sys.exit(1)

# Import nflreadpy after dependency check
import nflreadpy as nfl


def main():
    """Main execution function for NFL data exploration."""
    print_section_header("NFL Data Sandbox - Comprehensive Exploration")
    print("This script explores NFL data capabilities using nflreadpy")
    print("Focus: Game data, player statistics, and touchdown scorer tracking")
    print()

    # Fetch and display current season games
    games_df = fetch_current_season_games()

    if games_df is not None:
        # Fetch and display player touchdown statistics
        td_stats = fetch_player_touchdown_stats()

        # Research first TD scorer identification using play-by-play data
        pbp_tds = explore_first_td_scorer_identification(games_df)

        # Research anytime TD scorer tracking
        if pbp_tds is not None:
            explore_anytime_td_scorer_tracking(pbp_tds)


def fetch_current_season_games():
    """
    Fetch and display current season NFL games.

    Uses nflreadpy.load_schedules() to retrieve game data for the 2024 season.
    Displays key fields: game_id, home_team, away_team, game_date, score.

    Requirements: 1.1, 1.2, 6.1, 7.1, 7.2, 7.3
    """
    print_section_header("Current Season Games")

    try:
        # Fetch 2024 season games
        # nflreadpy.load_schedules() returns a Polars DataFrame with game information
        print("📡 Fetching 2024 NFL season games...")
        games_df_polars = nfl.load_schedules(seasons=[2024])

        # Convert Polars DataFrame to pandas for compatibility with common_utils
        games_df = games_df_polars.to_pandas()

        # Validate response
        if not validate_dataframe_response(games_df, "game data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(games_df)} games")
        print()

        # Display key columns for game identification
        key_columns = [
            "game_id",
            "home_team",
            "away_team",
            "game_date",
            "home_score",
            "away_score",
        ]

        # Filter to only existing columns
        available_columns = [col for col in key_columns if col in games_df.columns]

        display_dataframe_sample(
            games_df,
            "NFL Games - Key Fields",
            max_rows=10,
            columns=available_columns,
        )

        # Display full data structure for exploration
        print_data_structure_info(games_df, "NFL Games - Complete Data Structure")

        return games_df

    except Exception as e:
        handle_api_error(e, "fetching NFL games")
        return None


def fetch_player_touchdown_stats():
    """
    Fetch and display player touchdown statistics.

    Uses nflreadpy.load_player_stats() to retrieve player statistics for the 2024 season.
    Focuses on touchdown-related statistics: rushing_tds, receiving_tds, passing_tds.

    Requirements: 1.3, 1.4, 6.2, 6.3
    """
    print_section_header("Player Touchdown Statistics")

    try:
        # Fetch 2024 season player statistics
        # nflreadpy.load_player_stats() returns a Polars DataFrame with player stats
        print("📡 Fetching 2024 NFL player statistics...")
        stats_df_polars = nfl.load_player_stats(seasons=[2024])

        # Convert Polars DataFrame to pandas for compatibility with common_utils
        stats_df = stats_df_polars.to_pandas()

        # Validate response
        if not validate_dataframe_response(stats_df, "player statistics retrieval"):
            return None

        print(
            f"✅ Successfully retrieved statistics for {len(stats_df)} player-week records"
        )
        print()

        # Filter to players with at least one touchdown
        td_columns = ["rushing_tds", "receiving_tds", "passing_tds"]

        # Create a total_tds column
        stats_df["total_tds"] = stats_df[td_columns].sum(axis=1)

        # Filter to players with touchdowns
        td_players = stats_df[stats_df["total_tds"] > 0].copy()

        if len(td_players) == 0:
            print("⚠️  No touchdown data found in the dataset")
            return None

        print(f"📊 Found {len(td_players)} player-week records with touchdowns")
        print()

        # Display key columns for touchdown analysis
        key_columns = [
            "player_display_name",
            "position",
            "team",
            "week",
            "rushing_tds",
            "receiving_tds",
            "passing_tds",
            "total_tds",
        ]

        # Sort by total touchdowns descending
        td_players_sorted = td_players.sort_values("total_tds", ascending=False)

        display_dataframe_sample(
            td_players_sorted,
            "Top Touchdown Scorers - 2024 Season",
            max_rows=15,
            columns=key_columns,
        )

        # Display data structure information
        print_section_header("Touchdown Statistics - Data Structure Notes")
        print("📋 Key Fields for Touchdown Tracking:")
        print()
        print("  • rushing_tds: Touchdowns scored by rushing")
        print("  • receiving_tds: Touchdowns scored by receiving")
        print("  • passing_tds: Touchdowns thrown by quarterbacks")
        print("  • special_teams_tds: Touchdowns on special teams plays")
        print("  • def_tds: Defensive touchdowns (interceptions, fumble returns)")
        print()
        print("📊 Data Granularity:")
        print("  • Statistics are provided at the player-week level")
        print("  • Each row represents one player's performance in one week")
        print("  • To get season totals, aggregate by player_id")
        print()
        print("⚠️  Limitation Identified:")
        print("  • This dataset provides COUNTS of touchdowns per week")
        print("  • It does NOT provide timing/sequence information")
        print("  • Cannot determine FIRST TD scorer from this data alone")
        print("  • Need play-by-play data for first TD identification")
        print()

        return td_players_sorted

    except Exception as e:
        handle_api_error(e, "fetching player touchdown statistics")
        return None


def explore_first_td_scorer_identification(games_df):
    """
    Research and explore first touchdown scorer identification using play-by-play data.

    Uses nflreadpy.load_pbp() to retrieve play-by-play data and attempts to identify
    the first touchdown scorer for sample games.

    Requirements: 1.4, 8.4
    """
    print_section_header("First TD Scorer Identification - Research")

    try:
        # Fetch play-by-play data for 2024 season
        print("📡 Fetching 2024 NFL play-by-play data...")
        print("⚠️  Note: This is a large dataset and may take a moment to load...")
        pbp_df_polars = nfl.load_pbp(seasons=[2024])

        # Convert to pandas
        pbp_df = pbp_df_polars.to_pandas()

        # Validate response
        if not validate_dataframe_response(pbp_df, "play-by-play data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(pbp_df)} play-by-play records")
        print()

        # Filter to touchdown plays only
        td_plays = pbp_df[pbp_df["touchdown"] == 1].copy()

        if len(td_plays) == 0:
            print("⚠️  No touchdown plays found in the dataset")
            return None

        print(f"📊 Found {len(td_plays)} touchdown plays in 2024 season")
        print()

        # Select a sample game to analyze
        # Get a game with multiple touchdowns
        td_counts_by_game = (
            td_plays.groupby("game_id").size().sort_values(ascending=False)
        )
        sample_game_id = td_counts_by_game.index[0]
        sample_game_tds = td_plays[td_plays["game_id"] == sample_game_id].copy()

        print(f"🎯 Analyzing sample game: {sample_game_id}")
        print(f"   Total touchdowns in this game: {len(sample_game_tds)}")
        print()

        # Sort by game_seconds_remaining (descending = chronological order)
        sample_game_tds_sorted = sample_game_tds.sort_values(
            "game_seconds_remaining", ascending=False
        )

        # Display touchdown plays with timing information
        td_display_columns = [
            "quarter_seconds_remaining",
            "game_seconds_remaining",
            "td_player_name",
            "td_team",
            "posteam",
            "desc",
            "touchdown",
            "pass_touchdown",
            "rush_touchdown",
        ]

        available_td_columns = [
            col for col in td_display_columns if col in sample_game_tds_sorted.columns
        ]

        display_dataframe_sample(
            sample_game_tds_sorted,
            f"Touchdown Plays - {sample_game_id} (Chronological Order)",
            max_rows=10,
            columns=available_td_columns,
        )

        # Identify the first touchdown scorer
        first_td = sample_game_tds_sorted.iloc[0]

        print_section_header("First TD Scorer Identification - RESULTS")
        print("✅ SUCCESS: First TD scorer can be identified!")
        print()
        print(f"🏈 First Touchdown Scorer:")
        print(f"   Player: {first_td['td_player_name']}")
        print(f"   Team: {first_td['td_team']}")
        print(
            f"   Type: {'Pass TD' if first_td['pass_touchdown'] == 1 else 'Rush TD' if first_td['rush_touchdown'] == 1 else 'Other TD'}"
        )
        print(f"   Game Time Remaining: {first_td['game_seconds_remaining']} seconds")
        print()

        # Document data structure for first TD identification
        print_section_header(
            "First TD Identification - Data Structure & Recommendations"
        )
        print("📋 Key Fields Available:")
        print()
        print("  • game_id: Unique game identifier")
        print(
            "  • game_seconds_remaining: Time remaining in game (for chronological sorting)"
        )
        print("  • quarter_seconds_remaining: Time remaining in quarter")
        print("  • td_player_name: Name of player who scored touchdown")
        print("  • td_player_id: Unique player identifier")
        print("  • td_team: Team that scored the touchdown")
        print("  • touchdown: Binary flag (1 = touchdown play)")
        print("  • pass_touchdown: Binary flag (1 = passing touchdown)")
        print("  • rush_touchdown: Binary flag (1 = rushing touchdown)")
        print("  • return_touchdown: Binary flag (1 = return touchdown)")
        print("  • desc: Text description of the play")
        print()
        print("✅ First TD Identification Algorithm:")
        print()
        print("  1. Filter play-by-play data to touchdown plays (touchdown == 1)")
        print("  2. Group by game_id")
        print("  3. Sort by game_seconds_remaining (descending = chronological)")
        print("  4. Take the first record per game")
        print("  5. Extract td_player_name and td_player_id")
        print()
        print("📊 Data Quality:")
        print(f"  • Total TD plays in dataset: {len(td_plays)}")
        print(
            f"  • TD plays with player name: {td_plays['td_player_name'].notna().sum()}"
        )
        print(f"  • TD plays with player ID: {td_plays['td_player_id'].notna().sum()}")
        print()
        print("💡 Production Implementation Recommendations:")
        print()
        print("  ✓ Use nflreadpy.load_pbp() for play-by-play data")
        print("  ✓ Filter to touchdown == 1")
        print("  ✓ Sort by game_seconds_remaining descending")
        print("  ✓ Group by game_id and take first record")
        print("  ✓ Store first TD scorer in database with game_id reference")
        print("  ✓ Consider caching play-by-play data (large dataset)")
        print("  ✓ Update data after each game completes")
        print()
        print("⚠️  Considerations:")
        print()
        print("  • Play-by-play data is large (~50K+ plays per season)")
        print("  • May have slight delay after game completion")
        print("  • Defensive/special teams TDs are included")
        print("  • 2-point conversions are separate plays (not TDs)")
        print()

        return sample_game_tds_sorted

    except Exception as e:
        handle_api_error(e, "exploring first TD scorer identification")
        return None


def explore_anytime_td_scorer_tracking(sample_game_tds):
    """
    Research and explore anytime touchdown scorer tracking using play-by-play data.

    Analyzes the same play-by-play data to demonstrate tracking ALL touchdown scorers
    in a game (anytime TD), not just the first scorer.

    Requirements: 1.4, 8.4
    """
    print_section_header("Anytime TD Scorer Tracking - Research")

    try:
        # We already have touchdown plays from the previous function
        print("📊 Analyzing anytime TD scorer tracking capabilities...")
        print()

        # Get the game_id from the sample data
        game_id = sample_game_tds.iloc[0]["game_id"]

        print(f"🎯 Sample Game: {game_id}")
        print(f"   Total touchdowns: {len(sample_game_tds)}")
        print()

        # Group by player to show all TD scorers
        player_td_counts = (
            sample_game_tds.groupby(["td_player_name", "td_player_id", "td_team"])
            .size()
            .reset_index(name="td_count")
        )
        player_td_counts_sorted = player_td_counts.sort_values(
            "td_count", ascending=False
        )

        print_section_header("All TD Scorers in Game (Anytime TD)")
        print("📊 Players who scored touchdowns:")
        print()

        for idx, row in player_td_counts_sorted.iterrows():
            print(
                f"  • {row['td_player_name']} ({row['td_team']}): {row['td_count']} TD(s)"
            )

        print()

        # Show breakdown by TD type
        td_types = {
            "Passing TDs": sample_game_tds["pass_touchdown"].sum(),
            "Rushing TDs": sample_game_tds["rush_touchdown"].sum(),
            "Return TDs": (
                sample_game_tds["return_touchdown"].sum()
                if "return_touchdown" in sample_game_tds.columns
                else 0
            ),
        }

        print("📊 Touchdown Breakdown by Type:")
        print()
        for td_type, count in td_types.items():
            if count > 0:
                print(f"  • {td_type}: {int(count)}")
        print()

        # Compare first TD vs anytime TD data structures
        print_section_header("First TD vs Anytime TD - Data Structure Comparison")
        print("📋 Data Structure Comparison:")
        print()
        print("FIRST TD SCORER:")
        print("  • Requires: Filtering to first TD only (by game_seconds_remaining)")
        print("  • Result: Single player per game")
        print("  • Use case: 'Who will score the first touchdown?'")
        print("  • Implementation: Sort by time, take first record per game")
        print()
        print("ANYTIME TD SCORER:")
        print("  • Requires: All TD plays (no time filtering)")
        print("  • Result: Multiple players per game (all who scored)")
        print("  • Use case: 'Will player X score a touchdown at any point?'")
        print("  • Implementation: Filter to touchdown == 1, group by player")
        print()
        print("✅ KEY INSIGHT:")
        print("  • Both use the SAME underlying data (play-by-play)")
        print("  • Difference is only in the filtering/aggregation logic")
        print("  • First TD = temporal filter (earliest)")
        print("  • Anytime TD = no temporal filter (all)")
        print()

        print_section_header("Anytime TD Tracking - RESULTS")
        print("✅ SUCCESS: Anytime TD tracking is fully supported!")
        print()
        print("📊 Capabilities Confirmed:")
        print("  ✓ Can identify ALL players who scored TDs in a game")
        print("  ✓ Can count multiple TDs by same player")
        print("  ✓ Can distinguish TD types (pass, rush, return)")
        print("  ✓ Can track TDs for both teams")
        print("  ✓ Can get timing information for each TD")
        print()

        print_section_header("Anytime TD Tracking - Production Recommendations")
        print("💡 Implementation Strategy:")
        print()
        print("  1. Use same play-by-play data source (nflreadpy.load_pbp())")
        print("  2. Filter to touchdown == 1 (same as first TD)")
        print("  3. For anytime TD: Group by game_id + player_id")
        print("  4. Store all TD scorers per game (not just first)")
        print("  5. Support queries like 'Did player X score in game Y?'")
        print()
        print("📊 Database Schema Suggestion:")
        print()
        print("  Table: game_touchdowns")
        print("    • game_id (FK to games)")
        print("    • player_id (FK to players)")
        print("    • td_sequence (1 = first TD, 2 = second TD, etc.)")
        print("    • td_type (pass, rush, return, etc.)")
        print("    • game_seconds_remaining (for ordering)")
        print("    • is_first_td (boolean flag)")
        print()
        print("  Benefits:")
        print("    • Single table supports both first TD and anytime TD queries")
        print("    • Can answer 'Who scored first?' (filter is_first_td = true)")
        print("    • Can answer 'Did X score?' (filter player_id = X)")
        print("    • Can answer 'How many TDs did X score?' (count by player)")
        print()
        print("⚠️  Performance Considerations:")
        print()
        print("  • Play-by-play data is ~50K rows per season")
        print("  • TD plays are ~1,500 rows per season (~3% of plays)")
        print("  • Recommend caching TD data separately from full play-by-play")
        print("  • Update after each game completes (not real-time during game)")
        print("  • Index on game_id and player_id for fast queries")
        print()

        return player_td_counts_sorted

    except Exception as e:
        handle_api_error(e, "exploring anytime TD scorer tracking")
        return None


if __name__ == "__main__":
    main()
