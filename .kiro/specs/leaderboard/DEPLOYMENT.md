# Leaderboard Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the leaderboard feature to production. Since First6 is a self-hosted application, this guide assumes you're deploying to your own infrastructure using Docker Compose.

## Pre-Deployment Checklist

### Code Review

- [ ] All property-based tests passing (16 tests)
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] API endpoints tested manually
- [ ] Frontend UI tested on desktop and mobile
- [ ] Export functionality verified
- [ ] Real-time updates working
- [ ] Cache invalidation working correctly

### Documentation

- [ ] API documentation updated in Swagger
- [ ] User guide created and reviewed
- [ ] Admin guide created and reviewed
- [ ] Deployment guide reviewed (this document)

### Infrastructure

- [ ] Database backup completed
- [ ] Redis available and configured
- [ ] Sufficient disk space (check database size)
- [ ] Sufficient memory (Redis + PostgreSQL)
- [ ] Network connectivity verified

### Configuration

- [ ] Environment variables set correctly
- [ ] Redis URL configured
- [ ] Database URL configured
- [ ] Cache TTL configured appropriately
- [ ] CORS settings verified

## Deployment Steps

### Step 1: Backup Current System

**CRITICAL: Always backup before deploying**

```bash
# Backup database
docker compose exec db pg_dump -U first6_user first6_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup environment configuration
cp infra/docker/dev.env infra/docker/dev.env.backup

# Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup
```

### Step 2: Run Database Migrations

The leaderboard feature requires database indexes for optimal performance.

```bash
# Check current migration status
docker compose exec api alembic current

# View pending migrations
docker compose exec api alembic history

# Run migrations
docker compose exec api alembic upgrade head

# Verify migrations applied
docker compose exec api alembic current
```

**Expected migrations:**

- Index on `picks(status, user_id)`
- Index on `games(season, week_number)`

### Step 3: Verify Database Indexes

```bash
# Connect to database
docker compose exec db psql -U first6_user -d first6_db

# Check indexes exist
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('picks', 'games')
ORDER BY tablename, indexname;

# Expected indexes:
# - idx_picks_status_user
# - idx_games_season_week
# - idx_picks_game_status (if exists)

# Exit psql
\q
```

### Step 4: Deploy Backend Code

```bash
# Pull latest code (if using git)
git pull origin main

# Rebuild backend container
docker compose build api

# Restart backend service
docker compose up -d api

# Check logs for errors
docker compose logs -f api

# Look for:
# - "Application startup complete"
# - No ERROR messages
# - Successful database connection
```

### Step 5: Deploy Frontend Code

```bash
# Rebuild frontend container
docker compose build web

# Restart frontend service
docker compose up -d web

# Check logs for errors
docker compose logs -f web

# Look for:
# - Successful build
# - No compilation errors
# - Server running on expected port
```

### Step 6: Verify Redis Connection

```bash
# Check Redis is running
docker compose ps redis

# Test Redis connection
docker compose exec redis redis-cli PING

# Should return: PONG

# Check Redis memory
docker compose exec redis redis-cli INFO memory

# Verify no errors in logs
docker compose logs redis
```

### Step 7: Warm Cache (Optional but Recommended)

Pre-populate cache for better initial performance:

```bash
# Create cache warming script if not exists
cat > backend/sandbox/warm_cache.py << 'EOF'
import asyncio
from app.services.leaderboard_service import LeaderboardService
from app.db.session import AsyncSessionLocal
import redis.asyncio as redis
from app.core.config import settings

async def warm_cache(season: int):
    """Pre-populate cache with leaderboard data"""
    async with AsyncSessionLocal() as db:
        cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
        service = LeaderboardService(db, cache)

        try:
            # Warm season leaderboard
            print(f"Warming season {season} leaderboard...")
            await service.get_season_leaderboard(season)

            # Warm all weekly leaderboards
            for week in range(1, 19):
                print(f"Warming week {week}...")
                try:
                    await service.get_weekly_leaderboard(season, week)
                except Exception as e:
                    print(f"  Week {week} skipped: {e}")

            print("Cache warming complete!")
        finally:
            await cache.aclose()

if __name__ == "__main__":
    import sys
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    asyncio.run(warm_cache(season))
EOF

# Run cache warming
docker compose exec api python backend/sandbox/warm_cache.py 2024
```

### Step 8: Verify API Endpoints

Test each endpoint to ensure they're working:

```bash
# Test season leaderboard
curl http://localhost:8000/api/v1/leaderboard/season/2024

# Test weekly leaderboard
curl http://localhost:8000/api/v1/leaderboard/week/2024/1

# Test user stats (replace with actual user_id)
curl http://localhost:8000/api/v1/leaderboard/user/{user_id}/stats

# Test export
curl "http://localhost:8000/api/v1/leaderboard/export/2024?format=csv" -o test_export.csv

# Verify export file
head test_export.csv
```

**Expected responses:**

- 200 OK status codes
- Valid JSON responses
- No error messages
- Data matches expected format

### Step 9: Verify Frontend

```bash
# Open browser to frontend
# Navigate to: http://localhost:3000/standings

# Manual verification checklist:
# - [ ] Leaderboard loads without errors
# - [ ] Season tab displays data
# - [ ] Weekly tab displays data
# - [ ] Week selector works
# - [ ] User stats modal opens
# - [ ] Export button works
# - [ ] Current user is highlighted
# - [ ] Sorting works
# - [ ] Mobile responsive (test on phone or resize browser)
# - [ ] Real-time updates work (wait 30 seconds)
```

### Step 10: Monitor Performance

```bash
# Monitor API response times
docker compose logs -f api | grep "leaderboard"

# Monitor Redis cache hits
docker compose exec redis redis-cli INFO stats | grep keyspace

# Monitor database queries
docker compose exec db psql -U first6_user -d first6_db -c "
SELECT
    query,
    calls,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%leaderboard%'
ORDER BY mean_time DESC
LIMIT 5;
"

# Check system resources
docker stats
```

**Performance targets:**

- API response time: < 500ms
- Cache hit rate: > 80%
- Database query time: < 2 seconds
- Memory usage: Stable (no leaks)

### Step 11: Run Smoke Tests

```bash
# Run integration tests
docker compose exec api pytest backend/tests/test_leaderboard_integration.py -v

# Run property-based tests
docker compose exec api pytest backend/tests/test_leaderboard_properties.py -v

# Run API tests
docker compose exec api pytest backend/tests/test_leaderboard_api.py -v

# All tests should pass
```

### Step 12: Enable Monitoring

Set up monitoring for production:

```bash
# Check logs for errors every hour
# Set up cron job or monitoring tool

# Monitor cache hit rate
# Set up alert if < 80%

# Monitor API response times
# Set up alert if > 1 second

# Monitor database size
# Set up alert if growing too fast
```

## Post-Deployment Verification

### Functional Testing

1. **Season Leaderboard**

   - [ ] Loads within 500ms
   - [ ] Shows all users
   - [ ] Correct ranking order
   - [ ] Tie-breaking works
   - [ ] Points calculated correctly

2. **Weekly Leaderboard**

   - [ ] Week selector works
   - [ ] Shows correct week data
   - [ ] Filters properly
   - [ ] Empty states work

3. **User Statistics**

   - [ ] Modal opens on username click
   - [ ] All stats displayed
   - [ ] Best/worst week correct
   - [ ] Streaks calculated correctly
   - [ ] Chart displays properly

4. **Export**

   - [ ] CSV export works
   - [ ] JSON export works
   - [ ] Filename correct
   - [ ] Data complete

5. **Real-time Updates**
   - [ ] Polling works (30 seconds)
   - [ ] Manual refresh works
   - [ ] Cache invalidation works
   - [ ] Updates after scoring

### Performance Testing

Run load test to verify performance under load:

```bash
# Create load test script
cat > backend/sandbox/load_test.py << 'EOF'
import asyncio
import aiohttp
import time
from statistics import mean, median

async def test_request(session, url):
    start = time.time()
    async with session.get(url) as response:
        await response.json()
        return time.time() - start

async def load_test(url, num_requests=100):
    async with aiohttp.ClientSession() as session:
        tasks = [test_request(session, url) for _ in range(num_requests)]
        times = await asyncio.gather(*tasks)

        print(f"\nLoad Test: {num_requests} requests")
        print(f"Mean: {mean(times)*1000:.2f}ms")
        print(f"Median: {median(times)*1000:.2f}ms")
        print(f"Min: {min(times)*1000:.2f}ms")
        print(f"Max: {max(times)*1000:.2f}ms")
        print(f"95th percentile: {sorted(times)[int(len(times)*0.95)]*1000:.2f}ms")

asyncio.run(load_test("http://localhost:8000/api/v1/leaderboard/season/2024"))
EOF

# Run load test
docker compose exec api python backend/sandbox/load_test.py
```

**Performance targets:**

- Mean: < 200ms (with cache)
- 95th percentile: < 500ms
- Max: < 2 seconds

### User Acceptance Testing

Have a few users test the feature:

1. View season leaderboard
2. View weekly leaderboard
3. Click on usernames to see stats
4. Export data
5. Test on mobile device
6. Verify their own stats are correct

## Rollback Procedure

If issues are found after deployment:

### Quick Rollback

```bash
# Stop services
docker compose down

# Restore database backup
docker compose up -d db
cat backup_YYYYMMDD_HHMMSS.sql | docker compose exec -T db psql -U first6_user first6_db

# Restore configuration
cp infra/docker/dev.env.backup infra/docker/dev.env
cp docker-compose.yml.backup docker-compose.yml

# Restart services
docker compose up -d

# Verify system is working
curl http://localhost:8000/health
```

### Rollback Migrations

```bash
# Check current migration
docker compose exec api alembic current

# Downgrade one migration
docker compose exec api alembic downgrade -1

# Or downgrade to specific revision
docker compose exec api alembic downgrade <revision_id>

# Verify
docker compose exec api alembic current
```

### Clear Cache

If cache is causing issues:

```bash
# Clear all cache
docker compose exec redis redis-cli FLUSHDB

# Or clear specific keys
docker compose exec redis redis-cli --scan --pattern "leaderboard:*" | xargs docker compose exec redis redis-cli DEL
```

## Troubleshooting

### Issue: Migrations Fail

```bash
# Check migration status
docker compose exec api alembic current

# Check for conflicts
docker compose exec api alembic history

# Try manual migration
docker compose exec db psql -U first6_user -d first6_db

# Run index creation manually
CREATE INDEX IF NOT EXISTS idx_picks_status_user ON picks(status, user_id);
CREATE INDEX IF NOT EXISTS idx_games_season_week ON games(season, week_number);
```

### Issue: API Returns 503 Errors

```bash
# Check database connection
docker compose exec db psql -U first6_user -d first6_db -c "SELECT 1;"

# Check Redis connection
docker compose exec redis redis-cli PING

# Check API logs
docker compose logs api | tail -50

# Restart services
docker compose restart api
```

### Issue: Frontend Not Loading

```bash
# Check frontend logs
docker compose logs web

# Rebuild frontend
docker compose build web
docker compose up -d web

# Check nginx logs
docker compose logs nginx

# Verify API is accessible
curl http://localhost:8000/api/v1/leaderboard/season/2024
```

### Issue: Cache Not Working

```bash
# Check Redis is running
docker compose ps redis

# Check Redis logs
docker compose logs redis

# Test Redis connection
docker compose exec redis redis-cli PING

# Check cache keys
docker compose exec redis redis-cli KEYS "*"

# Clear cache and retry
docker compose exec redis redis-cli FLUSHDB
```

### Issue: Slow Performance

```bash
# Check database indexes
docker compose exec db psql -U first6_user -d first6_db -c "
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('picks', 'games');"

# Check cache hit rate
docker compose exec redis redis-cli INFO stats | grep keyspace

# Check query performance
docker compose exec db psql -U first6_user -d first6_db -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE query LIKE '%leaderboard%'
ORDER BY mean_time DESC
LIMIT 5;"

# Warm cache
docker compose exec api python backend/sandbox/warm_cache.py 2024
```

## Monitoring and Maintenance

### Daily Checks

```bash
# Check error logs
docker compose logs api | grep ERROR

# Check cache hit rate
docker compose exec redis redis-cli INFO stats | grep keyspace

# Check system resources
docker stats --no-stream
```

### Weekly Maintenance

```bash
# Vacuum database
docker compose exec db psql -U first6_user -d first6_db -c "VACUUM ANALYZE;"

# Check database size
docker compose exec db psql -U first6_user -d first6_db -c "
SELECT pg_size_pretty(pg_database_size('first6_db'));"

# Review slow queries
docker compose exec db psql -U first6_user -d first6_db -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"
```

### Monthly Tasks

```bash
# Full database backup
docker compose exec db pg_dump -U first6_user first6_db | gzip > backup_monthly_$(date +%Y%m%d).sql.gz

# Reindex database
docker compose exec db psql -U first6_user -d first6_db -c "REINDEX DATABASE first6_db;"

# Review and archive old logs
docker compose logs > logs_$(date +%Y%m%d).txt
```

## Success Criteria

Deployment is successful when:

- [ ] All migrations applied successfully
- [ ] All tests passing
- [ ] API endpoints responding < 500ms
- [ ] Frontend loads without errors
- [ ] Cache hit rate > 80%
- [ ] Export functionality works
- [ ] Real-time updates working
- [ ] Mobile responsive
- [ ] No errors in logs
- [ ] User acceptance testing passed
- [ ] Performance targets met
- [ ] Monitoring enabled
- [ ] Documentation complete

## Support

For issues during deployment:

1. Check logs: `docker compose logs -f`
2. Review this deployment guide
3. Check admin guide for troubleshooting
4. Review error messages carefully
5. Test in isolation (API, frontend, database, cache)
6. Consider rollback if critical issues found

## Deployment Checklist Summary

```
Pre-Deployment:
[ ] Code review complete
[ ] All tests passing
[ ] Documentation updated
[ ] Backup completed
[ ] Infrastructure verified

Deployment:
[ ] Database migrations run
[ ] Indexes verified
[ ] Backend deployed
[ ] Frontend deployed
[ ] Redis verified
[ ] Cache warmed
[ ] API endpoints tested
[ ] Frontend verified
[ ] Performance monitored
[ ] Smoke tests passed

Post-Deployment:
[ ] Functional testing complete
[ ] Performance testing complete
[ ] User acceptance testing complete
[ ] Monitoring enabled
[ ] Documentation shared with team

Success Criteria Met:
[ ] All systems operational
[ ] Performance targets met
[ ] No critical errors
[ ] Users can access feature
```

---

**Last Updated**: December 2024
**Version**: 1.0
**Deployment Date**: ******\_******
**Deployed By**: ******\_******
**Sign-off**: ******\_******
