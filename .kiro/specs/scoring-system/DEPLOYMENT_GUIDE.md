# Scoring System Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the scoring system to production. Follow these steps carefully to ensure a smooth deployment.

## Pre-Deployment Checklist

Before deploying, verify that all components are ready:

- [ ] All database migrations are created and tested
- [ ] All 18 property-based tests are passing
- [ ] Integration tests are passing
- [ ] API endpoints are functional in development
- [ ] Frontend UI is working correctly
- [ ] Scheduler is running in development
- [ ] nflreadpy integration is tested
- [ ] Documentation is complete
- [ ] Backup of production database is created

## Deployment Steps

### Step 1: Backup Production Database

**CRITICAL**: Always backup before making changes!

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker compose exec db pg_dump -U first6_user first6_db > backups/pre_scoring_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup was created
ls -lh backups/
```

### Step 2: Stop Production Services

```bash
# Stop all services
docker compose down

# Verify services are stopped
docker compose ps
```

### Step 3: Pull Latest Code

```bash
# Pull latest changes from repository
git pull origin main

# Verify you're on the correct branch/commit
git log -1
```

### Step 4: Update Dependencies

#### Backend Dependencies

```bash
# Check if nflreadpy is in requirements.txt
grep nflreadpy backend/requirements.txt

# If not present, add it
echo "nflreadpy>=0.1.0" >> backend/requirements.txt

# Verify APScheduler is present
grep APScheduler backend/requirements.txt
```

#### Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Return to root
cd ..
```

### Step 5: Run Database Migrations

```bash
# Start database service only
docker compose up -d db

# Wait for database to be ready
sleep 10

# Run migrations
docker compose run --rm api alembic upgrade head

# Verify migrations were applied
docker compose run --rm api alembic current
```

**Expected Output:**

```
INFO  [alembic.runtime.migration] Running upgrade <previous> -> <new>, Add scoring fields
```

**Verify Migration in Database:**

```bash
# Connect to database
docker compose exec db psql -U first6_user -d first6_db

# Check new columns exist
\d picks
\d users
\d games

# Exit psql
\q
```

**Expected New Columns:**

**picks table:**

- scored_at
- ftd_points
- attd_points
- total_points
- is_manual_override
- override_by_user_id
- override_at

**users table:**

- total_score
- total_wins
- total_losses

**games table:**

- first_td_scorer_player_id
- all_td_scorer_player_ids
- scored_at
- is_manually_scored

### Step 6: Build and Start Services

```bash
# Build updated images
docker compose build

# Start all services
docker compose up -d

# Verify all services are running
docker compose ps
```

**Expected Output:**

```
NAME                COMMAND                  SERVICE             STATUS
first6-api-1        "uvicorn app.main:..."   api                 running
first6-db-1         "docker-entrypoint..."   db                  running
first6-web-1        "nginx -g 'daemon ..."   web                 running
```

### Step 7: Verify Scheduler Started

```bash
# Check scheduler health
curl http://localhost:8000/api/v1/health/scheduler

# Check application logs for scheduler startup
docker compose logs api | grep "scheduler"
```

**Expected Output:**

```json
{
  "status": "healthy",
  "running": true,
  "jobs": [
    {
      "id": "fetch_upcoming_games",
      "name": "Fetch Upcoming Games",
      "next_run_time": "2024-12-08T01:59:00-05:00",
      "trigger": "cron[hour='1', minute='59']"
    },
    {
      "id": "grade_early_games",
      "name": "Grade Early Games",
      "next_run_time": "2024-12-08T16:30:00-05:00",
      "trigger": "cron[day_of_week='sun', hour='16', minute='30']"
    },
    {
      "id": "grade_late_games",
      "name": "Grade Late Games",
      "next_run_time": "2024-12-08T20:30:00-05:00",
      "trigger": "cron[day_of_week='sun', hour='20', minute='30']"
    }
  ],
  "timezone": "America/New_York"
}
```

### Step 8: Run Post-Deployment Tests

#### Test API Endpoints

```bash
# Get authentication token (replace with actual credentials)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | jq -r '.access_token')

# Test user score endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/scores/user/USER_ID

# Test health endpoints
curl http://localhost:8000/api/v1/health/system
curl http://localhost:8000/api/v1/health/scheduler
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/health/scoring
```

#### Test Frontend

1. Open browser to `http://localhost:3000`
2. Log in with test account
3. Navigate to Profile/Dashboard
4. Verify score card is displayed
5. Navigate to My Picks
6. Verify pick results are displayed (if any picks exist)
7. Click on a game to view game results modal

#### Test Scheduled Jobs (Optional)

**Warning**: This will trigger actual scoring if there are completed games!

```bash
# Manually trigger a job (for testing only)
docker compose exec api python -c "
from app.worker.scheduler import get_scheduler
import asyncio

async def test_job():
    scheduler = get_scheduler()
    # This would trigger the job immediately
    # Only do this in a test environment!
    pass

asyncio.run(test_job())
"
```

### Step 9: Monitor Initial Operation

Monitor the system for the first 24 hours after deployment:

```bash
# Watch logs in real-time
docker compose logs -f api

# Check for errors
docker compose logs api | grep ERROR

# Monitor scheduler
watch -n 60 'curl -s http://localhost:8000/api/v1/health/scheduler | jq'

# Monitor scoring health (requires admin token)
watch -n 300 'curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/health/scoring | jq'
```

### Step 10: Verify First Scheduled Run

Wait for the first scheduled job to run (next occurrence based on schedule):

**Daily at 1:59 AM EST** - Fetch upcoming games
**Sundays at 4:30 PM EST** - Grade early games
**Sundays at 8:30 PM EST** - Grade late games

After the first run:

```bash
# Check logs for job execution
docker compose logs api | grep "fetch_upcoming_games"
docker compose logs api | grep "grade_completed_games"

# Verify games were fetched/scored
docker compose exec db psql -U first6_user -d first6_db -c \
  "SELECT COUNT(*) FROM games WHERE scored_at IS NOT NULL;"

# Check for any errors
docker compose logs api | grep ERROR | tail -20
```

## Post-Deployment Verification

### Verify All Components

- [ ] Database migrations applied successfully
- [ ] All services running (api, db, web)
- [ ] Scheduler is running and jobs are scheduled
- [ ] Health endpoints return "healthy" status
- [ ] API endpoints are accessible
- [ ] Frontend displays correctly
- [ ] No errors in logs
- [ ] First scheduled job runs successfully

### Test Scoring Flow (When Games Complete)

After a game completes and is scored:

1. **Verify game was scored:**

   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/scores/game/GAME_ID
   ```

2. **Verify picks were graded:**

   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/scores/pick/PICK_ID
   ```

3. **Verify user scores updated:**

   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/scores/user/USER_ID
   ```

4. **Check database:**

   ```sql
   -- Connect to database
   docker compose exec db psql -U first6_user -d first6_db

   -- Check scored picks
   SELECT COUNT(*) FROM picks WHERE scored_at IS NOT NULL;

   -- Check user scores
   SELECT username, total_score, total_wins, total_losses
   FROM users
   WHERE total_score > 0
   ORDER BY total_score DESC
   LIMIT 10;

   -- Exit
   \q
   ```

## Rollback Procedure

If issues are encountered, follow this rollback procedure:

### Step 1: Stop Services

```bash
docker compose down
```

### Step 2: Restore Database Backup

```bash
# Find your backup file
ls -lh backups/

# Restore database
docker compose up -d db
sleep 10
docker compose exec -T db psql -U first6_user -d first6_db < backups/pre_scoring_backup_TIMESTAMP.sql
```

### Step 3: Revert Code

```bash
# Revert to previous commit
git log --oneline -10  # Find previous commit hash
git checkout PREVIOUS_COMMIT_HASH

# Or revert to previous tag
git checkout v1.0.0  # Replace with your version tag
```

### Step 4: Rebuild and Restart

```bash
# Rebuild with previous code
docker compose build

# Start services
docker compose up -d

# Verify services are running
docker compose ps
```

### Step 5: Verify Rollback

```bash
# Check health
curl http://localhost:8000/api/v1/health/system

# Verify database state
docker compose exec db psql -U first6_user -d first6_db -c \
  "SELECT COUNT(*) FROM picks WHERE scored_at IS NOT NULL;"
```

## Troubleshooting

### Issue: Migration Fails

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by 'xxxxx'`

**Solution**:

```bash
# Check current revision
docker compose run --rm api alembic current

# Check migration history
docker compose run --rm api alembic history

# If needed, stamp to specific revision
docker compose run --rm api alembic stamp head
```

### Issue: Scheduler Not Starting

**Error**: Scheduler health shows "not_initialized" or "stopped"

**Solution**:

```bash
# Check logs for errors
docker compose logs api | grep scheduler

# Verify scheduler.py exists
docker compose exec api ls -la app/worker/

# Verify main.py starts scheduler
docker compose exec api grep -A 5 "scheduler" app/main.py

# Restart service
docker compose restart api
```

### Issue: nflreadpy Import Error

**Error**: `ModuleNotFoundError: No module named 'nflreadpy'`

**Solution**:

```bash
# Verify nflreadpy in requirements.txt
docker compose exec api cat requirements.txt | grep nflreadpy

# Reinstall dependencies
docker compose exec api pip install -r requirements.txt

# Or rebuild container
docker compose build api
docker compose up -d api
```

### Issue: Frontend Not Showing Scores

**Symptoms**: Score card or pick results not displaying

**Solution**:

```bash
# Check browser console for errors
# Open browser DevTools (F12) and check Console tab

# Verify API is accessible
curl http://localhost:8000/api/v1/health/system

# Check frontend build
cd frontend
npm run build
cd ..

# Restart web service
docker compose restart web
```

### Issue: Database Connection Errors

**Error**: `could not connect to server: Connection refused`

**Solution**:

```bash
# Check database is running
docker compose ps db

# Check database logs
docker compose logs db

# Restart database
docker compose restart db

# Wait for database to be ready
sleep 10

# Test connection
docker compose exec db psql -U first6_user -d first6_db -c "SELECT 1;"
```

## Monitoring and Maintenance

### Daily Checks

```bash
# Check system health
curl http://localhost:8000/api/v1/health/system

# Check scheduler status
curl http://localhost:8000/api/v1/health/scheduler

# Check for errors in logs
docker compose logs api --since 24h | grep ERROR
```

### Weekly Checks

```bash
# Check scoring statistics (requires admin token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/health/scoring

# Review database size
docker compose exec db psql -U first6_user -d first6_db -c \
  "SELECT pg_size_pretty(pg_database_size('first6_db'));"

# Check disk space
df -h
```

### Monthly Maintenance

```bash
# Create database backup
docker compose exec db pg_dump -U first6_user first6_db > \
  backups/monthly_backup_$(date +%Y%m%d).sql

# Clean old logs
docker compose logs api > logs/api_$(date +%Y%m%d).log
docker compose logs --no-log-prefix api > /dev/null

# Update dependencies (if needed)
cd frontend && npm update && cd ..
docker compose exec api pip list --outdated
```

## Performance Optimization

### Database Indexes

Verify indexes are created:

```sql
-- Connect to database
docker compose exec db psql -U first6_user -d first6_db

-- Check indexes
\di

-- Expected indexes:
-- picks(game_id, status)
-- picks(user_id, status)
-- games(status, kickoff_time)
-- games(first_td_scorer_player_id)

-- If missing, create them:
CREATE INDEX IF NOT EXISTS idx_picks_game_status ON picks(game_id, status);
CREATE INDEX IF NOT EXISTS idx_picks_user_status ON picks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_games_status_kickoff ON games(status, kickoff_time);
CREATE INDEX IF NOT EXISTS idx_games_first_td_scorer ON games(first_td_scorer_player_id);
```

### Caching Configuration

Verify Redis is configured (if using caching):

```bash
# Check if Redis is running
docker compose ps redis

# Test Redis connection
docker compose exec redis redis-cli ping
# Expected: PONG
```

## Security Checklist

- [ ] Environment variables are set correctly (not using defaults)
- [ ] Database passwords are strong and unique
- [ ] JWT secret key is secure and unique
- [ ] Admin accounts have strong passwords
- [ ] HTTPS is enabled (if applicable)
- [ ] CORS settings are configured correctly
- [ ] Rate limiting is enabled
- [ ] Logs don't contain sensitive information

## Support and Escalation

### Getting Help

If you encounter issues during deployment:

1. **Check logs**: `docker compose logs api -f`
2. **Review this guide**: Troubleshooting section
3. **Check documentation**: Design and requirements docs
4. **Run tests**: `docker compose exec api pytest`
5. **Contact development team**: Provide logs and error details

### Emergency Contacts

- **Development Team**: dev@first6.com
- **System Administrator**: admin@first6.com
- **On-Call**: [Phone number]

### Escalation Procedure

1. **Level 1**: Check logs and troubleshooting guide
2. **Level 2**: Contact development team via email
3. **Level 3**: Emergency rollback (follow rollback procedure)
4. **Level 4**: Contact on-call engineer

## Deployment Checklist Summary

Use this checklist during deployment:

```
Pre-Deployment:
[ ] All tests passing
[ ] Documentation complete
[ ] Backup created

Deployment:
[ ] Services stopped
[ ] Code updated
[ ] Dependencies updated
[ ] Migrations run
[ ] Services started
[ ] Scheduler verified
[ ] Tests run
[ ] Monitoring enabled

Post-Deployment:
[ ] Health checks passing
[ ] No errors in logs
[ ] First scheduled job successful
[ ] User-facing features working
[ ] Performance acceptable

Documentation:
[ ] Deployment logged
[ ] Team notified
[ ] Monitoring configured
```

## Conclusion

The scoring system is now deployed to production! Monitor the system closely for the first 24-48 hours to ensure everything is working correctly.

**Next Steps:**

1. Monitor scheduled job executions
2. Verify scoring accuracy after first games
3. Collect user feedback
4. Address any issues promptly

**Remember**: Always backup before making changes, and don't hesitate to rollback if issues arise.

Good luck! 🚀
