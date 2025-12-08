# Requirements Document: Scoring System

## Introduction

This feature enables automatic scoring of user picks when NFL games complete. The system fetches game results and touchdown scorer data from nflreadpy, evaluates each pick against the actual game outcomes, awards points based on correctness, and updates user standings. The scoring system runs on a scheduled basis (daily at 1:59 AM EST, and on Sundays at 4:30 PM and 8:30 PM EST) to ensure timely grading of picks.

## Glossary

- **Scoring System**: The software component responsible for grading picks and calculating user points
- **Pick**: A user's prediction of which player will score a touchdown in a game
- **FTD (First Touchdown)**: The first touchdown scored in a game, worth 3 points if predicted correctly
- **ATTD (Anytime Touchdown)**: Any touchdown scored during a game, worth 1 point if predicted correctly
- **Game Result**: The final outcome of an NFL game including all touchdown scorers
- **Pick Status**: The state of a pick (pending, win, loss)
- **User Score**: The total points accumulated by a user across all graded picks
- **Touchdown Scorer**: A player who scored a touchdown in a game
- **First Touchdown Scorer**: The player who scored the first touchdown in a game
- **Scheduled Job**: An automated task that runs at specific times to fetch data and grade picks
- **nflreadpy**: The Python library used to fetch NFL game data and statistics

## Requirements

### Requirement 1

**User Story:** As a user, I want my picks to be automatically graded when games complete, so that I can see my results without manual intervention.

#### Acceptance Criteria

1. WHEN a game reaches final status, THE Scoring System SHALL identify all pending picks for that game
2. WHEN grading picks, THE Scoring System SHALL fetch touchdown scorer data from nflreadpy
3. WHEN grading picks, THE Scoring System SHALL update each pick's status to win or loss based on correctness
4. WHEN grading picks, THE Scoring System SHALL record the grading timestamp
5. WHEN a pick is graded, THE Scoring System SHALL not change the pick's status again for the same game

### Requirement 2

**User Story:** As a user, I want to earn 3 points for correctly predicting the first touchdown scorer, so that I am rewarded for accurate FTD predictions.

#### Acceptance Criteria

1. WHEN a user's pick matches the first touchdown scorer, THE Scoring System SHALL award 3 points to the user
2. WHEN calculating FTD points, THE Scoring System SHALL compare the pick's player_id with the first touchdown scorer's player_id
3. WHEN a user's pick does not match the first touchdown scorer, THE Scoring System SHALL award 0 points for FTD
4. WHEN awarding FTD points, THE Scoring System SHALL update the user's total score

### Requirement 3

**User Story:** As a user, I want to earn 1 point if my picked player scores any touchdown, so that I am rewarded for ATTD predictions.

#### Acceptance Criteria

1. WHEN a user's pick matches any touchdown scorer in the game, THE Scoring System SHALL award 1 point to the user
2. WHEN calculating ATTD points, THE Scoring System SHALL compare the pick's player_id with all touchdown scorers' player_ids
3. WHEN a user's pick does not match any touchdown scorer, THE Scoring System SHALL award 0 points for ATTD
4. WHEN awarding ATTD points, THE Scoring System SHALL update the user's total score

### Requirement 4

**User Story:** As a user, I want my pick to be marked as a loss if my player doesn't score, so that I have clear feedback on incorrect predictions.

#### Acceptance Criteria

1. WHEN a user's pick does not match the first touchdown scorer AND does not match any touchdown scorer, THE Scoring System SHALL mark the pick as loss
2. WHEN a user's pick does not match any touchdown scorer, THE Scoring System SHALL award 0 total points
3. WHEN marking a pick as loss, THE Scoring System SHALL update the pick status from pending to loss

### Requirement 5

**User Story:** As a user, I want my pick to be marked as a win if my player scores, so that I have clear feedback on correct predictions.

#### Acceptance Criteria

1. WHEN a user's pick matches the first touchdown scorer OR matches any touchdown scorer, THE Scoring System SHALL mark the pick as win
2. WHEN marking a pick as win, THE Scoring System SHALL update the pick status from pending to win
3. WHEN a pick is marked as win, THE Scoring System SHALL record the total points awarded (FTD + ATTD)

### Requirement 6

**User Story:** As a user, I want my pick to be graded as a loss if no touchdowns are scored in the game, so that the system handles edge cases appropriately.

#### Acceptance Criteria

1. WHEN a game completes with zero touchdowns, THE Scoring System SHALL mark all picks for that game as loss
2. WHEN a game has zero touchdowns, THE Scoring System SHALL award 0 points to all picks for that game
3. WHEN grading picks for a game with no touchdowns, THE Scoring System SHALL update all pick statuses from pending to loss

### Requirement 7

**User Story:** As a system administrator, I want the scoring system to fetch game data automatically on a schedule, so that picks are graded without manual intervention.

#### Acceptance Criteria

1. THE Scoring System SHALL fetch upcoming game data from nflreadpy daily at 1:59 AM EST
2. THE Scoring System SHALL fetch game results and touchdown data from nflreadpy on Sundays at 4:30 PM EST
3. THE Scoring System SHALL fetch game results and touchdown data from nflreadpy on Sundays at 8:30 PM EST
4. WHEN a scheduled job runs, THE Scoring System SHALL log the execution time and results
5. WHEN a scheduled job fails, THE Scoring System SHALL log the error and continue operation

### Requirement 8

**User Story:** As a system administrator, I want to view which games have been scored, so that I can verify the system is working correctly.

#### Acceptance Criteria

1. WHEN requesting scored games, THE Scoring System SHALL return all games with status marked as scored
2. WHEN displaying scored games, THE Scoring System SHALL include the scoring timestamp
3. WHEN displaying scored games, THE Scoring System SHALL include the number of picks graded
4. WHEN displaying scored games, THE Scoring System SHALL include the first touchdown scorer

### Requirement 9

**User Story:** As a system administrator, I want to manually trigger scoring for a specific game, so that I can handle edge cases or API failures.

#### Acceptance Criteria

1. WHEN an administrator triggers manual scoring for a game, THE Scoring System SHALL grade all pending picks for that game
2. WHEN manually scoring a game, THE Scoring System SHALL use the same grading logic as automatic scoring
3. WHEN manually scoring a game, THE Scoring System SHALL allow the administrator to specify the first touchdown scorer
4. WHEN manually scoring a game, THE Scoring System SHALL allow the administrator to specify all touchdown scorers

### Requirement 10

**User Story:** As a system administrator, I want to override a pick's score, so that I can correct errors or handle disputes.

#### Acceptance Criteria

1. WHEN an administrator overrides a pick's score, THE Scoring System SHALL update the pick status to the specified value
2. WHEN an administrator overrides a pick's score, THE Scoring System SHALL update the user's total score accordingly
3. WHEN an administrator overrides a pick's score, THE Scoring System SHALL record the override timestamp and administrator ID
4. WHEN an administrator overrides a pick's score, THE Scoring System SHALL mark the pick as manually overridden

### Requirement 11

**User Story:** As a user, I want to see my total score across all games, so that I can track my overall performance.

#### Acceptance Criteria

1. WHEN a user requests their total score, THE Scoring System SHALL calculate the sum of all points from graded picks
2. WHEN calculating total score, THE Scoring System SHALL include both FTD and ATTD points
3. WHEN calculating total score, THE Scoring System SHALL only include picks with status win
4. WHEN displaying total score, THE Scoring System SHALL include the number of wins and losses

### Requirement 12

**User Story:** As a user, I want to see the result of each individual pick, so that I can understand how I earned or lost points.

#### Acceptance Criteria

1. WHEN a user requests pick results, THE Scoring System SHALL return the pick status (win or loss)
2. WHEN displaying pick results, THE Scoring System SHALL include the points awarded (FTD and ATTD separately)
3. WHEN displaying pick results, THE Scoring System SHALL include the actual first touchdown scorer
4. WHEN displaying pick results, THE Scoring System SHALL include all touchdown scorers for the game

### Requirement 13

**User Story:** As a developer, I want the scoring system to handle API failures gracefully, so that temporary outages don't break the application.

#### Acceptance Criteria

1. WHEN nflreadpy API calls fail, THE Scoring System SHALL log the error with details
2. WHEN nflreadpy API calls fail, THE Scoring System SHALL retry up to 3 times with exponential backoff
3. WHEN nflreadpy API calls fail after retries, THE Scoring System SHALL continue operation without crashing
4. WHEN nflreadpy API calls fail, THE Scoring System SHALL send an alert notification to administrators

### Requirement 14

**User Story:** As a developer, I want the scoring system to validate data from nflreadpy, so that incorrect data doesn't corrupt pick results.

#### Acceptance Criteria

1. WHEN receiving game data from nflreadpy, THE Scoring System SHALL verify the game exists in the database
2. WHEN receiving touchdown scorer data, THE Scoring System SHALL verify each player exists in the database
3. WHEN receiving invalid data from nflreadpy, THE Scoring System SHALL log a validation error
4. WHEN receiving invalid data from nflreadpy, THE Scoring System SHALL skip grading for that game until valid data is available

### Requirement 15

**User Story:** As a user, I want the scoring system to handle multiple touchdowns by the same player correctly, so that my ATTD points are accurate.

#### Acceptance Criteria

1. WHEN a player scores multiple touchdowns in a game, THE Scoring System SHALL award ATTD points only once per pick
2. WHEN calculating ATTD points, THE Scoring System SHALL check if the player appears in the touchdown scorers list
3. WHEN a player scores multiple touchdowns, THE Scoring System SHALL not award multiple ATTD points for the same pick

### Requirement 16

**User Story:** As a user, I want my pick to earn both FTD and ATTD points if my player scores the first touchdown, so that I am rewarded for the most accurate prediction.

#### Acceptance Criteria

1. WHEN a user's pick matches the first touchdown scorer, THE Scoring System SHALL award both FTD points (3) and ATTD points (1)
2. WHEN calculating total points for a first touchdown scorer pick, THE Scoring System SHALL sum FTD and ATTD points to 4 total points
3. WHEN a pick earns both FTD and ATTD points, THE Scoring System SHALL record both point types separately
