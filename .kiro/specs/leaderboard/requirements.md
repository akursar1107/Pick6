# Leaderboard Requirements Document

## Introduction

The Leaderboard feature provides users with a competitive view of standings and rankings for the First6 NFL prediction platform. Users can view season-long standings, weekly rankings, and detailed statistics for all participants. The leaderboard is the primary mechanism for users to track their performance relative to others and adds the competitive element that makes the platform engaging.

## Glossary

- **System**: The First6 leaderboard service
- **User**: A registered participant making touchdown predictions
- **Season Leaderboard**: Rankings based on cumulative points across all weeks
- **Weekly Leaderboard**: Rankings based on points earned in a specific week
- **Total Points**: Sum of FTD points (3 each) and ATTD points (1 each)
- **Win-Loss Record**: Count of winning picks vs losing picks
- **Win Percentage**: Ratio of wins to total graded picks
- **Rank**: User's position in the leaderboard (1st, 2nd, 3rd, etc.)
- **Tie**: When two or more users have the same total points
- **Graded Pick**: A pick with status WIN or LOSS (not PENDING)

## Requirements

### Requirement 1: Season Leaderboard Display

**User Story:** As a user, I want to view the season leaderboard, so that I can see how I rank against other participants for the entire season.

#### Acceptance Criteria

1. WHEN a user views the season leaderboard THEN the System SHALL display all users ranked by total points in descending order
2. WHEN displaying user rankings THEN the System SHALL show rank, username, total points, FTD points, ATTD points, wins, losses, and win percentage
3. WHEN two users have equal total points THEN the System SHALL rank the user with more wins higher
4. WHEN two users have equal total points and equal wins THEN the System SHALL rank them as tied with the same rank number
5. WHEN calculating win percentage THEN the System SHALL divide wins by total graded picks and multiply by 100

### Requirement 2: Weekly Leaderboard Display

**User Story:** As a user, I want to view weekly leaderboards, so that I can see who performed best in specific weeks.

#### Acceptance Criteria

1. WHEN a user selects a specific week THEN the System SHALL display rankings based only on points earned in that week
2. WHEN displaying weekly rankings THEN the System SHALL show rank, username, weekly points, weekly wins, and weekly losses
3. WHEN a week has no graded picks THEN the System SHALL display a message indicating no data is available for that week
4. WHEN calculating weekly rankings THEN the System SHALL only include picks from games in the selected week
5. WHEN two users have equal weekly points THEN the System SHALL apply the same tie-breaking rules as the season leaderboard

### Requirement 3: User Statistics Display

**User Story:** As a user, I want to view detailed statistics for any participant, so that I can analyze performance trends and pick history.

#### Acceptance Criteria

1. WHEN a user clicks on a username in the leaderboard THEN the System SHALL display detailed statistics for that user
2. WHEN displaying user statistics THEN the System SHALL show total points, FTD record, ATTD record, best week, worst week, and current streak
3. WHEN calculating best week THEN the System SHALL identify the week with the highest points earned
4. WHEN calculating worst week THEN the System SHALL identify the week with the lowest points earned among weeks with graded picks
5. WHEN calculating current streak THEN the System SHALL count consecutive wins or losses from the most recent graded pick

### Requirement 4: Current User Highlighting

**User Story:** As a user, I want my position in the leaderboard to be visually highlighted, so that I can quickly find my ranking.

#### Acceptance Criteria

1. WHEN a logged-in user views the leaderboard THEN the System SHALL highlight the row containing their username
2. WHEN the current user is not visible in the viewport THEN the System SHALL provide a way to scroll to their position
3. WHEN the current user has no graded picks THEN the System SHALL display their row at the bottom with zero points
4. WHEN highlighting the current user THEN the System SHALL use a distinct visual style that differs from other rows
5. WHEN the user is not logged in THEN the System SHALL display the leaderboard without any highlighting

### Requirement 5: Real-time Updates

**User Story:** As a user, I want the leaderboard to update when games are scored, so that I see current standings without refreshing.

#### Acceptance Criteria

1. WHEN a game is scored THEN the System SHALL recalculate affected user rankings within 5 seconds
2. WHEN rankings change THEN the System SHALL update the leaderboard display for all viewing users
3. WHEN a pick is manually overridden THEN the System SHALL immediately recalculate rankings
4. WHEN multiple games are scored simultaneously THEN the System SHALL process all updates and recalculate rankings once
5. WHEN the leaderboard is being updated THEN the System SHALL display a loading indicator

### Requirement 6: Leaderboard Filtering and Sorting

**User Story:** As a user, I want to filter and sort the leaderboard, so that I can view data in different ways.

#### Acceptance Criteria

1. WHEN a user selects a week filter THEN the System SHALL display only data for that week
2. WHEN a user selects "All Weeks" THEN the System SHALL display season-long cumulative data
3. WHEN a user clicks a column header THEN the System SHALL sort the leaderboard by that column
4. WHEN sorting by a column THEN the System SHALL toggle between ascending and descending order
5. WHEN the leaderboard is sorted by a non-points column THEN the System SHALL maintain tie-breaking rules for equal values

### Requirement 7: Mobile Responsiveness

**User Story:** As a user, I want to view the leaderboard on my mobile device, so that I can check standings on the go.

#### Acceptance Criteria

1. WHEN a user views the leaderboard on a mobile device THEN the System SHALL display a responsive layout optimized for small screens
2. WHEN displaying on mobile THEN the System SHALL prioritize showing rank, username, and total points
3. WHEN additional statistics are hidden on mobile THEN the System SHALL provide a way to expand and view full details
4. WHEN scrolling the leaderboard on mobile THEN the System SHALL keep the header row fixed at the top
5. WHEN the leaderboard has many users THEN the System SHALL implement virtual scrolling for performance

### Requirement 8: Performance and Caching

**User Story:** As a system administrator, I want the leaderboard to load quickly, so that users have a smooth experience.

#### Acceptance Criteria

1. WHEN a user requests the leaderboard THEN the System SHALL return results within 500 milliseconds
2. WHEN rankings have not changed THEN the System SHALL serve cached leaderboard data
3. WHEN a game is scored THEN the System SHALL invalidate the leaderboard cache
4. WHEN calculating rankings for 100+ users THEN the System SHALL complete within 2 seconds
5. WHEN the database query is slow THEN the System SHALL return cached data with a staleness indicator

### Requirement 9: Empty State Handling

**User Story:** As a user, I want to see helpful messages when there is no leaderboard data, so that I understand why the leaderboard is empty.

#### Acceptance Criteria

1. WHEN no users have graded picks THEN the System SHALL display a message indicating the season has not started
2. WHEN a selected week has no games THEN the System SHALL display a message indicating no games for that week
3. WHEN all picks for a week are pending THEN the System SHALL display a message indicating games are in progress
4. WHEN displaying an empty state THEN the System SHALL provide a call-to-action to submit picks
5. WHEN the leaderboard has data but a filter returns no results THEN the System SHALL display a message suggesting to adjust filters

### Requirement 10: Leaderboard Export

**User Story:** As a user, I want to export leaderboard data, so that I can share standings or analyze data offline.

#### Acceptance Criteria

1. WHEN a user clicks the export button THEN the System SHALL generate a CSV file with leaderboard data
2. WHEN exporting THEN the System SHALL include all visible columns in the current view
3. WHEN exporting weekly data THEN the System SHALL include the week number in the filename
4. WHEN exporting season data THEN the System SHALL include the season year in the filename
5. WHEN the export is ready THEN the System SHALL automatically download the file to the user's device
