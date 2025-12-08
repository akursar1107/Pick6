# Leaderboard Implementation Plan

## Task List

- [x] 1. Set up leaderboard service and data models

  - Create LeaderboardService class with dependency injection
  - Define Pydantic models (LeaderboardEntry, UserStats, WeekPerformance, Streak)
  - Set up Redis cache client configuration
  - _Requirements: 1.1, 1.2_

    - [x] 1.1 Write property test for ranking order

    - **Property 1: Ranking order correctness**
    - **Validates: Requirements 1.1**

- [-] 2. Implement core ranking calculation logic

  - [x] 2.1 Implement calculate_rankings method

    - Group picks by user
    - Calculate FTD points (3 per win)
    - Calculate ATTD points (1 per win)
    - Count wins and losses
    - Sort by total points descending, then wins descending
    - _Requirements: 1.1, 1.5_

  - [-] 2.2 Write property test for tie-breaking by wins

    - **Property 2: Tie-breaking by wins**
    - **Validates: Requirements 1.3**

  - [ ] 2.3 Write property test for tied rank assignment
    - **Property 3: Tied rank assignment**
    - **Validates: Requirements 1.4**
  - [x] 2.4 Implement rank assignment with tie handling

    - Assign ranks based on sorted order
    - Handle ties (same points + same wins = same rank)
    - Set is_tied flag for tied users
    - _Requirements: 1.3, 1.4_

  - [ ] 2.5 Write property test for win percentage calculation
    - **Property 4: Win percentage calculation**
    - **Validates: Requirements 1.5**
  - [x] 2.6 Implement win percentage calculation

    - Calculate (wins / total_graded_picks) \* 100
    - Handle division by zero (no graded picks)
    - Round to 2 decimal places
    - _Requirements: 1.5_

- [x] 3. Implement season leaderboard

  - [x] 3.1 Implement get_season_leaderboard method

    - Query all picks for season
    - Filter to graded picks only (WIN or LOSS)
    - Call calculate_rankings
    - Return LeaderboardEntry list
    - _Requirements: 1.1, 1.2_

  - [x] 3.2 Write property test for required fields presence

    - **Property 6: Required fields presence**
    - **Validates: Requirements 1.2, 2.2**

  - [x] 3.3 Add database query optimization

    - Use aggregation in SQL query
    - Add indexes on (pick.status, pick.user_id)
    - Add indexes on (game.season, game.week_number)
    - Use GROUP BY for efficient counting
    - _Requirements: 8.1_

- [-] 4. Implement weekly leaderboard

  - [x] 4.1 Implement get_weekly_leaderboard method

    - Query picks for specific season and week

    - Filter to graded picks only
    - Call calculate_rankings
    - Return LeaderboardEntry list
    - _Requirements: 2.1, 2.2_

  - [x] 4.2 Write property test for week filtering

    - **Property 5: Week filtering correctness**
    - **Validates: Requirements 2.1, 2.4, 6.1**

  - [x] 4.3 Write property test for tie-breaking consistency

    - **Property 7: Tie-breaking consistency**
    - **Validates: Requirements 2.5**

  - [x] 4.4 Handle empty week scenario

    - Check if week has any graded picks
    - Return empty list with metadata if no picks
    - _Requirements: 2.3, 9.2_

- [x] 5. Implement user statistics

  - [x] 5.1 Implement get_user_stats method

    - Query all picks for user
    - Calculate total points, wins, losses
    - Calculate FTD and ATTD breakdowns
    - Calculate win percentages
    - _Requirements: 3.1, 3.2_

  - [x] 5.2 Write property test for best/worst week identification

    - **Property 8: Best and worst week identification**
    - **Validates: Requirements 3.3, 3.4**

  - [x] 5.3 Implement weekly performance breakdown

    - Group picks by week
    - Calculate points per week
    - Identify best week (max points)
    - Identify worst week (min points, excluding zero)
    - _Requirements: 3.3, 3.4_

  - [x] 5.4 Write property test for streak calculation

    - **Property 9: Streak calculation**
    - **Validates: Requirements 3.5**

  - [x] 5.5 Implement streak calculation

    - Order picks by date descending
    - Count consecutive wins or losses from most recent
    - Track longest win streak and longest loss streak
    - _Requirements: 3.5_

  - [x] 5.6 Write property test for user stats field presence

    - **Property 10: User stats field presence**
    - **Validates: Requirements 3.2**

- [x] 6. Implement caching layer

  - [x] 6.1 Implement cache key generation

    - Season leaderboard: `leaderboard:season:{season}`
    - Weekly leaderboard: `leaderboard:week:{season}:{week}`
    - User stats: `user:stats:{user_id}:{season}`
    - _Requirements: 8.2_

  - [x] 6.2 Write property test for cache hit when unchanged

    - **Property 13: Cache hit when unchanged**
    - **Validates: Requirements 8.2**

  - [x] 6.3 Implement cache get/set logic

    - Check cache before calculation
    - Set cache after calculation with 5-minute TTL
    - Serialize/deserialize LeaderboardEntry objects
    - _Requirements: 8.2_

  - [x] 6.4 Write property test for cache invalidation

    - **Property 12: Cache invalidation on score**
    - **Validates: Requirements 5.3, 8.3**

  - [x] 6.5 Implement cache invalidation

    - Invalidate on game scoring
    - Invalidate on pick override
    - Invalidate specific keys (season, week, user)
    - _Requirements: 5.3, 8.3_

  - [x] 6.6 Write property test for batch update efficiency

    - **Property 11: Batch update efficiency**
    - **Validates: Requirements 5.4**

  - [x] 6.7 Implement batch invalidation

    - Collect all affected cache keys
    - Invalidate all keys in single operation
    - Avoid multiple recalculations
    - _Requirements: 5.4_

- [x] 7. Create API endpoints

  - [x] 7.1 Create GET /api/v1/leaderboard/season/{season}

    - Validate season parameter
    - Call LeaderboardService.get_season_leaderboard
    - Return JSON response with LeaderboardEntry list
    - Add Swagger documentation
    - _Requirements: 1.1, 1.2_

  - [x] 7.2 Create GET /api/v1/leaderboard/week/{season}/{week}

    - Validate season and week parameters
    - Call LeaderboardService.get_weekly_leaderboard
    - Return JSON response with LeaderboardEntry list
    - Add Swagger documentation
    - _Requirements: 2.1, 2.2_

  - [x] 7.3 Create GET /api/v1/leaderboard/user/{user_id}/stats

    - Validate user_id parameter
    - Optional season query parameter
    - Call LeaderboardService.get_user_stats
    - Return JSON response with UserStats
    - Add Swagger documentation
    - _Requirements: 3.1, 3.2_

  - [x] 7.4 Create GET /api/v1/leaderboard/export/{season}

    - Optional week query parameter
    - Optional format query parameter (csv/json)
    - Generate CSV or JSON file
    - Set appropriate headers for download
    - Add Swagger documentation
    - _Requirements: 10.1, 10.2_

  - [x] 7.5 Write property test for export column matching

    - **Property 15: Export column matching**
    - **Validates: Requirements 10.2**

  - [x] 7.6 Write property test for export filename generation

    - **Property 16: Export filename generation**
    - **Validates: Requirements 10.3, 10.4**

  - [x] 7.7 Implement error handling for all endpoints

    - Handle invalid season (400)
    - Handle invalid week (400)
    - Handle user not found (404)
    - Handle database errors (503)
    - Return consistent error format
    - _Requirements: All_

  - [x] 7.8 Write unit tests for API endpoints

    - Test successful responses
    - Test error responses
    - Test parameter validation
    - Test authentication
    - _Requirements: All_

- [x] 8. Build frontend leaderboard page

  - [x] 8.1 Create LeaderboardPage component

    - Set up tab state (Season/Weekly)
    - Add week selector dropdown
    - Implement data fetching with React Query
    - Handle loading and error states
    - _Requirements: 1.1, 2.1_

  - [x] 8.2 Create LeaderboardTable component

    - Display rank, username, points, wins, losses, win %
    - Implement responsive column display
    - Add sorting by column headers
    - Highlight current user's row
    - _Requirements: 1.2, 4.1, 6.3_

  - [x] 8.3 Write property test for sort order preservation

    - **Property 14: Sort order preservation with tie-breaking**
    - **Validates: Requirements 6.5**

  - [x] 8.4 Implement column sorting

    - Toggle ascending/descending on header click
    - Maintain tie-breaking rules when sorting
    - Show sort indicator (arrow icon)
    - _Requirements: 6.3, 6.4, 6.5_

  - [x] 8.5 Implement current user highlighting

    - Check if row user matches logged-in user
    - Apply highlight CSS class
    - Add scroll-to-position button if not visible
    - _Requirements: 4.1, 4.2_

  - [x] 8.6 Create WeekSelector component

    - Dropdown with weeks 1-18
    - Show "All Weeks" option for season view
    - Highlight current week
    - _Requirements: 2.1, 6.1, 6.2_

  - [x] 8.7 Implement mobile responsive design

    - Stack columns on small screens
    - Show priority columns (rank, username, points)
    - Add expandable rows for full details
    - Fix header row on scroll
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 9. Build user statistics modal

  - [x] 9.1 Create UserStatsModal component

    - Display on username click
    - Show all UserStats fields
    - Add close button
    - _Requirements: 3.1, 3.2_

  - [x] 9.2 Create stats display sections

    - Overall stats card (points, W-L, win %)
    - FTD stats card
    - ATTD stats card
    - Best/worst week display
    - Current streak badge
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

  - [x] 9.3 Create weekly performance chart

    - Bar chart showing points per week
    - Highlight best and worst weeks
    - Show trend line
    - _Requirements: 3.3, 3.4_

- [x] 10. Implement export functionality

  - [x] 10.1 Add export button to leaderboard

    - Position in header area
    - Show dropdown for format (CSV/JSON)
    - Disable when no data
    - _Requirements: 10.1_

  - [x] 10.2 Implement CSV generation

    - Include all visible columns
    - Add headers row
    - Format data appropriately
    - Generate filename with season/week
    - _Requirements: 10.2, 10.3, 10.4_

  - [x] 10.3 Implement download trigger

    - Create blob from CSV data
    - Trigger browser download
    - Show success toast
    - _Requirements: 10.5_

- [x] 11. Implement empty states

  - [x] 11.1 Create EmptyState component

    - Reusable component for different scenarios
    - Show icon, message, and CTA
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 11.2 Add empty state for no graded picks

    - "Season hasn't started yet" message
    - CTA to submit picks
    - _Requirements: 9.1_

  - [x] 11.3 Add empty state for no games in week

    - "No games this week" message
    - _Requirements: 9.2_

  - [x] 11.4 Add empty state for pending picks

    - "Games in progress" message
    - Show loading indicator
    - _Requirements: 9.3_

  - [x] 11.5 Add empty state for no filter results

    - "No results found" message
    - Suggest adjusting filters
    - _Requirements: 9.5_

- [x] 12. Implement real-time updates

  - [x] 12.1 Set up React Query polling

    - Poll every 30 seconds
    - Refetch on window focus
    - Show loading indicator during update
    - _Requirements: 5.1, 5.2, 5.5_

  - [x] 12.2 Add manual refresh button

    - Icon button in header
    - Trigger immediate refetch
    - Show loading state
    - _Requirements: 5.2_

  - [x] 12.3 Integrate with scoring events

    - Listen for game scored events
    - Invalidate React Query cache
    - Trigger refetch
    - _Requirements: 5.1, 5.3_

- [x] 13. Add database indexes

  - [x] 13.1 Create migration for indexes

    - Index on (picks.status, picks.user_id)
    - Index on (games.season, games.week_number)
    - _Requirements: 8.1, 8.4_

  - [x] 13.2 Test query performance

    - Measure query time with 100+ users
    - Verify index usage with EXPLAIN
    - Optimize if needed
    - _Requirements: 8.1, 8.4_

- [x] 14. Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Integration testing

  - [x] 15.1 Test full leaderboard flow

    - Create users and picks
    - Score games
    - Verify rankings update
    - _Requirements: All_

  - [x] 15.2 Test cache behavior

    - Verify cache hits
    - Verify cache invalidation
    - Verify fallback to database
    - _Requirements: 8.2, 8.3_

  - [x] 15.3 Test export functionality

    - Export season leaderboard
    - Export weekly leaderboard
    - Verify CSV format
    - Verify filename
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 15.4 Test mobile responsiveness

    - Test on various screen sizes
    - Verify column visibility
    - Verify expandable rows
    - Verify fixed header
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 16. Documentation and deployment

  - [x] 16.1 Update API documentation

    - Document all endpoints in Swagger
    - Add request/response examples
    - Document error codes
    - _Requirements: All_

  - [x] 16.2 Create user guide

    - How to view leaderboard
    - How to interpret stats
    - How to export data
    - _Requirements: All_

  - [x] 16.3 Create admin guide

    - Cache management
    - Performance monitoring
    - Troubleshooting
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 16.4 Deploy to production

    - Run database migrations
    - Deploy backend code
    - Deploy frontend code
    - Verify functionality
    - Monitor performance
    - _Requirements: All_

## Implementation Complete

The Leaderboard feature will be complete when:

- ✅ All database indexes created
- ✅ LeaderboardService implemented with all methods
- ✅ Caching layer working with Redis
- ✅ All 16 property-based tests passing
- ✅ API endpoints functional
- ✅ Frontend UI displaying leaderboards
- ✅ User statistics modal working
- ✅ Export functionality working
- ✅ Real-time updates working
- ✅ Mobile responsive design
- ✅ Documentation complete

## Estimated Timeline

- **Day 1:** Tasks 1-3 (Service setup, ranking logic, season leaderboard)
- **Day 2:** Tasks 4-6 (Weekly leaderboard, user stats, caching)
- **Day 3:** Tasks 7-8 (API endpoints, frontend page)
- **Day 4:** Tasks 9-12 (Stats modal, export, empty states, real-time)
- **Day 5:** Tasks 13-16 (Indexes, testing, documentation, deployment)

**Total: 5 days to complete leaderboard feature**

## Next Steps

1. Review this implementation plan
2. Start with Task 1: Set up leaderboard service
3. Follow tasks in order
4. Run tests after each major section
5. Deploy to production after all tests pass
