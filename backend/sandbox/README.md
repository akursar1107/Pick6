# Sandbox Folder

This folder is for experimental, scratch, or prototype Python scripts. Use it to:

- Test new libraries or APIs (e.g., sports data ingestion)
- Prototype features before integrating into the main codebase
- Run quick data analysis or transformation scripts

**Guidelines:**

- Scripts here are not production code and may be deleted or refactored at any time.
- Use clear filenames and comments to describe the purpose of each script.
- Do not import from sandbox scripts in production modules.
- If a script becomes useful, move/refactor it into the appropriate service or module.

Example usage: `python sandbox/test_ingest.py`

---

## Sports Data Sandbox - Research Findings

This section documents the findings from comprehensive exploration of sports data libraries for NFL, NBA, MLB, NHL, and College Football (CFB). The research focused on validating first scorer and anytime scorer tracking capabilities across all sports.

### Executive Summary

**Research Objective**: Validate the feasibility of tracking first scorer and anytime scorer for touchdown/goal/run/basket events across five major sports.

**Key Finding**: ✅ **All sports support both first scorer and anytime scorer tracking** through play-by-play data APIs.

| Sport | Library    | First Scorer       | Anytime Scorer     | Data Quality | Production Ready    |
| ----- | ---------- | ------------------ | ------------------ | ------------ | ------------------- |
| NFL   | nflreadpy  | ✅ Fully Supported | ✅ Fully Supported | Excellent    | ✅ Yes              |
| NBA   | nba_api    | ✅ Supported\*     | N/A\*\*            | Good         | ⚠️ Unstable API     |
| MLB   | pybaseball | ✅ Fully Supported | ✅ Fully Supported | Excellent    | ✅ Yes              |
| NHL   | nhl-api-py | ✅ Fully Supported | ✅ Fully Supported | Excellent    | ✅ Yes              |
| CFB   | cfbd       | ✅ Possible\*\*\*  | ✅ Possible\*\*\*  | Good         | ⚠️ Requires Parsing |

\* NBA first basket tracking is theoretically possible but the nba_api library is unofficial and unstable  
\*\* NBA "anytime scoring" is not a relevant prop betting market (all players score throughout the game)  
\*\*\* CFB requires text parsing to extract player names from play descriptions

---

### Sport-by-Sport Findings

#### 1. NFL (National Football League)

**Library**: `nflreadpy`  
**Status**: ✅ **Production Ready**

**First Touchdown Scorer**:

- ✅ **Fully Supported** via play-by-play data
- Data Source: `nflreadpy.load_pbp(seasons=[2024])`
- Identification Method:
  1. Filter to `touchdown == 1`
  2. Sort by `game_seconds_remaining` (descending = chronological)
  3. Group by `game_id` and take first record
  4. Extract `td_player_name` and `td_player_id`

**Anytime Touchdown Scorer**:

- ✅ **Fully Supported** via same play-by-play data
- Identification Method:
  1. Filter to `touchdown == 1`
  2. Group by `game_id` + `player_id`
  3. All touchdown scorers identified with timing information

**Key Data Fields**:

- `game_id`: Unique game identifier
- `game_seconds_remaining`: Time remaining (for chronological sorting)
- `td_player_name`: Name of touchdown scorer
- `td_player_id`: Unique player identifier
- `touchdown`: Binary flag (1 = touchdown play)
- `pass_touchdown`, `rush_touchdown`, `return_touchdown`: TD type flags
- `desc`: Text description of the play

**Data Quality**:

- ~50,000+ plays per season
- ~1,500 touchdown plays per season
- Complete player identification (name + ID)
- Reliable timing information
- Includes all TD types (passing, rushing, return, defensive)

**Production Recommendations**:

- Use `nflreadpy.load_pbp()` for play-by-play data
- Cache play-by-play data (large dataset)
- Update after each game completes
- Index on `game_id` and `player_id` for fast queries
- Single table can support both first TD and anytime TD queries

---

#### 2. NBA (National Basketball Association)

**Library**: `nba_api`  
**Status**: ⚠️ **Unstable - Use with Caution**

**First Basket Scorer**:

- ✅ **Theoretically Supported** via PlayByPlayV2 endpoint
- ⚠️ **Practical Challenges**: Unofficial API, rate limiting, unstable structure
- Data Source: `playbyplayv2.PlayByPlayV2(game_id)`
- Identification Method:
  1. Filter to `EVENTMSGTYPE == 1` (made shots)
  2. Exclude free throws (`EVENTMSGTYPE == 3`)
  3. Sort by `PERIOD` and `PCTIMESTRING`
  4. Take first record
  5. Extract `PLAYER1_ID` and `PLAYER1_NAME`

**Anytime Scoring**:

- N/A - Not a relevant prop betting market for basketball
- All players score throughout the game
- Alternative props: "Player X to score 10+ points", "Player X to score 20+ points"

**Key Data Fields**:

- `GAME_ID`: Unique game identifier
- `EVENTNUM`: Sequential event number
- `EVENTMSGTYPE`: Type of event (1 = Made Shot)
- `PERIOD`: Quarter/period number
- `PCTIMESTRING`: Time remaining in period (MM:SS)
- `PLAYER1_ID`: Primary player involved (scorer)
- `PLAYER1_NAME`: Name of primary player
- `SCORE`: Current score after the play

**Data Quality**:

- Detailed play-by-play available
- Complete player identification
- Timing information available
- ⚠️ API is unofficial and can change without notice
- ⚠️ Rate limiting may apply
- ⚠️ Requires per-game API calls (no bulk endpoint)

**Production Recommendations**:

- **Option 1**: Use nba_api with robust error handling and retry logic
- **Option 2**: Consider paid data providers (SportsRadar, ESPN API)
- **Option 3**: Start with manual tracking for MVP
- **Alternative**: Focus on player game totals (more stable API)
- Implement exponential backoff for rate limits
- Cache all successfully retrieved data
- Monitor for API structure changes

---

#### 3. MLB (Major League Baseball)

**Library**: `pybaseball`  
**Status**: ✅ **Production Ready**

**First Home Run Scorer**:

- ✅ **Fully Supported** via Statcast data
- Data Source: `pybaseball.statcast(start_dt, end_dt)`
- Identification Method:
  1. Filter to `events == 'home_run'`
  2. Group by `game_pk` (unique game identifier)
  3. Sort by `at_bat_number` (ascending = chronological)
  4. Take first record per game
  5. Extract `player_name` and `batter` (player ID)

**Anytime Home Run Scorer**:

- ✅ **Fully Supported** via same Statcast data
- Identification Method:
  1. Filter to `events == 'home_run'`
  2. Group by `game_pk` + `batter`
  3. All home run scorers identified with rich details

**Key Data Fields**:

- `game_pk`: MLB's official unique game identifier
- `at_bat_number`: Sequential at-bat number (for chronological sorting)
- `player_name`: Name of the batter
- `batter`: MLB player ID
- `events`: Event type ('home_run' for home runs)
- `inning`: Inning number
- `inning_topbot`: 'Top' or 'Bot' (which half of inning)
- `launch_speed`: Exit velocity in mph
- `launch_angle`: Launch angle in degrees
- `hit_distance_sc`: Distance in feet

**Data Quality**:

- ~700,000 pitches per season
- ~5,000-6,000 home runs per season
- Complete player identification (name + ID)
- Rich physics data (exit velocity, launch angle, distance)
- Reliable timing information via `at_bat_number`
- Available from 2015 onwards

**Production Recommendations**:

- Use `pybaseball.statcast()` for play-by-play home run data
- Fetch by date range to manage API rate limits
- Cache home run data separately from full Statcast data
- Update after each game completes
- Index on `game_pk` and `batter` for fast queries
- Single table supports both first HR and anytime HR queries
- Store rich HR details (exit velo, distance, angle) for analysis

---

#### 4. NHL (National Hockey League)

**Library**: `nhl-api-py` (nhlpy)  
**Status**: ✅ **Production Ready**

**First Goal Scorer**:

- ✅ **Fully Supported** via play-by-play data
- Data Source: `client.game_center.play_by_play(game_id)`
- Identification Method:
  1. Extract `plays` array from response
  2. Filter plays where `typeDescKey == 'goal'`
  3. First goal is `goal_events[0]` (chronologically ordered)
  4. Extract `details.scoringPlayerId` and `details.scoringPlayerName`

**Anytime Goal Scorer**:

- ✅ **Fully Supported** via same play-by-play data
- Identification Method:
  1. Filter plays where `typeDescKey == 'goal'`
  2. Iterate through ALL goal events
  3. Extract scorer from each goal's `details.scoringPlayerId`
  4. Track all unique scorers or all goal instances

**Key Data Fields**:

- `game_id`: Unique game identifier
- `periodDescriptor.number`: Period when goal was scored (1, 2, 3, OT)
- `timeInPeriod`: Time elapsed in period (MM:SS)
- `timeRemaining`: Time remaining in period
- `details.scoringPlayerId`: Unique player ID of goal scorer
- `details.scoringPlayerName`: Full name of goal scorer
- `details.eventOwnerTeamId`: Team ID of scoring team
- `details.shotType`: Type of shot (wrist, slap, backhand, etc.)
- `details.assist1PlayerId`, `details.assist2PlayerId`: Assist players

**Data Quality**:

- Complete play-by-play data available
- Goals are chronologically ordered in plays array
- Complete player identification (name + ID)
- Precise timing information
- Includes assist information
- Near real-time updates during games

**Production Recommendations**:

- Use `NHLClient.game_center.play_by_play(game_id)` for play-by-play data
- Poll endpoint during live games for real-time updates
- Cache completed game data
- Single API call provides data for both first and anytime goals
- Store all goals per game with `is_first_goal` boolean flag
- Index on `game_id` and `scorer_id` for fast queries
- Consider tracking hat tricks (3+ goals) as bonus prop

---

#### 5. CFB (College Football)

**Library**: `cfbd` (College Football Data API)  
**Status**: ⚠️ **Requires Text Parsing**

> **⚠️ DEPENDENCY CONFLICT WARNING**  
> The `cfbd` library requires pydantic v1, which conflicts with the main application's pydantic v2 dependency.
> Therefore, `cfbd` is NOT included in the main `requirements.txt` and should only be installed in isolated
> sandbox environments. For production use, consider alternative approaches or wait for pydantic v2 support.

**First Touchdown Scorer**:

- ✅ **Possible** via play-by-play data with text parsing
- Data Source: `PlaysApi.get_plays(year, week, season_type)`
- Identification Method:
  1. Filter for `scoring == True` or plays with 'touchdown' in type/text
  2. Sort by `period` (ascending) and `clock` (descending)
  3. First touchdown is first play in sorted list
  4. Parse `play_text` field to extract player name (requires regex/NLP)

**Anytime Touchdown Scorer**:

- ✅ **Possible** via same play-by-play data with text parsing
- Identification Method:
  1. Filter for all touchdown plays
  2. Parse each `play_text` to extract player names
  3. Build list of all touchdown scorers

**Key Data Fields**:

- `id`: Unique play identifier
- `offense`: Scoring team
- `period`: Quarter/period number
- `clock`: Time remaining (MM:SS format)
- `play_type`: Type of play (Rush TD, Pass TD, etc.)
- `play_text`: Detailed play description (contains player names)
- `scoring`: Boolean flag for scoring plays
- `home_score`, `away_score`: Scores after play

**Data Quality**:

- Play-by-play data available
- Chronological ordering via period + clock
- Scoring flags on plays
- ⚠️ Player names embedded in text descriptions (not structured fields)
- ⚠️ Requires text parsing to extract player names
- ⚠️ May have inconsistent formats

**Production Recommendations**:

- Requires free API key from collegefootballdata.com
- Build robust player name parser with regex patterns
- Maintain roster database for validation
- Implement fuzzy matching for name variations
- Log unparseable plays for manual review
- Test with completed games first
- Validate against known TD scorers
- Monitor parsing success rate
- **Alternative**: If parsing proves unreliable, consider manual data entry for high-priority games

---

### Common Data Patterns Across Sports

#### Structural Similarities

All five sports share these common patterns for scorer tracking:

1. **Play-by-Play Data Availability**

   - All sports provide detailed play-by-play data via their respective APIs
   - Data includes timing, player identification, and event types

2. **Chronological Ordering**

   - All sports provide mechanisms to sort plays chronologically:
     - NFL: `game_seconds_remaining` (descending)
     - NBA: `PERIOD` + `PCTIMESTRING`
     - MLB: `at_bat_number` (ascending)
     - NHL: Plays array is pre-ordered chronologically
     - CFB: `period` + `clock` (descending)

3. **Scoring Event Identification**

   - All sports have clear flags or filters for scoring events:
     - NFL: `touchdown == 1`
     - NBA: `EVENTMSGTYPE == 1` (made shots)
     - MLB: `events == 'home_run'`
     - NHL: `typeDescKey == 'goal'`
     - CFB: `scoring == True` or 'touchdown' in text

4. **Player Identification**

   - All sports provide player identification (name and/or ID):
     - NFL: `td_player_name`, `td_player_id`
     - NBA: `PLAYER1_NAME`, `PLAYER1_ID`
     - MLB: `player_name`, `batter` (player ID)
     - NHL: `scoringPlayerName`, `scoringPlayerId`
     - CFB: Player names in `play_text` (requires parsing)

5. **Unified Data Model**
   - All sports can use a similar database schema:
     ```
     game_scoring_events:
       - game_id (FK to games)
       - player_id (FK to players)
       - event_sequence (1 = first scorer, 2 = second, etc.)
       - event_type (touchdown, goal, home_run, basket)
       - period/inning
       - time_in_period
       - is_first_scorer (boolean flag)
     ```

#### Structural Differences

1. **Player Name Extraction**

   - **Structured** (NFL, NBA, MLB, NHL): Player names in dedicated fields
   - **Unstructured** (CFB): Player names embedded in text descriptions

2. **Game Identifiers**

   - **Official IDs** (MLB, NHL): `game_pk`, `game_id` from league APIs
   - **Constructed IDs** (NFL, NBA, CFB): May need to construct from date + teams

3. **Data Granularity**

   - **Pitch/Play Level** (MLB): ~700K pitches per season
   - **Play Level** (NFL, NHL, CFB): ~50K plays per season
   - **Event Level** (NBA): ~200K events per season

4. **Real-Time Availability**

   - **Near Real-Time** (NHL): Play-by-play updates during games
   - **Delayed** (NFL, MLB, NBA, CFB): Data available after game completion or with slight delay

5. **API Stability**
   - **Stable** (NFL, MLB, NHL, CFB): Official or well-maintained libraries
   - **Unstable** (NBA): Unofficial API, subject to change

---

### Cross-Sport Unified Architecture

Based on the research findings, here's a recommended unified architecture for scorer tracking across all sports:

#### 1. Common Data Model

```python
# Unified scoring event model
class ScoringEvent:
    game_id: str              # Unique game identifier
    sport: str                # 'nfl', 'nba', 'mlb', 'nhl', 'cfb'
    player_id: str            # Unique player identifier
    player_name: str          # Player full name
    team_id: str              # Team identifier
    event_type: str           # 'touchdown', 'goal', 'home_run', 'basket'
    event_sequence: int       # 1 = first scorer, 2 = second, etc.
    is_first_scorer: bool     # True if this is the first scoring event
    period: int               # Period/quarter/inning number
    time_in_period: str       # Time when event occurred
    game_time_remaining: int  # Seconds remaining (for sorting)
    event_details: dict       # Sport-specific details (shot type, distance, etc.)
    created_at: datetime      # When this record was created
```

#### 2. Unified Service Interface

```python
class ScorerTrackingService:
    """Unified interface for scorer tracking across all sports"""

    def get_first_scorer(self, game_id: str, sport: str) -> ScoringEvent:
        """Get the first scorer for a game"""

    def get_all_scorers(self, game_id: str, sport: str) -> List[ScoringEvent]:
        """Get all scorers for a game (anytime scorers)"""

    def did_player_score_first(self, game_id: str, player_id: str) -> bool:
        """Check if a specific player scored first"""

    def did_player_score(self, game_id: str, player_id: str) -> bool:
        """Check if a specific player scored at any point"""

    def get_player_scoring_count(self, game_id: str, player_id: str) -> int:
        """Get the number of times a player scored in a game"""
```

#### 3. Sport-Specific Adapters

Each sport implements a common adapter interface:

```python
class SportDataAdapter(ABC):
    """Abstract base class for sport-specific data adapters"""

    @abstractmethod
    def fetch_play_by_play(self, game_id: str) -> dict:
        """Fetch play-by-play data for a game"""

    @abstractmethod
    def extract_scoring_events(self, play_by_play_data: dict) -> List[ScoringEvent]:
        """Extract scoring events from play-by-play data"""

    @abstractmethod
    def identify_first_scorer(self, scoring_events: List[ScoringEvent]) -> ScoringEvent:
        """Identify the first scorer from a list of scoring events"""
```

Implementations:

- `NFLDataAdapter` (uses nflreadpy)
- `NBADataAdapter` (uses nba_api)
- `MLBDataAdapter` (uses pybaseball)
- `NHLDataAdapter` (uses nhl-api-py)
- `CFBDataAdapter` (uses cfbd)

#### 4. Caching Strategy

```python
# Cache play-by-play data per game
cache_key = f"pbp:{sport}:{game_id}"
ttl = 3600  # 1 hour for live games, indefinite for completed games

# Cache scoring events per game
cache_key = f"scoring:{sport}:{game_id}"
ttl = indefinite  # Scoring events don't change after game completion
```

#### 5. Database Schema

```sql
-- Games table (unified across sports)
CREATE TABLE games (
    id VARCHAR(255) PRIMARY KEY,
    sport VARCHAR(10) NOT NULL,
    home_team_id VARCHAR(255) NOT NULL,
    away_team_id VARCHAR(255) NOT NULL,
    game_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    home_score INT,
    away_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sport_date (sport, game_date),
    INDEX idx_status (status)
);

-- Scoring events table (unified across sports)
CREATE TABLE scoring_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    sport VARCHAR(10) NOT NULL,
    player_id VARCHAR(255) NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    team_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_sequence INT NOT NULL,
    is_first_scorer BOOLEAN NOT NULL,
    period INT NOT NULL,
    time_in_period VARCHAR(20),
    game_time_remaining INT,
    event_details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id),
    INDEX idx_game_player (game_id, player_id),
    INDEX idx_first_scorer (game_id, is_first_scorer),
    INDEX idx_sport_player (sport, player_id),
    UNIQUE KEY unique_game_sequence (game_id, event_sequence)
);
```

---

### Production Implementation Roadmap

#### Phase 1: Foundation (Week 1-2)

- [ ] Implement unified data models (`ScoringEvent`, `Game`, `Player`)
- [ ] Create abstract `SportDataAdapter` interface
- [ ] Set up database schema for unified scorer tracking
- [ ] Implement caching layer (Redis)

#### Phase 2: Sport-Specific Adapters (Week 3-4)

- [ ] Implement `NFLDataAdapter` (highest priority)
- [ ] Implement `MLBDataAdapter`
- [ ] Implement `NHLDataAdapter`
- [ ] Implement `NBADataAdapter` (with error handling for API instability)
- [ ] Implement `CFBDataAdapter` (with text parsing)

#### Phase 3: Service Layer (Week 5)

- [ ] Implement `ScorerTrackingService` with unified interface
- [ ] Add error handling and retry logic
- [ ] Implement data validation and quality checks
- [ ] Add logging and monitoring

#### Phase 4: Testing & Validation (Week 6)

- [ ] Test with historical game data for each sport
- [ ] Validate first scorer identification accuracy
- [ ] Validate anytime scorer tracking accuracy
- [ ] Performance testing and optimization

#### Phase 5: Production Deployment (Week 7-8)

- [ ] Deploy to staging environment
- [ ] Monitor data quality and API stability
- [ ] Implement alerting for data issues
- [ ] Deploy to production
- [ ] Set up automated data refresh jobs

---

### API Limitations and Workarounds

#### NFL (nflreadpy)

- **Limitation**: Play-by-play data is large (~50K plays per season)
- **Workaround**: Cache play-by-play data, filter to touchdown plays only for storage

#### NBA (nba_api)

- **Limitation**: Unofficial API, unstable, rate limiting
- **Workaround**: Implement robust error handling, exponential backoff, consider paid alternatives
- **Alternative**: Focus on player game totals instead of first basket

#### MLB (pybaseball)

- **Limitation**: Statcast data is pitch-level (~700K pitches per season)
- **Workaround**: Cache home run data separately, fetch by date range to manage rate limits

#### NHL (nhl-api-py)

- **Limitation**: Requires per-game API calls (no bulk endpoint)
- **Workaround**: Batch fetch for multiple games, cache completed game data indefinitely

#### CFB (cfbd)

- **Limitation**: Player names in text descriptions, requires parsing
- **Workaround**: Build robust regex parser, maintain roster database for validation
- **Alternative**: Manual data entry for high-priority games if parsing fails

---

### Performance and Caching Strategies

#### 1. Multi-Level Caching

```
Level 1: In-Memory Cache (Redis)
  - Cache play-by-play data per game (TTL: 1 hour for live, indefinite for completed)
  - Cache scoring events per game (TTL: indefinite)
  - Cache player lookups (TTL: 24 hours)

Level 2: Database Cache
  - Store all scoring events in database
  - Pre-compute first scorer flags
  - Index on game_id, player_id, is_first_scorer

Level 3: CDN Cache (for API responses)
  - Cache API responses for completed games
  - Invalidate on game status change
```

#### 2. Data Refresh Strategy

```
Live Games:
  - Poll play-by-play API every 30-60 seconds
  - Update scoring events as they occur
  - Invalidate cache on new scoring event

Completed Games:
  - Fetch play-by-play data once after game completion
  - Store scoring events permanently
  - Never invalidate cache for completed games

Scheduled Games:
  - Pre-fetch game schedules daily
  - Mark games as "pending" until they start
```

#### 3. API Rate Limiting

```
NFL (nflreadpy):
  - No known rate limits
  - Batch fetch by season

NBA (nba_api):
  - Unofficial API, rate limits unknown
  - Implement exponential backoff (1s, 2s, 4s, 8s)
  - Max 10 requests per minute (conservative)

MLB (pybaseball):
  - No strict rate limits
  - Fetch by date range (1-7 days at a time)

NHL (nhl-api-py):
  - No known rate limits
  - Batch fetch for multiple games

CFB (cfbd):
  - Free tier: 200 requests per hour
  - Batch fetch by week
```

---

### Alternative Data Sources

If primary libraries prove insufficient, consider these alternatives:

#### Commercial Data Providers

- **SportsRadar**: Comprehensive sports data, real-time feeds, expensive
- **Sportradar**: Similar to SportsRadar, enterprise-level
- **ESPN API**: Unofficial but widely used, free but unstable
- **The Odds API**: Betting-focused data, includes prop markets

#### Web Scraping (Last Resort)

- **ESPN.com**: Game data, play-by-play, player stats
- **Official League Sites**: NFL.com, NBA.com, MLB.com, NHL.com
- **Caution**: Against TOS, fragile, requires maintenance

#### Manual Data Entry

- **Use Case**: High-priority games, MVP phase, data validation
- **Implementation**: Build admin interface for manual entry
- **Workflow**: Watch games live, enter first scorer data manually

---

### Next Steps for Production Integration

1. **Immediate (This Week)**

   - Review and approve this research documentation
   - Prioritize sports for implementation (recommend: NFL → MLB → NHL → CFB → NBA)
   - Set up development environment with all required libraries
   - Create database schema for unified scorer tracking

2. **Short-Term (Next 2 Weeks)**

   - Implement unified data models and service interface
   - Build NFL adapter (highest priority for First6)
   - Test with historical NFL game data
   - Validate first TD and anytime TD tracking accuracy

3. **Medium-Term (Next Month)**

   - Implement adapters for MLB, NHL, CFB
   - Build robust error handling and retry logic
   - Implement caching layer
   - Set up monitoring and alerting

4. **Long-Term (Next Quarter)**
   - Implement NBA adapter (if first basket tracking is desired)
   - Optimize performance and caching
   - Add support for additional prop types (hat tricks, multi-goal games, etc.)
   - Build admin interface for manual data entry and validation

---

### Conclusion

The research validates that **first scorer and anytime scorer tracking is feasible across all five sports** using their respective Python libraries. The data quality is excellent for NFL, MLB, and NHL, good for CFB (with text parsing), and challenging but possible for NBA (due to API instability).

A unified architecture can be built to support scorer tracking across all sports, with sport-specific adapters handling the differences in data structure and API access patterns. The recommended approach is to start with NFL (highest priority for First6), then expand to other sports incrementally.

**Key Takeaway**: The technical foundation for First6's scorer tracking features is solid. All required data is available through free or low-cost APIs. The main implementation challenges are:

1. Building robust error handling for unstable APIs (NBA)
2. Implementing text parsing for unstructured data (CFB)
3. Managing API rate limits and caching strategies
4. Ensuring data quality and accuracy through validation

With proper implementation, First6 can offer comprehensive first scorer and anytime scorer tracking across all major sports.
