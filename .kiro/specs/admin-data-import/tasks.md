s# Implementation Plan: Admin Data Import Feature

## Overview

This implementation plan breaks down the Admin Data Import feature into discrete, manageable tasks. Each task builds on previous work and includes specific requirements references.

---

## Task List

- [x] 1. Database setup and models

  - Create ImportJob model with all required fields
  - Create database migration for import_jobs table
  - Add indexes for performance (season, status, admin_user_id, started_at)
  - Add relationship to User model
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 2. Backend service implementation

- [x] 2.1 Create NFLDataImportService class

  - Implement service initialization with database session
  - Add helper methods for team and player creation
  - Implement error handling and logging
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 2.2 Implement schedule fetching

  - Add fetch_schedule() method using nflreadpy
  - Handle season and week filtering
  - Add error handling for network failures
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 2.3 Implement game creation/update logic

  - Add create_or_update_game() method
  - Handle game status determination
  - Implement team lookup/creation
  - Return tuple of (Game, was_created) for statistics
  - _Requirements: 1.3, 8.2, 8.3, 8.5_

- [x] 2.4 Implement game grading logic

  - Add grade_game() method for completed games
  - Fetch play-by-play data from nflreadpy
  - Identify first TD scorer and all TD scorers
  - Create player records as needed
  - Handle games with no touchdowns
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 2.5 Implement main import method

  - Add import_season_data() orchestration method
  - Process games sequentially with progress tracking
  - Collect statistics (teams, players, games created/updated)
  - Handle errors gracefully and continue processing
  - Return ImportStats object
  - _Requirements: 1.4, 1.5, 3.5, 4.3_

- [x] 2.6 Write property test for import idempotency

  - **Property 1: Import idempotency**
  - Generate random season/week combinations
  - Import data twice
  - Verify same final database state
  - **Validates: Requirements 1.3, 8.5**

- [x] 2.7 Write property test for error isolation

  - **Property 8: Error isolation**
  - Simulate game import failures
  - Verify other games continue processing
  - **Validates: Requirements 3.5**

- [x] 3. Progress tracking implementation

- [x] 3.1 Create ImportProgressTracker class

  - Implement Redis-based progress storage
  - Add update_progress() method
  - Add get_progress() method
  - Add mark_complete() and mark_failed() methods
  - Set Redis key expiration to 24 hours
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 3.2 Integrate progress tracking in import service

  - Update progress after each game processed
  - Track current step description
  - Update statistics counters
  - Handle progress updates on errors
  - _Requirements: 4.2, 4.3, 4.4_

- [x] 3.3 Write property test for progress monotonicity

  - **Property 2: Progress monotonicity**
  - Generate random progress updates
  - Verify games_processed never decreases
  - **Validates: Requirements 4.2, 4.3**

- [x] 4. Background task implementation

- [x] 4.1 Create background task for import execution

  - Implement async task using existing worker infrastructure
  - Call NFLDataImportService.import_season_data()
  - Update ImportJob status in database
  - Handle task failures and timeouts
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 4.2 Add concurrent import prevention

  - Check for running imports before starting
  - Query ImportJob table for running status
  - Return error if import already in progress
  - _Requirements: 5.5_

- [x] 4.3 Write property test for concurrent import prevention

  - **Property 7: Concurrent import prevention**
  - Attempt to start multiple imports for same season
  - Verify only one runs at a time
  - **Validates: Requirements 5.5**

- [x] 5. API endpoints implementation

- [x] 5.1 Create admin import router

  - Create new router file: api/v1/admin/import.py
  - Add admin authentication dependency
  - Set up route prefix: /api/v1/admin/import
  - _Requirements: 1.1, Security requirements_

- [x] 5.2 Implement POST /start endpoint

  - Create ImportStartRequest schema with validation
  - Validate season year (2020-2030)
  - Validate week numbers (1-18)
  - Create ImportJob record
  - Queue background task
  - Return job_id and estimated duration
  - _Requirements: 1.1, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [x] 5.3 Implement GET /status/:id endpoint

  - Fetch ImportJob from database
  - Get current progress from Redis
  - Return combined status and progress
  - Handle job not found errors
  - _Requirements: 4.1, 4.2, 4.3, 5.4_

- [x] 5.4 Implement GET /history endpoint

  - Query ImportJob table with filters
  - Support pagination (limit, offset)
  - Filter by season and status
  - Order by started_at descending
  - Return list of import history items
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 5.5 Write property test for week validation

  - **Property 6: Week validation**
  - Generate random week numbers (valid and invalid)
  - Verify API rejects invalid weeks
  - **Validates: Requirements 2.4**

- [x] 5.6 Write property test for admin authentication

  - **Property 10: Admin authentication requirement**
  - Attempt import with non-admin user
  - Verify request is rejected
  - **Validates: Requirements 1.1, Security requirements**

- [x] 6. Frontend components implementation

- [x] 6.1 Create ImportDataButton component

  - Add button to AdminScoringPage
  - Style with primary variant
  - Handle click to open modal
  - Position in page header area
  - _Requirements: 1.1_

- [x] 6.2 Create ImportDataModal component

  - Create modal with configuration form
  - Add season dropdown (2020-2030)
  - Add week selection (all or specific)
  - Add multi-select for specific weeks
  - Add "Grade completed games" checkbox
  - Implement form validation
  - Handle form submission
  - _Requirements: 1.2, 2.1, 2.2, 2.3, 2.4, 3.1_

- [x] 6.3 Create ImportProgressModal component

  - Create modal for progress display
  - Implement polling (every 2 seconds)
  - Display current step and progress bar
  - Show games processed / total games
  - Display statistics counters
  - Show error messages if any
  - Handle completion state
  - Allow closing modal while import runs
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.2, 5.3_

- [x] 6.4 Create ImportHistoryList component

  - Fetch import history from API
  - Display table with recent imports
  - Show season, weeks, status, timestamp
  - Display statistics for each import
  - Highlight running imports
  - Add filter options (season, status)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.5 Integrate components in AdminScoringPage

  - Add ImportDataButton to page header
  - Add ImportHistoryList to page (collapsible section)
  - Wire up modal state management
  - Handle import completion callbacks
  - Refresh games list after import
  - _Requirements: 1.1, 6.1_

- [x] 7. API client functions

- [x] 7.1 Create import API client functions

  - Add startImport() function
  - Add getImportStatus() function
  - Add getImportHistory() function
  - Add proper TypeScript types
  - Handle API errors
  - _Requirements: All API endpoints_

- [x] 7.2 Create React Query hooks

  - Add useStartImport mutation hook
  - Add useImportStatus query hook with polling
  - Add useImportHistory query hook
  - Configure proper cache invalidation
  - _Requirements: All API endpoints_

- [x] 8. Warning and validation features

- [x] 8.1 Implement existing data detection

  - Query database for existing games in selected season/weeks
  - Count games that would be created vs updated
  - Display warning in modal before import
  - Show confirmation dialog if data exists
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 8.2 Write property test for existing data preservation

  - **Property 9: Existing data preservation**
  - Create game with picks
  - Re-import same game
  - Verify picks remain unchanged
  - **Validates: Requirements 8.5**

- [x] 9. Error handling and user feedback

- [x] 9.1 Implement comprehensive error handling

  - Add try-catch blocks in all service methods
  - Log errors with context
  - Return user-friendly error messages
  - Handle network failures with retries
  - Handle database errors with rollback
  - _Requirements: Error handling section_

- [x] 9.2 Add user-facing error messages

  - Display validation errors in modal
  - Show network errors with retry option
  - Display concurrent import errors
  - Show permission denied errors
  - Add toast notifications for all error types
  - _Requirements: Error handling section_

- [x] 10. Testing and validation

- [x] 10.1 Write property test for status transitions

  - **Property 3: Status transition validity**
  - Generate random status transitions
  - Verify only valid transitions occur (pending → running → completed/failed)
  - **Validates: Requirements 4.1, 4.5**

- [x] 10.2 Write property test for statistics consistency

  - **Property 4: Statistics consistency**
  - Generate random import statistics
  - Verify games_created + games_updated = total_games
  - **Validates: Requirements 1.5, 4.4**

- [x] 10.3 Write property test for grading conditional execution

  - **Property 5: Grading conditional execution**
  - Import with grade_games=false
  - Verify games_graded remains 0
  - **Validates: Requirements 3.2, 3.4**

- [x] 10.4 Write integration test for end-to-end import

  - Start import with test season
  - Verify games created in database
  - Verify teams and players created
  - Verify progress tracking works
  - Verify completion statistics

- [x] 10.5 Write integration test for grading

  - Import with grading enabled
  - Verify touchdown scorers identified
  - Verify player records created
  - Verify game.first_td_scorer_player_id set

- [x] 11. Documentation and deployment

- [x] 11.1 Update API documentation

  - Document all import endpoints in Swagger
  - Add request/response examples
  - Document error codes
  - Add authentication requirements
  - _Requirements: All_

- [x] 11.2 Create user guide

  - Document how to use import feature
  - Add screenshots of modal
  - Explain season/week selection
  - Explain grading option
  - Document import history
  - _Requirements: All_

- [x] 11.3 Update admin guide

  - Document import feature administration
  - Explain concurrent import prevention
  - Document troubleshooting steps
  - Add monitoring recommendations
  - _Requirements: All_

- [x] 11.4 Run database migration

  - Test migration in development
  - Review migration SQL
  - Run migration in production
  - Verify indexes created
  - _Requirements: 1_

- [x] 11.5 Deploy and verify

  - Deploy backend code
  - Deploy frontend code
  - Verify import functionality works
  - Test with real NFL data
  - Monitor for errors
  - _Requirements: All_

## Checkpoint

- [x] 12. Final checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.

---

## Implementation Complete

The Admin Data Import feature will be complete when:

- ✅ ImportJob model created and migrated
- ✅ NFLDataImportService implemented with all methods
- ✅ Progress tracking working with Redis
- ✅ Background task execution working
- ✅ All 3 API endpoints functional
- ✅ All 4 frontend components implemented
- ✅ Import modal with configuration working
- ✅ Progress modal with real-time updates working
- ✅ Import history display working
- ✅ Existing data warning working
- ✅ All 10 property-based tests passing
- ✅ Integration tests passing
- ✅ Documentation complete
- ✅ Feature deployed and verified

## Estimated Timeline

- **Day 1:** Tasks 1-2 (Database, service implementation)
- **Day 2:** Tasks 3-4 (Progress tracking, background tasks)
- **Day 3:** Tasks 5-7 (API endpoints, API client)
- **Day 4:** Tasks 6, 8-9 (Frontend components, error handling)
- **Day 5:** Tasks 10-11 (Testing, documentation, deployment)

**Total: 5 days to complete admin data import feature**

## Next Steps

1. Review this implementation plan
2. Start with Task 1: Database setup and models
3. Follow tasks in order
4. Run tests after each major section
5. Deploy to production after all tests pass

---

## Notes

- Optional tasks (marked with \*) are property-based tests and integration tests
- These tests are important for correctness but can be implemented after core functionality
- Focus on core implementation first, then add comprehensive testing
- All property tests should run at least 100 iterations
