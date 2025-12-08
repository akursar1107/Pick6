# Scoring System Admin Guide

## Overview

This guide provides administrators with instructions for managing the scoring system, including manual scoring, score overrides, monitoring, and troubleshooting.

## Table of Contents

1. [Manual Scoring Process](#manual-scoring-process)
2. [Score Override Process](#score-override-process)
3. [Monitoring and Alerts](#monitoring-and-alerts)
4. [Troubleshooting](#troubleshooting)

---

## Manual Scoring Process

### When to Use Manual Scoring

Manual scoring should be used when:

- The automatic scoring job fails due to API issues
- Game data from nflreadpy is incorrect or incomplete
- A game needs to be re-scored due to data corrections
- Testing the scoring system with specific scenarios

### Prerequisites

- Admin authentication token
- Game ID for the game to be scored
- Player IDs for touchdown scorers

### Step-by-Step Process

#### 1. Identify the Game

First, get the game ID from the database or API:

```bash
# Using the API
curl -X GET "http://localhost:8000/api/v1/games?status=final" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Identify Touchdown Scorers

Get the player IDs for the touchdown scorers. You can:

- Look up players in the database
- Use the players API endpoint
- Reference official NFL game data

#### 3. Submit Manual Scoring Request

Use the manual scoring endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/scores/game/{game_id}/manual" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_td_scorer": "789e4567-e89b-12d3-a456-426614174000",
    "all_td_scorers": [
      "789e4567-e89b-12d3-a456-426614174000",
      "456e4567-e89b-12d3-a456-426614174000"
    ]
  }'
```

**Request Body Fields:**

- `first_td_scorer` (UUID, optional): Player ID of the first touchdown scorer. Set to `null` if no touchdowns.
- `all_td_scorers` (array of UUIDs): List of all players who scored touchdowns. Empty array if no touchdowns.

#### 4. Verify Results

Check the response to confirm successful scoring:

```json
{
  "message": "Game scored successfully",
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "picks_graded": 25
}
```

#### 5. Validate Pick Results

Spot-check a few picks to ensure they were graded correctly:

```bash
curl -X GET "http://localhost:8000/api/v1/scores/pick/{pick_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Important Notes

- Manual scoring uses the same grading logic as automatic scoring
- The game will be marked as `is_manually_scored: true`
- Manual scoring is idempotent - running it multiple times won't change results
- All picks for the game will be re-graded based on the provided touchdown data
- User scores will be recalculated automatically

---

## Score Override Process

### When to Use Score Overrides

Score overrides should be used when:

- A specific pick was graded incorrectly due to a bug
- Resolving user disputes about scoring
- Correcting data entry errors
- Testing specific scoring scenarios

### Prerequisites

- Admin authentication token
- Pick ID for the pick to be overridden
- Desired status (win or loss)
- Desired point values (FTD and ATTD)

### Step-by-Step Process

#### 1. Identify the Pick

Get the pick ID from the database or API:

```bash
# Get picks for a specific user
curl -X GET "http://localhost:8000/api/v1/picks?user_id={user_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. Review Current Pick Status

Check the current scoring details:

```bash
curl -X GET "http://localhost:8000/api/v1/scores/pick/{pick_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. Submit Override Request

Use the override endpoint:

```bash
curl -X PATCH "http://localhost:8000/api/v1/scores/pick/{pick_id}/override" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "win",
    "ftd_points": 3,
    "attd_points": 1
  }'
```

**Request Body Fields:**

- `status` (string): Either "win" or "loss"
- `ftd_points` (integer): Points for first touchdown (0 or 3)
- `attd_points` (integer): Points for anytime touchdown (0 or 1)

**Valid Point Combinations:**

- Loss: `status: "loss"`, `ftd_points: 0`, `attd_points: 0`
- ATTD only: `status: "win"`, `ftd_points: 0`, `attd_points: 1`
- FTD only: `status: "win"`, `ftd_points: 3`, `attd_points: 0`
- FTD + ATTD: `status: "win"`, `ftd_points: 3`, `attd_points: 1`

#### 4. Verify Override

Check the response to confirm the override:

```json
{
  "message": "Pick score overridden successfully",
  "pick_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "win",
  "ftd_points": 3,
  "attd_points": 1,
  "total_points": 4
}
```

#### 5. Verify User Score Update

Check that the user's total score was updated correctly:

```bash
curl -X GET "http://localhost:8000/api/v1/scores/user/{user_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Audit Trail

All overrides are tracked with:

- `is_manual_override: true` flag on the pick
- `override_by_user_id`: Admin user ID who performed the override
- `override_at`: Timestamp of the override

Query overrides in the database:

```sql
SELECT
  p.id,
  p.status,
  p.total_points,
  p.override_at,
  u.username as overridden_by
FROM picks p
LEFT JOIN users u ON p.override_by_user_id = u.id
WHERE p.is_manual_override = true
ORDER BY p.override_at DESC;
```

---

## Monitoring and Alerts

### Health Check Endpoints

#### Scheduler Health

Check if scheduled jobs are running:

```bash
curl -X GET "http://localhost:8000/api/v1/health/scheduler"
```

**Response:**

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
    }
  ],
  "timezone": "America/New_York"
}
```

#### Scoring System Health

Check scoring system statistics (admin only):

```bash
curl -X GET "http://localhost:8000/api/v1/health/scoring" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**

```json
{
  "status": "healthy",
  "database_healthy": true,
  "statistics": {
    "picks_graded_7d": 150,
    "games_scored_7d": 12,
    "pending_picks": 45,
    "last_scoring_time": "2024-12-07T20:30:00Z",
    "last_scored_game": "2024_12_07_KC_BUF"
  },
  "issues": null
}
```

#### Overall System Health

Check all components:

```bash
curl -X GET "http://localhost:8000/api/v1/health/system"
```

### Monitoring Dashboard

Access the admin monitoring dashboard at:

```
http://localhost:3000/admin/monitoring
```

The dashboard displays:

- Scheduler status and next run times
- Recent job executions and results
- API health and error rates
- Scoring statistics (picks graded, errors)

### Alert Notifications

The system sends email alerts for:

- Scheduled job failures
- nflreadpy API failures after retries
- Data validation errors
- High number of pending picks (>1000)
- No scoring activity for >48 hours

**Configure alerts in:** `backend/app/core/config.py`

```python
ALERT_EMAIL_RECIPIENTS = ["admin@example.com"]
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
```

### Log Files

Check application logs for detailed information:

```bash
# View backend logs
docker compose logs api -f

# View scheduler logs
docker compose logs api -f | grep "scheduler"

# View scoring logs
docker compose logs api -f | grep "scoring"
```

---

## Troubleshooting

### Issue: Scheduled Jobs Not Running

**Symptoms:**

- Health check shows scheduler status as "stopped"
- No recent scoring activity
- Picks remain in "pending" status

**Diagnosis:**

```bash
# Check scheduler health
curl -X GET "http://localhost:8000/api/v1/health/scheduler"

# Check application logs
docker compose logs api | grep "scheduler"
```

**Solutions:**

1. **Restart the application:**

   ```bash
   docker compose restart api
   ```

2. **Check scheduler initialization:**

   - Verify `scheduler.start()` is called in `backend/app/main.py`
   - Check for errors during startup

3. **Verify timezone configuration:**
   - Ensure `America/New_York` timezone is set correctly
   - Check system timezone settings

### Issue: nflreadpy API Failures

**Symptoms:**

- Games not being scored automatically
- Error logs showing API connection failures
- Alert emails about API failures

**Diagnosis:**

```bash
# Check recent errors
docker compose logs api | grep "nflreadpy" | grep "ERROR"

# Check scoring health
curl -X GET "http://localhost:8000/api/v1/health/scoring" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Solutions:**

1. **Verify nflreadpy is installed:**

   ```bash
   docker compose exec api pip show nflreadpy
   ```

2. **Test API connectivity:**

   ```bash
   docker compose exec api python -c "import nflreadpy; print('OK')"
   ```

3. **Use manual scoring as workaround:**

   - Follow the [Manual Scoring Process](#manual-scoring-process)
   - Get touchdown data from official NFL sources

4. **Check for rate limiting:**
   - Review API call frequency
   - Add delays between requests if needed

### Issue: Incorrect Scoring Results

**Symptoms:**

- Users reporting wrong scores
- Pick results don't match actual game outcomes
- Total scores don't add up correctly

**Diagnosis:**

1. **Check specific pick:**

   ```bash
   curl -X GET "http://localhost:8000/api/v1/scores/pick/{pick_id}" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Check game result:**

   ```bash
   curl -X GET "http://localhost:8000/api/v1/scores/game/{game_id}" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Verify touchdown data:**
   - Compare with official NFL game data
   - Check `first_td_scorer_player_id` and `all_td_scorer_player_ids` in database

**Solutions:**

1. **If game data is wrong:**

   - Use manual scoring with correct touchdown data
   - Follow [Manual Scoring Process](#manual-scoring-process)

2. **If specific pick is wrong:**

   - Use score override to correct the pick
   - Follow [Score Override Process](#score-override-process)

3. **If scoring logic is wrong:**
   - Review property-based tests
   - Check for bugs in `ScoringService`
   - Run tests: `docker compose exec api pytest tests/test_scoring_properties.py`

### Issue: High Number of Pending Picks

**Symptoms:**

- Health check shows "degraded" status
- Large number of picks with status "pending"
- Games completed but not scored

**Diagnosis:**

```bash
# Check pending picks count
curl -X GET "http://localhost:8000/api/v1/health/scoring" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Query database
docker compose exec db psql -U first6_user -d first6_db -c \
  "SELECT COUNT(*) FROM picks WHERE status = 'pending';"
```

**Solutions:**

1. **Check for unscored games:**

   ```sql
   SELECT id, external_id, kickoff_time, status
   FROM games
   WHERE status = 'final' AND scored_at IS NULL
   ORDER BY kickoff_time DESC;
   ```

2. **Manually score pending games:**

   - Identify games that should be scored
   - Use manual scoring for each game

3. **Investigate why automatic scoring failed:**
   - Check scheduler logs
   - Check for API failures
   - Verify job execution times

### Issue: User Score Discrepancies

**Symptoms:**

- User's total_score doesn't match sum of pick points
- Win/loss counts are incorrect

**Diagnosis:**

1. **Calculate expected score:**

   ```sql
   SELECT
     user_id,
     SUM(total_points) as calculated_score,
     COUNT(CASE WHEN status = 'win' THEN 1 END) as calculated_wins,
     COUNT(CASE WHEN status = 'loss' THEN 1 END) as calculated_losses
   FROM picks
   WHERE user_id = 'USER_ID_HERE'
   GROUP BY user_id;
   ```

2. **Compare with stored values:**
   ```sql
   SELECT total_score, total_wins, total_losses
   FROM users
   WHERE id = 'USER_ID_HERE';
   ```

**Solutions:**

1. **Recalculate user scores:**

   ```python
   # Run in Python shell
   docker compose exec api python

   from app.db.session import SessionLocal
   from app.services.scoring import ScoringService
   from uuid import UUID

   async def fix_user_score(user_id: str):
       async with SessionLocal() as db:
           service = ScoringService(db)
           score = await service.get_user_total_score(UUID(user_id))
           print(f"Recalculated score: {score}")
           await db.commit()

   import asyncio
   asyncio.run(fix_user_score("USER_ID_HERE"))
   ```

2. **If issue persists:**
   - Check for bugs in `update_user_score` method
   - Review property-based tests for user score accuracy
   - Run: `docker compose exec api pytest tests/test_scoring_properties.py::test_property_14_user_total_score_accuracy`

### Getting Help

If you encounter issues not covered in this guide:

1. **Check application logs:**

   ```bash
   docker compose logs api -f
   ```

2. **Run property-based tests:**

   ```bash
   docker compose exec api pytest tests/test_scoring_properties.py -v
   ```

3. **Review the design document:**

   - See `.kiro/specs/scoring-system/design.md`
   - Check correctness properties

4. **Contact development team:**
   - Provide error logs
   - Include steps to reproduce
   - Share relevant pick/game IDs

---

## Best Practices

### Regular Monitoring

- Check health endpoints daily
- Review alert emails promptly
- Monitor pending picks count
- Verify scheduled jobs are running

### Data Validation

- Always verify touchdown data before manual scoring
- Cross-reference with official NFL sources
- Spot-check automated scoring results

### Audit Trail

- Document all manual scoring actions
- Keep records of score overrides
- Note reasons for administrative actions

### Testing

- Test manual scoring in development environment first
- Verify score overrides with small point values
- Run property-based tests after code changes

---

## Quick Reference

### Common Commands

```bash
# Check scheduler status
curl http://localhost:8000/api/v1/health/scheduler

# Check scoring health (admin)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/health/scoring

# Manual score a game (admin)
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_td_scorer":"UUID","all_td_scorers":["UUID"]}' \
  http://localhost:8000/api/v1/scores/game/GAME_ID/manual

# Override pick score (admin)
curl -X PATCH -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"win","ftd_points":3,"attd_points":1}' \
  http://localhost:8000/api/v1/scores/pick/PICK_ID/override

# View logs
docker compose logs api -f

# Restart application
docker compose restart api
```

### Scoring Rules

- **FTD (First Touchdown):** 3 points
- **ATTD (Anytime Touchdown):** 1 point
- **FTD + ATTD (same player):** 4 points total
- **No touchdown:** 0 points, status = loss

### Support Contacts

- Development Team: dev@first6.com
- System Alerts: alerts@first6.com
- Documentation: https://docs.first6.com
