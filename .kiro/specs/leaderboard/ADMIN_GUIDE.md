# Leaderboard Admin Guide

## Overview

This guide provides administrators with information on managing the First6 leaderboard system, including cache management, performance monitoring, and troubleshooting common issues.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Cache Management](#cache-management)
3. [Performance Monitoring](#performance-monitoring)
4. [Database Optimization](#database-optimization)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Tasks](#maintenance-tasks)
7. [API Endpoints](#api-endpoints)

## Architecture Overview

### System Components

```
┌─────────────────┐
│   Frontend UI   │  React application with TanStack Query
│  (React/TS)     │  Polling: 30 seconds
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  API Endpoints  │  FastAPI with async handlers
│  (FastAPI)      │  /api/v1/leaderboard/*
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Leaderboard     │  Business logic layer
│ Service         │  Ranking calculations
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Cache  │ │Database│  PostgreSQL with indexes
│(Redis) │ │(Postgres)│  Async queries
└────────┘ └────────┘
```

### Data Flow

1. **Request** → API endpoint receives request
2. **Cache Check** → Service checks Redis for cached data
3. **Cache Hit** → Return cached data immediately (< 50ms)
4. **Cache Miss** → Query database, calculate rankings
5. **Cache Set** → Store results in Redis with 5-minute TTL
6. **Response** → Return data to client

### Cache Strategy

- **TTL**: 5 minutes for all leaderboard data
- **Invalidation**: On game scoring or pick override
- **Keys**: Structured by season/week/user
- **Fallback**: Database query if Redis unavailable

## Cache Management

### Cache Keys Structure

```
leaderboard:season:{season}              # Season leaderboard
leaderboard:week:{season}:{week}         # Weekly leaderboard
user:stats:{user_id}:{season}            # User statistics
```

### Viewing Cache Contents

#### Connect to Redis

```bash
# Using Docker
docker compose exec redis redis-cli

# Or connect directly
redis-cli -h localhost -p 6379
```

#### Check Cache Keys

```bash
# List all leaderboard keys
KEYS leaderboard:*

# List all user stats keys
KEYS user:stats:*

# Get specific cache entry
GET leaderboard:season:2024

# Check TTL (time to live)
TTL leaderboard:season:2024
```

### Manual Cache Invalidation

#### Clear Specific Cache

```bash
# Clear season leaderboard
redis-cli DEL leaderboard:season:2024

# Clear specific week
redis-cli DEL leaderboard:week:2024:5

# Clear user stats
redis-cli DEL user:stats:{user_id}:2024
```

#### Clear All Leaderboard Cache

```bash
# Clear all leaderboard keys
redis-cli --scan --pattern "leaderboard:*" | xargs redis-cli DEL

# Clear all user stats
redis-cli --scan --pattern "user:stats:*" | xargs redis-cli DEL

# Clear everything (use with caution!)
redis-cli FLUSHDB
```

#### Programmatic Cache Invalidation

```python
# Using Python in backend container
docker compose exec api python

from app.services.leaderboard_service import LeaderboardService
from app.db.session import get_db
import redis.asyncio as redis
import asyncio

async def clear_cache():
    cache = redis.from_url("redis://redis:6379", decode_responses=True)

    # Clear season cache
    await cache.delete("leaderboard:season:2024")

    # Clear all week caches for season
    for week in range(1, 19):
        await cache.delete(f"leaderboard:week:2024:{week}")

    await cache.aclose()

asyncio.run(clear_cache())
```

### Cache Warming

Pre-populate cache before high-traffic periods:

```python
# Warm cache script (backend/sandbox/warm_cache.py)
import asyncio
from app.services.leaderboard_service import LeaderboardService
from app.db.session import AsyncSessionLocal
import redis.asyncio as redis

async def warm_cache(season: int):
    """Pre-populate cache with leaderboard data"""
    async with AsyncSessionLocal() as db:
        cache = redis.from_url("redis://redis:6379", decode_responses=True)
        service = LeaderboardService(db, cache)

        # Warm season leaderboard
        print(f"Warming season {season} leaderboard...")
        await service.get_season_leaderboard(season)

        # Warm all weekly leaderboards
        for week in range(1, 19):
            print(f"Warming week {week}...")
            await service.get_weekly_leaderboard(season, week)

        await cache.aclose()
        print("Cache warming complete!")

# Run it
asyncio.run(warm_cache(2024))
```

Run the script:

```bash
docker compose exec api python backend/sandbox/warm_cache.py
```

### Cache Monitoring

#### Monitor Cache Hit Rate

```bash
# Get Redis stats
redis-cli INFO stats

# Look for:
# - keyspace_hits: Number of successful key lookups
# - keyspace_misses: Number of failed key lookups
# - Hit rate = hits / (hits + misses)
```

#### Monitor Cache Memory Usage

```bash
# Check memory usage
redis-cli INFO memory

# Look for:
# - used_memory_human: Total memory used
# - used_memory_peak_human: Peak memory usage
# - maxmemory: Maximum memory limit
```

#### Set Memory Limits

Edit `docker-compose.yml`:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Performance Monitoring

### Key Metrics to Track

#### Response Time Targets

- **Season Leaderboard**: < 500ms (target: 200ms with cache)
- **Weekly Leaderboard**: < 500ms (target: 200ms with cache)
- **User Stats**: < 500ms (target: 150ms with cache)
- **Export**: < 2 seconds for 100 users

#### Cache Performance Targets

- **Hit Rate**: > 80%
- **Miss Penalty**: < 2 seconds for calculation
- **TTL**: 5 minutes (adjust based on traffic)

### Monitoring Tools

#### Application Logs

```bash
# View API logs
docker compose logs -f api

# Filter for leaderboard requests
docker compose logs api | grep "leaderboard"

# Check for errors
docker compose logs api | grep "ERROR"
```

#### Database Query Performance

```sql
-- Check slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%leaderboard%'
ORDER BY mean_time DESC
LIMIT 10;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('picks', 'games', 'users')
ORDER BY idx_scan DESC;
```

#### Redis Performance

```bash
# Monitor Redis in real-time
redis-cli --stat

# Monitor specific commands
redis-cli MONITOR

# Get slow log
redis-cli SLOWLOG GET 10
```

### Performance Testing

#### Load Testing Script

```python
# backend/sandbox/load_test_leaderboard.py
import asyncio
import aiohttp
import time
from statistics import mean, median

async def test_endpoint(session, url):
    """Test single endpoint request"""
    start = time.time()
    async with session.get(url) as response:
        await response.json()
        return time.time() - start

async def load_test(base_url, endpoint, num_requests=100):
    """Run load test on endpoint"""
    async with aiohttp.ClientSession() as session:
        tasks = [
            test_endpoint(session, f"{base_url}{endpoint}")
            for _ in range(num_requests)
        ]
        times = await asyncio.gather(*tasks)

        print(f"\nLoad Test Results for {endpoint}")
        print(f"Requests: {num_requests}")
        print(f"Mean: {mean(times)*1000:.2f}ms")
        print(f"Median: {median(times)*1000:.2f}ms")
        print(f"Min: {min(times)*1000:.2f}ms")
        print(f"Max: {max(times)*1000:.2f}ms")

# Run tests
asyncio.run(load_test(
    "http://localhost:8000",
    "/api/v1/leaderboard/season/2024",
    num_requests=100
))
```

Run the test:

```bash
docker compose exec api python backend/sandbox/load_test_leaderboard.py
```

## Database Optimization

### Required Indexes

The leaderboard requires these indexes for optimal performance:

```sql
-- Index on picks for status and user filtering
CREATE INDEX IF NOT EXISTS idx_picks_status_user
ON picks(status, user_id);

-- Index on games for season and week filtering
CREATE INDEX IF NOT EXISTS idx_games_season_week
ON games(season, week_number);

-- Composite index for pick queries
CREATE INDEX IF NOT EXISTS idx_picks_game_status
ON picks(game_id, status);
```

### Verify Indexes

```sql
-- Check if indexes exist
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('picks', 'games')
ORDER BY tablename, indexname;

-- Check index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('picks', 'games')
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Query Optimization

#### Analyze Query Plans

```sql
-- Explain season leaderboard query
EXPLAIN ANALYZE
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
WHERE g.season = 2024
  AND p.status IN ('WIN', 'LOSS')
GROUP BY u.id, u.username, u.display_name
ORDER BY (ftd_points + attd_points) DESC, wins DESC;
```

Look for:

- **Seq Scan**: Should use indexes instead
- **High cost**: Indicates slow operations
- **Actual time**: Compare to estimated time

### Database Maintenance

```bash
# Vacuum and analyze tables
docker compose exec db psql -U first6_user -d first6_db -c "VACUUM ANALYZE picks;"
docker compose exec db psql -U first6_user -d first6_db -c "VACUUM ANALYZE games;"

# Reindex if needed
docker compose exec db psql -U first6_user -d first6_db -c "REINDEX TABLE picks;"
```

## Troubleshooting

### Common Issues

#### Issue: Leaderboard Not Updating

**Symptoms:**

- Rankings don't change after games are scored
- Stale data displayed to users

**Diagnosis:**

```bash
# Check if cache is being invalidated
redis-cli KEYS "leaderboard:*"

# Check last update time
redis-cli TTL leaderboard:season:2024

# Check API logs for errors
docker compose logs api | grep "leaderboard" | tail -50
```

**Solutions:**

1. Manually clear cache: `redis-cli FLUSHDB`
2. Restart leaderboard service: `docker compose restart api`
3. Check scoring service is running
4. Verify cache invalidation logic in code

#### Issue: Slow Response Times

**Symptoms:**

- Leaderboard takes > 2 seconds to load
- Timeout errors in frontend

**Diagnosis:**

```bash
# Check database query performance
docker compose exec db psql -U first6_user -d first6_db

# Run EXPLAIN ANALYZE on leaderboard queries
# Check if indexes are being used

# Check Redis performance
redis-cli --latency

# Check API response times in logs
docker compose logs api | grep "leaderboard"
```

**Solutions:**

1. Verify indexes exist: See [Database Optimization](#database-optimization)
2. Increase cache TTL to reduce database load
3. Add more Redis memory
4. Optimize database queries
5. Consider read replicas for high traffic

#### Issue: Incorrect Rankings

**Symptoms:**

- Users ranked in wrong order
- Tie-breaking not working correctly
- Points don't match picks

**Diagnosis:**

```bash
# Clear cache to force recalculation
redis-cli FLUSHDB

# Check raw data in database
docker compose exec db psql -U first6_user -d first6_db

# Query user picks directly
SELECT
    u.username,
    p.status,
    p.is_ftd,
    p.is_attd,
    g.season,
    g.week_number
FROM picks p
JOIN users u ON p.user_id = u.id
JOIN games g ON p.game_id = g.id
WHERE g.season = 2024
  AND p.status IN ('WIN', 'LOSS')
ORDER BY u.username, g.week_number;
```

**Solutions:**

1. Clear cache and recalculate
2. Check for data integrity issues in picks table
3. Verify scoring logic is correct
4. Run property-based tests to validate ranking logic
5. Check for timezone issues in game dates

#### Issue: Cache Memory Full

**Symptoms:**

- Redis out of memory errors
- Cache eviction happening too frequently
- Performance degradation

**Diagnosis:**

```bash
# Check Redis memory usage
redis-cli INFO memory

# Check number of keys
redis-cli DBSIZE

# Check eviction stats
redis-cli INFO stats | grep evicted
```

**Solutions:**

1. Increase Redis memory limit in docker-compose.yml
2. Reduce cache TTL to expire data faster
3. Implement cache key cleanup script
4. Use more aggressive eviction policy (allkeys-lru)

#### Issue: Export Fails

**Symptoms:**

- Export button doesn't work
- File download fails
- Incomplete data in export

**Diagnosis:**

```bash
# Check API logs for export errors
docker compose logs api | grep "export"

# Test export endpoint directly
curl "http://localhost:8000/api/v1/leaderboard/export/2024?format=csv"

# Check file size limits
docker compose exec api python -c "import sys; print(sys.maxsize)"
```

**Solutions:**

1. Check for large datasets (> 1000 users)
2. Implement pagination for large exports
3. Increase request timeout limits
4. Check disk space on server
5. Verify CSV generation logic

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
# In backend/app/core/config.py
class Settings(BaseSettings):
    DEBUG: bool = True  # Enable debug mode
    LOG_LEVEL: str = "DEBUG"  # Detailed logging
```

Restart the API:

```bash
docker compose restart api
```

### Health Checks

#### API Health Check

```bash
# Check API is responding
curl http://localhost:8000/health

# Check leaderboard endpoint
curl http://localhost:8000/api/v1/leaderboard/season/2024
```

#### Redis Health Check

```bash
# Ping Redis
redis-cli PING

# Should return: PONG
```

#### Database Health Check

```bash
# Connect to database
docker compose exec db psql -U first6_user -d first6_db -c "SELECT 1;"

# Should return: 1
```

## Maintenance Tasks

### Daily Tasks

1. **Monitor Cache Hit Rate**

   ```bash
   redis-cli INFO stats | grep keyspace
   ```

   Target: > 80% hit rate

2. **Check Error Logs**

   ```bash
   docker compose logs api | grep "ERROR" | tail -20
   ```

3. **Verify Leaderboard Updates**
   - Check that rankings update after games are scored
   - Verify cache invalidation is working

### Weekly Tasks

1. **Database Maintenance**

   ```bash
   docker compose exec db psql -U first6_user -d first6_db -c "VACUUM ANALYZE;"
   ```

2. **Review Performance Metrics**

   - Check average response times
   - Review slow query log
   - Monitor database size growth

3. **Cache Cleanup**
   ```bash
   # Remove stale keys (optional)
   redis-cli --scan --pattern "user:stats:*" | xargs redis-cli DEL
   ```

### Monthly Tasks

1. **Performance Testing**

   - Run load tests
   - Verify response times under load
   - Test with realistic user counts

2. **Index Maintenance**

   ```bash
   docker compose exec db psql -U first6_user -d first6_db -c "REINDEX DATABASE first6_db;"
   ```

3. **Backup Verification**
   - Verify database backups are working
   - Test restore procedure
   - Document any issues

### Season Start Tasks

1. **Cache Warming**

   - Pre-populate cache for new season
   - Run warm_cache.py script

2. **Index Verification**

   - Verify all indexes exist
   - Check index performance

3. **Capacity Planning**
   - Estimate user growth
   - Plan Redis memory allocation
   - Review database size projections

## API Endpoints

### Endpoint Reference

#### GET /api/v1/leaderboard/season/{season}

Get season-long leaderboard.

**Parameters:**

- `season` (path): Season year (2020-2025)

**Response:** 200 OK

```json
[
  {
    "rank": 1,
    "user_id": "uuid",
    "username": "string",
    "display_name": "string",
    "total_points": 45,
    "ftd_points": 36,
    "attd_points": 9,
    "wins": 15,
    "losses": 3,
    "pending": 2,
    "win_percentage": 83.33,
    "is_tied": false
  }
]
```

**Errors:**

- 400: Invalid season
- 503: Service unavailable

#### GET /api/v1/leaderboard/week/{season}/{week}

Get weekly leaderboard.

**Parameters:**

- `season` (path): Season year
- `week` (path): Week number (1-18)

**Response:** Same as season endpoint

**Errors:**

- 400: Invalid season or week
- 503: Service unavailable

#### GET /api/v1/leaderboard/user/{user_id}/stats

Get detailed user statistics.

**Parameters:**

- `user_id` (path): User UUID
- `season` (query, optional): Season filter

**Response:** 200 OK

```json
{
  "user_id": "uuid",
  "username": "string",
  "display_name": "string",
  "total_points": 45,
  "total_wins": 15,
  "total_losses": 3,
  "total_pending": 2,
  "win_percentage": 83.33,
  "current_rank": 1,
  "ftd_wins": 12,
  "ftd_losses": 2,
  "ftd_points": 36,
  "ftd_percentage": 85.71,
  "attd_wins": 9,
  "attd_losses": 1,
  "attd_points": 9,
  "attd_percentage": 90.0,
  "best_week": {...},
  "worst_week": {...},
  "weekly_breakdown": [...],
  "current_streak": {...},
  "longest_win_streak": 7,
  "longest_loss_streak": 2
}
```

**Errors:**

- 400: Invalid season
- 404: User not found
- 503: Service unavailable

#### GET /api/v1/leaderboard/export/{season}

Export leaderboard data.

**Parameters:**

- `season` (path): Season year
- `week` (query, optional): Week number
- `format` (query): "csv" or "json" (default: "csv")

**Response:** 200 OK (file download)

**Errors:**

- 400: Invalid parameters
- 503: Service unavailable

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/first6_db

# Cache Settings
CACHE_TTL=300  # 5 minutes in seconds
```

### Tuning Parameters

#### Cache TTL

Adjust based on traffic patterns:

```python
# In leaderboard_service.py
CACHE_TTL = 300  # 5 minutes (default)
# Increase for lower traffic: 600 (10 minutes)
# Decrease for high traffic: 180 (3 minutes)
```

#### Polling Frequency

Adjust frontend polling:

```typescript
// In frontend/src/hooks/useLeaderboardUpdates.ts
const POLL_INTERVAL = 30000; // 30 seconds (default)
// Increase for lower traffic: 60000 (1 minute)
// Decrease for high traffic: 15000 (15 seconds)
```

## Security Considerations

### Rate Limiting

Consider implementing rate limiting for export endpoints:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/export/{season}")
@limiter.limit("10/minute")  # 10 exports per minute
async def export_leaderboard(...):
    ...
```

### Access Control

Ensure proper authentication:

```python
from app.api.dependencies import get_current_user

@router.get("/season/{season}")
async def get_season_leaderboard(
    ...,
    current_user = Depends(get_current_user)  # Require auth
):
    ...
```

## Support and Escalation

### When to Escalate

Escalate to development team if:

- Cache invalidation consistently fails
- Database queries consistently slow (> 5 seconds)
- Memory leaks detected
- Data integrity issues found
- Security vulnerabilities discovered

### Logging and Reporting

When reporting issues, include:

1. Error messages from logs
2. Steps to reproduce
3. Affected endpoints
4. Number of users impacted
5. Cache and database metrics
6. Recent changes or deployments

---

**Last Updated**: December 2024
**Version**: 1.0
**Maintainer**: First6 Development Team
