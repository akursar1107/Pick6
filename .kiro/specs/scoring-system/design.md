# Design Document: Scoring System

## Overview

The Scoring System automatically grades user picks when NFL games complete, awards points based on touchdown predictions, and maintains user scores. The system integrates with nflreadpy to fetch game results and touchdown scorer data on a scheduled basis (daily at 1:59 AM EST for upcoming games, and on Sundays at 4:30 PM and 8:30 PM EST for game results). Each pick is evaluated against actual game outcomes: correct First Touchdown (FTD) predictions earn 3 points, correct Anytime Touchdown (ATTD) predictions earn 1 point, and picks can earn both if the player scored the first touchdown (4 points total). The system includes admin override capabilities for handling edge cases and API failures.

## Architecture

### System Components

```
┌─────────────────┐
│  Scheduled Jobs │
│  (APScheduler)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  NFL Data       │
│  Ingestion      │
│  (nflreadpy)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Scoring        │
│  Service        │
│  (Business      │
│   Logic)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Database       │
│  (PostgreSQL)   │
└─────────────────┘
```

### Layer Responsibilities

**Scheduled Jobs Layer** (`app/worker/scheduler.py`):

- Configure APScheduler with timezone support
- Define cron jobs for data fetching (1:59 AM, 4:30 PM, 8:30 PM)
- Handle job execution errors
- Log job runs and results

**NFL Data Ingestion Layer** (`app/services/nfl_ingest.py`):

- Fetch game schedules from nflreadpy
- Fetch game results and scores
- Fetch touchdown scorer data
- Validate and transform data
- Handle API errors with retries

**Scoring Service Layer** (`app/services/scoring_service.py`):

- Identify pending picks for completed games
- Calculate FTD points (3 points if correct)
- Calculate ATTD points (1 point if player scored)
- Update pick status (pending → win/loss)
- Update user total scores
- Handle edge cases (no touchdowns, multiple TDs by same player)

**API Layer** (`app/api/v1/endpoints/scores.py`):

- GET /api/v1/scores/user/{user_id} - Get user's total score
- GET /api/v1/scores/pick/{pick_id} - Get pick result details
- GET /api/v1/scores/game/{game_id} - Get game scoring results
- POST /api/v1/scores/game/{game_id}/manual - Manual scoring (admin)
- PATCH /api/v1/scores/pick/{pick_id}/override - Override pick score (admin)

**Database Layer**:

- Pick model (add scored_at, ftd_points, attd_points, is_manual_override fields)
- User model (add total_score, total_wins, total_losses fields)
- Game model (add first_td_scorer_player_id, all_td_scorer_player_ids, scored_at fields)

## Components and Interfaces

### Scheduled Jobs

#### Job Configuration

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

scheduler = AsyncIOScheduler()
est = timezone('America/New_York')

# Daily at 1:59 AM EST - Fetch upcoming games
scheduler.add_job(
    fetch_upcoming_games,
    CronTrigger(hour=1, minute=59, timezone=est),
    id='fetch_upcoming_games',
    name='Fetch Upcoming Games',
    replace_existing=True
)

# Sundays at 4:30 PM EST - Grade early games
scheduler.add_job(
    grade_completed_games,
    CronTrigger(day_of_week='sun', hour=16, minute=30, timezone=est),
    id='grade_early_games',
    name='Grade Early Games',
    replace_existing=True
)

# Sundays at 8:30 PM EST - Grade late games
scheduler.add_job(
    grade_completed_games,
    CronTrigger(day_of_week='sun', hour=20, minute=30, timezone=est),
    id='grade_late_games',
    name='Grade Late Games',
    replace_existing=True
)
```

### NFL Data Ingestion Service

#### NFLIngestService Methods

```python
class NFLIngestService:
    async def fetch_upcoming_games(self, season: int, week: int) -> List[GameData]:
        """Fetch upcoming games from nflreadpy"""

    async def fetch_game_results(self, game_id: str) -> GameResult:
        """Fetch final score and status for a game"""

    async def fetch_touchdown_scorers(self, game_id: str) -> TouchdownData:
        """Fetch all touchdown scorers and first TD scorer"""

    async def sync_games_to_database(self, games: List[GameData]) -> None:
        """Update database with game data"""

    async def update_game_results(self, game_id: UUID, result: GameResult) -> None:
        """Update game with final results"""
```

### Scoring Service

#### ScoringService Methods

```python
class ScoringService:
    async def grade_game(self, game_id: UUID) -> ScoringResult:
        """Grade all pending picks for a completed game"""

    async def calculate_ftd_points(self, pick: Pick, first_td_scorer: UUID) -> int:
        """Calculate FTD points (3 if correct, 0 if not)"""

    async def calculate_attd_points(self, pick: Pick, all_td_scorers: List[UUID]) -> int:
        """Calculate ATTD points (1 if player scored, 0 if not)"""

    async def update_pick_result(
        self,
        pick: Pick,
        ftd_points: int,
        attd_points: int,
        status: PickResult
    ) -> None:
        """Update pick with scoring results"""

    async def update_user_score(self, user_id: UUID, points: int) -> None:
        """Add points to user's total score"""

    async def get_user_total_score(self, user_id: UUID) -> UserScore:
        """Calculate user's total score from all graded picks"""

    async def manual_grade_game(
        self,
        game_id: UUID,
        first_td_scorer: UUID,
        all_td_scorers: List[UUID],
        admin_id: UUID
    ) -> ScoringResult:
        """Manually grade a game (admin override)"""

    async def override_pick_score(
        self,
        pick_id: UUID,
        status: PickResult,
        ftd_points: int,
        attd_points: int,
        admin_id: UUID
    ) -> Pick:
        """Override a pick's score (admin)"""
```

## Data Models

### Pick Model Updates

```python
class Pick(Base):
    __tablename__ = "picks"

    # Existing fields
    id: UUID
    user_id: UUID
    game_id: UUID
    player_id: UUID
    status: PickResult  # pending, win, loss
    pick_submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    # New scoring fields
    scored_at: datetime (nullable)  # When pick was graded
    ftd_points: int (default=0)  # Points from FTD (0 or 3)
    attd_points: int (default=0)  # Points from ATTD (0 or 1)
    total_points: int (default=0)  # ftd_points + attd_points
    is_manual_override: bool (default=False)  # True if admin overrode
    override_by_user_id: UUID (nullable)  # Admin who overrode
    override_at: datetime (nullable)  # When override happened
```

### User Model Updates

```python
class User(Base):
    __tablename__ = "users"

    # Existing fields
    id: UUID
    email: str
    username: str
    # ... other fields

    # New scoring fields
    total_score: int (default=0)  # Sum of all points
    total_wins: int (default=0)  # Count of winning picks
    total_losses: int (default=0)  # Count of losing picks
    win_percentage: float (computed)  # wins / (wins + losses)
```

### Game Model Updates

```python
class Game(Base):
    __tablename__ = "games"

    # Existing fields
    id: UUID
    external_id: str
    home_team_id: UUID
    away_team_id: UUID
    kickoff_time: datetime
    status: GameStatus
    # ... other fields

    # New scoring fields
    first_td_scorer_player_id: UUID (nullable)  # First TD scorer
    all_td_scorer_player_ids: List[UUID] (nullable)  # All TD scorers (JSON array)
    scored_at: datetime (nullable)  # When game was scored
    is_manually_scored: bool (default=False)  # True if admin scored
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Pending pick identification

_For any_ completed game, the scoring system should identify exactly the picks with status=pending for that game_id.
**Validates: Requirements 1.1**

### Property 2: Pick status update on grading

_For any_ pick that is graded, the status should change from pending to either win or loss, never remaining pending.
**Validates: Requirements 1.3**

### Property 3: Grading timestamp recorded

_For any_ pick that is graded, the scored_at timestamp should be set to a recent time (within last minute).
**Validates: Requirements 1.4**

### Property 4: Grading idempotence

_For any_ pick that has been graded, grading the same game again should not change the pick's status or points.
**Validates: Requirements 1.5**

### Property 5: FTD points correctness

_For any_ pick, if the pick's player_id matches the first_td_scorer_player_id, then ftd_points should be 3; otherwise ftd_points should be 0.
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 6: ATTD points correctness

_For any_ pick, if the pick's player_id appears in all_td_scorer_player_ids, then attd_points should be 1; otherwise attd_points should be 0.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 7: User score update

_For any_ pick that is graded, the user's total_score should increase by the pick's total_points (ftd_points + attd_points).
**Validates: Requirements 2.4, 3.4**

### Property 8: Loss status for non-scoring picks

_For any_ pick where the player did not score (ftd_points=0 and attd_points=0), the status should be loss.
**Validates: Requirements 4.1, 4.3**

### Property 9: Win status for scoring picks

_For any_ pick where the player scored (ftd_points>0 or attd_points>0), the status should be win.
**Validates: Requirements 5.1, 5.2**

### Property 10: Total points calculation

_For any_ pick, total_points should equal ftd_points + attd_points.
**Validates: Requirements 5.3**

### Property 11: Zero touchdown game handling

_For any_ game with zero touchdowns (first_td_scorer_player_id is null), all picks for that game should have status=loss and total_points=0.
**Validates: Requirements 6.1**

### Property 12: Multiple touchdowns by same player

_For any_ pick where the player appears multiple times in touchdown events, attd_points should still be 1 (not multiplied by number of TDs).
**Validates: Requirements 15.1, 15.2, 15.3**

### Property 13: FTD and ATTD stacking

_For any_ pick where the player scored the first touchdown, both ftd_points (3) and attd_points (1) should be awarded, totaling 4 points.
**Validates: Requirements 16.1, 16.2, 16.3**

### Property 14: User total score accuracy

_For any_ user, the total_score should equal the sum of total_points from all picks with status=win.
**Validates: Requirements 11.1, 11.2, 11.3**

### Property 15: Win/loss count accuracy

_For any_ user, total_wins should equal the count of picks with status=win, and total_losses should equal the count of picks with status=loss.
**Validates: Requirements 11.4**

### Property 16: Manual scoring equivalence

_For any_ game that is manually scored, the grading logic should produce the same results as automatic scoring given the same touchdown data.
**Validates: Requirements 9.1, 9.2**

### Property 17: Override audit trail

_For any_ pick that is overridden by an admin, is_manual_override should be true, override_by_user_id should be set, and override_at should be recent.
**Validates: Requirements 10.3, 10.4**

### Property 18: Data validation

_For any_ game data received from nflreadpy, if the game_id doesn't exist in the database or player_ids don't exist, the grading should be skipped and an error logged.
**Validates: Requirements 14.1, 14.2, 14.3, 14.4**

## Error Handling

### API Failures (nflreadpy)

**Connection Errors:**

- Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- Log each retry attempt
- After 3 failures, log error and send admin alert
- Continue operation (don't crash)

**Invalid Data:**

- Validate game exists in database
- Validate all player_ids exist in database
- If validation fails, skip grading and log error
- Send admin alert for manual intervention

**Rate Limiting:**

- Respect API rate limits
- Add delays between requests if needed
- Cache data when possible

### Scoring Errors

**Missing Data:**

- If first_td_scorer is missing but game is complete, log warning
- If all_td_scorers is empty, treat as zero touchdown game
- Allow admin to manually enter data

**Duplicate Grading:**

- Check if game already scored before grading
- If already scored, skip grading (idempotent)
- Log warning if duplicate grading attempted

**Database Errors:**

- Wrap all database operations in transactions
- Rollback on error
- Log error with full context
- Retry transient errors

### Scheduled Job Errors

**Job Execution Failures:**

- Log error with stack trace
- Send admin alert
- Continue with next scheduled run
- Don't crash scheduler

**Timezone Issues:**

- Always use pytz for timezone handling
- Store all times in UTC in database
- Convert to EST for scheduling

## Testing Strategy

### Unit Testing

Unit tests will cover specific examples and edge cases:

**Scoring Logic:**

- FTD correct (3 points)
- ATTD correct (1 point)
- Both FTD and ATTD correct (4 points)
- Neither correct (0 points, loss)
- Zero touchdown game (all losses)
- Multiple TDs by same player (1 ATTD point)

**Data Validation:**

- Valid game data
- Invalid game_id
- Invalid player_id
- Missing touchdown data

**Admin Overrides:**

- Manual scoring
- Score override
- Audit trail recording

### Property-Based Testing

Property-based tests will verify universal properties using **Hypothesis** (Python property-based testing library). Each test will run a minimum of 100 iterations with randomly generated data.

**Test Configuration:**

```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Test implementation
```

**Data Generators:**

```python
# Generate random picks
pick_strategy = st.builds(
    Pick,
    player_id=st.uuids(),
    game_id=st.uuids(),
    status=st.just(PickResult.PENDING)
)

# Generate random game results
game_result_strategy = st.builds(
    GameResult,
    first_td_scorer=st.one_of(st.none(), st.uuids()),
    all_td_scorers=st.lists(st.uuids(), min_size=0, max_size=10)
)

# Generate random touchdown data
touchdown_data_strategy = st.builds(
    TouchdownData,
    first_scorer=st.one_of(st.none(), st.uuids()),
    all_scorers=st.lists(st.uuids(), min_size=0, max_size=10)
)
```

**Property Test Examples:**

```python
@settings(max_examples=100)
@given(
    pick=pick_strategy,
    first_td_scorer=st.one_of(st.none(), st.uuids())
)
async def test_property_5_ftd_points_correctness(pick, first_td_scorer):
    """
    Feature: scoring-system, Property 5: FTD points correctness
    For any pick, if the pick's player_id matches the first_td_scorer_player_id,
    then ftd_points should be 3; otherwise ftd_points should be 0.
    """
    # Action: Calculate FTD points
    ftd_points = await scoring_service.calculate_ftd_points(pick, first_td_scorer)

    # Assert: Verify correctness
    if pick.player_id == first_td_scorer:
        assert ftd_points == 3
    else:
        assert ftd_points == 0
```

Each correctness property will be implemented as a property-based test with the format:
`**Feature: scoring-system, Property {number}: {property_text}**`

### Integration Testing

Integration tests will verify end-to-end workflows:

- Complete scoring flow (fetch data → grade picks → update scores)
- Scheduled job execution
- nflreadpy integration
- Manual scoring workflow
- Score override workflow

### Test Data Management

- Use database transactions with rollback for test isolation
- Mock nflreadpy responses for predictable testing
- Create test fixtures for common scenarios
- Use factories for generating test data

## Performance Considerations

### Database Optimization

**Indexes:**

- `picks(game_id, status)` - For finding pending picks
- `picks(user_id, status)` - For calculating user scores
- `games(status, kickoff_time)` - For finding completed games
- `games(first_td_scorer_player_id)` - For scoring lookups

**Query Optimization:**

- Batch update picks for a game in single transaction
- Use bulk updates for user scores
- Eager load related data (game, player, user)

### Caching Strategy

**User Scores:**

- Cache user total scores with 5-minute TTL
- Invalidate on pick grading
- Key: `user_score:{user_id}`

**Game Results:**

- Cache game results after scoring
- No expiration (immutable once scored)
- Key: `game_result:{game_id}`

### Scheduled Job Performance

**Job Execution Time:**

- Target: < 30 seconds per job
- Batch process games (10 at a time)
- Parallel processing where possible

**API Rate Limiting:**

- Respect nflreadpy rate limits
- Add delays between requests if needed
- Cache responses when possible

## Security Considerations

### Authentication

- All scoring endpoints require authentication
- Admin endpoints require admin role
- Manual scoring requires admin privileges
- Score overrides require admin privileges

### Authorization

- Users can view their own scores
- Users can view pick results for their picks
- Admins can view all scores
- Admins can manually score games
- Admins can override pick scores

### Audit Trail

- Log all manual scoring actions
- Log all score overrides
- Record admin user_id for all manual actions
- Record timestamps for all actions

### Data Integrity

- Validate all data from nflreadpy
- Prevent duplicate grading with idempotency checks
- Use database transactions for atomic updates
- Verify player_ids exist before grading

## Deployment Considerations

### Database Migrations

Migration to add scoring fields:

```python
def upgrade():
    # Add scoring fields to picks table
    op.add_column('picks', sa.Column('scored_at', sa.DateTime(), nullable=True))
    op.add_column('picks', sa.Column('ftd_points', sa.Integer(), default=0))
    op.add_column('picks', sa.Column('attd_points', sa.Integer(), default=0))
    op.add_column('picks', sa.Column('total_points', sa.Integer(), default=0))
    op.add_column('picks', sa.Column('is_manual_override', sa.Boolean(), default=False))
    op.add_column('picks', sa.Column('override_by_user_id', sa.UUID(), nullable=True))
    op.add_column('picks', sa.Column('override_at', sa.DateTime(), nullable=True))

    # Add scoring fields to users table
    op.add_column('users', sa.Column('total_score', sa.Integer(), default=0))
    op.add_column('users', sa.Column('total_wins', sa.Integer(), default=0))
    op.add_column('users', sa.Column('total_losses', sa.Integer(), default=0))

    # Add scoring fields to games table
    op.add_column('games', sa.Column('first_td_scorer_player_id', sa.UUID(), nullable=True))
    op.add_column('games', sa.Column('all_td_scorer_player_ids', sa.JSON(), nullable=True))
    op.add_column('games', sa.Column('scored_at', sa.DateTime(), nullable=True))
    op.add_column('games', sa.Column('is_manually_scored', sa.Boolean(), default=False))

    # Add foreign key constraints
    op.create_foreign_key(None, 'picks', 'users', ['override_by_user_id'], ['id'])
    op.create_foreign_key(None, 'games', 'players', ['first_td_scorer_player_id'], ['id'])
```

### Scheduled Job Setup

**APScheduler Configuration:**

- Run in separate process or container
- Persist job state to database
- Configure timezone correctly (America/New_York)
- Set up job monitoring and alerts

**Job Monitoring:**

- Log all job executions
- Track job duration
- Alert on job failures
- Dashboard for job status

### Monitoring

**Metrics to Track:**

- Scoring job execution time
- Number of picks graded per job
- API call success/failure rate
- User score distribution
- Pick win/loss ratio

**Alerts:**

- Job execution failures
- API failures after retries
- Data validation errors
- Scoring errors

### Backup Strategy

**Data Backup:**

- Daily database backups
- Backup before each scoring run
- Retain backups for 30 days

**Rollback Plan:**

- Ability to revert scoring for a game
- Ability to recalculate user scores
- Admin tools for data correction

## Future Enhancements

### Phase 2 Features

- Real-time scoring during games (WebSocket updates)
- Scoring notifications (email, push)
- Historical scoring data and trends
- Advanced statistics (win rate by position, team, etc.)
- Scoring predictions and projections

### Technical Improvements

- Parallel processing of multiple games
- Distributed job scheduling (Celery)
- Advanced caching strategies
- Machine learning for data validation
- Automated anomaly detection
