# Implementation Plan: Scoring System

## Overview

This implementation plan transforms the Scoring System design into actionable coding tasks. The plan follows a bottom-up approach: starting with database migrations and models, then building the scoring service logic, integrating nflreadpy for data fetching, setting up scheduled jobs, creating API endpoints, and finally building the frontend UI. Each task builds incrementally on previous work, with property-based tests integrated throughout to validate correctness.

## Existing Code to Leverage

Several components already exist that can accelerate development:

**ScoringService** (`backend/app/services/scoring.py`):

- ✅ Basic class structure exists
- ✅ `grade_picks_for_game()` method skeleton
- ✅ Database query patterns for picks and games
- ⚠️ Needs updates: Remove `pick_type` field, add ATTD logic, add points calculation, add new fields

**NFLIngestService** (`backend/app/services/nfl_ingest.py`):

- ✅ Basic class structure exists
- ✅ HTTP client patterns with httpx
- ⚠️ Needs updates: Switch from BallDontLie API to nflreadpy, add touchdown scorer methods

**Database Models**:

- ✅ Pick, Game, User models exist with relationships
- ⚠️ Needs updates: Add new scoring fields via migration

**Estimated Time Savings:** 15-20% (3-3.5 weeks instead of 4 weeks)

## Testing Approach

**All property-based tests are REQUIRED** for this feature. The comprehensive testing approach ensures:

- High confidence in scoring correctness (critical for user trust)
- Edge cases are caught early (zero TDs, multiple TDs, etc.)
- Same proven methodology from pick-submission feature
- 18 properties validated with 100+ iterations each

Tasks marked with `` in the list below are property-based tests and should be implemented alongside their corresponding functionality.

## Tasks

- [x] 1. Update database models and create migrations

  - [x] 1.1 Add scoring fields to Pick model

    - Update `backend/app/db/models/pick.py`
    - Add fields: scored_at, ftd_points, attd_points, total_points
    - Add fields: is_manual_override, override_by_user_id, override_at
    - _Requirements: 1.4, 2.1, 3.1, 5.3, 10.3, 10.4_

  - [x] 1.2 Add scoring fields to User model

    - Update `backend/app/db/models/user.py`
    - Add fields: total_score, total_wins, total_losses
    - Add computed property: win_percentage
    - _Requirements: 11.1, 11.4_

  - [x] 1.3 Add scoring fields to Game model

    - Update `backend/app/db/models/game.py`
    - Add fields: first_td_scorer_player_id, all_td_scorer_player_ids (JSON array)
    - Add fields: scored_at, is_manually_scored
    - Add foreign key to Player for first_td_scorer_player_id
    - _Requirements: 2.2, 3.2, 8.4_

  - [x] 1.4 Create database migration

    - Generate Alembic migration for all model changes
    - Include upgrade and downgrade functions
    - Test migration on clean database
    - _Requirements: All scoring requirements_

- [x] 2. Implement core scoring service logic

  - [x] 2.1 Update ScoringService class

    - Update `backend/app/services/scoring.py` (already exists with basic structure)
    - Remove references to `pick_type` field (removed in pick-submission spec)
    - Implement `calculate_ftd_points(pick, first_td_scorer)` method
    - Implement `calculate_attd_points(pick, all_td_scorers)` method
    - Implement `update_pick_result(pick, ftd_points, attd_points, status)` method
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 5.1, 5.2_

  - [x] 2.2 Write property test for FTD points correctness

    - **Property 5: FTD points correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [x] 2.3 Write property test for ATTD points correctness

    - **Property 6: ATTD points correctness**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [x] 2.4 Write property test for total points calculation

    - **Property 10: Total points calculation**
    - **Validates: Requirements 5.3**

  - [x] 2.5 Write property test for FTD and ATTD stacking

    - **Property 13: FTD and ATTD stacking**
    - **Validates: Requirements 16.1, 16.2, 16.3**

  - [x] 2.6 Write property test for multiple touchdowns by same player

    - **Property 12: Multiple touchdowns by same player**
    - **Validates: Requirements 15.1, 15.2, 15.3**

- [x] 3. Implement game grading logic

  - [x] 3.1 Implement grade_game method

    - Add `grade_game(game_id)` method to ScoringService
    - Identify all pending picks for the game
    - Fetch touchdown data from game
    - Calculate points for each pick
    - Update pick statuses and points
    - Update user scores
    - _Requirements: 1.1, 1.3, 1.4, 2.4, 3.4_

  - [x] 3.2 Write property test for pending pick identification

    - **Property 1: Pending pick identification**
    - **Validates: Requirements 1.1**

  - [x] 3.3 Write property test for pick status update

    - **Property 2: Pick status update on grading**
    - **Validates: Requirements 1.3**

  - [x] 3.4 Write property test for grading timestamp

    - **Property 3: Grading timestamp recorded**
    - **Validates: Requirements 1.4**

  - [x] 3.5 Write property test for grading idempotence

    - **Property 4: Grading idempotence**
    - **Validates: Requirements 1.5**

  - [x] 3.6 Write property test for loss status

    - **Property 8: Loss status for non-scoring picks**
    - **Validates: Requirements 4.1, 4.3**

  - [x] 3.7 Write property test for win status

    - **Property 9: Win status for scoring picks**
    - **Validates: Requirements 5.1, 5.2**

  - [x] 3.8 Write property test for zero touchdown game

    - **Property 11: Zero touchdown game handling**
    - **Validates: Requirements 6.1**

- [x] 4. Implement user score tracking

  - [x] 4.1 Implement update_user_score method

    - Add `update_user_score(user_id, points)` method to ScoringService
    - Increment user's total_score by points
    - Increment total_wins or total_losses based on pick status
    - Update win_percentage
    - _Requirements: 2.4, 3.4, 11.1, 11.4_

  - [x] 4.2 Implement get_user_total_score method

    - Add `get_user_total_score(user_id)` method to ScoringService
    - Calculate sum of total_points from all winning picks
    - Return UserScore object with total, wins, losses, percentage
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 4.3 Write property test for user score update

    - **Property 7: User score update**
    - **Validates: Requirements 2.4, 3.4**

  - [x] 4.4 Write property test for user total score accuracy

    - **Property 14: User total score accuracy**
    - **Validates: Requirements 11.1, 11.2, 11.3**

  - [x] 4.5 Write property test for win/loss count accuracy

    - **Property 15: Win/loss count accuracy**
    - **Validates: Requirements 11.4**

- [x] 5. Integrate nflreadpy for data fetching

  - [x] 5.1 Enhance NFLIngestService with game results

    - Update `backend/app/services/nfl_ingest.py`
    - Implement `fetch_game_results(game_id)` method using nflreadpy
    - Implement `fetch_touchdown_scorers(game_id)` method using nflreadpy
    - Parse and transform nflreadpy data to internal format
    - _Requirements: 1.2, 7.1, 7.2, 7.3_

  - [x] 5.2 Implement data validation

    - Add `validate_game_data(game_data)` method
    - Verify game exists in database
    - Verify all player_ids exist in database
    - Log validation errors
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 5.3 Write property test for data validation

    - **Property 18: Data validation**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.4**

  - [x] 5.4 Implement error handling and retries

    - Add retry logic with exponential backoff (3 attempts)
    - Handle connection errors gracefully
    - Log all errors with context
    - Send admin alerts on failure
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [x] 5.5 Implement update_game_results method

    - Add `update_game_results(game_id, result)` method to NFLIngestService
    - Update game with first_td_scorer_player_id
    - Update game with all_td_scorer_player_ids
    - Mark game as scored
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 6. Set up scheduled jobs with APScheduler

  - [x] 6.1 Create scheduler configuration

    - Create `backend/app/worker/scheduler.py`
    - Configure AsyncIOScheduler with timezone support
    - Set up job persistence (optional)
    - Add job monitoring and logging
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 6.2 Implement fetch_upcoming_games job

    - Create job function to fetch upcoming games
    - Schedule for daily at 1:59 AM EST
    - Call NFLIngestService.fetch_upcoming_games
    - Update database with game data
    - _Requirements: 7.1_

  - [x] 6.3 Implement grade_completed_games job

    - Create job function to grade completed games
    - Schedule for Sundays at 4:30 PM EST
    - Schedule for Sundays at 8:30 PM EST
    - Find completed games since last run
    - Call ScoringService.grade_game for each
    - _Requirements: 7.2, 7.3_

  - [x] 6.4 Add job error handling

    - Wrap job functions in try/except
    - Log errors with stack traces
    - Send admin alerts on failures
    - Don't crash scheduler on errors
    - _Requirements: 7.5_

  - [x] 6.5 Start scheduler in main application

    - Update `backend/app/main.py`
    - Start scheduler on application startup
    - Shutdown scheduler on application shutdown
    - Add health check endpoint for scheduler status
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 7. Implement admin override functionality

  - [x] 7.1 Implement manual_grade_game method

    - Add `manual_grade_game(game_id, first_td_scorer, all_td_scorers, admin_id)` to ScoringService
    - Use same grading logic as automatic scoring
    - Mark game as manually scored
    - Record admin_id and timestamp
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 7.2 Write property test for manual scoring equivalence

    - **Property 16: Manual scoring equivalence**
    - **Validates: Requirements 9.1, 9.2**

  - [x] 7.3 Implement override_pick_score method

    - Add `override_pick_score(pick_id, status, ftd_points, attd_points, admin_id)` to ScoringService
    - Update pick with new status and points
    - Recalculate user's total score
    - Mark pick as manually overridden
    - Record admin_id and timestamp
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 7.4 Write property test for override audit trail

    - **Property 17: Override audit trail**
    - **Validates: Requirements 10.3, 10.4**

- [x] 8. Create scoring API endpoints

  - [x] 8.1 Create scoring schemas

    - Create `backend/app/schemas/scoring.py`
    - Define UserScoreResponse schema
    - Define PickResultResponse schema
    - Define GameResultResponse schema
    - Define ManualScoringRequest schema
    - Define OverridePickRequest schema
    - _Requirements: 11.1, 12.1, 8.1_

  - [x] 8.2 Implement GET /api/v1/scores/user/{user_id}

    - Create `backend/app/api/v1/endpoints/scores.py`
    - Implement endpoint to get user's total score
    - Add authentication requirement
    - Return total score, wins, losses, win percentage
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 8.3 Implement GET /api/v1/scores/pick/{pick_id}

    - Implement endpoint to get pick result details
    - Add authentication requirement
    - Verify user owns pick or is admin
    - Return pick status, points breakdown, actual scorers
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [x] 8.4 Implement GET /api/v1/scores/game/{game_id}

    - Implement endpoint to get game scoring results
    - Add authentication requirement
    - Return first TD scorer, all TD scorers, scoring timestamp
    - Return count of picks graded
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 8.5 Implement POST /api/v1/scores/game/{game_id}/manual

    - Implement endpoint for manual game scoring
    - Add admin authentication requirement
    - Accept first_td_scorer and all_td_scorers in request body
    - Call ScoringService.manual_grade_game
    - Return grading results
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 8.6 Implement PATCH /api/v1/scores/pick/{pick_id}/override

    - Implement endpoint for pick score override
    - Add admin authentication requirement
    - Accept status, ftd_points, attd_points in request body
    - Call ScoringService.override_pick_score
    - Return updated pick
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 9. Build frontend scoring UI

  - [x] 9.1 Create API client functions

    - Create `frontend/src/lib/api/scores.ts`
    - Implement getUserScore(userId) function
    - Implement getPickResult(pickId) function
    - Implement getGameResult(gameId) function
    - Add proper TypeScript types
    - _Requirements: 11.1, 12.1, 8.1_

  - [x] 9.2 Create TypeScript types for scoring

    - Create `frontend/src/types/scoring.ts`
    - Define UserScore type
    - Define PickResult type
    - Define GameResult type
    - Export types for use across components
    - _Requirements: 11.1, 12.1, 8.1_

  - [x] 9.3 Create UserScoreCard component

    - Create `frontend/src/components/scoring/UserScoreCard.tsx`
    - Display total score, wins, losses, win percentage
    - Show rank (if leaderboard data available)
    - Add loading and error states
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 9.4 Enhance MyPicks component with results

    - Update `frontend/src/components/picks/MyPicks.tsx`
    - Show pick status (win/loss) with visual indicators
    - Show points earned (FTD + ATTD breakdown)
    - Show actual first TD scorer
    - Add tooltip with all TD scorers
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [x] 9.5 Create GameResultsModal component

    - Create `frontend/src/components/scoring/GameResultsModal.tsx`
    - Display game scoring details
    - Show first TD scorer with player info
    - Show all TD scorers list
    - Show number of picks graded
    - Show scoring timestamp
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 9.6 Add scoring indicators to AvailableGames

    - Update `frontend/src/components/picks/AvailableGames.tsx`
    - Show if game has been scored
    - Show user's result for scored games (win/loss badge)
    - Show points earned for scored games
    - _Requirements: 8.1, 12.1_

- [x] 10. Build admin scoring UI

  - [x] 10.1 Create ManualScoringForm component

    - Create `frontend/src/components/admin/ManualScoringForm.tsx`
    - Form to select game
    - Player search for first TD scorer
    - Multi-select for all TD scorers
    - Submit button to trigger manual scoring
    - Show confirmation and results
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 10.2 Create PickOverrideForm component

    - Create `frontend/src/components/admin/PickOverrideForm.tsx`
    - Form to select pick
    - Inputs for status, FTD points, ATTD points
    - Show current values
    - Submit button to override
    - Show confirmation and audit trail
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 10.3 Create AdminScoringPage

    - Create `frontend/src/pages/AdminScoringPage.tsx`
    - Include ManualScoringForm
    - Include PickOverrideForm
    - Show recent scoring activity
    - Show games pending scoring
    - Add admin-only route protection
    - _Requirements: 9.1, 10.1_

- [x] 11. Add error handling and monitoring

  - [x] 11.1 Implement error logging

    - Add structured logging for all scoring operations
    - Log job executions with duration
    - Log API calls to nflreadpy
    - Log grading results (picks processed, errors)
    - _Requirements: 7.4, 7.5, 13.1_

  - [x] 11.2 Implement admin alerts

    - Create alert service for critical errors
    - Send email alerts on job failures
    - Send alerts on API failures after retries
    - Send alerts on data validation errors
    - _Requirements: 13.4_

  - [x] 11.3 Add health check endpoints

    - Add GET /api/v1/health/scheduler endpoint
    - Return scheduler status and last run times
    - Add GET /api/v1/health/scoring endpoint
    - Return recent scoring statistics
    - _Requirements: 7.4_

  - [x] 11.4 Create admin monitoring dashboard

    - Create `frontend/src/pages/AdminMonitoringPage.tsx`
    - Show scheduler status and next run times
    - Show recent job executions and results
    - Show API health and error rates
    - Show scoring statistics (picks graded, errors)
    - _Requirements: 7.4, 8.1_

- [x] 12. Testing and validation

  - [x] 12.1 Run all property-based tests

    - Execute all 18 property tests
    - Verify 100+ iterations per test
    - Fix any failing tests
    - Ensure all correctness properties hold
    - _Requirements: All requirements_

  - [x] 12.2 Integration testing

    - Test complete scoring flow end-to-end
    - Test scheduled job execution
    - Test nflreadpy integration with real data
    - Test manual scoring workflow
    - Test override workflow
    - _Requirements: All requirements_

  - [x] 12.3 Test edge cases

    - Test zero touchdown games
    - Test multiple TDs by same player
    - Test API failures and retries
    - Test invalid data handling
    - Test duplicate grading attempts
    - _Requirements: 6.1, 13.1, 14.1, 15.1_

  - [x] 12.4 Performance testing

    - Test grading 100+ picks for a game
    - Test scheduled job execution time
    - Verify database query performance
    - Test concurrent grading scenarios
    - _Requirements: All requirements_

- [x] 13. Documentation and deployment

  - [x] 13.1 Update API documentation

    - Document all scoring endpoints in Swagger
    - Add request/response examples
    - Document error codes
    - Add authentication requirements
    - _Requirements: All requirements_

  - [x] 13.2 Create admin guide

    - Document manual scoring process
    - Document override process
    - Document monitoring and alerts
    - Document troubleshooting steps
    - _Requirements: 9.1, 10.1_

  - [x] 13.3 Update user documentation

    - Explain scoring rules (FTD=3, ATTD=1)
    - Explain how to view scores
    - Explain pick results display
    - Add FAQ for common questions
    - _Requirements: 2.1, 3.1, 11.1, 12.1_

  - [x] 13.4 Deploy to production

    - Run database migrations
    - Deploy updated backend code
    - Deploy updated frontend code
    - Start scheduler
    - Verify scheduled jobs run correctly
    - Monitor for errors
    - _Requirements: All requirements_

## Implementation Complete

The Scoring System will be complete when:

- ✅ All database migrations applied
- ✅ Scoring service implemented with all methods
- ✅ nflreadpy integration working
- ✅ Scheduled jobs running on schedule
- ✅ All 18 property-based tests passing
- ✅ API endpoints functional
- ✅ Frontend UI displaying scores
- ✅ Admin override tools working
- ✅ Error handling and monitoring in place
- ✅ Documentation complete

## Estimated Timeline

- **Week 1 (Days 1-7):** Tasks 1-5 (Database, scoring logic, nflreadpy integration)
- **Week 2 (Days 8-14):** Tasks 6-8 (Scheduled jobs, admin overrides, API endpoints)
- **Week 3 (Days 15-21):** Tasks 9-11 (Frontend UI, admin UI, monitoring)
- **Week 4 (Days 22-28):** Tasks 12-13 (Testing, documentation, deployment)

**Total: 4 weeks to complete scoring system**

## Next Steps

1. Review this implementation plan
2. Start with Task 1: Database migrations
3. Follow tasks in order
4. Run tests after each major section
5. Deploy to production after all tests pass
