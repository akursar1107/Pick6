# Design Document: Pick Submission & Management

## Overview

The Pick Submission & Management feature provides the core user interaction for First6, enabling users to submit, view, edit, and delete their touchdown predictions. Each user can submit one pick per game, which automatically counts for both First Touchdown (FTD) and Anytime Touchdown (ATTD) scoring categories. The system enforces business rules around timing (picks must be before kickoff), uniqueness (one pick per user per game), and authorization (users can only manage their own picks).

This design builds upon the existing database models (Pick, Game, Player, User) and extends the current API endpoints with proper validation, authentication, and business logic.

## Architecture

### System Components

```
┌─────────────────┐
│   React UI      │
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI        │
│  API Layer      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pick Service   │
│  (Business      │
│   Logic)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLAlchemy     │
│  (Database)     │
└─────────────────┘
```

### Layer Responsibilities

**API Layer** (`app/api/v1/endpoints/picks.py`):

- Request validation via Pydantic schemas
- Authentication/authorization checks
- HTTP response formatting
- Error handling and status codes

**Service Layer** (`app/services/pick_service.py`):

- Business logic validation (kickoff time checks, duplicate detection)
- Database operations via SQLAlchemy
- Cross-entity queries (joins with games, players, users)
- Transaction management

**Database Layer** (`app/db/models/`):

- Data persistence
- Referential integrity via foreign keys
- Timestamps and audit fields

## Components and Interfaces

### API Endpoints

#### POST /api/v1/picks

Create a new pick for a game.

**Request Body:**

```json
{
  "game_id": "uuid",
  "player_id": "uuid"
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "game_id": "uuid",
  "player_id": "uuid",
  "status": "pending",
  "pick_submitted_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- 400: Validation error (duplicate pick, after kickoff, invalid IDs)
- 401: Unauthenticated
- 404: Game or player not found

#### GET /api/v1/picks

Retrieve picks with optional filters.

**Query Parameters:**

- `game_id` (optional): Filter by game
- `user_id` (optional): Filter by user (defaults to authenticated user)

**Response (200 OK):**

```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "game_id": "uuid",
    "player_id": "uuid",
    "status": "pending",
    "pick_submitted_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "game": {
      "home_team": "Chiefs",
      "away_team": "Bills",
      "kickoff_time": "2024-01-15T18:00:00Z"
    },
    "player": {
      "name": "Patrick Mahomes",
      "team": "Chiefs",
      "position": "QB"
    }
  }
]
```

#### GET /api/v1/picks/{pick_id}

Retrieve a specific pick by ID.

**Response (200 OK):** Same as single pick object above

**Error Responses:**

- 401: Unauthenticated
- 403: Not authorized to view this pick
- 404: Pick not found

#### PATCH /api/v1/picks/{pick_id}

Update an existing pick (change player selection).

**Request Body:**

```json
{
  "player_id": "uuid"
}
```

**Response (200 OK):** Updated pick object

**Error Responses:**

- 400: Validation error (after kickoff)
- 401: Unauthenticated
- 403: Not authorized to modify this pick
- 404: Pick not found

#### DELETE /api/v1/picks/{pick_id}

Delete a pick before kickoff.

**Response (204 No Content)**

**Error Responses:**

- 400: Cannot delete after kickoff
- 401: Unauthenticated
- 403: Not authorized to delete this pick
- 404: Pick not found

#### GET /api/v1/games/available

Retrieve games available for picks (future kickoffs).

**Response (200 OK):**

```json
[
  {
    "id": "uuid",
    "home_team": "Chiefs",
    "away_team": "Bills",
    "kickoff_time": "2024-01-15T18:00:00Z",
    "week_number": 18,
    "user_pick": {
      "id": "uuid",
      "player_name": "Patrick Mahomes"
    }
  }
]
```

#### GET /api/v1/players/search

Search for players by name.

**Query Parameters:**

- `q`: Search query string

**Response (200 OK):**

```json
[
  {
    "id": "uuid",
    "name": "Patrick Mahomes",
    "team": "Chiefs",
    "position": "QB"
  }
]
```

### Service Methods

#### PickService

```python
class PickService:
    async def create_pick(
        self,
        user_id: UUID,
        game_id: UUID,
        player_id: UUID
    ) -> Pick

    async def get_user_picks(
        self,
        user_id: UUID,
        game_id: Optional[UUID] = None
    ) -> List[Pick]

    async def get_pick_by_id(
        self,
        pick_id: UUID
    ) -> Optional[Pick]

    async def update_pick(
        self,
        pick_id: UUID,
        user_id: UUID,
        player_id: UUID
    ) -> Pick

    async def delete_pick(
        self,
        pick_id: UUID,
        user_id: UUID
    ) -> None

    async def check_duplicate_pick(
        self,
        user_id: UUID,
        game_id: UUID
    ) -> bool

    async def validate_pick_timing(
        self,
        game_id: UUID
    ) -> bool
```

#### GameService

```python
class GameService:
    async def get_available_games(
        self,
        user_id: Optional[UUID] = None
    ) -> List[GameWithPick]

    async def get_game_by_id(
        self,
        game_id: UUID
    ) -> Optional[Game]

    async def is_game_locked(
        self,
        game_id: UUID
    ) -> bool
```

#### PlayerService

```python
class PlayerService:
    async def search_players(
        self,
        query: str,
        limit: int = 20
    ) -> List[Player]

    async def get_player_by_id(
        self,
        player_id: UUID
    ) -> Optional[Player]
```

## Data Models

### Pick Model (Existing - Modified)

```python
class Pick(Base):
    __tablename__ = "picks"

    id: UUID (PK)
    user_id: UUID (FK -> users.id)
    game_id: UUID (FK -> games.id)
    player_id: UUID (FK -> players.id)

    status: PickResult (pending, win, loss, void)
    is_manual_override: bool

    settled_at: datetime (nullable)
    pick_submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'game_id', name='uq_user_game_pick'),
    )
```

**Key Changes:**

- Remove `pick_type` field (no longer needed since one pick covers both FTD and ATTD)
- Add unique constraint on (user_id, game_id) to enforce one pick per user per game
- Remove `snapshot_odds` field (not needed for MVP)

### Game Model (Existing - No Changes)

Already has necessary fields:

- `kickoff_time`: For validation
- `status`: For determining if game is locked
- `first_td_scorer_player_id`: For FTD scoring (handled in scoring feature)

### Player Model (To Be Created)

```python
class Player(Base):
    __tablename__ = "players"

    id: UUID (PK)
    external_id: str (unique, indexed)
    name: str
    team_id: UUID (FK -> teams.id)
    position: str
    jersey_number: int (nullable)
    is_active: bool

    created_at: datetime
    updated_at: datetime
```

### Team Model (To Be Created)

```python
class Team(Base):
    __tablename__ = "teams"

    id: UUID (PK)
    external_id: str (unique, indexed)
    name: str
    abbreviation: str
    city: str

    created_at: datetime
    updated_at: datetime
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property Reflection

After analyzing all acceptance criteria, I've identified the following redundancies:

- **Properties 1.2, 1.3, 1.4** (timestamp capture, user association, storing IDs) can be combined into a single comprehensive property about pick creation completeness
- **Property 7.3** is redundant with **Property 7.1** - if we verify only future games are returned, we've already verified past games are excluded
- **Properties 2.2, 6.2, 7.2, 8.2** all test that response objects include required fields - these can be consolidated into fewer, more comprehensive properties

After consolidation, here are the unique correctness properties:

### Property 1: Valid pick creation

_For any_ valid pick submission (user, game with future kickoff, player), creating the pick should result in a pick record with pending status, correct user_id, game_id, player_id, and a submission timestamp near the current time.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Kickoff time enforcement for creation

_For any_ game with a kickoff time in the past, attempting to create a pick for that game should be rejected with an error.
**Validates: Requirements 1.5**

### Property 3: User pick filtering

_For any_ user, retrieving picks for that user should return only picks where the user_id matches that user.
**Validates: Requirements 2.1**

### Property 4: Game pick filtering

_For any_ game, retrieving picks filtered by that game should return only picks where the game_id matches that game.
**Validates: Requirements 2.3**

### Property 5: Pick response completeness

_For any_ pick retrieved from the system, the response should include all required fields: game information, player information, and submission timestamp.
**Validates: Requirements 2.2**

### Property 6: Pick update modifies player

_For any_ pick with a future kickoff time, updating the pick with a new player_id should result in the pick record having the new player_id.
**Validates: Requirements 3.1**

### Property 7: Update timestamp changes

_For any_ pick that is updated, the updated_at timestamp should change to reflect the modification time.
**Validates: Requirements 3.2**

### Property 8: Kickoff time enforcement for updates

_For any_ pick associated with a game that has a kickoff time in the past, attempting to update the pick should be rejected with an error.
**Validates: Requirements 3.3**

### Property 9: Submission timestamp invariance

_For any_ pick that is updated, the pick_submitted_at timestamp should remain unchanged from its original value.
**Validates: Requirements 3.4**

### Property 10: Pick deletion removes record

_For any_ pick with a future kickoff time, deleting the pick should result in the pick no longer existing in the database.
**Validates: Requirements 4.1**

### Property 11: Kickoff time enforcement for deletion

_For any_ pick associated with a game that has a kickoff time in the past, attempting to delete the pick should be rejected with an error.
**Validates: Requirements 4.2**

### Property 12: Duplicate pick prevention

_For any_ user and game combination where a pick already exists, attempting to create another pick for the same user and game should be rejected with an error.
**Validates: Requirements 5.1, 5.2**

### Property 13: Update does not trigger duplicate detection

_For any_ existing pick, updating the pick with a new player_id should succeed without being rejected as a duplicate.
**Validates: Requirements 5.3**

### Property 14: Player search returns matches

_For any_ search query string, the returned players should have names that match the query string.
**Validates: Requirements 6.1**

### Property 15: Player search response completeness

_For any_ player returned from search, the response should include player name, team, and position.
**Validates: Requirements 6.2**

### Property 16: Non-matching search returns empty

_For any_ search query that does not match any player names, the system should return an empty list.
**Validates: Requirements 6.4**

### Property 17: Available games are future games

_For any_ game returned as available, the kickoff time should be in the future relative to the current time.
**Validates: Requirements 7.1**

### Property 18: Available games response completeness

_For any_ available game returned, the response should include home team, away team, kickoff time, and game week.
**Validates: Requirements 7.2**

### Property 19: Available games ordered by kickoff

_For any_ list of available games returned, the games should be ordered by kickoff_time in ascending order.
**Validates: Requirements 7.4**

### Property 20: Games with picks are indicated

_For any_ user viewing available games, games where that user has submitted a pick should be indicated with the pick information including player name.
**Validates: Requirements 8.1, 8.2**

### Property 21: Unauthenticated creation rejected

_For any_ pick creation attempt without authentication, the request should be rejected with an authentication error.
**Validates: Requirements 9.1**

### Property 22: Unauthenticated viewing rejected

_For any_ pick viewing attempt without authentication, the request should be rejected with an authentication error.
**Validates: Requirements 9.2**

### Property 23: Cross-user modification rejected

_For any_ pick owned by user A, an attempt by user B to modify that pick should be rejected with an authorization error.
**Validates: Requirements 9.3**

### Property 24: Cross-user deletion rejected

_For any_ pick owned by user A, an attempt by user B to delete that pick should be rejected with an authorization error.
**Validates: Requirements 9.4**

## Error Handling

### Validation Errors

**Timing Violations:**

- Picks cannot be created, updated, or deleted after game kickoff
- Return HTTP 400 with message: "Cannot modify pick after game kickoff"

**Duplicate Picks:**

- Users cannot create multiple picks for the same game
- Return HTTP 400 with message: "Pick already exists for this game"

**Invalid References:**

- Game ID must exist and be valid
- Player ID must exist and be valid
- Return HTTP 404 with message: "Game not found" or "Player not found"

### Authentication Errors

**Missing Authentication:**

- All pick operations require authentication
- Return HTTP 401 with message: "Authentication required"

### Authorization Errors

**Cross-User Access:**

- Users can only modify/delete their own picks
- Return HTTP 403 with message: "Not authorized to modify this pick"

### Database Errors

**Connection Failures:**

- Retry logic for transient failures
- Return HTTP 503 with message: "Service temporarily unavailable"

**Constraint Violations:**

- Handle unique constraint violations gracefully
- Return HTTP 400 with appropriate message

## Testing Strategy

### Unit Testing

Unit tests will cover specific examples and edge cases:

**Pick Creation:**

- Create pick with valid data
- Create pick with invalid game_id (404)
- Create pick with invalid player_id (404)
- Create pick after kickoff (400)
- Create duplicate pick (400)

**Pick Retrieval:**

- Get picks for user with no picks (empty list)
- Get picks for specific game
- Get pick by ID that doesn't exist (404)

**Pick Updates:**

- Update pick before kickoff
- Update pick after kickoff (400)
- Update non-existent pick (404)
- Update another user's pick (403)

**Pick Deletion:**

- Delete pick before kickoff
- Delete pick after kickoff (400)
- Delete non-existent pick (404)
- Delete another user's pick (403)

**Player Search:**

- Search with empty query (empty list)
- Search with no matches (empty list)

**Available Games:**

- Get available games when all games are in the past (empty list)

### Property-Based Testing

Property-based tests will verify universal properties across many random inputs using **Hypothesis** (Python property-based testing library). Each test will run a minimum of 100 iterations with randomly generated data.

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
# Generate random UUIDs
uuid_strategy = st.uuids()

# Generate random future datetimes
future_datetime = st.datetimes(
    min_value=datetime.now(timezone.utc) + timedelta(hours=1),
    max_value=datetime.now(timezone.utc) + timedelta(days=30)
)

# Generate random past datetimes
past_datetime = st.datetimes(
    min_value=datetime.now(timezone.utc) - timedelta(days=30),
    max_value=datetime.now(timezone.utc) - timedelta(hours=1)
)

# Generate random player names
player_name = st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))

# Generate random pick data
pick_data = st.builds(
    PickCreate,
    game_id=uuid_strategy,
    player_id=uuid_strategy
)
```

**Property Test Examples:**

Each property from the Correctness Properties section will be implemented as a property-based test. For example:

```python
@settings(max_examples=100)
@given(
    user_id=st.uuids(),
    game_id=st.uuids(),
    player_id=st.uuids(),
    kickoff_time=future_datetime
)
async def test_property_1_valid_pick_creation(user_id, game_id, player_id, kickoff_time):
    """
    Feature: pick-submission, Property 1: Valid pick creation
    For any valid pick submission, creating the pick should result in a pick
    record with pending status and correct attributes.
    """
    # Setup: Create game with future kickoff
    game = await create_test_game(game_id, kickoff_time)
    player = await create_test_player(player_id)

    # Action: Create pick
    pick = await pick_service.create_pick(user_id, game_id, player_id)

    # Assert: Verify all properties
    assert pick.status == PickResult.PENDING
    assert pick.user_id == user_id
    assert pick.game_id == game_id
    assert pick.player_id == player_id
    assert abs((pick.pick_submitted_at - datetime.now(timezone.utc)).total_seconds()) < 5
```

### Integration Testing

Integration tests will verify end-to-end workflows:

- Complete pick submission flow (create → view → update → delete)
- Pick submission with game data ingestion
- Multiple users submitting picks for the same game
- Pick submission near kickoff time boundary

### Test Data Management

- Use database transactions with rollback for test isolation
- Create test fixtures for common scenarios (users, games, players)
- Use factory pattern for generating test data
- Clean up test data after each test

## Performance Considerations

### Database Indexing

Ensure indexes exist on:

- `picks.user_id` (for user pick queries)
- `picks.game_id` (for game pick queries)
- `picks(user_id, game_id)` (for duplicate detection)
- `games.kickoff_time` (for available games queries)
- `players.name` (for player search)

### Query Optimization

- Use `select_related` / `joinedload` for eager loading of related entities (game, player, team)
- Limit player search results to reasonable number (20-50)
- Cache available games list with short TTL (5-10 minutes)

### Caching Strategy

**Available Games:**

- Cache for 5 minutes
- Invalidate on game status changes
- Key: `available_games:{user_id}`

**Player Search:**

- Cache search results for 1 hour
- Key: `player_search:{query}`

## Security Considerations

### Authentication

- All endpoints require valid JWT token
- Token includes user_id claim
- Token expiration enforced

### Authorization

- Users can only view/modify/delete their own picks
- Service layer validates user_id matches authenticated user
- Admin users can view all picks (future enhancement)

### Input Validation

- All UUIDs validated for format
- Game and player IDs validated for existence
- Timestamps validated for reasonable ranges
- Search queries sanitized to prevent SQL injection

### Rate Limiting

- Implement rate limiting on pick creation (e.g., 10 picks per minute per user)
- Implement rate limiting on player search (e.g., 30 searches per minute per user)

## Deployment Considerations

### Database Migrations

Migration to add unique constraint:

```python
def upgrade():
    op.create_unique_constraint(
        'uq_user_game_pick',
        'picks',
        ['user_id', 'game_id']
    )

    # Remove pick_type column if it exists
    op.drop_column('picks', 'pick_type')

    # Remove snapshot_odds column if it exists
    op.drop_column('picks', 'snapshot_odds')
```

### Backward Compatibility

- Existing picks with `pick_type` field will need migration
- Consolidate FTD and ATTD picks for same user/game into single pick
- Preserve most recent pick if duplicates exist

### Monitoring

- Track pick submission rate
- Monitor API response times
- Alert on high error rates (>5% of requests)
- Track duplicate pick attempts (may indicate UX issues)

## Future Enhancements

### Phase 2 Features

- Bulk pick submission (multiple games at once)
- Pick confidence levels (high/medium/low)
- Pick history and analytics
- Social features (see friends' picks after kickoff)
- Push notifications for pick reminders

### Technical Improvements

- WebSocket support for real-time pick updates
- Optimistic locking for concurrent updates
- Soft deletes for pick audit trail
- Pick versioning for change history
