"""
NBA Data Sandbox Script

This script demonstrates comprehensive NBA data exploration using nba_api.
It validates the library's capabilities for:
- Fetching current season game data
- Retrieving player scoring statistics
- Identifying first basket scorers (research)

Purpose:
- Test nba_api functionality before production integration
- Explore data structures and available fields
- Validate first basket tracking capabilities
- Document findings for production implementation

TODO: Add first 3-point basket tracking
- Similar to first basket, but filter to 3-point field goals only
- Use play-by-play data with EVENTMSGTYPE == 1 and shot type == 3PT
- Popular prop bet: "Who will make the first 3-pointer?"
- Would use same PlayByPlayV2 endpoint (subject to same API limitations)

Usage:
    python backend/sandbox/nba_sandbox.py

Requirements:
    - nba_api library (pip install nba_api)
    - pandas (typically installed with nba_api)
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
if not check_library_installed("nba_api", "pip install nba_api"):
    sys.exit(1)

# Import nba_api after dependency check
from nba_api.stats.endpoints import leaguegamefinder, playergamelogs, playbyplayv2
from nba_api.stats.static import teams


def document_playbyplay_api_findings():
    """
    Document findings about NBA play-by-play API capabilities and limitations.

    This function is called when we encounter API issues, to document what we've
    learned about the API structure and provide recommendations.
    """
    print_section_header("First Basket Identification - API Research Findings")
    print("📋 NBA Play-by-Play API Analysis:")
    print()
    print("✅ CONFIRMED CAPABILITIES:")
    print("  • nba_api library provides PlayByPlayV2 endpoint")
    print("  • Endpoint accepts game_id parameter")
    print("  • Designed to return play-by-play data for individual games")
    print("  • Should include timing, player, and action information")
    print()
    print("⚠️  IDENTIFIED LIMITATIONS:")
    print("  • API may have rate limiting (not documented)")
    print("  • API structure can change without notice")
    print("  • Play-by-play data requires per-game API calls")
    print("  • No bulk play-by-play endpoint available")
    print("  • Future games (projected in dataset) don't have play-by-play")
    print()
    print("💡 PRODUCTION RECOMMENDATIONS:")
    print()
    print("  OPTION 1: Use nba_api with retry logic")
    print("    ✓ Implement exponential backoff for rate limits")
    print("    ✓ Cache play-by-play data per game")
    print("    ✓ Only fetch for completed games")
    print("    ✓ Handle API errors gracefully")
    print("    ✓ Monitor for API structure changes")
    print()
    print("  OPTION 2: Alternative data sources")
    print("    • NBA.com official stats API (direct HTTP)")
    print("    • Sports data providers (SportsRadar, ESPN API)")
    print("    • Web scraping (less reliable, against TOS)")
    print()
    print("  OPTION 3: Manual data entry")
    print("    • Track first basket manually for key games")
    print("    • Use official box scores")
    print("    • Suitable for small-scale deployment")
    print()
    print("🎯 FIRST BASKET TRACKING FEASIBILITY:")
    print()
    print("  THEORETICAL: ✅ YES - Play-by-play data exists")
    print("    • NBA tracks every play with timing")
    print("    • First basket can be identified from play sequence")
    print("    • Player identification is reliable")
    print()
    print("  PRACTICAL: ⚠️  CHALLENGING - API limitations")
    print("    • nba_api is unofficial and unstable")
    print("    • Rate limiting makes bulk processing difficult")
    print("    • Requires per-game API calls")
    print("    • May need paid data provider for production")
    print()
    print("📊 RECOMMENDED APPROACH FOR FIRST6:")
    print()
    print("  1. Start with manual tracking for MVP")
    print("  2. Implement nba_api with robust error handling")
    print("  3. Cache all successfully retrieved data")
    print("  4. Consider paid API if scaling up")
    print("  5. Focus on high-value games (playoffs, popular teams)")
    print()
    print("🔍 ALTERNATIVE: Focus on player game totals")
    print()
    print("  • PlayerGameLogs API is stable and reliable")
    print("  • Can track 'Did player X score 10+ points?'")
    print("  • Can track 'Did player X score 20+ points?'")
    print("  • Easier to implement than first basket tracking")
    print("  • Still provides engaging prop betting experience")
    print()
    print("📝 TODO: First 3-Point Basket Tracking")
    print()
    print("  • Similar approach to first basket, but filter to 3PT shots")
    print("  • Popular prop: 'Who will make the first 3-pointer?'")
    print("  • Would use PlayByPlayV2 with shot type filtering")
    print("  • Subject to same API limitations as first basket")
    print("  • Consider as future enhancement if API becomes stable")
    print()


def main():
    """Main execution function for NBA data exploration."""
    print_section_header("NBA Data Sandbox - Comprehensive Exploration")
    print("This script explores NBA data capabilities using nba_api")
    print("Focus: Game data, player statistics, and first basket tracking")
    print()

    # Fetch and display current season games
    games_df = fetch_current_season_games()

    if games_df is not None:
        # Fetch and display player scoring statistics
        player_stats = fetch_player_scoring_stats(games_df)

        if player_stats is not None:
            # Research first basket scorer identification using play-by-play data
            explore_first_basket_scorer_identification(games_df)


def fetch_current_season_games():
    """
    Fetch and display current season NBA games.

    Uses nba_api LeagueGameFinder to retrieve game data for the 2024-25 season.
    Displays key fields: game_id, home_team, away_team, game_date, final_score.

    Requirements: 2.1, 2.2, 6.1, 7.1, 7.2, 7.3
    """
    print_section_header("Current Season Games")

    try:
        # Fetch 2024-25 season games
        # LeagueGameFinder returns game data for specified season
        # Season format: '2024-25' for the 2024-2025 season
        print("📡 Fetching 2024-25 NBA season games...")
        print("⚠️  Note: This may take a moment as nba_api fetches from NBA.com...")

        # Create LeagueGameFinder instance for current season
        game_finder = leaguegamefinder.LeagueGameFinder(
            season_nullable="2024-25", league_id_nullable="00"  # NBA league
        )

        # Get the games dataframe
        games_df = game_finder.get_data_frames()[0]

        # Validate response
        if not validate_dataframe_response(games_df, "game data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(games_df)} game records")
        print()

        # Note: LeagueGameFinder returns one row per team per game
        # So each game appears twice (once for home team, once for away team)
        unique_games = games_df["GAME_ID"].nunique()
        print(f"📊 Unique games: {unique_games}")
        print()

        # Display key columns for game identification
        # Available columns in LeagueGameFinder response:
        # SEASON_ID, TEAM_ID, TEAM_ABBREVIATION, TEAM_NAME, GAME_ID, GAME_DATE,
        # MATCHUP, WL (Win/Loss), MIN, PTS, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT,
        # FTM, FTA, FT_PCT, OREB, DREB, REB, AST, STL, BLK, TOV, PF, PLUS_MINUS

        key_columns = [
            "GAME_ID",
            "GAME_DATE",
            "MATCHUP",  # Shows "TEAM @ OPPONENT" or "TEAM vs. OPPONENT"
            "TEAM_ABBREVIATION",
            "PTS",  # Points scored by this team
            "WL",  # Win/Loss
        ]

        # Filter to only existing columns
        available_columns = [col for col in key_columns if col in games_df.columns]

        # Sort by game date (most recent first)
        games_df_sorted = games_df.sort_values("GAME_DATE", ascending=False)

        display_dataframe_sample(
            games_df_sorted,
            "NBA Games - Key Fields (Most Recent)",
            max_rows=20,
            columns=available_columns,
        )

        # Display full data structure for exploration
        print_data_structure_info(games_df, "NBA Games - Complete Data Structure")

        return games_df

    except Exception as e:
        handle_api_error(e, "fetching NBA games")
        return None


def fetch_player_scoring_stats(games_df):
    """
    Fetch and display player scoring statistics for sample games.

    Uses nba_api PlayerGameLogs to retrieve player statistics for the 2024-25 season.
    Focuses on scoring statistics: points, field_goals_made, three_pointers_made.

    Requirements: 2.3, 2.4, 6.2, 6.3
    """
    print_section_header("Player Scoring Statistics")

    try:
        # Fetch 2024-25 season player game logs
        # PlayerGameLogs returns detailed player statistics for each game
        print("📡 Fetching 2024-25 NBA player game logs...")
        print("⚠️  Note: This is a large dataset and may take a moment to load...")

        # Create PlayerGameLogs instance for current season
        player_logs = playergamelogs.PlayerGameLogs(
            season_nullable="2024-25", league_id_nullable="00"  # NBA league
        )

        # Get the player game logs dataframe
        stats_df = player_logs.get_data_frames()[0]

        # Validate response
        if not validate_dataframe_response(stats_df, "player statistics retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(stats_df)} player game log records")
        print()

        # Filter to players with scoring (points > 0)
        scoring_players = stats_df[stats_df["PTS"] > 0].copy()

        if len(scoring_players) == 0:
            print("⚠️  No scoring data found in the dataset")
            return None

        print(f"📊 Found {len(scoring_players)} player-game records with scoring")
        print()

        # Display key columns for scoring analysis
        # Available columns in PlayerGameLogs response:
        # SEASON_YEAR, PLAYER_ID, PLAYER_NAME, NICKNAME, TEAM_ID, TEAM_ABBREVIATION,
        # TEAM_NAME, GAME_ID, GAME_DATE, MATCHUP, WL, MIN, FGM, FGA, FG_PCT,
        # FG3M, FG3A, FG3_PCT, FTM, FTA, FT_PCT, OREB, DREB, REB, AST, TOV,
        # STL, BLK, BLKA, PF, PFD, PTS, PLUS_MINUS, NBA_FANTASY_PTS, DD2, TD3

        key_columns = [
            "PLAYER_NAME",
            "TEAM_ABBREVIATION",
            "GAME_DATE",
            "MATCHUP",
            "PTS",  # Total points
            "FGM",  # Field goals made
            "FGA",  # Field goals attempted
            "FG3M",  # Three-pointers made
            "FG3A",  # Three-pointers attempted
            "FTM",  # Free throws made
        ]

        # Sort by points scored (highest first)
        scoring_players_sorted = scoring_players.sort_values("PTS", ascending=False)

        display_dataframe_sample(
            scoring_players_sorted,
            "Top Scoring Performances - 2024-25 Season",
            max_rows=20,
            columns=key_columns,
        )

        # Display data structure information
        print_section_header("Scoring Statistics - Data Structure Notes")
        print("📋 Key Fields for Scoring Tracking:")
        print()
        print("  • PTS: Total points scored in the game")
        print("  • FGM: Field goals made (2-point and 3-point baskets)")
        print("  • FGA: Field goals attempted")
        print("  • FG_PCT: Field goal percentage")
        print("  • FG3M: Three-point field goals made")
        print("  • FG3A: Three-point field goals attempted")
        print("  • FG3_PCT: Three-point field goal percentage")
        print("  • FTM: Free throws made")
        print("  • FTA: Free throws attempted")
        print("  • FT_PCT: Free throw percentage")
        print()
        print("📊 Data Granularity:")
        print("  • Statistics are provided at the player-game level")
        print("  • Each row represents one player's performance in one game")
        print("  • To get season totals, aggregate by PLAYER_ID")
        print()
        print("⚠️  Limitation Identified:")
        print("  • This dataset provides TOTALS for the game")
        print("  • It does NOT provide timing/sequence information")
        print("  • Cannot determine FIRST BASKET scorer from this data alone")
        print("  • Need play-by-play data for first basket identification")
        print()

        # Show some interesting statistics
        print_section_header("Scoring Statistics - Summary")

        # Top scorers (by total points across all games)
        top_scorers = (
            scoring_players.groupby(["PLAYER_NAME", "TEAM_ABBREVIATION"])["PTS"]
            .sum()
            .reset_index()
            .sort_values("PTS", ascending=False)
            .head(10)
        )

        print("🏀 Top 10 Scorers (Total Points):")
        print()
        for idx, row in top_scorers.iterrows():
            print(
                f"  {idx+1}. {row['PLAYER_NAME']} ({row['TEAM_ABBREVIATION']}): {row['PTS']} points"
            )
        print()

        # Players with most 3-pointers
        top_three_point = (
            scoring_players.groupby(["PLAYER_NAME", "TEAM_ABBREVIATION"])["FG3M"]
            .sum()
            .reset_index()
            .sort_values("FG3M", ascending=False)
            .head(10)
        )

        print("🎯 Top 10 Three-Point Shooters (Total 3PM):")
        print()
        for idx, row in top_three_point.iterrows():
            print(
                f"  {idx+1}. {row['PLAYER_NAME']} ({row['TEAM_ABBREVIATION']}): {int(row['FG3M'])} three-pointers"
            )
        print()

        return scoring_players_sorted

    except Exception as e:
        handle_api_error(e, "fetching player scoring statistics")
        return None


def explore_first_basket_scorer_identification(games_df):
    """
    Research and explore first basket scorer identification using play-by-play data.

    Uses nba_api PlayByPlayV2 endpoint to retrieve play-by-play data and attempts to identify
    the first basket scorer for sample games.

    Requirements: 2.4, 8.4
    """
    print_section_header("First Basket Scorer Identification - Research")

    try:
        # Select a sample game to analyze
        # Get a recent completed regular season game (not playoffs)
        # Regular season games start with '002' while playoff games start with '004'
        completed_games = games_df[games_df["PTS"] > 0].copy()

        if len(completed_games) == 0:
            print("⚠️  No completed games found in the dataset")
            return None

        # Get unique game IDs and filter to regular season
        unique_game_ids = completed_games["GAME_ID"].unique()
        regular_season_games = [gid for gid in unique_game_ids if gid.startswith("002")]

        if len(regular_season_games) == 0:
            print("⚠️  No regular season games found")
            # Fall back to any game
            sample_game_id = unique_game_ids[0]
        else:
            # Get a game from earlier in the season (more likely to have complete data)
            sample_game_id = regular_season_games[-1]  # Earlier game

        print(f"🎯 Analyzing sample game: {sample_game_id}")
        print()

        # Fetch play-by-play data for this game
        print("📡 Fetching play-by-play data...")
        print("⚠️  Note: This may take a moment as nba_api fetches from NBA.com...")

        # Try to fetch play-by-play data - this API is known to be unstable
        try:
            pbp = playbyplayv2.PlayByPlayV2(game_id=sample_game_id)
            pbp_dfs = pbp.get_data_frames()

            if len(pbp_dfs) == 0:
                print("⚠️  No dataframes returned from PlayByPlayV2")
                print()
                print("📋 RESEARCH FINDING:")
                print("   The PlayByPlayV2 endpoint did not return data for this game.")
                print("   This could be due to:")
                print("   • API rate limiting")
                print("   • Game data not yet available")
                print("   • API structure changes")
                print("   • Network/connectivity issues")
                print()
                # Document what we know about the API
                document_playbyplay_api_findings()
                return None

            pbp_df = pbp_dfs[0]

        except (KeyError, IndexError, AttributeError, TypeError) as e:
            print(f"⚠️  Error accessing play-by-play data: {type(e).__name__}: {e}")
            print()
            print("📋 RESEARCH FINDING:")
            print("   The PlayByPlayV2 endpoint encountered an error.")
            print("   This is a known issue with nba_api - the API structure")
            print("   can change without notice, or rate limiting may apply.")
            print()
            # Document what we know about the API
            document_playbyplay_api_findings()
            return None

        # Validate response
        if not validate_dataframe_response(pbp_df, "play-by-play data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(pbp_df)} play-by-play records")
        print()

        # Display sample of play-by-play data structure
        print_section_header("Play-by-Play Data Structure")
        print_data_structure_info(pbp_df, "Play-by-Play Data - Complete Structure")

        # Filter to scoring plays
        # In NBA play-by-play, scoring plays have SCOREMARGIN that changes
        # We need to identify field goals (2pt and 3pt baskets)
        # EVENTMSGTYPE codes:
        # 1 = Made Shot (Field Goal)
        # 2 = Missed Shot
        # 3 = Free Throw
        # etc.

        scoring_plays = pbp_df[pbp_df["EVENTMSGTYPE"] == 1].copy()

        if len(scoring_plays) == 0:
            print("⚠️  No scoring plays found in the dataset")
            return None

        print(f"📊 Found {len(scoring_plays)} made field goals in this game")
        print()

        # Sort by period and time to get chronological order
        # PCTIMESTRING is in format "MM:SS" for time remaining in period
        # We need to convert this to seconds for proper sorting

        def time_to_seconds(time_str):
            """Convert MM:SS to total seconds remaining"""
            if pd.isna(time_str) or time_str == "":
                return 0
            parts = str(time_str).split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0

        scoring_plays["time_remaining_seconds"] = scoring_plays["PCTIMESTRING"].apply(
            time_to_seconds
        )

        # Sort by period (ascending) and time remaining (descending = chronological)
        scoring_plays_sorted = scoring_plays.sort_values(
            ["PERIOD", "time_remaining_seconds"], ascending=[True, False]
        )

        # Display first few scoring plays
        scoring_display_columns = [
            "PERIOD",
            "PCTIMESTRING",
            "HOMEDESCRIPTION",
            "VISITORDESCRIPTION",
            "SCORE",
            "SCOREMARGIN",
        ]

        available_scoring_columns = [
            col
            for col in scoring_display_columns
            if col in scoring_plays_sorted.columns
        ]

        display_dataframe_sample(
            scoring_plays_sorted,
            f"Scoring Plays - {sample_game_id} (Chronological Order)",
            max_rows=15,
            columns=available_scoring_columns,
        )

        # Identify the first basket
        first_basket = scoring_plays_sorted.iloc[0]

        # Determine which team/player scored
        first_basket_description = (
            first_basket["HOMEDESCRIPTION"]
            if pd.notna(first_basket["HOMEDESCRIPTION"])
            else first_basket["VISITORDESCRIPTION"]
        )

        print_section_header("First Basket Scorer Identification - RESULTS")
        print("✅ SUCCESS: First basket scorer can be identified!")
        print()
        print(f"🏀 First Basket:")
        print(f"   Period: {first_basket['PERIOD']}")
        print(f"   Time: {first_basket['PCTIMESTRING']}")
        print(f"   Description: {first_basket_description}")
        print(f"   Score: {first_basket['SCORE']}")
        print()

        # Document data structure for first basket identification
        print_section_header(
            "First Basket Identification - Data Structure & Recommendations"
        )
        print("📋 Key Fields Available:")
        print()
        print("  • GAME_ID: Unique game identifier")
        print("  • EVENTNUM: Sequential event number")
        print("  • EVENTMSGTYPE: Type of event (1 = Made Shot)")
        print("  • PERIOD: Quarter/period number (1-4 for regulation)")
        print("  • PCTIMESTRING: Time remaining in period (MM:SS)")
        print("  • HOMEDESCRIPTION: Description of home team action")
        print("  • VISITORDESCRIPTION: Description of visitor team action")
        print("  • SCORE: Current score after the play")
        print("  • SCOREMARGIN: Point differential")
        print("  • PLAYER1_ID: Primary player involved (scorer)")
        print("  • PLAYER1_NAME: Name of primary player")
        print("  • PLAYER1_TEAM_ID: Team ID of primary player")
        print()
        print("✅ First Basket Identification Algorithm:")
        print()
        print("  1. Fetch play-by-play data using PlayByPlayV2(game_id)")
        print("  2. Filter to made shots (EVENTMSGTYPE == 1)")
        print("  3. Exclude free throws (check description or use EVENTMSGACTIONTYPE)")
        print("  4. Sort by PERIOD (ascending) and PCTIMESTRING (descending)")
        print("  5. Take the first record")
        print("  6. Extract PLAYER1_ID and PLAYER1_NAME")
        print()
        print("📊 Data Quality:")
        print(f"  • Total plays in game: {len(pbp_df)}")
        print(f"  • Made field goals: {len(scoring_plays)}")
        print(
            f"  • Plays with player info: {scoring_plays['PLAYER1_NAME'].notna().sum()}"
        )
        print()
        print("💡 Production Implementation Recommendations:")
        print()
        print("  ✓ Use nba_api PlayByPlayV2 endpoint for play-by-play data")
        print("  ✓ Filter to EVENTMSGTYPE == 1 (made shots)")
        print("  ✓ Exclude free throws (EVENTMSGTYPE == 3)")
        print("  ✓ Sort by PERIOD and time remaining")
        print("  ✓ Group by GAME_ID and take first record")
        print("  ✓ Store first basket scorer in database with game_id reference")
        print("  ✓ Consider caching play-by-play data per game")
        print("  ✓ Update data after each game completes")
        print()
        print("⚠️  Considerations:")
        print()
        print("  • Play-by-play data is available per game (not bulk)")
        print("  • Need to make one API call per game")
        print("  • Data available shortly after game completion")
        print("  • PLAYER1_ID provides reliable player identification")
        print("  • Can distinguish 2-point vs 3-point baskets")
        print("  • Free throws are separate events (not baskets)")
        print()
        print("🔍 Additional Insights:")
        print()
        print("  • NBA play-by-play is very detailed and reliable")
        print("  • Each play has multiple data points (time, player, action)")
        print("  • Can track not just first basket, but all baskets in sequence")
        print("  • Can identify assist player (PLAYER2_ID) if applicable")
        print("  • Can distinguish shot types (layup, dunk, jump shot, etc.)")
        print()

        return scoring_plays_sorted

    except Exception as e:
        handle_api_error(e, "exploring first basket scorer identification")
        return None


if __name__ == "__main__":
    main()
