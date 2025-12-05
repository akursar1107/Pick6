# Design Document: Sports Data Sandbox Implementation

## Overview

This design outlines the implementation of sandbox scripts for testing and prototyping sports data ingestion across five major sports: NFL, NBA, MLB, NHL, and College Football (CFB). Each sandbox script will demonstrate the capabilities of its respective data library, explore data structures, and validate API functionality before production integration.

The sandbox scripts serve as a research and development tool to:

- **Validate first scorer identification capabilities** (first TD, first basket, first run, first goal)
- **Validate anytime scorer tracking capabilities** (anytime TD, anytime goal, anytime run)
- Understand each library's API patterns and play-by-play data access
- Identify common data structures across sports for scorer tracking
- Test error handling and edge cases
- Document findings for future production implementation
- Validate that libraries meet First6's specific scorer tracking requirements

**Note**: NBA is included for first basket tracking only, as "anytime scoring" is not a relevant prop betting market for basketball.

### Critical Research Questions

The sandbox scripts must answer these key questions for each sport:

1. **Can we identify the first scorer?** Does the API provide play-by-play data with timing information to determine who scored first?
2. **Can we track all scorers?** Does the API provide complete scoring data for all players who scored in a game?
3. **Is the data real-time or delayed?** What is the latency between actual game events and API data availability?
4. **What is the data format?** How is scoring data structured, and can it be normalized across sports?
5. **Are there API limitations?** Rate limits, authentication requirements, or data availability constraints?

## Architecture

### Component Structure

```
backend/sandbox/
├── README.md                    # Existing sandbox documentation
├── test_ingest.py              # Existing NFL basic test (to be enhanced)
├── nfl_sandbox.py              # Comprehensive NFL data exploration
├── nba_sandbox.py              # NBA data exploration
├── mlb_sandbox.py              # MLB data exploration
├── nhl_sandbox.py              # NHL data exploration
├── cfb_sandbox.py              # CFB data exploration
└── common_utils.py             # Shared utilities for all sandbox scripts
```

### Design Principles

1. **Independence**: Each script runs standalone without dependencies on production code
2. **Clarity**: Extensive comments and documentation for learning purposes
3. **Error Resilience**: Graceful handling of missing dependencies and API failures
4. **Consistency**: Similar structure across all scripts for easy comparison
5. **Exploration**: Focus on discovering capabilities rather than production-ready code

## Components and Interfaces

### Common Utilities Module (`common_utils.py`)

Shared functionality across all sandbox scripts:

```python
def check_library_installed(library_name: str, install_command: str) -> bool:
    """Check if a library is installed and provide installation instructions"""

def display_dataframe_sample(df, title: str, max_rows: int = 5):
    """Display a formatted sample of a pandas DataFrame"""

def handle_api_error(error: Exception, context: str):
    """Standardized error handling and display"""

def print_section_header(title: str):
    """Print a formatted section header for output organization"""
```

### NFL Sandbox Script (`nfl_sandbox.py`)

**Library**: nflreadpy

**Key Functions**:

- Fetch current season games
- Retrieve player touchdown statistics (rushing, receiving, passing)
- **Identify first touchdown scorer per game**
- **Track all touchdown scorers (anytime TD)**
- Explore play-by-play data for touchdown timing

**Data Points of Interest**:

- Game schedule and results
- Player touchdown data with timing information
- **First touchdown scorer identification** (critical for First6)
- **Anytime touchdown scorer tracking** (critical for First6)
- Play sequence and game clock data

### NBA Sandbox Script (`nba_sandbox.py`)

**Library**: nba_api

**Key Functions**:

- Fetch current season games using `leaguegamefinder`
- Retrieve player game logs
- **Identify first basket scorer per game**
- Explore play-by-play data for scoring timing

**Data Points of Interest**:

- Game schedule and scores
- **First basket scorer identification** (critical for First6)
- Player scoring statistics
- Play-by-play timing data

### MLB Sandbox Script (`mlb_sandbox.py`)

**Library**: pybaseball

**Key Functions**:

- Fetch game schedule using `schedule_and_record`
- Retrieve player batting and scoring statistics
- **Identify first run scorer per game**
- **Track all run scorers (anytime scorer)**
- Explore play-by-play data for scoring timing

**Data Points of Interest**:

- Game schedule and results
- **First run scorer identification** (critical for First6)
- **Anytime run scorer tracking** (critical for First6)
- Player batting statistics (hits, home runs, RBIs)
- Play-by-play scoring data

### NHL Sandbox Script (`nhl_sandbox.py`)

**Library**: nhl-api-py

**Key Functions**:

- Fetch current season games
- Retrieve player goal statistics
- **Identify first goal scorer per game**
- **Track all goal scorers (anytime goal)**
- Explore play-by-play data for goal timing

**Data Points of Interest**:

- Game schedule and scores
- **First goal scorer identification** (critical for First6)
- **Anytime goal scorer tracking** (critical for First6)
- Player goals and assists
- Game events and play-by-play timing

### CFB Sandbox Script (`cfb_sandbox.py`)

**Library**: TBD (Research required - likely cfbd or collegefootballdata)

**Approach**:

- Investigate available Python libraries (cfbd, collegefootballdata)
- Test API access and authentication requirements
- **Validate first touchdown scorer data availability**
- **Validate anytime touchdown scorer data availability**
- Document data availability and limitations
- Provide recommendations for production implementation

**Data Points of Interest**:

- Game schedule and scores
- **First touchdown scorer identification** (critical for First6)
- **Anytime touchdown scorer tracking** (critical for First6)
- Player touchdown statistics
- Play-by-play data availability

## Data Models

### Common Data Structure Pattern

Each sport's data will be explored for these common entities:

**Game Entity**:

```python
{
    "game_id": str,           # Unique identifier
    "home_team": str,         # Home team name/abbreviation
    "away_team": str,         # Away team name/abbreviation
    "game_date": datetime,    # Game date and time
    "home_score": int,        # Home team score (if final)
    "away_score": int,        # Away team score (if final)
    "status": str,            # Game status (scheduled, in_progress, final)
    "season": int,            # Season year
    "week": int               # Week number (if applicable)
}
```

**Player Entity**:

```python
{
    "player_id": str,         # Unique identifier
    "name": str,              # Player full name
    "team": str,              # Current team
    "position": str,          # Playing position
    "statistics": dict        # Sport-specific stats
}
```

**Team Entity**:

```python
{
    "team_id": str,           # Unique identifier
    "name": str,              # Full team name
    "abbreviation": str,      # Team abbreviation
    "conference": str,        # Conference/division
    "location": str           # City/location
}
```

### Sport-Specific Scorer Tracking Data

**NFL (Touchdown Scoring)**:

- `player_id`: Player identifier
- `player_name`: Player name
- `touchdown_type`: Type of TD (rushing, receiving)
- `game_time`: Time of touchdown (quarter, clock)
- `play_sequence`: Play number in game
- **`is_first_td`: Boolean flag for first TD of game** (CRITICAL)
- **`is_anytime_td`: Boolean flag for any TD** (CRITICAL)

**NBA (First Basket Only)**:

- `player_id`: Player identifier
- `player_name`: Player name
- `basket_type`: Type of basket (2pt, 3pt, FT)
- `game_time`: Time of basket (quarter, clock)
- `play_sequence`: Play number in game
- **`is_first_basket`: Boolean flag for first basket of game** (CRITICAL)

**MLB (Run Scoring)**:

- `player_id`: Player identifier
- `player_name`: Player name
- `inning`: Inning when run scored
- `play_sequence`: Play number in game
- **`is_first_run`: Boolean flag for first run of game** (CRITICAL)
- **`is_anytime_run`: Boolean flag for any run** (CRITICAL)

**NHL (Goal Scoring)**:

- `player_id`: Player identifier
- `player_name`: Player name
- `goal_type`: Type of goal (even strength, power play, short-handed)
- `period`: Period when goal scored
- `game_time`: Time of goal (period, clock)
- `play_sequence`: Play number in game
- **`is_first_goal`: Boolean flag for first goal of game** (CRITICAL)
- **`is_anytime_goal`: Boolean flag for any goal** (CRITICAL)

**CFB (Touchdown Scoring)**:

- Same structure as NFL
- May have additional college-specific fields

## Error Handling

### Dependency Management

Each script will implement a try-except block for imports:

```python
try:
    from library_name import required_functions
except ImportError:
    print(f"Error: library_name is not installed")
    print(f"Install with: pip install library_name")
    exit(1)
```

### API Error Handling

All API calls will be wrapped in try-except blocks:

```python
try:
    data = fetch_function()
    # Process data
except Exception as e:
    print(f"Error fetching data: {type(e).__name__}")
    print(f"Details: {str(e)}")
    print("This may be due to API rate limits, network issues, or invalid parameters")
```

### Data Validation

Scripts will check for empty or invalid responses:

```python
if data is None or (hasattr(data, 'empty') and data.empty):
    print("Warning: No data returned from API")
    print("This may indicate no games scheduled or invalid query parameters")
```

## Testing Strategy

### Manual Testing Approach

Since these are sandbox/prototype scripts, testing will be manual and exploratory:

1. **Dependency Testing**: Run each script without libraries installed to verify error messages
2. **Data Retrieval Testing**: Execute scripts to verify successful data fetching
3. **Output Validation**: Review displayed data for completeness and accuracy
4. **Error Scenario Testing**: Test with invalid parameters to verify error handling
5. **Cross-Sport Comparison**: Compare outputs to identify common patterns

### Validation Checklist

For each sandbox script:

- [ ] Script runs without errors when dependencies are installed
- [ ] Clear error message when dependencies are missing
- [ ] Successfully retrieves game data
- [ ] Successfully retrieves player statistics
- [ ] Displays data in readable format
- [ ] Handles API errors gracefully
- [ ] Includes helpful comments and documentation
- [ ] Demonstrates multiple API endpoints
- [ ] Documents data structure findings
- [ ] Notes any limitations or special considerations

### Property-Based Testing

Since these are exploratory sandbox scripts, formal property-based testing is not required. However, we can document expected properties for future production implementation:

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

Since these are exploratory sandbox scripts focused on research and prototyping rather than production code, the correctness properties focus on consistent behavior patterns, error handling, and documentation quality across all scripts.

### Property 1: Game data display completeness

_For any_ game data retrieved from any sports API (NFL, NBA, MLB, NHL, CFB), when displayed to the user, the output SHALL include the key identifying fields: game_id, home_team, away_team, game_date, and score information.

**Validates: Requirements 1.2, 2.2, 3.2, 4.2, 5.2**

### Property 2: Player statistics display completeness

_For any_ player statistics retrieved from any sports API, when displayed to the user, the output SHALL include sport-appropriate scoring statistics (touchdowns for NFL, points for NBA, batting stats for MLB, goals/assists for NHL).

**Validates: Requirements 1.4, 2.4, 3.4, 4.4**

### Property 3: API error handling

_For any_ API call that raises an exception, the script SHALL catch the exception, display an informative error message including the error type and context, and continue or exit gracefully without exposing raw stack traces to the user.

**Validates: Requirements 1.5, 2.5, 3.5, 4.5, 5.4**

### Property 4: Import error handling

_For any_ required library that is not installed, the script SHALL catch the ImportError, display the library name and installation command, and exit gracefully with exit code 1 without displaying a stack trace.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 5: Script documentation completeness

_For any_ sandbox script file, the code SHALL include: a module-level docstring explaining purpose and usage, inline comments for API calls explaining parameters, comments describing data structures, and section headers for code organization.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

### Property 6: Output formatting consistency

_For any_ two sandbox scripts, the output formatting pattern SHALL be consistent, using the same approach for section headers, data display, and error messages to enable easy cross-sport comparison.

**Validates: Requirements 8.3**

### Examples (Not Universal Properties)

The following are specific test cases that validate particular API integrations work correctly:

- **Example 1**: NFL sandbox script successfully retrieves current season game data (Requirement 1.1)
- **Example 2**: NFL sandbox script successfully retrieves player statistics (Requirement 1.3)
- **Example 3**: NBA sandbox script successfully retrieves current season game data (Requirement 2.1)
- **Example 4**: NBA sandbox script successfully retrieves player statistics (Requirement 2.3)
- **Example 5**: MLB sandbox script successfully retrieves current season game data (Requirement 3.1)
- **Example 6**: MLB sandbox script successfully retrieves player statistics (Requirement 3.3)
- **Example 7**: NHL sandbox script successfully retrieves current season game data (Requirement 4.1)
- **Example 8**: NHL sandbox script successfully retrieves player statistics (Requirement 4.3)
- **Example 9**: CFB sandbox script successfully retrieves game data (Requirement 5.1)
- **Example 10**: Scripts execute normally when all dependencies are installed (Requirement 7.4)

These examples will be validated through manual execution and observation rather than automated testing.

## Implementation Notes

### Library-Specific Considerations

**nflreadpy**:

- Returns pandas DataFrames
- Provides multiple functions: `games()`, `players()`, `rosters()`
- Season parameter is required for most functions
- Data is cached locally to reduce API calls
- **KEY RESEARCH**: Determine if play-by-play data includes touchdown timing and sequence
- **KEY RESEARCH**: Validate ability to identify first TD scorer vs anytime TD scorers

**nba_api**:

- Object-oriented API with multiple endpoint classes
- `LeagueGameFinder` for game queries
- `PlayerGameLog` for player statistics
- `PlayByPlayV2` for detailed play-by-play data
- Requires careful parameter formatting
- Rate limiting may apply
- **KEY RESEARCH**: Determine if play-by-play data can identify first basket scorer
- **KEY RESEARCH**: Validate real-time data availability during games

**pybaseball**:

- Returns pandas DataFrames
- `schedule_and_record()` for game schedules
- `batting_stats()` for player statistics
- `statcast()` for detailed play-by-play data
- Date range queries use start_date and end_date
- Data sourced from multiple providers (Baseball Reference, FanGraphs)
- **KEY RESEARCH**: Determine if play-by-play data includes run scoring sequence
- **KEY RESEARCH**: Validate ability to identify first run scorer vs anytime run scorers

**nhl-api-py**:

- RESTful API wrapper
- `Schedule` class for game data
- `Players` class for player information
- Game feed includes play-by-play events
- JSON response format
- Well-documented endpoint structure
- **KEY RESEARCH**: Determine if play-by-play data includes goal timing and sequence
- **KEY RESEARCH**: Validate ability to identify first goal scorer vs anytime goal scorers

**CFB**:

- Research needed to identify best library
- Potential options: `cfbd` (College Football Data API), `collegefootballdata`
- May require API key registration
- Data availability may be limited compared to professional sports
- **KEY RESEARCH**: Determine if any library provides play-by-play touchdown data
- **KEY RESEARCH**: Assess feasibility of first TD / anytime TD tracking for college football

### Development Workflow

1. Start with NFL sandbox (already has basic implementation)
2. Implement common utilities module
3. Enhance NFL sandbox with comprehensive examples
4. Implement NBA, MLB, NHL sandboxes following NFL pattern
5. Research and implement CFB sandbox
6. Document findings and recommendations for production integration

### Success Criteria

The sandbox implementation will be considered successful when:

- **First scorer identification is validated for all sports** (or documented as unavailable)
- **Anytime scorer tracking is validated for NFL, MLB, NHL, CFB** (or documented as unavailable)
- All five sport sandbox scripts execute without errors
- Each script demonstrates play-by-play data access (if available)
- Scorer tracking data structures are clearly documented
- Common patterns across sports for scorer tracking are identified
- Limitations and special considerations for scorer data are documented
- Error handling is consistent and informative
- Code is well-commented and educational
- Clear recommendations are provided for production implementation

### Future Production Integration

Insights from sandbox exploration will inform:

- **Scorer tracking architecture design** (first scorer vs anytime scorer)
- **Play-by-play data ingestion strategies** for real-time scorer identification
- Unified data ingestion architecture across sports
- Common interface definitions for scorer tracking across sports
- Error handling and retry strategies for live game data
- Data transformation and normalization for scorer data
- Caching strategies for game and scorer data
- API rate limiting and quota management
- Real-time vs delayed data handling approaches
- Fallback strategies when play-by-play data is unavailable
