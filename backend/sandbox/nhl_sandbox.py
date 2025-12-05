"""
NHL Data Sandbox Script

This script demonstrates comprehensive NHL data exploration using nhl-api-py.
It validates the library's capabilities for:
- Fetching current season game data
- Retrieving player goal statistics
- Identifying first goal scorers (research)
- Tracking anytime goal scorers (research)

Purpose:
- Test nhl-api-py functionality before production integration
- Explore data structures and available fields
- Validate first goal and anytime goal tracking capabilities
- Document findings for production implementation

Usage:
    python backend/sandbox/nhl_sandbox.py

Requirements:
    - nhl-api-py library (pip install nhl-api-py)
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
if not check_library_installed("nhlpy", "pip install nhl-api-py"):
    sys.exit(1)

# Import nhl-api-py after dependency check
from nhlpy import NHLClient
import pandas as pd


def main():
    """Main execution function for NHL data exploration."""
    print_section_header("NHL Data Sandbox - Comprehensive Exploration")
    print("This script explores NHL data capabilities using nhl-api-py")
    print("Focus: Game data, player statistics, and goal scorer tracking")
    print()

    try:
        # Fetch and display current season games
        games_df = fetch_current_season_games()

        if games_df is not None and len(games_df) > 0:
            # Fetch and display player goal statistics
            player_stats = fetch_player_goal_stats()

            if player_stats is not None:
                print("✅ NHL sandbox script tasks 5.1 and 5.2 complete")
                print()

            # Research first goal scorer identification
            first_goal_research = research_first_goal_scorer(games_df)

            if first_goal_research:
                print("✅ NHL sandbox script task 5.3 complete")
                print()

            # Research anytime goal scorer tracking
            anytime_goal_research = research_anytime_goal_scorer(games_df)

            if anytime_goal_research:
                print("✅ NHL sandbox script task 5.4 complete")
                print()
        else:
            print(
                "❌ Failed to retrieve game data. Cannot proceed with further analysis."
            )
            print("   Please check your network connection and try again.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        print("   Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print("\n❌ Unexpected error in main execution:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        print("\n   This may be due to:")
        print("   • Network connectivity issues")
        print("   • NHL API service disruption")
        print("   • Changes to the nhl-api-py library")
        print("\n   Please try again later or check the NHL API status.")
        sys.exit(1)


def fetch_player_goal_stats():
    """
    Fetch and display player goal statistics for sample games.

    Uses nhlpy to retrieve player statistics including goals, assists, and points.
    Displays scoring statistics for top players.

    Requirements: 4.3, 4.4, 6.2, 6.3
    """
    print_section_header("Player Goal Statistics")

    try:
        print("📡 Fetching NHL player statistics...")
        print("⚠️  Note: Retrieving player stats from NHL API...")
        print()

        # Create NHLClient instance
        try:
            client = NHLClient()
        except Exception as e:
            print(f"❌ Failed to create NHL API client: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            return None

        # Fetch player statistics for the 2024-25 season
        # The stats endpoint provides player statistics
        # We'll use the skater stats summary endpoint

        # Get current season stats for skaters (non-goalies)
        # The player_stats endpoint requires season parameter
        season = "20242025"  # NHL season format: YYYYYYYY

        print(f"   Fetching skater statistics for {season} season")
        print()

        # Fetch skater stats using the stats endpoint
        # This returns summary statistics for all players
        try:
            stats_data = client.stats.skater_stats_summary(
                start_season=season, end_season=season, limit=50  # Get top 50 players
            )
        except AttributeError as e:
            print(f"❌ API method not found: {str(e)}")
            print("   The nhl-api-py library may have changed its API structure.")
            return None
        except ConnectionError as e:
            print(f"❌ Network connection error: {str(e)}")
            print("   Please check your internet connection and try again.")
            return None
        except Exception as e:
            print(f"❌ Error fetching player statistics: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            return None

        # Validate stats data response
        if not stats_data:
            print("❌ No player statistics data returned from NHL API")
            print(
                "   The API may be temporarily unavailable or no data exists for this season."
            )
            return None

        if not isinstance(stats_data, list):
            print(f"❌ Unexpected response format: {type(stats_data).__name__}")
            print("   Expected a list but received a different data type.")
            return None

        # Parse the stats data structure
        # stats_data is a list of player dictionaries
        player_stats_data = []

        if stats_data:
            for player in stats_data:
                # Extract player statistics
                player_info = {
                    "player_id": player.get("playerId", ""),
                    "player_name": player.get("skaterFullName", ""),
                    "team": player.get("teamAbbrevs", ""),
                    "position": player.get("positionCode", ""),
                    "games_played": player.get("gamesPlayed", 0),
                    "goals": player.get("goals", 0),
                    "assists": player.get("assists", 0),
                    "points": player.get("points", 0),
                    "plus_minus": player.get("plusMinus", 0),
                    "shots": player.get("shots", 0),
                    "shooting_pct": player.get("shootingPct", 0.0),
                    "pp_goals": player.get("ppGoals", 0),
                    "sh_goals": player.get("shGoals", 0),
                    "gw_goals": player.get("gameWinningGoals", 0),
                }
                player_stats_data.append(player_info)

        # Convert to DataFrame
        player_stats_df = pd.DataFrame(player_stats_data)

        # Validate response
        if not validate_dataframe_response(
            player_stats_df, "player statistics retrieval"
        ):
            return None

        print(
            f"✅ Successfully retrieved statistics for {len(player_stats_df)} players"
        )
        print()

        # Display key columns for player scoring statistics
        key_columns = [
            "player_name",
            "team",
            "position",
            "games_played",
            "goals",
            "assists",
            "points",
        ]

        # Filter to only existing columns
        available_columns = [
            col for col in key_columns if col in player_stats_df.columns
        ]

        # Sort by points (highest first) to show top scorers
        player_stats_sorted = player_stats_df.sort_values("points", ascending=False)

        display_dataframe_sample(
            player_stats_sorted,
            "NHL Player Statistics - Top Scorers",
            max_rows=20,
            columns=available_columns,
        )

        # Display full data structure for exploration
        print_data_structure_info(
            player_stats_df, "NHL Player Statistics - Complete Data Structure"
        )

        # Show some summary statistics
        print_section_header("NHL Player Statistics - Summary")

        # Top goal scorers
        print("🏒 Top 5 Goal Scorers:")
        print()
        top_goal_scorers = player_stats_sorted.nlargest(5, "goals")
        for idx, player in top_goal_scorers.iterrows():
            print(
                f"  • {player['player_name']} ({player['team']}): {player['goals']} goals"
            )
        print()

        # Top point leaders
        print("⭐ Top 5 Point Leaders:")
        print()
        top_point_leaders = player_stats_sorted.nlargest(5, "points")
        for idx, player in top_point_leaders.iterrows():
            print(
                f"  • {player['player_name']} ({player['team']}): {player['points']} points ({player['goals']}G, {player['assists']}A)"
            )
        print()

        # Average statistics
        print("📊 League Averages (from sample):")
        print(f"  • Average Goals per Player: {player_stats_df['goals'].mean():.2f}")
        print(
            f"  • Average Assists per Player: {player_stats_df['assists'].mean():.2f}"
        )
        print(f"  • Average Points per Player: {player_stats_df['points'].mean():.2f}")
        print()

        return player_stats_df

    except Exception as e:
        handle_api_error(e, "fetching NHL player statistics")
        return None


def fetch_current_season_games():
    """
    Fetch and display current season NHL games.

    Uses nhlpy NHLClient to retrieve game data for the 2024-25 season.
    Displays key fields: game_id, home_team, away_team, game_date, final_score.

    Requirements: 4.1, 4.2, 6.1, 7.1, 7.2, 7.3
    """
    print_section_header("Current Season Games")

    try:
        # Fetch 2024-25 season games
        # nhlpy NHLClient provides access to NHL API endpoints
        print("📡 Fetching 2024-25 NHL season games...")
        print("⚠️  Note: This may take a moment as nhlpy fetches from NHL.com...")

        # Create NHLClient instance
        try:
            client = NHLClient()
        except Exception as e:
            print(f"❌ Failed to create NHL API client: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            print(
                "   This may indicate an issue with the nhl-api-py library installation."
            )
            return None

        # NHL 2024-25 season started in October 2024
        # Let's fetch games using daily_schedule for a specific date
        # The daily_schedule method takes a single date and returns games for that day

        # Get a date from the current season
        target_date = "2024-11-15"  # Mid-season date to get good sample

        print(f"   Fetching games for {target_date}")
        print()

        # Fetch schedule data using daily_schedule
        # This returns games for the specified date
        try:
            schedule_data = client.schedule.daily_schedule(date=target_date)
        except AttributeError as e:
            print(f"❌ API method not found: {str(e)}")
            print("   The nhl-api-py library may have changed its API structure.")
            print("   Please check the library documentation for updates.")
            return None
        except ConnectionError as e:
            print(f"❌ Network connection error: {str(e)}")
            print("   Please check your internet connection and try again.")
            return None
        except TimeoutError as e:
            print(f"❌ Request timeout: {str(e)}")
            print("   The NHL API is taking too long to respond.")
            print("   Please try again later.")
            return None

        # Validate schedule data response
        if not schedule_data:
            print("❌ No data returned from NHL API")
            print(
                "   The API may be temporarily unavailable or the date may be invalid."
            )
            return None

        if not isinstance(schedule_data, dict):
            print(f"❌ Unexpected response format: {type(schedule_data).__name__}")
            print("   Expected a dictionary but received a different data type.")
            return None

        # The schedule_data contains game information
        # We need to extract and format it into a DataFrame
        games_data = []

        # Parse the schedule data structure
        if "games" not in schedule_data:
            print("⚠️  No 'games' field found in API response")
            print("   The API response structure may have changed.")
            print(f"   Available fields: {list(schedule_data.keys())}")
            return None

        if schedule_data and "games" in schedule_data:
            for game in schedule_data["games"]:
                # Extract game information
                game_info = {
                    "game_id": game.get("id", ""),
                    "game_date": schedule_data.get("date", ""),
                    "season": game.get("season", ""),
                    "game_type": game.get("gameType", ""),
                    "home_team": game.get("homeTeam", {}).get("abbrev", ""),
                    "home_team_name": game.get("homeTeam", {})
                    .get("placeName", {})
                    .get("default", ""),
                    "away_team": game.get("awayTeam", {}).get("abbrev", ""),
                    "away_team_name": game.get("awayTeam", {})
                    .get("placeName", {})
                    .get("default", ""),
                    "home_score": game.get("homeTeam", {}).get("score", None),
                    "away_score": game.get("awayTeam", {}).get("score", None),
                    "game_state": game.get("gameState", ""),
                    "venue": game.get("venue", {}).get("default", ""),
                }
                games_data.append(game_info)

        # Convert to DataFrame
        games_df = pd.DataFrame(games_data)

        # Validate response
        if not validate_dataframe_response(games_df, "game data retrieval"):
            return None

        print(f"✅ Successfully retrieved {len(games_df)} games")
        print()

        # Display key columns for game identification
        key_columns = [
            "game_id",
            "game_date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "game_state",
        ]

        # Filter to only existing columns
        available_columns = [col for col in key_columns if col in games_df.columns]

        # Sort by game date (most recent first)
        games_df_sorted = games_df.sort_values("game_date", ascending=False)

        display_dataframe_sample(
            games_df_sorted,
            "NHL Games - Key Fields (Most Recent)",
            max_rows=15,
            columns=available_columns,
        )

        # Display full data structure for exploration
        print_data_structure_info(games_df, "NHL Games - Complete Data Structure")

        # Show some summary statistics
        print_section_header("NHL Games - Summary Statistics")

        # Count games by state
        if "game_state" in games_df.columns:
            print("📊 Games by State:")
            print()
            state_counts = games_df["game_state"].value_counts()
            for state, count in state_counts.items():
                print(f"  • {state}: {count} games")
            print()

        # Count completed games (with scores)
        completed_games = games_df[games_df["home_score"].notna()]
        print(f"📊 Completed games (with final scores): {len(completed_games)}")
        print()

        return games_df

    except Exception as e:
        handle_api_error(e, "fetching NHL games")
        return None


def fetch_play_by_play_data(client, game_id):
    """
    Fetch play-by-play data with comprehensive error handling.

    Args:
        client: NHLClient instance
        game_id: Game identifier

    Returns:
        dict: Play-by-play data or None if error occurs
    """
    try:
        pbp_data = client.game_center.play_by_play(game_id)
    except AttributeError as e:
        print(f"❌ API method not found: {str(e)}")
        print("   The nhl-api-py library may have changed its API structure.")
        return None
    except ConnectionError as e:
        print(f"❌ Network connection error: {str(e)}")
        print("   Please check your internet connection and try again.")
        return None
    except TimeoutError as e:
        print(f"❌ Request timeout: {str(e)}")
        print("   The NHL API is taking too long to respond.")
        return None
    except Exception as e:
        print(f"❌ Error fetching play-by-play data: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        return None

    if not pbp_data:
        print("❌ No play-by-play data returned from API")
        print("   The game may not have play-by-play data available yet.")
        return None

    if not isinstance(pbp_data, dict):
        print(f"❌ Unexpected response format: {type(pbp_data).__name__}")
        print("   Expected a dictionary but received a different data type.")
        return None

    return pbp_data


def research_first_goal_scorer(games_df):
    """
    Research and implement first goal scorer identification using play-by-play data.

    Explores the NHL API's game feed play-by-play data to determine if we can:
    1. Identify the first goal scorer for a game
    2. Extract goal timing and sequence information
    3. Distinguish between different goal types (even strength, power play, etc.)

    This function attempts to fetch play-by-play data for sample games and
    documents the data structure and capabilities for production implementation.

    Requirements: 4.4, 8.4
    """
    print_section_header("First Goal Scorer Identification Research")

    try:
        print("🔬 Researching first goal scorer identification capabilities...")
        print("   Exploring NHL API play-by-play data structure")
        print()

        # Create NHLClient instance
        try:
            client = NHLClient()
        except Exception as e:
            print(f"❌ Failed to create NHL API client: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            return None

        # Get a completed game from our games_df to analyze
        # Filter to games with scores (completed games)
        completed_games = games_df[games_df["home_score"].notna()].copy()

        if len(completed_games) == 0:
            print("⚠️  No completed games found in dataset")
            print("   Cannot research first goal scorer without completed games")
            return None

        # Select the first completed game for analysis
        sample_game = completed_games.iloc[0]
        game_id = sample_game["game_id"]

        print(f"📊 Analyzing sample game:")
        print(f"   Game ID: {game_id}")
        print(f"   Matchup: {sample_game['away_team']} @ {sample_game['home_team']}")
        print(
            f"   Final Score: {sample_game['away_team']} {sample_game['away_score']} - {sample_game['home_team']} {sample_game['home_score']}"
        )
        print()

        # Fetch play-by-play data using the game_play_by_play endpoint
        print("📡 Fetching play-by-play data from NHL API...")
        print("   This includes all game events with timing information")
        print()

        pbp_data = fetch_play_by_play_data(client, game_id)

        if not pbp_data:
            return None

        print("✅ Successfully retrieved play-by-play data")
        print()

        # Build a player ID to name mapping from roster
        player_map = {}
        roster_spots = pbp_data.get("rosterSpots", [])
        for spot in roster_spots:
            player_id = spot.get("playerId")
            first_name = spot.get("firstName", {}).get("default", "")
            last_name = spot.get("lastName", {}).get("default", "")
            full_name = f"{first_name} {last_name}".strip()
            if player_id and full_name:
                player_map[player_id] = full_name

        print(f"✅ Built player roster with {len(player_map)} players")
        print()

        # Explore the data structure
        print_section_header("Play-by-Play Data Structure Analysis")

        print("📋 Top-level keys in play-by-play response:")
        print()
        for key in pbp_data.keys():
            print(f"  • {key}")
        print()

        # Extract plays/events
        plays = pbp_data.get("plays", [])

        if not plays:
            print("⚠️  No plays found in play-by-play data")
            return None

        print(f"📊 Total plays/events in game: {len(plays)}")
        print()

        # Filter to goal events only
        goal_events = [play for play in plays if play.get("typeDescKey") == "goal"]

        print(f"🏒 Total goals in game: {len(goal_events)}")
        print()

        if len(goal_events) == 0:
            print("⚠️  No goal events found in this game")
            print("   This may be a shutout or data may not be available")
            return None

        # Analyze the first goal
        print_section_header("First Goal Analysis")

        first_goal = goal_events[0]

        print("🎯 First Goal Details:")
        print()
        print(
            f"  • Period: {first_goal.get('periodDescriptor', {}).get('number', 'N/A')}"
        )
        print(f"  • Time in Period: {first_goal.get('timeInPeriod', 'N/A')}")
        print(f"  • Time Remaining: {first_goal.get('timeRemaining', 'N/A')}")

        # Extract goal scorer information
        details = first_goal.get("details", {})

        if details:
            scorer_id = details.get("scoringPlayerId")
            scorer_name = player_map.get(scorer_id, f"Player ID {scorer_id}")
            assist1_id = details.get("assist1PlayerId")
            assist1_name = (
                player_map.get(assist1_id, f"Player ID {assist1_id}")
                if assist1_id
                else "None"
            )
            assist2_id = details.get("assist2PlayerId")
            assist2_name = (
                player_map.get(assist2_id, f"Player ID {assist2_id}")
                if assist2_id
                else "None"
            )

            print(f"  • Scoring Player ID: {scorer_id}")
            print(f"  • Scoring Player: {scorer_name}")
            print(f"  • Assist 1 Player: {assist1_name}")
            print(f"  • Assist 2 Player: {assist2_name}")
            print(f"  • Scoring Team ID: {details.get('eventOwnerTeamId', 'N/A')}")
            print(f"  • Shot Type: {details.get('shotType', 'N/A')}")

        print()

        # Show complete structure of first goal event
        print("📋 Complete First Goal Event Structure:")
        print()
        print("   Available fields in goal event:")
        for key in first_goal.keys():
            value = first_goal[key]
            if isinstance(value, dict):
                print(f"     • {key}: (nested object with {len(value)} fields)")
            elif isinstance(value, list):
                print(f"     • {key}: (list with {len(value)} items)")
            else:
                print(f"     • {key}: {value}")
        print()

        # Display all goals in chronological order
        print_section_header("All Goals in Chronological Order")

        print(f"🏒 Displaying all {len(goal_events)} goals:")
        print()

        for idx, goal in enumerate(goal_events, 1):
            period = goal.get("periodDescriptor", {}).get("number", "N/A")
            time_in_period = goal.get("timeInPeriod", "N/A")
            details = goal.get("details", {})
            scorer_id = details.get("scoringPlayerId")
            scorer = player_map.get(scorer_id, f"Player ID {scorer_id}")
            team_id = details.get("eventOwnerTeamId", "N/A")

            # Mark the first goal
            first_marker = " ⭐ FIRST GOAL" if idx == 1 else ""

            print(
                f"  {idx}. Period {period} @ {time_in_period} - {scorer} (Team: {team_id}){first_marker}"
            )

        print()

        # Document findings
        print_section_header("First Goal Identification - Findings & Recommendations")

        print("✅ CAPABILITY CONFIRMED: First Goal Scorer Identification")
        print()
        print("📊 Data Availability:")
        print("  • Play-by-play data is available via play_by_play endpoint")
        print("  • Goal events are clearly identified with typeDescKey='goal'")
        print("  • Goals are ordered chronologically in the plays array")
        print("  • First goal is simply the first goal event in the array")
        print()

        print("🏒 Goal Event Data Structure:")
        print("  • periodDescriptor.number: Period when goal was scored (1, 2, 3, OT)")
        print("  • timeInPeriod: Time elapsed in period (MM:SS format)")
        print("  • timeRemaining: Time remaining in period")
        print("  • details.scoringPlayerId: Unique player ID of goal scorer")
        print("  • details.scoringPlayerName: Full name of goal scorer")
        print("  • details.eventOwnerTeamId: Team ID of scoring team")
        print("  • details.shotType: Type of shot (wrist, slap, backhand, etc.)")
        print("  • details.assist1PlayerName: First assist (if applicable)")
        print("  • details.assist2PlayerName: Second assist (if applicable)")
        print()

        print("🎯 First Goal Identification Method:")
        print(
            "  1. Fetch play-by-play data using client.game_center.play_by_play(game_id)"
        )
        print("  2. Extract plays array from response")
        print("  3. Filter plays where typeDescKey == 'goal'")
        print("  4. First goal is goal_events[0]")
        print(
            "  5. Extract scorer from details.scoringPlayerName or details.scoringPlayerId"
        )
        print()

        print("⚡ Real-Time Considerations:")
        print("  • Play-by-play data updates in near real-time during games")
        print("  • First goal can be identified as soon as it appears in the feed")
        print("  • Data includes precise timing information for verification")
        print()

        print("💡 Production Implementation Recommendations:")
        print()
        print("  1. Data Fetching:")
        print("     • Use NHLClient.game_center.play_by_play(game_id)")
        print("     • Poll this endpoint during live games for real-time updates")
        print("     • Cache completed game data to avoid redundant API calls")
        print()

        print("  2. First Goal Extraction:")
        print("     • Filter plays where typeDescKey == 'goal'")
        print("     • Take first element from filtered list")
        print("     • Extract details.scoringPlayerId and details.scoringPlayerName")
        print()

        print("  3. Data Validation:")
        print("     • Verify goal events are chronologically ordered")
        print("     • Check for empty goal lists (shutouts)")
        print("     • Validate player IDs against roster data")
        print()

        print("  4. Edge Cases to Handle:")
        print("     • Shutout games (no goals)")
        print("     • Delayed penalty goals (may have special attributes)")
        print("     • Own goals (check team attribution)")
        print("     • Overturned goals (may appear then disappear from feed)")
        print()

        print("  5. Database Schema Suggestions:")
        print("     • Store game_id, first_goal_scorer_id, first_goal_scorer_name")
        print("     • Store period, time_in_period for verification")
        print("     • Store goal_type (even strength, power play, short-handed)")
        print("     • Add timestamp for when data was fetched")
        print()

        print("✅ CONCLUSION: First goal scorer identification is FULLY SUPPORTED")
        print("   The NHL API provides comprehensive play-by-play data with all")
        print("   necessary information to reliably identify first goal scorers.")
        print()

        # Return summary data for further processing
        first_goal_details = goal_events[0].get("details", {})
        first_scorer_id = first_goal_details.get("scoringPlayerId")
        first_scorer_name = player_map.get(
            first_scorer_id, f"Player ID {first_scorer_id}"
        )

        return {
            "supported": True,
            "sample_game_id": game_id,
            "total_goals": len(goal_events),
            "first_goal_scorer": first_scorer_name,
            "first_goal_scorer_id": first_scorer_id,
            "first_goal_period": first_goal.get("periodDescriptor", {}).get(
                "number", "N/A"
            ),
            "first_goal_time": first_goal.get("timeInPeriod", "N/A"),
            "data_structure": "play-by-play with goal events",
            "api_endpoint": "game_center.play_by_play",
        }

    except Exception as e:
        handle_api_error(e, "researching first goal scorer identification")
        return None


def research_anytime_goal_scorer(games_df):
    """
    Research and implement anytime goal scorer tracking using play-by-play data.

    Explores the NHL API's game feed play-by-play data to determine if we can:
    1. Track all goal scorers in a game (anytime goal)
    2. Extract complete goal scoring data for all players
    3. Compare data structure with first goal identification

    This function attempts to fetch play-by-play data for sample games and
    documents the data structure and capabilities for anytime goal tracking.

    Requirements: 4.4, 8.4
    """
    print_section_header("Anytime Goal Scorer Tracking Research")

    try:
        print("🔬 Researching anytime goal scorer tracking capabilities...")
        print("   Exploring complete goal scoring data for all players")
        print()

        # Create NHLClient instance
        client = NHLClient()

        # Get a completed game from our games_df to analyze
        # Filter to games with scores (completed games)
        completed_games = games_df[games_df["home_score"].notna()].copy()

        if len(completed_games) == 0:
            print("⚠️  No completed games found in dataset")
            print("   Cannot research anytime goal scorer without completed games")
            return None

        # Select the first completed game for analysis
        sample_game = completed_games.iloc[0]
        game_id = sample_game["game_id"]

        print(f"📊 Analyzing sample game:")
        print(f"   Game ID: {game_id}")
        print(f"   Matchup: {sample_game['away_team']} @ {sample_game['home_team']}")
        print(
            f"   Final Score: {sample_game['away_team']} {sample_game['away_score']} - {sample_game['home_team']} {sample_game['home_score']}"
        )
        print()

        # Fetch play-by-play data using the game_play_by_play endpoint
        print("📡 Fetching play-by-play data from NHL API...")
        print("   This includes all game events with timing information")
        print()

        pbp_data = fetch_play_by_play_data(client, game_id)

        if not pbp_data:
            return None

        print("✅ Successfully retrieved play-by-play data")
        print()

        # Build a player ID to name mapping from roster
        player_map = {}
        roster_spots = pbp_data.get("rosterSpots", [])
        for spot in roster_spots:
            player_id = spot.get("playerId")
            first_name = spot.get("firstName", {}).get("default", "")
            last_name = spot.get("lastName", {}).get("default", "")
            full_name = f"{first_name} {last_name}".strip()
            if player_id and full_name:
                player_map[player_id] = full_name

        print(f"✅ Built player roster with {len(player_map)} players")
        print()

        # Extract plays/events
        plays = pbp_data.get("plays", [])

        if not plays:
            print("⚠️  No plays found in play-by-play data")
            return None

        print(f"📊 Total plays/events in game: {len(plays)}")
        print()

        # Filter to goal events only
        goal_events = [play for play in plays if play.get("typeDescKey") == "goal"]

        print(f"🏒 Total goals in game: {len(goal_events)}")
        print()

        if len(goal_events) == 0:
            print("⚠️  No goal events found in this game")
            print("   This may be a shutout or data may not be available")
            return None

        # Analyze ALL goals for anytime goal tracking
        print_section_header("Anytime Goal Scorer Analysis")

        print("🎯 Tracking ALL Goal Scorers (Anytime Goal):")
        print()

        # Create a comprehensive list of all goal scorers with details
        all_goal_scorers = []
        unique_scorers = set()

        for idx, goal in enumerate(goal_events, 1):
            period = goal.get("periodDescriptor", {}).get("number", "N/A")
            period_type = goal.get("periodDescriptor", {}).get("periodType", "REG")
            time_in_period = goal.get("timeInPeriod", "N/A")
            time_remaining = goal.get("timeRemaining", "N/A")

            # Extract goal scorer information
            details = goal.get("details", {})
            scorer_id = details.get("scoringPlayerId")
            scorer_name = player_map.get(scorer_id, f"Player ID {scorer_id}")
            team_id = details.get("eventOwnerTeamId", "N/A")
            shot_type = details.get("shotType", "N/A")

            # Get assist information
            assist1_id = details.get("assist1PlayerId")
            assist1_name = (
                player_map.get(assist1_id, f"Player ID {assist1_id}")
                if assist1_id
                else None
            )
            assist2_id = details.get("assist2PlayerId")
            assist2_name = (
                player_map.get(assist2_id, f"Player ID {assist2_id}")
                if assist2_id
                else None
            )

            # Determine goal situation (even strength, power play, short-handed)
            # This information may be in the situationCode or other fields
            situation_code = details.get("situationCode", "N/A")

            goal_info = {
                "goal_number": idx,
                "scorer_id": scorer_id,
                "scorer_name": scorer_name,
                "team_id": team_id,
                "period": period,
                "period_type": period_type,
                "time_in_period": time_in_period,
                "time_remaining": time_remaining,
                "shot_type": shot_type,
                "situation_code": situation_code,
                "assist1_name": assist1_name,
                "assist2_name": assist2_name,
                "is_first_goal": idx == 1,
            }

            all_goal_scorers.append(goal_info)
            unique_scorers.add(scorer_name)

            # Display goal information
            first_marker = " ⭐ FIRST GOAL" if idx == 1 else ""
            assists_str = ""
            if assist1_name:
                assists_str = f" (Assists: {assist1_name}"
                if assist2_name:
                    assists_str += f", {assist2_name}"
                assists_str += ")"

            print(
                f"  Goal {idx}: {scorer_name} - Period {period} @ {time_in_period}{first_marker}"
            )
            print(f"          Team: {team_id}, Shot Type: {shot_type}{assists_str}")
            print()

        print(f"📊 Summary:")
        print(f"  • Total goals in game: {len(all_goal_scorers)}")
        print(f"  • Unique goal scorers: {len(unique_scorers)}")
        print()

        # Show unique scorers and their goal counts
        print("🏒 Goal Scorers Summary:")
        print()

        # Count goals per player
        scorer_counts = {}
        for goal in all_goal_scorers:
            scorer = goal["scorer_name"]
            scorer_counts[scorer] = scorer_counts.get(scorer, 0) + 1

        # Sort by goal count (descending)
        sorted_scorers = sorted(scorer_counts.items(), key=lambda x: x[1], reverse=True)

        for scorer, count in sorted_scorers:
            goals_text = "goal" if count == 1 else "goals"
            print(f"  • {scorer}: {count} {goals_text}")

        print()

        # Identify players with multiple goals
        multi_goal_scorers = [
            (scorer, count) for scorer, count in sorted_scorers if count > 1
        ]

        if multi_goal_scorers:
            print("🎩 Multi-Goal Scorers:")
            print()
            for scorer, count in multi_goal_scorers:
                if count == 2:
                    print(f"  • {scorer}: 2 goals (Brace)")
                elif count == 3:
                    print(f"  • {scorer}: 3 goals (Hat Trick)")
                elif count >= 4:
                    print(f"  • {scorer}: {count} goals")
            print()

        # Compare first goal vs anytime goal data structures
        print_section_header("First Goal vs Anytime Goal - Data Structure Comparison")

        print("📊 Data Structure Analysis:")
        print()

        print("✅ IDENTICAL DATA STRUCTURE:")
        print("  • Both first goal and anytime goal use the same play-by-play data")
        print("  • Each goal event has the same fields and structure")
        print("  • No difference in data availability or format")
        print()

        print("🔍 Key Fields Available for ALL Goals:")
        print("  • periodDescriptor.number: Period when goal was scored")
        print("  • periodDescriptor.periodType: Regular, OT, or SO")
        print("  • timeInPeriod: Time elapsed in period (MM:SS)")
        print("  • timeRemaining: Time remaining in period")
        print("  • details.scoringPlayerId: Player ID of goal scorer")
        print("  • details.eventOwnerTeamId: Team ID of scoring team")
        print("  • details.shotType: Type of shot")
        print("  • details.situationCode: Game situation code")
        print("  • details.assist1PlayerId: First assist player ID")
        print("  • details.assist2PlayerId: Second assist player ID")
        print()

        print("🎯 First Goal vs Anytime Goal Identification:")
        print()
        print("  First Goal:")
        print("    • Filter plays where typeDescKey == 'goal'")
        print("    • Take the FIRST element: goal_events[0]")
        print("    • Extract scorer from details.scoringPlayerId")
        print()
        print("  Anytime Goal:")
        print("    • Filter plays where typeDescKey == 'goal'")
        print("    • Iterate through ALL elements: goal_events[0...n]")
        print("    • Extract scorer from details.scoringPlayerId for each")
        print("    • Track all unique scorers or all goal instances")
        print()

        print("💡 Implementation Differences:")
        print()
        print("  First Goal:")
        print("    • Single query: Get first goal event")
        print("    • One scorer per game")
        print("    • Binary outcome: Did player X score first? (Yes/No)")
        print()
        print("  Anytime Goal:")
        print("    • Multiple queries: Get all goal events")
        print("    • Multiple scorers per game (potentially)")
        print("    • Binary outcome: Did player X score at all? (Yes/No)")
        print("    • Can also track: How many goals did player X score?")
        print()

        # Document findings
        print_section_header("Anytime Goal Tracking - Findings & Recommendations")

        print("✅ CAPABILITY CONFIRMED: Anytime Goal Scorer Tracking")
        print()
        print("📊 Data Availability:")
        print("  • Complete goal data available via play_by_play endpoint")
        print("  • All goals are included in chronological order")
        print("  • Each goal has full details (scorer, time, assists, etc.)")
        print("  • No difference in data structure between first and subsequent goals")
        print()

        print("🏒 Anytime Goal Tracking Method:")
        print(
            "  1. Fetch play-by-play data using client.game_center.play_by_play(game_id)"
        )
        print("  2. Extract plays array from response")
        print("  3. Filter plays where typeDescKey == 'goal'")
        print("  4. Iterate through ALL goal events (not just first)")
        print("  5. Extract scorer from each goal's details.scoringPlayerId")
        print("  6. Build list of all scorers or check if specific player scored")
        print()

        print("⚡ Real-Time Considerations:")
        print("  • Same as first goal - play-by-play updates in near real-time")
        print("  • New goals appear in the feed as they occur")
        print("  • Can track anytime goal status throughout the game")
        print()

        print("💡 Production Implementation Recommendations:")
        print()
        print("  1. Unified Data Fetching:")
        print("     • Use same play-by-play endpoint for both first and anytime goals")
        print("     • Single API call provides data for both prop types")
        print("     • Efficient: No need for separate queries")
        print()

        print("  2. Anytime Goal Extraction:")
        print("     • Filter plays where typeDescKey == 'goal'")
        print("     • Iterate through all goal events")
        print("     • For each goal, extract details.scoringPlayerId")
        print("     • Check if target player ID appears in any goal event")
        print()

        print("  3. Database Schema Suggestions:")
        print("     • Store all goals per game (not just first)")
        print(
            "     • Schema: game_id, goal_number, scorer_id, scorer_name, period, time"
        )
        print("     • Add is_first_goal boolean flag for easy first goal queries")
        print("     • Add goal_type (even strength, PP, SH) for additional props")
        print()

        print("  4. Query Patterns:")
        print("     • First Goal: SELECT * WHERE game_id = X AND is_first_goal = true")
        print(
            "     • Anytime Goal: SELECT * WHERE game_id = X AND scorer_id = Y (any row)"
        )
        print("     • Multi-Goal: SELECT COUNT(*) WHERE game_id = X AND scorer_id = Y")
        print()

        print("  5. Prop Betting Integration:")
        print("     • First Goal Prop: Check if player scored first goal")
        print("     • Anytime Goal Prop: Check if player scored any goal")
        print("     • Both can be resolved from same dataset")
        print("     • Consider tracking hat tricks (3+ goals) as bonus prop")
        print()

        print("  6. Edge Cases to Handle:")
        print("     • Shutout games (no goals at all)")
        print("     • Own goals (verify team attribution)")
        print("     • Overturned goals (may disappear from feed)")
        print("     • Empty net goals (may have special attributes)")
        print()

        print("✅ CONCLUSION: Anytime goal scorer tracking is FULLY SUPPORTED")
        print("   The NHL API provides complete goal data for all scorers.")
        print("   First goal and anytime goal use identical data structures.")
        print("   Both prop types can be efficiently tracked from single API call.")
        print()

        # Return summary data
        return {
            "supported": True,
            "sample_game_id": game_id,
            "total_goals": len(all_goal_scorers),
            "unique_scorers": len(unique_scorers),
            "multi_goal_scorers": len(multi_goal_scorers),
            "all_scorers": list(unique_scorers),
            "goal_details": all_goal_scorers,
            "data_structure": "play-by-play with goal events (same as first goal)",
            "api_endpoint": "game_center.play_by_play (same as first goal)",
            "comparison": "Identical data structure to first goal tracking",
        }

    except Exception as e:
        handle_api_error(e, "researching anytime goal scorer tracking")
        return None


if __name__ == "__main__":
    main()
