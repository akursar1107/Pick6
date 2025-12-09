# Design Document: Admin Data Import Feature

## Overview

The Admin Data Import feature provides a user-friendly interface for importing NFL season data directly from the Admin Scoring Dashboard. This feature eliminates the need for command-line scripts by implementing a new, clean service architecture with real-time progress tracking and background job execution.

The implementation consists of:

- **Frontend**: Import modal with configuration options and progress tracking
- **Backend**: New NFLDataImportService with API endpoints
- **Background Jobs**: Async task execution with progress updates
- **Database**: Import history tracking

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin Dashboard UI                       │
│  ┌────────────────┐  ┌──────────────────────────────────┐  │
│  │ Import Data    │  │  Import Progress Modal           │  │
│  │ Button         │→ │  - Season/Week Selection         │  │
│  └────────────────┘  │  - Grading Option                │  │
│                      │  - Progress Tracking              │  │
│                      │  - Import History                 │  │
│                      └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/v1/admin/import/                               │  │
│  │  - POST /start      (initiate import)                │  │
│  │  - GET  /status/:id (get progress)                   │  │
│  │  - GET  /history    (get import history)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  NFLDataImportService                                │  │
│  │  - import_season_data()                              │  │
│  │  - fetch_schedule()                                  │  │
│  │  - create_or_update_game()                           │  │
│  │  - grade_game()                                      │  │
│  │  - track_progress()                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Background Task Queue (Celery/ARQ)                  │  │
│  │  - Async import execution                            │  │
│  │  - Progress updates                                  │  │
│  │  - Error handling                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      External Services                       │
│  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │  nflreadpy       │  │  PostgreSQL Database         │   │
│  │  - Schedules     │  │  - Games                     │   │
│  │  - Play-by-play  │  │  - Teams                     │   │
│  │  - Player data   │  │  - Players                   │   │
│  └──────────────────┘  │  - Import History            │   │
│                        └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **User Initiates Import**

   - Admin clicks "Import Data" button
   - Modal opens with configuration form
   - User selects season, weeks, and grading option

2. **Backend Processes Request**

   - API validates input parameters
   - Creates import job record in database
   - Queues background task
   - Returns job ID to frontend

3. **Background Task Executes**

   - Fetches schedule from nflreadpy
   - Processes games sequentially
   - Updates progress in database
   - Grades completed games if requested

4. **Frontend Tracks Progress**
   - Polls status endpoint every 2 seconds
   - Updates progress UI
   - Displays completion statistics

## Components and Interfaces

### Frontend Components

#### 1. ImportDataButton Component

```typescript
interface ImportDataButtonProps {
  onImportComplete?: () => void;
}

// Renders button that opens import modal
// Located in AdminScoringPage
```

#### 2. ImportDataModal Component

```typescript
interface ImportDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportStart: (config: ImportConfig) => void;
}

interface ImportConfig {
  season: number;
  weeks: number[] | "all";
  gradeGames: boolean;
}

// Main modal with configuration form
// Handles user input and validation
```

#### 3. ImportProgressModal Component

```typescript
interface ImportProgressModalProps {
  jobId: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete: (stats: ImportStats) => void;
}

interface ImportProgress {
  status: "pending" | "running" | "completed" | "failed";
  current_step: string;
  games_processed: number;
  total_games: number;
  teams_created: number;
  players_created: number;
  games_created: number;
  games_updated: number;
  games_graded: number;
  errors: string[];
}

// Displays real-time progress
// Polls status endpoint
// Shows completion statistics
```

#### 4. ImportHistoryList Component

```typescript
interface ImportHistoryListProps {
  limit?: number;
}

interface ImportHistoryItem {
  id: string;
  season: number;
  weeks: number[] | "all";
  grade_games: boolean;
  status: "completed" | "failed" | "running";
  started_at: string;
  completed_at: string | null;
  stats: ImportStats;
  admin_user_id: string;
}

// Displays recent import operations
// Shows status and statistics
```

### Backend Services

#### 1. NFLDataImportService

```python
class NFLDataImportService:
    """Service for importing NFL data from nflreadpy"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.progress_tracker = ImportProgressTracker()

    async def import_season_data(
        self,
        season: int,
        weeks: List[int] | None,
        grade_games: bool,
        job_id: str
    ) -> ImportStats:
        """
        Main import method

        Args:
            season: NFL season year (e.g., 2024)
            weeks: List of week numbers or None for all weeks
            grade_games: Whether to fetch TD data
            job_id: Import job ID for progress tracking

        Returns:
            ImportStats with counts of created/updated records
        """
        pass

    async def fetch_schedule(
        self,
        season: int,
        weeks: List[int] | None
    ) -> List[Dict[str, Any]]:
        """Fetch schedule from nflreadpy"""
        pass

    async def create_or_update_game(
        self,
        game_data: Dict[str, Any]
    ) -> Tuple[Game, bool]:
        """
        Create or update game record

        Returns:
            Tuple of (Game, was_created)
        """
        pass

    async def grade_game(
        self,
        game: Game
    ) -> bool:
        """
        Grade completed game by fetching TD data

        Returns:
            True if grading succeeded
        """
        pass

    async def get_or_create_team(
        self,
        team_abbr: str
    ) -> Team:
        """Get or create team by abbreviation"""
        pass

    async def get_or_create_player(
        self,
        player_id: str,
        player_name: str,
        position: str,
        team: Team
    ) -> Player:
        """Get or create player"""
        pass
```

#### 2. ImportProgressTracker

```python
class ImportProgressTracker:
    """Tracks import progress in Redis"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def update_progress(
        self,
        job_id: str,
        progress: ImportProgress
    ) -> None:
        """Update progress in Redis"""
        pass

    async def get_progress(
        self,
        job_id: str
    ) -> ImportProgress | None:
        """Get current progress"""
        pass

    async def mark_complete(
        self,
        job_id: str,
        stats: ImportStats
    ) -> None:
        """Mark import as complete"""
        pass

    async def mark_failed(
        self,
        job_id: str,
        error: str
    ) -> None:
        """Mark import as failed"""
        pass
```

### API Endpoints

#### POST /api/v1/admin/import/start

```python
class ImportStartRequest(BaseModel):
    season: int = Field(ge=2020, le=2030)
    weeks: List[int] | Literal['all'] = 'all'
    grade_games: bool = False

class ImportStartResponse(BaseModel):
    job_id: str
    message: str
    estimated_duration_minutes: int

@router.post("/start")
async def start_import(
    request: ImportStartRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ImportStartResponse:
    """Initiate NFL data import"""
    pass
```

#### GET /api/v1/admin/import/status/{job_id}

```python
class ImportStatusResponse(BaseModel):
    job_id: str
    status: Literal['pending', 'running', 'completed', 'failed']
    progress: ImportProgress
    stats: ImportStats | None

@router.get("/status/{job_id}")
async def get_import_status(
    job_id: str,
    current_user: User = Depends(get_current_admin_user)
) -> ImportStatusResponse:
    """Get import job status"""
    pass
```

#### GET /api/v1/admin/import/history

```python
class ImportHistoryResponse(BaseModel):
    imports: List[ImportHistoryItem]
    total: int

@router.get("/history")
async def get_import_history(
    limit: int = 10,
    offset: int = 0,
    season: int | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ImportHistoryResponse:
    """Get import history"""
    pass
```

## Data Models

### ImportJob Model

```python
class ImportJob(Base):
    """Tracks import operations"""

    __tablename__ = "import_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    weeks: Mapped[List[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    grade_games: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending"
    )  # pending, running, completed, failed

    # Progress tracking
    current_step: Mapped[str | None] = mapped_column(String(200), nullable=True)
    games_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_games: Mapped[int] = mapped_column(Integer, default=0)

    # Statistics
    teams_created: Mapped[int] = mapped_column(Integer, default=0)
    players_created: Mapped[int] = mapped_column(Integer, default=0)
    games_created: Mapped[int] = mapped_column(Integer, default=0)
    games_updated: Mapped[int] = mapped_column(Integer, default=0)
    games_graded: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    errors: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Audit fields
    admin_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    admin_user: Mapped["User"] = relationship("User", back_populates="import_jobs")
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Import idempotency

_For any_ season and week combination, importing the same data multiple times should result in the same final database state (games may be updated but not duplicated)
**Validates: Requirements 1.3, 8.5**

### Property 2: Progress monotonicity

_For any_ import job, the games_processed count should never decrease during execution
**Validates: Requirements 4.2, 4.3**

### Property 3: Status transition validity

_For any_ import job, status transitions should follow the valid sequence: pending → running → (completed | failed)
**Validates: Requirements 4.1, 4.5**

### Property 4: Statistics consistency

_For any_ completed import job, the sum of games_created and games_updated should equal total_games
**Validates: Requirements 1.5, 4.4**

### Property 5: Grading conditional execution

_For any_ import job where grade_games is false, games_graded should remain 0
**Validates: Requirements 3.2, 3.4**

### Property 6: Week validation

_For any_ import request with specific weeks, all week numbers should be between 1 and 18
**Validates: Requirements 2.4**

### Property 7: Concurrent import prevention

_For any_ season, only one import job should be in "running" status at a time
**Validates: Requirements 5.5**

### Property 8: Error isolation

_For any_ import job where one game fails to import, other games should continue to be processed
**Validates: Requirements 3.5**

### Property 9: Existing data preservation

_For any_ game update during import, existing pick data should remain unchanged
**Validates: Requirements 8.5**

### Property 10: Admin authentication requirement

_For any_ import operation, the requesting user must have admin privileges
**Validates: Requirements 1.1, Security requirements**

## Error Handling

### Import Errors

1. **Network Errors**

   - Retry nflreadpy calls up to 3 times with exponential backoff
   - Log failures and continue with next game
   - Report network errors in final statistics

2. **Data Validation Errors**

   - Skip invalid game data
   - Log validation errors with game_id
   - Continue processing remaining games

3. **Database Errors**

   - Rollback failed transactions
   - Log database errors
   - Mark import job as failed if critical error

4. **Concurrent Import Errors**
   - Check for running imports before starting
   - Return error if import already in progress
   - Provide clear error message to user

### User-Facing Errors

- **Invalid Season**: "Season must be between 2020 and 2030"
- **Invalid Weeks**: "Week numbers must be between 1 and 18"
- **Concurrent Import**: "An import is already in progress for this season. Please wait for it to complete."
- **Network Failure**: "Failed to fetch data from NFL API. Please try again later."
- **Permission Denied**: "You must be an admin to import data."

## Testing Strategy

### Unit Tests

1. **NFLDataImportService Tests**

   - Test fetch_schedule with various season/week combinations
   - Test create_or_update_game with new and existing games
   - Test grade_game with completed games
   - Test error handling for network failures

2. **ImportProgressTracker Tests**

   - Test progress updates in Redis
   - Test progress retrieval
   - Test completion marking
   - Test failure marking

3. **API Endpoint Tests**
   - Test start_import with valid/invalid parameters
   - Test get_import_status with valid/invalid job IDs
   - Test get_import_history with filters
   - Test admin authentication

### Property-Based Tests

1. **Property 1: Import idempotency**

   - Generate random season/week combinations
   - Import twice
   - Verify same final state

2. **Property 2: Progress monotonicity**

   - Generate random import progress updates
   - Verify games_processed never decreases

3. **Property 3: Status transition validity**

   - Generate random status transitions
   - Verify only valid transitions occur

4. **Property 4: Statistics consistency**

   - Generate random import statistics
   - Verify games_created + games_updated = total_games

5. **Property 6: Week validation**
   - Generate random week numbers
   - Verify validation rejects invalid weeks

### Integration Tests

1. **End-to-End Import Test**

   - Start import with test season
   - Verify games created in database
   - Verify teams and players created
   - Verify progress tracking works

2. **Grading Integration Test**

   - Import with grading enabled
   - Verify touchdown scorers identified
   - Verify player records created

3. **Concurrent Import Test**
   - Start two imports for same season
   - Verify second import is rejected

## Performance Considerations

### Import Performance

- **Batch Processing**: Process games in batches of 10 to reduce database round-trips
- **Connection Pooling**: Use database connection pool for concurrent operations
- **Caching**: Cache team lookups to avoid repeated queries
- **Async Operations**: Use async/await for all I/O operations

### Progress Tracking

- **Redis Storage**: Store progress in Redis for fast updates and retrieval
- **Polling Interval**: Frontend polls every 2 seconds to balance responsiveness and load
- **Expiration**: Set Redis keys to expire after 24 hours

### Database Optimization

- **Indexes**: Add indexes on import_jobs.season, import_jobs.status, import_jobs.admin_user_id
- **Bulk Inserts**: Use bulk insert operations where possible
- **Transaction Management**: Use transactions for atomic operations

## Security Considerations

### Authentication and Authorization

- All import endpoints require admin authentication
- Validate user has admin role before allowing import
- Log all import operations with admin user ID

### Input Validation

- Validate season year is reasonable (2020-2030)
- Validate week numbers are valid (1-18)
- Sanitize all user inputs to prevent injection attacks

### Rate Limiting

- Limit import operations to 1 per admin per hour
- Prevent abuse of import functionality
- Return clear error message when rate limit exceeded

## Deployment Considerations

### Database Migration

```sql
-- Create import_jobs table
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season INTEGER NOT NULL,
    weeks INTEGER[],
    grade_games BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    current_step VARCHAR(200),
    games_processed INTEGER DEFAULT 0,
    total_games INTEGER DEFAULT 0,
    teams_created INTEGER DEFAULT 0,
    players_created INTEGER DEFAULT 0,
    games_created INTEGER DEFAULT 0,
    games_updated INTEGER DEFAULT 0,
    games_graded INTEGER DEFAULT 0,
    errors TEXT[],
    admin_user_id UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

-- Create indexes
CREATE INDEX idx_import_jobs_season ON import_jobs(season);
CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_jobs_admin_user_id ON import_jobs(admin_user_id);
CREATE INDEX idx_import_jobs_started_at ON import_jobs(started_at DESC);
```

### Environment Variables

```bash
# Import configuration
IMPORT_MAX_CONCURRENT_JOBS=1
IMPORT_TIMEOUT_MINUTES=30
IMPORT_RETRY_ATTEMPTS=3
IMPORT_RETRY_DELAY_SECONDS=5
```

### Background Task Configuration

- Configure Celery/ARQ worker for background tasks
- Set task timeout to 30 minutes
- Configure retry policy for failed tasks
- Set up monitoring for task queue

## Future Enhancements

1. **WebSocket Support**: Replace polling with WebSocket for real-time updates
2. **Bulk Import**: Support importing multiple seasons at once
3. **Scheduled Imports**: Allow scheduling imports for future dates
4. **Import Templates**: Save common import configurations as templates
5. **Export Functionality**: Export import history as CSV/JSON
6. **Notification System**: Send email/Slack notifications on import completion
