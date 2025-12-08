# Leaderboard Design Document

## Overview

The Leaderboard feature provides a competitive ranking system for First6 users. It calculates and displays user rankings based on their touchdown prediction performance, supporting both season-long and weekly views. The system is designed for real-time updates, efficient caching, and responsive display across devices.

**Key Design Goals:**

- Fast leaderboard calculation (< 500ms response time)
- Real-time updates when games are scored
- Efficient caching to minimize database load
- Responsive UI for mobile and desktop
- Extensible for future features (badges, achievements, etc.)

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend UI   │
│  (React/TS)     │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  API Endpoints  │
│  (FastAPI)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Leaderboard     │
│ Service         │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Cache  │ │Database│
│(Redis) │ │(Postgres)│
└────────┘ └────────┘
```

### Component Interaction Flow

1. **User Request** → Frontend requests leaderboard data
2. **API Layer** → Validates request, checks cache
3. **Cache Hit** → Returns cached data immediately
4. **Cache Miss** → Service calculates rankings from database
5. **Response** → Returns ranked data, updates cache
6. **Game Scored** → Invalidates cache, triggers recalculation

## Components and Interfaces

### 1. LeaderboardService

**Responsibility:** Calculate user rankings and statistics

**Key Methods:**

```python
class LeaderboardService:
    async def get_season_leaderboard(
        self,
        season: int
    ) -> List[LeaderboardEntry]

    async def get_weekly_leaderboard(
        self,
        season: int,
        week: int
    ) -> List[LeaderboardEntry]

    async def get_user_stats(
        self,
        user_id: UUID
    ) -> UserStats

    async def calculate_rankings(
        self,
        picks: List[Pick]
    ) -> List[LeaderboardEntry]

    async def invalidate_cache(
        self,
        season: int,
        week: Optional[int] = None
    ) -> None
```

**Dependencies:**

- Database session (AsyncSession)
- Cache service (Redis)
- Pick model
- User model

### 2. API Endpoints

**Endpoints:**

```python
GET /api/v1/leaderboard/season/{season}
    Query params: None
    Response: List[LeaderboardEntry]

GET /api/v1/leaderboard/week/{season}/{week}
    Query params: None
    Response: List[LeaderboardEntry]

GET /api/v1/leaderboard/user/{user_id}/stats
    Query params: season (optional)
    Response: UserStats

GET /api/v1/leaderboard/export/{season}
    Query params: week (optional), format (csv/json)
    Response: File download
```

### 3. Frontend Components

**LeaderboardPage**

- Main container component
- Manages tab state (Season/Weekly)
- Handles week selection
- Coordinates data fetching

**LeaderboardTable**

- Displays ranked user data
- Handles sorting
- Highlights current user
- Responsive column display

**UserStatsModal**

- Shows detailed user statistics
- Displays pick history
- Shows performance trends

**WeekSelector**

- Dropdown for week selection
- Shows current week by default
- Handles week navigation

## Data Models

### LeaderboardEntry

```python
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    display_name: str
    total_points: int
    ftd_points: int
    attd_points: int
    wins: int
    losses: int
    pending: int
    win_percentage: float
    is_tied: bool  # True if tied with previous rank
```

### UserStats

```python
class UserStats(BaseModel):
    user_id: UUID
    username: str
    display_name: str

    # Overall stats
    total_points: int
    total_wins: int
    total_losses: int
    total_pending: int
    win_percentage: float
    current_rank: int

    # FTD stats
    ftd_wins: int
    ftd_losses: int
    ftd_points: int
    ftd_percentage: float

    # ATTD stats
    attd_wins: int
    attd_losses: int
    attd_points: int
    attd_percentage: float

    # Weekly performance
    best_week: Optional[WeekPerformance]
    worst_week: Optional[WeekPerformance]
    weekly_breakdown: List[WeekPerformance]

    # Streaks
    current_streak: Streak
    longest_win_streak: int
    longest_loss_streak: int
```

### WeekPerformance

```python
class WeekPerformance(BaseModel):
    week: int
    points: int
    wins: int
    losses: int
    rank: int
```

### Streak

```python
class Streak(BaseModel):
    type: Literal["win", "loss", "none"]
    count: int
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property Reflection

After reviewing all testable properties from the prework, I've identified the following consolidations to eliminate redundancy:

**Redundancies Identified:**

- Properties 2.1 and 2.4 both test week filtering - can be combined
- Properties 2.1 and 6.1 are identical - remove duplicate
- Property 1.2 and 2.2 test field presence - can be combined into one comprehensive property
- Properties 3.3 and 3.4 (best/worst week) can be combined into a single min/max property

**Consolidated Properties:**
The following properties provide unique validation value without redundancy.

### Correctness Properties

**Property 1: Ranking order correctness**
_For any_ set of users with point totals, when calculating rankings, each user's rank should correspond to their position in descending order by total points
**Validates: Requirements 1.1**

**Property 2: Tie-breaking by wins**
_For any_ two users with equal total points, the user with more wins should be ranked higher
**Validates: Requirements 1.3**

**Property 3: Tied rank assignment**
_For any_ two users with equal total points and equal wins, both users should receive the same rank number
**Validates: Requirements 1.4**

**Property 4: Win percentage calculation**
_For any_ user with graded picks, the win percentage should equal (wins / total_graded_picks) \* 100
**Validates: Requirements 1.5**

**Property 5: Week filtering correctness**
_For any_ week selection, the leaderboard should only include picks from games in that specific week, and no picks from other weeks should be included
**Validates: Requirements 2.1, 2.4, 6.1**

**Property 6: Required fields presence**
_For any_ leaderboard entry (season or weekly), the output should contain rank, username, total points, FTD points, ATTD points, wins, losses, and win percentage
**Validates: Requirements 1.2, 2.2**

**Property 7: Tie-breaking consistency**
_For any_ set of users with tied points, the tie-breaking rules (more wins ranks higher, equal wins results in tied rank) should apply identically in both season and weekly leaderboards
**Validates: Requirements 2.5**

**Property 8: Best and worst week identification**
_For any_ user with multiple weeks of graded picks, the best week should be the week with maximum points and the worst week should be the week with minimum points among weeks with graded picks
**Validates: Requirements 3.3, 3.4**

**Property 9: Streak calculation**
_For any_ sequence of graded picks ordered by date, the current streak should count consecutive wins or losses starting from the most recent pick
**Validates: Requirements 3.5**

**Property 10: User stats field presence**
_For any_ user, the statistics output should contain total points, FTD record, ATTD record, best week, worst week, and current streak
**Validates: Requirements 3.2**

**Property 11: Batch update efficiency**
_For any_ set of multiple games scored simultaneously, the system should recalculate rankings exactly once after all updates are processed
**Validates: Requirements 5.4**

**Property 12: Cache invalidation on score**
_For any_ game that is scored or pick that is overridden, the leaderboard cache should be invalidated
**Validates: Requirements 5.3, 8.3**

**Property 13: Cache hit when unchanged**
_For any_ leaderboard request when no picks have been scored since the last request, the system should serve data from cache without recalculating
**Validates: Requirements 8.2**

**Property 14: Sort order preservation with tie-breaking**
_For any_ column sort operation, when two users have equal values in the sorted column, the tie-breaking rules (points, then wins) should still apply
**Validates: Requirements 6.5**

**Property 15: Export column matching**
_For any_ leaderboard export, the CSV should include exactly the columns that are visible in the current view
**Validates: Requirements 10.2**

**Property 16: Export filename generation**
_For any_ export operation, the filename should include the season year, and if weekly data, should also include the week number
**Validates: Requirements 10.3, 10.4**

## Error Handling

### Error Scenarios

1. **No Graded Picks**

   - Return empty leaderboard with appropriate message
   - HTTP 200 with empty array and metadata

2. **Invalid Week Number**

   - Validate week is between 1-18
   - Return HTTP 400 with error message

3. **Invalid Season**

   - Validate season is reasonable (2020-2030)
   - Return HTTP 400 with error message

4. **User Not Found**

   - Return HTTP 404 for user stats endpoint
   - Include helpful error message

5. **Database Connection Error**

   - Return cached data if available
   - Return HTTP 503 if no cache available
   - Log error for admin investigation

6. **Cache Connection Error**

   - Fall back to database calculation
   - Log warning for admin investigation
   - Continue serving requests

7. **Calculation Timeout**
   - Return HTTP 504 if calculation exceeds 5 seconds
   - Log error with user count and query details
   - Suggest optimization if recurring

### Error Response Format

```python
{
    "error": {
        "code": "INVALID_WEEK",
        "message": "Week number must be between 1 and 18",
        "details": {
            "provided_week": 25,
            "valid_range": "1-18"
        }
    }
}
```

## Testing Strategy

### Unit Tests

**LeaderboardService Tests:**

- Test ranking calculation with various point distributions
- Test tie-breaking logic (equal points, equal wins)
- Test week filtering
- Test user stats calculation
- Test cache invalidation logic
- Test empty state handling

**API Endpoint Tests:**

- Test successful responses
- Test error responses (invalid week, invalid season)
- Test authentication/authorization
- Test query parameter validation

### Property-Based Tests

**Test Framework:** Hypothesis (Python)
**Iterations:** 100+ per property

**Property Test 1: Ranking Order**

- Generate random users with random points
- Calculate rankings
- Verify descending order by points

**Property Test 2: Tie-Breaking**

- Generate users with tied points but different wins
- Verify ranking by wins

**Property Test 3: Win Percentage**

- Generate random win/loss combinations
- Verify calculation accuracy

**Property Test 4: Week Filtering**

- Generate picks across multiple weeks
- Filter to specific week
- Verify no cross-week contamination

**Property Test 5: Streak Calculation**

- Generate random win/loss sequences
- Verify streak count from most recent

**Property Test 6: Cache Behavior**

- Generate score events
- Verify cache invalidation
- Verify cache hits when unchanged

**Property Test 7: Export Consistency**

- Generate leaderboard data
- Export to CSV
- Verify data matches source

### Integration Tests

- Test full leaderboard flow (picks → scoring → rankings)
- Test real-time update flow
- Test cache invalidation on game scoring
- Test export functionality end-to-end

### Performance Tests

- Test leaderboard calculation with 100+ users
- Test cache hit rate
- Test response time under load
- Test concurrent request handling

## Implementation Notes

### Ranking Algorithm

```python
def calculate_rankings(picks: List[Pick]) -> List[LeaderboardEntry]:
    # 1. Group picks by user
    user_picks = group_by_user(picks)

    # 2. Calculate points for each user
    user_scores = []
    for user_id, picks in user_picks.items():
        ftd_points = sum(3 for p in picks if p.status == WIN and p.is_ftd)
        attd_points = sum(1 for p in picks if p.status == WIN and p.is_attd)
        wins = sum(1 for p in picks if p.status == WIN)
        losses = sum(1 for p in picks if p.status == LOSS)

        user_scores.append({
            'user_id': user_id,
            'total_points': ftd_points + attd_points,
            'ftd_points': ftd_points,
            'attd_points': attd_points,
            'wins': wins,
            'losses': losses
        })

    # 3. Sort by points (desc), then wins (desc)
    user_scores.sort(key=lambda x: (-x['total_points'], -x['wins']))

    # 4. Assign ranks with tie handling
    rankings = []
    current_rank = 1
    for i, score in enumerate(user_scores):
        # Check if tied with previous
        if i > 0:
            prev = user_scores[i-1]
            if (score['total_points'] == prev['total_points'] and
                score['wins'] == prev['wins']):
                # Tied - use same rank
                rank = rankings[-1]['rank']
            else:
                # Not tied - use position
                rank = i + 1
        else:
            rank = 1

        rankings.append({
            **score,
            'rank': rank,
            'is_tied': i > 0 and rank == rankings[-1]['rank']
        })

    return rankings
```

### Caching Strategy

**Cache Keys:**

```
leaderboard:season:{season}
leaderboard:week:{season}:{week}
user:stats:{user_id}:{season}
```

**Cache TTL:**

- Season leaderboard: 5 minutes
- Weekly leaderboard: 5 minutes
- User stats: 5 minutes

**Invalidation Triggers:**

- Game scored
- Pick overridden
- Manual cache clear (admin)

**Cache Warming:**

- Pre-calculate current week on Sunday mornings
- Pre-calculate season leaderboard daily

### Database Queries

**Optimizations:**

- Index on (pick.status, pick.user_id)
- Index on (game.week_number, game.season)
- Use database aggregation for counting
- Limit result set to active users

**Query Example:**

```sql
SELECT
    u.id,
    u.username,
    u.display_name,
    SUM(CASE WHEN p.status = 'WIN' AND p.is_ftd THEN 3 ELSE 0 END) as ftd_points,
    SUM(CASE WHEN p.status = 'WIN' AND p.is_attd THEN 1 ELSE 0 END) as attd_points,
    SUM(CASE WHEN p.status = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN p.status = 'LOSS' THEN 1 ELSE 0 END) as losses
FROM users u
LEFT JOIN picks p ON u.id = p.user_id
LEFT JOIN games g ON p.game_id = g.id
WHERE g.season = :season
  AND p.status IN ('WIN', 'LOSS')
GROUP BY u.id, u.username, u.display_name
ORDER BY (ftd_points + attd_points) DESC, wins DESC
```

### Frontend State Management

**React Query Keys:**

```typescript
["leaderboard", "season", season][("leaderboard", "week", season, week)][
  ("user", "stats", userId, season)
];
```

**Refetch Triggers:**

- On window focus (stale data check)
- Every 30 seconds (polling for updates)
- Manual refresh button
- After game scoring event (WebSocket)

**Optimistic Updates:**

- Update cache immediately on pick submission
- Revert on error
- Show loading state during recalculation

## Deployment Considerations

### Database Migrations

**New Indexes:**

```sql
CREATE INDEX idx_picks_status_user ON picks(status, user_id);
CREATE INDEX idx_games_season_week ON games(season, week_number);
```

**No Schema Changes Required:**

- All data exists in current tables
- Leaderboard is calculated, not stored

### API Versioning

- Endpoints under `/api/v1/leaderboard/`
- Maintain backward compatibility
- Version bump if breaking changes needed

### Monitoring

**Metrics to Track:**

- Leaderboard calculation time
- Cache hit rate
- API response time
- Error rate
- Concurrent users viewing leaderboard

**Alerts:**

- Calculation time > 2 seconds
- Cache hit rate < 80%
- Error rate > 1%
- Response time > 500ms

### Rollback Plan

1. **If leaderboard breaks:**

   - Disable leaderboard endpoints
   - Show maintenance message
   - Users can still submit picks

2. **If performance degrades:**

   - Increase cache TTL
   - Reduce polling frequency
   - Add rate limiting

3. **If data is incorrect:**
   - Clear cache
   - Recalculate from source
   - Investigate calculation bug

## Future Enhancements

### Phase 2 Features

1. **Historical Trends**

   - Week-over-week performance graphs
   - Season comparison charts
   - Performance heatmaps

2. **Achievements/Badges**

   - Perfect week badge
   - Win streak badges
   - Milestone badges (100 picks, etc.)

3. **Social Features**

   - Share leaderboard position
   - Challenge friends
   - Trash talk comments

4. **Advanced Stats**

   - Player pick frequency
   - Team pick distribution
   - Success rate by game type (TNF, SNF, MNF)

5. **Predictions**
   - Projected final standings
   - Win probability for upcoming picks
   - Historical performance trends

### Extensibility Points

- Pluggable ranking algorithms
- Custom scoring rules per league
- Multiple leaderboard types (FTD-only, ATTD-only)
- Private leagues with separate leaderboards
