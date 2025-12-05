# -*- coding: utf-8 -*-
"""
College Football (CFB) Data Sandbox Script

This script demonstrates the capabilities of the cfbd library (College Football Data API)
for retrieving college football game data, player statistics, and play-by-play information.

Purpose:
- Test cfbd library integration and API access
- Explore game schedule and scoring data
- Research first touchdown scorer identification capabilities
- Research anytime touchdown scorer tracking capabilities
- Validate data structures for production integration

Usage:
    python cfb_sandbox.py

Requirements:
    - cfbd library: pip install cfbd
    - pandas: pip install pandas
    - API Key: Register at https://collegefootballdata.com/ for a free API key

IMPORTANT DEPENDENCY NOTE:
    The cfbd library requires pydantic v1, which conflicts with the main application's
    pydantic v2 dependency. Therefore, cfbd is NOT included in the main requirements.txt
    and should only be installed in isolated sandbox environments.

    To use this script:
    1. Create a separate virtual environment
    2. Install cfbd: pip install cfbd
    3. Run the script in that environment

Note: This is a sandbox/research script. It is not part of the production codebase.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add parent directory to path for common_utils import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_utils import (
    check_library_installed,
    display_dataframe_sample,
    handle_api_error,
    print_section_header,
    validate_dataframe_response,
    print_data_structure_info,
)

# Check for required library
if not check_library_installed("cfbd", "pip install cfbd"):
    sys.exit(1)

import cfbd
from cfbd.rest import ApiException
import pandas as pd
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================


def setup_api_client():
    """
    Configure the CFBD API client with authentication.

    The College Football Data API requires a free API key.
    Register at: https://collegefootballdata.com/

    To use this script with authentication:
    1. Register for a free API key
    2. Set the CFBD_API_KEY environment variable:
       - Windows: set CFBD_API_KEY=your_key_here
       - Linux/Mac: export CFBD_API_KEY=your_key_here
    3. Or modify this function to hardcode your key (not recommended for production)

    Returns:
        cfbd.Configuration: Configured API client
    """
    configuration = cfbd.Configuration()

    # Try to get API key from environment variable
    api_key = os.environ.get("CFBD_API_KEY")

    if api_key:
        configuration.api_key["Authorization"] = api_key
        configuration.api_key_prefix["Authorization"] = "Bearer"
        print("✓ API key configured from environment variable")
    else:
        print("⚠️  WARNING: No API key configured")
        print("   The College Football Data API requires authentication.")
        print("   Register at: https://collegefootballdata.com/")
        print("   Set environment variable: CFBD_API_KEY=your_key_here")
        print("   Some endpoints may work without authentication, but most require it.")
        print()

    return configuration


# ============================================================================
# GAME DATA RETRIEVAL
# ============================================================================


def fetch_games(configuration, year=2024, week=1, season_type="regular"):
    """
    Fetch college football games for a specific week.

    Args:
        configuration: CFBD API configuration
        year: Season year (default: 2024)
        week: Week number (default: 1)
        season_type: 'regular', 'postseason', or 'both' (default: 'regular')

    Returns:
        pandas.DataFrame: Game data with key fields
    """
    print_section_header(f"Fetching CFB Games - {year} Season, Week {week}")

    api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

    try:
        # Fetch games for the specified week
        games = api_instance.get_games(year=year, week=week, season_type=season_type)

        if not games:
            print("⚠️  No games found for the specified parameters")
            print(f"   Year: {year}, Week: {week}, Season Type: {season_type}")
            print()
            return pd.DataFrame()

        # Convert to DataFrame for easier display
        games_data = []
        for game in games:
            games_data.append(
                {
                    "game_id": game.id,
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "game_date": game.start_date,
                    "home_points": game.home_points if game.home_points else 0,
                    "away_points": game.away_points if game.away_points else 0,
                    "completed": game.completed,
                    "conference_game": game.conference_game,
                    "venue": game.venue if hasattr(game, "venue") else "N/A",
                }
            )

        df = pd.DataFrame(games_data)

        print(f"✓ Successfully retrieved {len(df)} games")
        print()

        return df

    except ApiException as e:
        if e.status == 401:
            print("❌ Authentication Error (401 Unauthorized)")
            print("   The API requires authentication for this endpoint.")
            print("   Please set your API key:")
            print("   1. Register at: https://collegefootballdata.com/")
            print("   2. Set environment variable: CFBD_API_KEY=your_key_here")
            print()
        else:
            handle_api_error(e, f"fetching CFB games for {year} week {week}")
        return pd.DataFrame()
    except Exception as e:
        handle_api_error(e, f"fetching CFB games for {year} week {week}")
        return pd.DataFrame()


def display_game_data(games_df):
    """
    Display game data in a formatted, readable way.

    Args:
        games_df: DataFrame containing game data
    """
    if not validate_dataframe_response(games_df, "game data retrieval"):
        return

    # Display sample of games
    display_columns = [
        "game_id",
        "home_team",
        "away_team",
        "home_points",
        "away_points",
        "completed",
    ]
    display_dataframe_sample(
        games_df, "College Football Games", max_rows=10, columns=display_columns
    )

    # Show some statistics
    print_section_header("Game Statistics")
    print(f"Total games: {len(games_df)}")
    print(f"Completed games: {games_df['completed'].sum()}")
    print(f"Conference games: {games_df['conference_game'].sum()}")
    print()


# ============================================================================
# PLAY-BY-PLAY DATA AND TOUCHDOWN TRACKING
# ============================================================================


def fetch_play_by_play_data(configuration, year=2024, week=1, season_type="regular"):
    """
    Fetch play-by-play data for games in a specific week.

    This function explores the PlaysApi to retrieve detailed play-by-play
    information, which is essential for identifying touchdown scorers.

    Args:
        configuration: CFBD API configuration
        year: Season year (default: 2024)
        week: Week number (default: 1)
        season_type: 'regular', 'postseason', or 'both' (default: 'regular')

    Returns:
        pandas.DataFrame: Play-by-play data
    """
    print_section_header(f"Fetching Play-by-Play Data - {year} Week {week}")

    api_instance = cfbd.PlaysApi(cfbd.ApiClient(configuration))

    try:
        # Fetch plays for the specified week
        plays = api_instance.get_plays(year=year, week=week, season_type=season_type)

        if not plays:
            print("⚠️  No play-by-play data found")
            print()
            return pd.DataFrame()

        # Convert to DataFrame
        plays_data = []
        for play in plays:
            plays_data.append(
                {
                    "id": play.id if hasattr(play, "id") else None,
                    "offense": play.offense if hasattr(play, "offense") else None,
                    "defense": play.defense if hasattr(play, "defense") else None,
                    "home": play.home if hasattr(play, "home") else None,
                    "away": play.away if hasattr(play, "away") else None,
                    "period": play.period if hasattr(play, "period") else None,
                    "clock": play.clock if hasattr(play, "clock") else None,
                    "play_type": play.play_type if hasattr(play, "play_type") else None,
                    "play_text": play.play_text if hasattr(play, "play_text") else None,
                    "scoring": play.scoring if hasattr(play, "scoring") else False,
                    "home_score": play.home_score if hasattr(play, "home_score") else 0,
                    "away_score": play.away_score if hasattr(play, "away_score") else 0,
                }
            )

        df = pd.DataFrame(plays_data)

        print(f"✓ Successfully retrieved {len(df)} plays")
        print()

        return df

    except ApiException as e:
        if e.status == 401:
            print("❌ Authentication Error (401 Unauthorized)")
            print("   Play-by-play data requires API authentication.")
            print()
        else:
            handle_api_error(e, f"fetching play-by-play data for {year} week {week}")
        return pd.DataFrame()
    except Exception as e:
        handle_api_error(e, f"fetching play-by-play data for {year} week {week}")
        return pd.DataFrame()


def identify_first_td_scorer(plays_df):
    """
    Attempt to identify the first touchdown scorer from play-by-play data.

    This function demonstrates the feasibility of first TD identification
    by filtering for touchdown plays and analyzing the chronological sequence.

    Args:
        plays_df: DataFrame containing play-by-play data

    Returns:
        dict: Information about first TD scorer identification capability
    """
    print_section_header("First Touchdown Scorer Identification")

    if not validate_dataframe_response(plays_df, "play-by-play data"):
        return {"possible": False, "reason": "No play-by-play data available"}

    # Filter for touchdown plays
    # Look for plays marked as scoring or with 'touchdown' in play type/text
    td_plays = plays_df[
        (plays_df["scoring"] == True)
        | (plays_df["play_type"].str.contains("touchdown", case=False, na=False))
        | (plays_df["play_text"].str.contains("touchdown", case=False, na=False))
    ].copy()

    if td_plays.empty:
        print("⚠️  No touchdown plays found in the data")
        print("   This could mean:")
        print("   • No touchdowns scored in these games")
        print("   • Play-by-play data doesn't include TD information")
        print("   • Different filtering criteria needed")
        print()
        return {"possible": False, "reason": "No touchdown plays found"}

    print(f"✓ Found {len(td_plays)} touchdown plays")
    print()

    # Sort by period and clock to get chronological order
    # Note: Clock counts down, so we need to sort appropriately
    td_plays_sorted = td_plays.sort_values(["period", "clock"], ascending=[True, False])

    # Display first few touchdown plays
    print("First touchdown plays (chronologically):")
    print()

    display_columns = ["offense", "period", "clock", "play_type", "play_text"]
    available_columns = [
        col for col in display_columns if col in td_plays_sorted.columns
    ]

    for idx, (_, play) in enumerate(td_plays_sorted.head(3).iterrows(), 1):
        print(f"TD #{idx}:")
        print(f"  Team: {play['offense']}")
        print(f"  Period: {play['period']}, Clock: {play['clock']}")
        print(f"  Play Type: {play['play_type']}")
        print(
            f"  Description: {play['play_text'][:100]}..."
            if len(str(play["play_text"])) > 100
            else f"  Description: {play['play_text']}"
        )
        print()

    # Analyze first TD
    first_td = td_plays_sorted.iloc[0]

    print("=" * 70)
    print("FIRST TD IDENTIFICATION ANALYSIS")
    print("=" * 70)
    print()
    print("✓ First TD Identification: POSSIBLE")
    print()
    print("Data Available:")
    print(f"  • Chronological ordering: Yes (period + clock)")
    print(f"  • Scoring team: {first_td['offense']}")
    print(f"  • Play description: Available")
    print(
        f"  • Timing information: Period {first_td['period']}, Clock {first_td['clock']}"
    )
    print()
    print("Player Name Extraction:")
    play_text = str(first_td["play_text"])
    print(f"  Play text: {play_text[:150]}...")
    print()
    print("  Analysis: Player names appear to be embedded in play text.")
    print("  Production implementation would need to:")
    print("    1. Parse play text to extract player names")
    print("    2. Use regex or NLP to identify scorer")
    print("    3. Validate against roster data")
    print()

    return {
        "possible": True,
        "first_td_team": first_td["offense"],
        "first_td_period": first_td["period"],
        "first_td_clock": first_td["clock"],
        "first_td_description": play_text,
        "total_tds": len(td_plays),
        "data_structure": "Play text contains player names, requires parsing",
    }


def analyze_td_data_structure(plays_df):
    """
    Analyze the structure of touchdown data for production recommendations.

    Args:
        plays_df: DataFrame containing play-by-play data
    """
    print_section_header("Touchdown Data Structure Analysis")

    if not validate_dataframe_response(plays_df, "play-by-play data"):
        return

    # Filter for TD plays
    td_plays = plays_df[
        (plays_df["scoring"] == True)
        | (plays_df["play_type"].str.contains("touchdown", case=False, na=False))
        | (plays_df["play_text"].str.contains("touchdown", case=False, na=False))
    ]

    if td_plays.empty:
        print("⚠️  No touchdown data to analyze")
        print()
        return

    print("Available Fields for TD Tracking:")
    print()

    # Check what fields are available
    fields_analysis = {
        "id": "Unique play identifier",
        "offense": "Scoring team",
        "period": "Quarter/period number",
        "clock": "Game clock (time remaining)",
        "play_type": "Type of play (rush, pass, etc.)",
        "play_text": "Detailed play description",
        "scoring": "Boolean flag for scoring plays",
        "home_score": "Home team score after play",
        "away_score": "Away team score after play",
    }

    for field, description in fields_analysis.items():
        if field in td_plays.columns:
            non_null = td_plays[field].notna().sum()
            print(f"  ✓ {field}: {description}")
            print(f"    Available in {non_null}/{len(td_plays)} TD plays")
        else:
            print(f"  ✗ {field}: Not available")
        print()

    # Sample TD play text for parsing analysis
    print("Sample TD Play Texts (for player name extraction):")
    print()
    for idx, text in enumerate(td_plays["play_text"].head(3), 1):
        print(f"{idx}. {text}")
        print()


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """
    Main execution function for CFB sandbox exploration.
    """
    print("=" * 80)
    print("  COLLEGE FOOTBALL DATA SANDBOX")
    print("  Testing cfbd library capabilities")
    print("=" * 80)
    print()

    # Setup API client
    configuration = setup_api_client()
    print()

    # Fetch and display game data
    games_df = fetch_games(configuration, year=2024, week=1)

    if not games_df.empty:
        display_game_data(games_df)

        # Show data structure for reference
        print_data_structure_info(games_df, "CFB Games Data Structure")

    # Fetch and analyze play-by-play data for TD tracking
    plays_df = fetch_play_by_play_data(configuration, year=2024, week=1)

    if not plays_df.empty:
        # Attempt first TD identification
        first_td_result = identify_first_td_scorer(plays_df)

        # Analyze TD data structure
        analyze_td_data_structure(plays_df)

        # Show play-by-play data structure
        print_data_structure_info(plays_df, "Play-by-Play Data Structure")

    print("=" * 80)
    print("  CFB SANDBOX EXPLORATION COMPLETE")
    print("=" * 80)
    print()

    # Print comprehensive findings documentation
    print_research_findings_summary()


def print_research_findings_summary():
    """
    Print comprehensive research findings and recommendations.

    This documents the capabilities discovered through API exploration,
    even if live data testing was limited by authentication.
    """
    print("=" * 80)
    print("RESEARCH FINDINGS: CFB TOUCHDOWN TRACKING")
    print("=" * 80)
    print()

    print("1. LIBRARY SELECTION")
    print("-" * 80)
    print("Selected Library: cfbd (College Football Data API)")
    print()
    print("Rationale:")
    print("  ✓ Official Python client for comprehensive CFB data")
    print("  ✓ Well-maintained with active development")
    print("  ✓ Provides play-by-play data via PlaysApi")
    print("  ✓ Free API with registration at collegefootballdata.com")
    print("  ✓ Similar REST-based structure to other sports APIs")
    print()
    print("Available API Endpoints:")
    print("  • GamesApi: Game schedules, scores, team stats")
    print("  • PlaysApi: Play-by-play data, play stats, play types")
    print("  • PlayersApi: Player search and usage statistics")
    print("  • StatsApi: Team and player statistics")
    print()

    print("2. FIRST TOUCHDOWN SCORER IDENTIFICATION")
    print("-" * 80)
    print("Capability: POSSIBLE")
    print()
    print("Data Available:")
    print("  ✓ Play-by-play data via PlaysApi.get_plays()")
    print("  ✓ Chronological ordering (period + clock)")
    print("  ✓ Scoring flag on plays")
    print("  ✓ Play type classification")
    print("  ✓ Detailed play text descriptions")
    print("  ✓ Offense/defense team identification")
    print()
    print("Implementation Approach:")
    print("  1. Fetch play-by-play data for a game")
    print("  2. Filter for scoring plays or plays with 'touchdown' in type/text")
    print("  3. Sort by period (ascending) and clock (descending)")
    print("  4. First touchdown is the first play in sorted list")
    print("  5. Parse play_text field to extract player name")
    print()
    print("Data Structure:")
    print("  {")
    print("    'id': 'unique_play_id',")
    print("    'offense': 'scoring_team',")
    print("    'period': 1,  # Quarter number")
    print("    'clock': '12:34',  # Time remaining")
    print("    'play_type': 'Rush TD' or 'Pass TD',")
    print("    'play_text': 'Player Name 5 yd run (PAT good)',")
    print("    'scoring': True,")
    print("    'home_score': 7,")
    print("    'away_score': 0")
    print("  }")
    print()
    print("Player Name Extraction:")
    print("  • Player names embedded in play_text field")
    print("  • Requires text parsing (regex or NLP)")
    print("  • Example patterns:")
    print("    - 'John Smith 25 yd pass from QB Name (PAT good)'")
    print("    - 'Running Back 3 yd run (kick failed)'")
    print("  • Recommend validating against roster data")
    print()

    print("3. ANYTIME TOUCHDOWN SCORER TRACKING")
    print("-" * 80)
    print("Capability: POSSIBLE")
    print()
    print("Data Available:")
    print("  ✓ Same play-by-play data as first TD")
    print("  ✓ All scoring plays included in response")
    print("  ✓ Can filter for all touchdown plays in a game")
    print()
    print("Implementation Approach:")
    print("  1. Fetch play-by-play data for a game")
    print("  2. Filter for all scoring plays with 'touchdown'")
    print("  3. Parse each play_text to extract player names")
    print("  4. Build list of all touchdown scorers")
    print("  5. Track multiple TDs by same player")
    print()
    print("Comparison to First TD:")
    print("  • Same data source (PlaysApi)")
    print("  • Same parsing requirements")
    print("  • Difference: collect ALL TD plays instead of just first")
    print("  • Can track rushing TDs, receiving TDs, return TDs separately")
    print()

    print("4. DATA STRUCTURE COMPARISON")
    print("-" * 80)
    print("Similarities to Other Sports:")
    print("  ✓ Play-by-play data with chronological ordering")
    print("  ✓ Scoring flags on plays")
    print("  ✓ Team identification")
    print("  ✓ Timing information (period/clock)")
    print()
    print("CFB-Specific Considerations:")
    print("  • Larger number of teams (130+ FBS schools)")
    print("  • Conference-based organization")
    print("  • Player names in text descriptions (not structured fields)")
    print("  • May need roster data for player ID mapping")
    print()

    print("5. LIMITATIONS AND CONSIDERATIONS")
    print("-" * 80)
    print("Authentication:")
    print("  • Requires free API key from collegefootballdata.com")
    print("  • All endpoints require authentication")
    print()
    print("Rate Limits:")
    print("  • Unknown - need to test with live API key")
    print("  • Recommend implementing rate limiting in production")
    print()
    print("Data Availability:")
    print("  • Historical data available for past seasons")
    print("  • Real-time data availability during games: UNKNOWN")
    print("  • Recommend testing during live games")
    print()
    print("Player Name Parsing:")
    print("  • Not structured - requires text parsing")
    print("  • May have inconsistent formats")
    print("  • Recommend building robust parser with fallbacks")
    print("  • Consider maintaining player name database")
    print()

    print("6. PRODUCTION IMPLEMENTATION RECOMMENDATIONS")
    print("-" * 80)
    print()
    print("Architecture:")
    print("  1. Create CFBDataService class")
    print("  2. Implement play-by-play data fetching")
    print("  3. Build player name parser with regex patterns")
    print("  4. Cache play-by-play data to reduce API calls")
    print("  5. Implement error handling for parsing failures")
    print()
    print("Player Name Extraction:")
    print("  • Use regex patterns for common formats")
    print("  • Maintain roster database for validation")
    print("  • Implement fuzzy matching for name variations")
    print("  • Log unparseable plays for manual review")
    print()
    print("Testing Strategy:")
    print("  • Test with completed games first")
    print("  • Validate against known TD scorers")
    print("  • Test with various play types (rush, pass, return)")
    print("  • Monitor parsing success rate")
    print()
    print("Caching Strategy:")
    print("  • Cache play-by-play data per game")
    print("  • Invalidate cache when game status changes")
    print("  • Consider caching parsed player names")
    print()
    print("Alternative Approaches:")
    print("  • If parsing proves unreliable, consider:")
    print("    - Using player game stats as fallback")
    print("    - Combining multiple data sources")
    print("    - Manual data entry for critical games")
    print()
    print("If cfbd Library is Insufficient:")
    print("  • Alternative data sources:")
    print("    - ESPN API (unofficial)")
    print("    - NCAA.com web scraping")
    print("    - Sports data aggregators (SportsRadar, etc.)")
    print("  • Hybrid approach:")
    print("    - Use cfbd for game schedules")
    print("    - Supplement with web scraping for TD data")
    print("  • Manual data entry:")
    print("    - For high-priority games only")
    print("    - Build admin interface for data entry")
    print()

    print("7. NEXT STEPS")
    print("-" * 80)
    print("Immediate:")
    print("  1. Obtain valid API key from collegefootballdata.com")
    print("  2. Test with real game data from 2024 season")
    print("  3. Validate play-by-play data structure")
    print("  4. Test player name parsing with sample plays")
    print()
    print("Short-term:")
    print("  1. Implement player name parser")
    print("  2. Test with multiple games to validate consistency")
    print("  3. Measure parsing success rate")
    print("  4. Document edge cases and failures")
    print()
    print("Long-term:")
    print("  1. Integrate into production data ingestion pipeline")
    print("  2. Build unified scorer tracking across all sports")
    print("  3. Implement real-time data updates during games")
    print("  4. Add monitoring and alerting for data quality")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
