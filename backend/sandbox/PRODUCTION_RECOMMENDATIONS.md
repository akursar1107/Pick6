# Production Implementation Recommendations

## Sports Data Scorer Tracking - Production Integration Guide

This document provides comprehensive recommendations for integrating the sports data scorer tracking capabilities researched in the sandbox scripts into the First6 production codebase.

---

## Table of Contents

1. [Unified Scorer Tracking Architecture](#unified-scorer-tracking-architecture)
2. [API Limitations and Workarounds](#api-limitations-and-workarounds)
3. [Caching and Performance Strategies](#caching-and-performance-strategies)
4. [Data Quality and Validation](#data-quality-and-validation)
5. [Error Handling and Resilience](#error-handling-and-resilience)
6. [Alternative Data Sources](#alternative-data-sources)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Monitoring and Alerting](#monitoring-and-alerting)

---

## 1. Unified Scorer Tracking Architecture

### 1.1 Core Design Principles

**Principle 1: Sport-Agnostic Service Layer**

- Create a unified `ScorerTrackingService` that works across all sports
- Hide sport-specific implementation details behind adapters
- Provide consistent API for querying first scorer and anytime scorer data

**Principle 2: Adapter Pattern for Sport-Specific Logic**

- Each sport implements a common `SportDataAdapter` interface
- Adapters handle API calls, data parsing, and event extraction
- Allows adding new sports without modifying core service logic

**Principle 3: Single Source of Truth**

- Store all scoring events in a unified database table
- Use `is_first_scorer` flag to identify first scorers
- Support both first scorer and anytime scorer queries from same dataset

**Principle 4: Caching at Multiple Levels**

- Cache play-by-play data (expensive to fetch)
- Cache extracted scoring events (computed once)
- Cache query results (frequently accessed)

### 1.2 Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  /api/v1/games/{game_id}/first-scorer                       │
│  /api/v1/games/{game_id}/scorers                            │
│  /api/v1/players/{player_id}/scoring-history                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  ScorerTrackingService                       │
│  - get_first_scorer(game_id, sport)                         │
│  - get_all_scorers(game_id, sport)                          │
│  - did_player_score_first(game_id, player_id)               │
│  - did_player_score(game_id, player_id)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Sport Data Adapters                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   NFL    │  │   MLB    │  │   NHL    │  │   CFB    │   │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                             │
│  nflreadpy  │  pybaseball  │  nhl-api-py  │  cfbd          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Caching Layer (Redis)                     │
│  - Play-by-play data cache                                   │
│  - Scoring events cache                                      │
│  - Query results cache                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database (PostgreSQL)                       │
│  - games table                                               │
│  - scoring_events table                                      │
│  - players table                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Data Models

**Game Model**

```python
class Game(Base):
    __tablename__ = "games"

    id = Column(String(255), primary_key=True)
    sport = Column(String(10), nullable=False)  # 'nfl', 'mlb', 'nhl', 'cfb'
    home_team_id = Column(String(255), nullable=False)
    away_team_id = Column(String(255), nullable=False)
    game_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)  # 'scheduled', 'live', 'completed'
    home_score = Column(Integer)
    away_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scoring_events = relationship("ScoringEvent", back_populates="game")
```

**ScoringEvent Model**

```python
class ScoringEvent(Base):
    __tablename__ = "scoring_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    game_id = Column(String(255), ForeignKey("games.id"), nullable=False)
    sport = Column(String(10), nullable=False)
    player_id = Column(String(255), nullable=False)
    player_name = Column(String(255), nullable=False)
    team_id = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'touchdown', 'goal', 'home_run'
    event_sequence = Column(Integer, nullable=False)  # 1 = first, 2 = second, etc.
    is_first_scorer = Column(Boolean, nullable=False, default=False)
    period = Column(Integer, nullable=False)
    time_in_period = Column(String(20))
    game_time_remaining = Column(Integer)  # Seconds remaining (for sorting)
    event_details = Column(JSON)  # Sport-specific details
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    game = relationship("Game", back_populates="scoring_events")

    # Indexes
    __table_args__ = (
        Index('idx_game_player', 'game_id', 'player_id'),
        Index('idx_first_scorer', 'game_id', 'is_first_scorer'),
        Index('idx_sport_player', 'sport', 'player_id'),
        UniqueConstraint('game_id', 'event_sequence', name='unique_game_sequence'),
    )
```

### 1.4 Service Interface

**ScorerTrackingService**

```python
class ScorerTrackingService:
    """Unified service for scorer tracking across all sports"""

    def __init__(self, db_session, cache_client, adapters: Dict[str, SportDataAdapter]):
        self.db = db_session
        self.cache = cache_client
        self.adapters = adapters

    async def get_first_scorer(self, game_id: str, sport: str) -> Optional[ScoringEvent]:
        """Get the first scorer for a game"""
        # Check cache first
        cache_key = f"first_scorer:{sport}:{game_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return ScoringEvent(**cached)

        # Query database
        event = await self.db.query(ScoringEvent).filter(
            ScoringEvent.game_id == game_id,
            ScoringEvent.is_first_scorer == True
        ).first()

        if event:
            await self.cache.set(cache_key, event.dict(), ttl=None)  # Cache indefinitely
            return event

        # Fetch from API if not in database
        await self.refresh_scoring_events(game_id, sport)
        return await self.get_first_scorer(game_id, sport)

    async def get_all_scorers(self, game_id: str, sport: str) -> List[ScoringEvent]:
        """Get all scorers for a game (anytime scorers)"""
        cache_key = f"all_scorers:{sport}:{game_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [ScoringEvent(**e) for e in cached]

        events = await self.db.query(ScoringEvent).filter(
            ScoringEvent.game_id == game_id
        ).order_by(ScoringEvent.event_sequence).all()

        if events:
            await self.cache.set(cache_key, [e.dict() for e in events], ttl=None)
            return events

        await self.refresh_scoring_events(game_id, sport)
        return await self.get_all_scorers(game_id, sport)

    async def did_player_score_first(self, game_id: str, player_id: str) -> bool:
        """Check if a specific player scored first"""
        first_scorer = await self.get_first_scorer(game_id, self._get_sport_for_game(game_id))
        return first_scorer and first_scorer.player_id == player_id

    async def did_player_score(self, game_id: str, player_id: str) -> bool:
        """Check if a specific player scored at any point"""
        event = await self.db.query(ScoringEvent).filter(
            ScoringEvent.game_id == game_id,
            ScoringEvent.player_id == player_id
        ).first()
        return event is not None

    async def refresh_scoring_events(self, game_id: str, sport: str):
        """Fetch and store scoring events from external API"""
        adapter = self.adapters.get(sport)
        if not adapter:
            raise ValueError(f"No adapter found for sport: {sport}")

        # Fetch play-by-play data
        pbp_data = await adapter.fetch_play_by_play(game_id)

        # Extract scoring events
        events = adapter.extract_scoring_events(pbp_data)

        # Store in database
        for event in events:
            await self.db.merge(event)
        await self.db.commit()

        # Invalidate cache
        await self.cache.delete(f"first_scorer:{sport}:{game_id}")
        await self.cache.delete(f"all_scorers:{sport}:{game_id}")
```

### 1.5 Sport Data Adapter Interface

**Abstract Base Class**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SportDataAdapter(ABC):
    """Abstract base class for sport-specific data adapters"""

    @abstractmethod
    async def fetch_play_by_play(self, game_id: str) -> Dict[str, Any]:
        """
        Fetch play-by-play data for a game from external API.

        Args:
            game_id: Unique game identifier

        Returns:
            Raw play-by-play data from API
        """
        pass

    @abstractmethod
    def extract_scoring_events(self, pbp_data: Dict[str, Any]) -> List[ScoringEvent]:
        """
        Extract scoring events from play-by-play data.

        Args:
            pbp_data: Raw play-by-play data from API

        Returns:
            List of ScoringEvent objects, ordered chronologically
        """
        pass

    @abstractmethod
    def identify_first_scorer(self, scoring_events: List[ScoringEvent]) -> Optional[ScoringEvent]:
        """
        Identify the first scorer from a list of scoring events.

        Args:
            scoring_events: List of scoring events

        Returns:
            First scoring event, or None if no scoring events
        """
        pass
```

**NFL Adapter Implementation**

```python
class NFLDataAdapter(SportDataAdapter):
    """Adapter for NFL data using nflreadpy"""

    def __init__(self):
        import nflreadpy as nfl
        self.nfl = nfl

    async def fetch_play_by_play(self, game_id: str) -> Dict[str, Any]:
        """Fetch NFL play-by-play data"""
        # Extract season from game_id (format: 2024_01_NYJ_BUF)
        season = int(game_id.split('_')[0])

        # Fetch play-by-play data for the season
        pbp_df = self.nfl.load_pbp(seasons=[season])

        # Filter to specific game
        game_pbp = pbp_df[pbp_df['game_id'] == game_id]

        return game_pbp.to_dict('records')

    def extract_scoring_events(self, pbp_data: List[Dict]) -> List[ScoringEvent]:
        """Extract touchdown events from NFL play-by-play data"""
        # Filter to touchdown plays
        td_plays = [play for play in pbp_data if play.get('touchdown') == 1]

        # Sort by game_seconds_remaining (descending = chronological)
        td_plays_sorted = sorted(td_plays, key=lambda x: x.get('game_seconds_remaining', 0), reverse=True)

        # Convert to ScoringEvent objects
        events = []
        for idx, play in enumerate(td_plays_sorted, 1):
            event = ScoringEvent(
                game_id=play['game_id'],
                sport='nfl',
                player_id=play.get('td_player_id', ''),
                player_name=play.get('td_player_name', ''),
                team_id=play.get('td_team', ''),
                event_type='touchdown',
                event_sequence=idx,
                is_first_scorer=(idx == 1),
                period=play.get('quarter', 0),
                time_in_period=play.get('time', ''),
                game_time_remaining=play.get('game_seconds_remaining', 0),
                event_details={
                    'td_type': 'pass' if play.get('pass_touchdown') == 1 else 'rush' if play.get('rush_touchdown') == 1 else 'other',
                    'description': play.get('desc', ''),
                }
            )
            events.append(event)

        return events

    def identify_first_scorer(self, scoring_events: List[ScoringEvent]) -> Optional[ScoringEvent]:
        """Identify first touchdown scorer"""
        if not scoring_events:
            return None
        return scoring_events[0]  # Already sorted chronologically
```

---

## 2. API Limitations and Workarounds

### 2.1 NFL (nflreadpy)

**Limitations:**

- Play-by-play data is large (~50,000 plays per season)
- No real-time API during games (data available after game completion)
- Season-level data fetching (cannot fetch single game)

**Workarounds:**

```python
# Cache play-by-play data at season level
cache_key = f"nfl:pbp:{season}"
ttl = 86400  # 24 hours

# Filter to touchdown plays only for storage
td_plays = pbp_df[pbp_df['touchdown'] == 1]

# Store only touchdown plays in database (reduces storage by 97%)
```

**Recommended Approach:**

1. Fetch play-by-play data once per day for current season
2. Cache in Redis with 24-hour TTL
3. Store only touchdown plays in database
4. Update after each game completes (check game status)

### 2.2 NBA (nba_api)

**Limitations:**

- Unofficial API, can change without notice
- Rate limiting (undocumented)
- Requires per-game API calls
- API structure instability

**Workarounds:**

```python
# Implement exponential backoff
async def fetch_with_retry(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            await asyncio.sleep(wait_time)

# Rate limiting
rate_limiter = AsyncLimiter(max_rate=10, time_period=60)  # 10 requests per minute

# Fallback to player game totals
if play_by_play_fails:
    use_player_game_logs_instead()
```

**Recommended Approach:**

1. **For MVP**: Skip NBA first basket tracking, focus on player game totals
2. **For Production**: Consider paid data provider (SportsRadar, ESPN API)
3. **If using nba_api**: Implement robust error handling, cache aggressively
4. **Alternative Props**: "Player X to score 10+ points", "Player X to score 20+ points"

### 2.3 MLB (pybaseball)

**Limitations:**

- Statcast data is pitch-level (~700,000 pitches per season)
- API rate limiting (undocumented)
- Date range queries only (no single game fetch)

**Workarounds:**

```python
# Fetch by date range (1-7 days at a time)
start_date = "2024-09-20"
end_date = "2024-09-22"
statcast_df = statcast(start_dt=start_date, end_dt=end_date)

# Filter to home runs only
hr_plays = statcast_df[statcast_df['events'] == 'home_run']

# Cache home run data separately
cache_key = f"mlb:hr:{start_date}:{end_date}"
ttl = None  # Cache indefinitely for past dates
```

**Recommended Approach:**

1. Fetch Statcast data by date range (weekly batches)
2. Filter to home run events only
3. Store home runs in database with rich details (exit velo, distance, angle)
4. Update daily for recent games
5. Cache completed game data indefinitely

### 2.4 NHL (nhl-api-py)

**Limitations:**

- Requires per-game API calls
- No bulk endpoint for multiple games

**Workarounds:**

```python
# Batch fetch for multiple games
async def fetch_multiple_games(game_ids: List[str]):
    tasks = [fetch_play_by_play(game_id) for game_id in game_ids]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Cache completed games indefinitely
if game_status == 'completed':
    ttl = None  # Never expire
else:
    ttl = 300  # 5 minutes for live games
```

**Recommended Approach:**

1. Fetch play-by-play data per game
2. Batch fetch for multiple games using asyncio
3. Cache completed games indefinitely
4. Poll live games every 30-60 seconds
5. Store all goals with is_first_goal flag

### 2.5 CFB (cfbd)

> **⚠️ CRITICAL DEPENDENCY CONFLICT**  
> The `cfbd` library requires pydantic v1, which conflicts with the main application's pydantic v2 dependency.
> This is a **blocking issue** for production integration. Consider these alternatives:
>
> 1. Wait for cfbd to update to pydantic v2 (check: https://github.com/CFBD/cfbd-python)
> 2. Use direct REST API calls instead of the Python library
> 3. Run CFB data ingestion in a separate microservice with isolated dependencies
> 4. Use alternative data sources for college football

**Limitations:**

- **BLOCKING**: Pydantic v1 dependency conflict
- Player names in text descriptions (not structured fields)
- Requires text parsing
- Free tier: 200 requests per hour
- Requires API key

**Workarounds:**

```python
# Build robust player name parser
import re

def extract_player_name(play_text: str) -> Optional[str]:
    """Extract player name from play description"""
    patterns = [
        r'^([A-Z][a-z]+ [A-Z][a-z]+) \d+ yd',  # "John Smith 25 yd"
        r'^([A-Z][a-z]+) \d+ yd',  # "Smith 25 yd"
        r'to ([A-Z][a-z]+ [A-Z][a-z]+) for',  # "to John Smith for"
    ]

    for pattern in patterns:
        match = re.search(pattern, play_text)
        if match:
            return match.group(1)

    return None

# Validate against roster
def validate_player_name(name: str, roster: List[str]) -> Optional[str]:
    """Fuzzy match player name against roster"""
    from difflib import get_close_matches
    matches = get_close_matches(name, roster, n=1, cutoff=0.8)
    return matches[0] if matches else None
```

**Recommended Approach:**

1. Obtain free API key from collegefootballdata.com
2. Build regex-based player name parser
3. Maintain roster database for validation
4. Implement fuzzy matching for name variations
5. Log unparseable plays for manual review
6. **Fallback**: Manual data entry for high-priority games

---

## 3. Caching and Performance Strategies

### 3.1 Multi-Level Caching Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Level 1: Application Memory (LRU Cache)                     │
│ - Query results (100 most recent)                           │
│ - TTL: 5 minutes                                             │
│ - Size: 100 MB                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 2: Redis (Distributed Cache)                          │
│ - Play-by-play data (per game)                              │
│ - Scoring events (per game)                                 │
│ - Player lookups                                             │
│ - TTL: Variable (see below)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 3: PostgreSQL (Persistent Storage)                    │
│ - All scoring events                                         │
│ - Game metadata                                              │
│ - Player information                                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Cache TTL Strategy

```python
def get_cache_ttl(game_status: str, data_type: str) -> Optional[int]:
    """Determine cache TTL based on game status and data type"""

    if game_status == 'completed':
        # Completed games: cache indefinitely
        return None

    elif game_status == 'live':
        # Live games: short TTL for real-time updates
        if data_type == 'play_by_play':
            return 60  # 1 minute
        elif data_type == 'scoring_events':
            return 30  # 30 seconds
        else:
            return 300  # 5 minutes

    elif game_status == 'scheduled':
        # Scheduled games: longer TTL
        return 3600  # 1 hour

    else:
        # Unknown status: default TTL
        return 300  # 5 minutes
```

### 3.3 Cache Key Patterns

```python
# Play-by-play data
cache_key = f"pbp:{sport}:{game_id}"

# Scoring events
cache_key = f"scoring:{sport}:{game_id}"

# First scorer
cache_key = f"first_scorer:{sport}:{game_id}"

# All scorers
cache_key = f"all_scorers:{sport}:{game_id}"

# Player scoring history
cache_key = f"player_scoring:{sport}:{player_id}:{season}"

# Game metadata
cache_key = f"game:{sport}:{game_id}"
```

### 3.4 Cache Invalidation Strategy

```python
async def invalidate_game_cache(game_id: str, sport: str):
    """Invalidate all cache entries for a game"""
    keys_to_delete = [
        f"pbp:{sport}:{game_id}",
        f"scoring:{sport}:{game_id}",
        f"first_scorer:{sport}:{game_id}",
        f"all_scorers:{sport}:{game_id}",
    ]

    await cache.delete_many(keys_to_delete)

# Invalidate when:
# 1. Game status changes (scheduled -> live -> completed)
# 2. New scoring event detected
# 3. Manual data correction
```

### 3.5 Performance Optimization

**Database Indexing:**

```sql
-- Index for first scorer queries
CREATE INDEX idx_first_scorer ON scoring_events(game_id, is_first_scorer);

-- Index for player scoring queries
CREATE INDEX idx_player_scoring ON scoring_events(player_id, game_id);

-- Index for sport-specific queries
CREATE INDEX idx_sport_game ON scoring_events(sport, game_id);

-- Composite index for common query patterns
CREATE INDEX idx_game_player_first ON scoring_events(game_id, player_id, is_first_scorer);
```

**Query Optimization:**

```python
# Use select_related to avoid N+1 queries
events = await db.query(ScoringEvent).options(
    selectinload(ScoringEvent.game),
    selectinload(ScoringEvent.player)
).filter(ScoringEvent.game_id == game_id).all()

# Use pagination for large result sets
events = await db.query(ScoringEvent).filter(
    ScoringEvent.player_id == player_id
).order_by(ScoringEvent.created_at.desc()).limit(50).all()
```

**Batch Processing:**

```python
# Fetch multiple games in parallel
async def fetch_games_batch(game_ids: List[str], sport: str):
    adapter = get_adapter(sport)
    tasks = [adapter.fetch_play_by_play(gid) for gid in game_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Process in batches of 10
batch_size = 10
for i in range(0, len(game_ids), batch_size):
    batch = game_ids[i:i+batch_size]
    await fetch_games_batch(batch, sport)
```

---

## 4. Data Quality and Validation

### 4.1 Data Validation Rules

**Scoring Event Validation:**

```python
def validate_scoring_event(event: ScoringEvent) -> List[str]:
    """Validate a scoring event and return list of errors"""
    errors = []

    # Required fields
    if not event.game_id:
        errors.append("game_id is required")
    if not event.player_id:
        errors.append("player_id is required")
    if not event.player_name:
        errors.append("player_name is required")

    # Logical validation
    if event.event_sequence < 1:
        errors.append("event_sequence must be >= 1")
    if event.is_first_scorer and event.event_sequence != 1:
        errors.append("first scorer must have event_sequence = 1")
    if event.period < 1:
        errors.append("period must be >= 1")

    # Sport-specific validation
    if event.sport == 'nfl' and event.period > 5:  # 4 quarters + OT
        errors.append("NFL period cannot exceed 5")
    if event.sport == 'nhl' and event.period > 5:  # 3 periods + OT + SO
        errors.append("NHL period cannot exceed 5")

    return errors
```

### 4.2 Data Quality Checks

**Automated Quality Checks:**

```python
async def run_quality_checks(game_id: str):
    """Run automated quality checks on scoring data"""

    # Check 1: First scorer flag consistency
    first_scorers = await db.query(ScoringEvent).filter(
        ScoringEvent.game_id == game_id,
        ScoringEvent.is_first_scorer == True
    ).all()

    if len(first_scorers) > 1:
        logger.error(f"Multiple first scorers found for game {game_id}")

    # Check 2: Event sequence consistency
    events = await db.query(ScoringEvent).filter(
        ScoringEvent.game_id == game_id
    ).order_by(ScoringEvent.event_sequence).all()

    for idx, event in enumerate(events, 1):
        if event.event_sequence != idx:
            logger.error(f"Event sequence gap in game {game_id}: expected {idx}, got {event.event_sequence}")

    # Check 3: Chronological ordering
    for i in range(len(events) - 1):
        if events[i].game_time_remaining < events[i+1].game_time_remaining:
            logger.error(f"Chronological ordering violation in game {game_id}")

    # Check 4: Player ID consistency
    for event in events:
        if not event.player_id or event.player_id == '':
            logger.warning(f"Missing player_id for event {event.id} in game {game_id}")
```

### 4.3 Data Reconciliation

**Cross-Reference with Official Sources:**

```python
async def reconcile_with_official_source(game_id: str, sport: str):
    """Cross-reference our data with official league sources"""

    # Fetch our data
    our_events = await db.query(ScoringEvent).filter(
        ScoringEvent.game_id == game_id
    ).all()

    # Fetch official data (e.g., from league website)
    official_data = await fetch_official_game_data(game_id, sport)

    # Compare
    discrepancies = []
    if len(our_events) != len(official_data['scoring_events']):
        discrepancies.append(f"Event count mismatch: {len(our_events)} vs {len(official_data['scoring_events'])}")

    # Check first scorer
    if our_events and official_data['first_scorer']:
        our_first = our_events[0].player_name
        official_first = official_data['first_scorer']
        if our_first != official_first:
            discrepancies.append(f"First scorer mismatch: {our_first} vs {official_first}")

    if discrepancies:
        logger.error(f"Data reconciliation failed for game {game_id}: {discrepancies}")
        await send_alert("Data Quality Issue", discrepancies)

    return discrepancies
```

---

## 5. Error Handling and Resilience

### 5.1 Error Handling Strategy

**Layered Error Handling:**

```python
class ScorerTrackingError(Exception):
    """Base exception for scorer tracking errors"""
    pass

class APIError(ScorerTrackingError):
    """External API error"""
    pass

class DataParsingError(ScorerTrackingError):
    """Error parsing data from API"""
    pass

class ValidationError(ScorerTrackingError):
    """Data validation error"""
    pass

# Error handling in service layer
async def get_first_scorer_safe(game_id: str, sport: str) -> Optional[ScoringEvent]:
    """Get first scorer with comprehensive error handling"""
    try:
        return await get_first_scorer(game_id, sport)
    except APIError as e:
        logger.error(f"API error fetching first scorer for {game_id}: {e}")
        # Try cache fallback
        cached = await cache.get(f"first_scorer:{sport}:{game_id}")
        if cached:
            logger.info(f"Returning cached data for {game_id}")
            return ScoringEvent(**cached)
        raise
    except DataParsingError as e:
        logger.error(f"Data parsing error for {game_id}: {e}")
        # Alert for manual review
        await send_alert("Data Parsing Error", str(e))
        return None
    except ValidationError as e:
        logger.error(f"Validation error for {game_id}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error fetching first scorer for {game_id}")
        raise
```

### 5.2 Retry Logic

**Exponential Backoff with Jitter:**

```python
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError)),
    before_sleep=lambda retry_state: logger.info(f"Retrying after {retry_state.next_action.sleep} seconds")
)
async def fetch_with_retry(func, *args, **kwargs):
    """Fetch data with exponential backoff retry"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Fetch failed: {e}")
        raise
```

### 5.3 Circuit Breaker Pattern

**Prevent Cascading Failures:**

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60, expected_exception=APIError)
async def fetch_play_by_play_with_circuit_breaker(game_id: str, sport: str):
    """Fetch play-by-play data with circuit breaker"""
    adapter = get_adapter(sport)
    return await adapter.fetch_play_by_play(game_id)

# Circuit breaker states:
# - CLOSED: Normal operation
# - OPEN: Too many failures, reject requests immediately
# - HALF_OPEN: Testing if service recovered
```

### 5.4 Graceful Degradation

**Fallback Strategies:**

```python
async def get_first_scorer_with_fallback(game_id: str, sport: str) -> Optional[ScoringEvent]:
    """Get first scorer with multiple fallback strategies"""

    # Strategy 1: Try primary data source
    try:
        return await get_first_scorer(game_id, sport)
    except APIError:
        logger.warning(f"Primary API failed for {game_id}, trying fallback")

    # Strategy 2: Try cache
    try:
        cached = await cache.get(f"first_scorer:{sport}:{game_id}")
        if cached:
            return ScoringEvent(**cached)
    except Exception:
        logger.warning(f"Cache failed for {game_id}")

    # Strategy 3: Try alternative data source
    try:
        return await get_first_scorer_from_alternative_source(game_id, sport)
    except Exception:
        logger.warning(f"Alternative source failed for {game_id}")

    # Strategy 4: Return None and flag for manual review
    await flag_for_manual_review(game_id, "All data sources failed")
    return None
```

---

## 6. Alternative Data Sources

### 6.1 Commercial Data Providers

**SportsRadar**

- **Pros**: Comprehensive coverage, real-time data, reliable
- **Cons**: Expensive ($1,000+ per month), enterprise contracts
- **Use Case**: Production at scale, real-time prop betting

**Sportradar**

- **Pros**: Similar to SportsRadar, good documentation
- **Cons**: Expensive, enterprise-focused
- **Use Case**: Large-scale production deployment

**The Odds API**

- **Pros**: Betting-focused, includes prop markets, affordable
- **Cons**: Limited play-by-play data
- **Use Case**: Prop betting odds, market data

### 6.2 Free/Low-Cost Alternatives

**ESPN API (Unofficial)**

- **Pros**: Free, comprehensive coverage
- **Cons**: Unofficial, can change without notice, no support
- **Use Case**: MVP, small-scale deployment

**Official League APIs**

- **NFL**: NFL.com API (limited, unofficial)
- **NBA**: NBA.com API (used by nba_api)
- **MLB**: MLB Stats API (official, free)
- **NHL**: NHL.com API (official, free)
- **Use Case**: Direct API access, bypass library limitations

### 6.3 Web Scraping (Last Resort)

**Targets:**

- ESPN.com: Game data, play-by-play, player stats
- Official league sites: NFL.com, NBA.com, MLB.com, NHL.com
- Sports reference sites: Pro-Football-Reference, Baseball-Reference

**Implementation:**

```python
import httpx
from bs4 import BeautifulSoup

async def scrape_first_scorer(game_url: str) -> Optional[str]:
    """Scrape first scorer from game page (last resort)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(game_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find scoring plays section
        scoring_section = soup.find('div', class_='scoring-plays')
        if not scoring_section:
            return None

        # Extract first scoring play
        first_play = scoring_section.find('div', class_='play-item')
        if not first_play:
            return None

        # Extract player name
        player_name = first_play.find('span', class_='player-name').text
        return player_name
```

**Cautions:**

- Against Terms of Service for most sites
- Fragile (breaks when HTML structure changes)
- Rate limiting and IP blocking risks
- Requires ongoing maintenance

### 6.4 Manual Data Entry

**When to Use:**

- MVP phase with limited games
- High-priority games (playoffs, championships)
- Data validation and quality checks
- Fallback when all automated sources fail

**Implementation:**

```python
# Admin interface for manual data entry
@router.post("/admin/scoring-events")
async def create_scoring_event_manual(
    event: ScoringEventCreate,
    current_user: User = Depends(get_admin_user)
):
    """Manually create a scoring event (admin only)"""

    # Validate
    errors = validate_scoring_event(event)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # Create
    db_event = ScoringEvent(**event.dict())
    db.add(db_event)
    await db.commit()

    # Invalidate cache
    await invalidate_game_cache(event.game_id, event.sport)

    # Log
    logger.info(f"Manual scoring event created by {current_user.username}: {event}")

    return db_event
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Week 1: Data Models and Database**

- [ ] Create database schema (games, scoring_events, players tables)
- [ ] Implement SQLAlchemy models
- [ ] Create database migrations
- [ ] Set up indexes for performance
- [ ] Write unit tests for models

**Week 2: Service Layer and Caching**

- [ ] Implement ScorerTrackingService
- [ ] Set up Redis caching layer
- [ ] Implement cache key patterns and TTL strategy
- [ ] Write unit tests for service layer
- [ ] Set up logging and monitoring

### Phase 2: Sport-Specific Adapters (Weeks 3-4)

**Week 3: NFL and MLB Adapters**

- [ ] Implement NFLDataAdapter using nflreadpy
- [ ] Implement MLBDataAdapter using pybaseball
- [ ] Write integration tests with real API data
- [ ] Implement error handling and retry logic
- [ ] Document adapter usage and limitations

**Week 4: NHL and CFB Adapters**

- [ ] Implement NHLDataAdapter using nhl-api-py
- [ ] Implement CFBDataAdapter using cfbd
- [ ] Build player name parser for CFB
- [ ] Write integration tests
- [ ] Document adapter usage and limitations

### Phase 3: API Layer (Week 5)

**API Endpoints:**

- [ ] GET /api/v1/games/{game_id}/first-scorer
- [ ] GET /api/v1/games/{game_id}/scorers
- [ ] GET /api/v1/players/{player_id}/scoring-history
- [ ] POST /api/v1/admin/scoring-events (manual entry)
- [ ] GET /api/v1/games/{game_id}/scoring-events

**Implementation:**

- [ ] Create FastAPI routers
- [ ] Implement request/response schemas
- [ ] Add authentication and authorization
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Write integration tests

### Phase 4: Testing and Validation (Week 6)

**Testing:**

- [ ] Unit tests for all components (target: 80% coverage)
- [ ] Integration tests with real API data
- [ ] End-to-end tests for complete workflows
- [ ] Performance tests (load testing, stress testing)
- [ ] Data quality validation tests

**Validation:**

- [ ] Validate against historical game data
- [ ] Cross-reference with official league sources
- [ ] Test error handling and edge cases
- [ ] Validate caching behavior
- [ ] Test graceful degradation

### Phase 5: Production Deployment (Weeks 7-8)

**Week 7: Staging Deployment**

- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Monitor performance and errors
- [ ] Test with live game data
- [ ] Fix any issues discovered

**Week 8: Production Deployment**

- [ ] Deploy to production
- [ ] Set up monitoring and alerting
- [ ] Configure automated data refresh jobs
- [ ] Document operational procedures
- [ ] Train team on system usage

---

## 8. Monitoring and Alerting

### 8.1 Key Metrics to Monitor

**System Health:**

- API response times (p50, p95, p99)
- Cache hit rates
- Database query performance
- Error rates by type
- Request throughput

**Data Quality:**

- Number of games processed per day
- Number of scoring events captured
- Data validation failure rate
- Missing player IDs
- Chronological ordering violations

**External APIs:**

- API call success rate
- API response times
- Rate limit violations
- Circuit breaker state changes

### 8.2 Alerting Rules

**Critical Alerts (Page On-Call):**

```python
# API error rate > 10%
if error_rate > 0.10:
    send_alert("CRITICAL: High API error rate", severity="critical")

# No data for completed games
if game.status == 'completed' and not game.scoring_events:
    send_alert("CRITICAL: Missing scoring data for completed game", severity="critical")

# Data validation failures
if validation_failure_rate > 0.05:
    send_alert("CRITICAL: High data validation failure rate", severity="critical")
```

**Warning Alerts (Review Next Day):**

```python
# Cache hit rate < 80%
if cache_hit_rate < 0.80:
    send_alert("WARNING: Low cache hit rate", severity="warning")

# Slow API responses
if api_response_time_p95 > 5000:  # 5 seconds
    send_alert("WARNING: Slow API responses", severity="warning")

# Missing player names
if missing_player_names > 10:
    send_alert("WARNING: Multiple missing player names", severity="warning")
```

### 8.3 Monitoring Dashboard

**Recommended Metrics Dashboard:**

```
┌─────────────────────────────────────────────────────────────┐
│ Scorer Tracking System - Monitoring Dashboard               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ System Health                                                │
│ ├─ API Response Time (p95): 250ms                           │
│ ├─ Cache Hit Rate: 92%                                       │
│ ├─ Error Rate: 0.5%                                          │
│ └─ Requests/min: 150                                         │
│                                                              │
│ Data Quality                                                 │
│ ├─ Games Processed Today: 45                                │
│ ├─ Scoring Events Captured: 287                             │
│ ├─ Validation Failures: 2                                    │
│ └─ Missing Player IDs: 0                                     │
│                                                              │
│ External APIs                                                │
│ ├─ NFL API Success Rate: 99.8%                              │
│ ├─ MLB API Success Rate: 98.5%                              │
│ ├─ NHL API Success Rate: 99.2%                              │
│ └─ CFB API Success Rate: 95.0%                              │
│                                                              │
│ Recent Alerts                                                │
│ ├─ [WARNING] Low CFB API success rate (2 hours ago)         │
│ └─ [INFO] Cache cleared for game NFL_2024_W10_BUF_KC        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.4 Logging Strategy

**Structured Logging:**

```python
import structlog

logger = structlog.get_logger()

# Log API calls
logger.info("api_call",
    sport="nfl",
    game_id="2024_01_NYJ_BUF",
    endpoint="play_by_play",
    duration_ms=250,
    status="success"
)

# Log data quality issues
logger.warning("data_quality_issue",
    sport="cfb",
    game_id="401520123",
    issue_type="missing_player_name",
    play_text="Smith 25 yd run (PAT good)"
)

# Log errors
logger.error("api_error",
    sport="nba",
    game_id="0022400123",
    error_type="rate_limit",
    retry_count=3,
    exc_info=True
)
```

---

## Conclusion

This production implementation guide provides a comprehensive roadmap for integrating sports data scorer tracking into the First6 application. The key recommendations are:

1. **Start with NFL** (highest priority, best data quality)
2. **Use unified architecture** (sport-agnostic service layer with adapters)
3. **Implement robust caching** (multi-level caching with smart TTL)
4. **Handle errors gracefully** (retry logic, circuit breakers, fallbacks)
5. **Monitor data quality** (automated validation, reconciliation, alerting)
6. **Plan for scale** (batch processing, async operations, indexing)

The research validates that all required data is available through free or low-cost APIs. With proper implementation following these recommendations, First6 can offer reliable first scorer and anytime scorer tracking across all major sports.

**Next Steps:**

1. Review and approve this implementation plan
2. Prioritize sports for implementation (recommend: NFL → MLB → NHL → CFB)
3. Begin Phase 1 (Foundation) implementation
4. Set up development environment and testing infrastructure
5. Start with NFL adapter as proof of concept

For questions or clarifications, refer to the sandbox scripts and research findings in the README.md file.
