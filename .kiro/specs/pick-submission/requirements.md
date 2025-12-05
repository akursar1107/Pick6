# Requirements Document: Pick Submission & Management

## Introduction

This feature enables users to submit, view, edit, and delete their First Touchdown (FTD) and Anytime Touchdown (ATTD) predictions for NFL games. Users can manage their picks before game kickoff, with validation ensuring data integrity and preventing duplicate or late submissions. The system provides a seamless user experience for the core prediction workflow.

## Glossary

- **Pick System**: The software component responsible for managing user predictions
- **User**: An authenticated person who submits predictions
- **Pick**: A user's prediction of which player will score a touchdown in a game (counts for both FTD and ATTD)
- **FTD**: First Touchdown - scoring category for the first touchdown in a game
- **ATTD**: Anytime Touchdown - scoring category for any touchdown during a game
- **Game**: An NFL game with scheduled kickoff time
- **Player**: An NFL player eligible to score touchdowns
- **Kickoff Time**: The scheduled start time of an NFL game
- **Pick Window**: The time period before kickoff when picks can be submitted or modified
- **Duplicate Pick**: Multiple picks for the same game by the same user

## Requirements

### Requirement 1

**User Story:** As a user, I want to submit a player pick for an upcoming game, so that I can participate in the prediction competition for both First Touchdown and Anytime Touchdown.

#### Acceptance Criteria

1. WHEN a user submits a valid pick before kickoff, THE Pick System SHALL create the pick record with pending status
2. WHEN a user submits a pick, THE Pick System SHALL capture the submission timestamp
3. WHEN a user submits a pick, THE Pick System SHALL associate the pick with the authenticated user's ID
4. WHEN a user submits a pick, THE Pick System SHALL store the selected player ID and game ID
5. IF a user attempts to submit a pick after kickoff, THEN THE Pick System SHALL reject the submission and return an error message
6. WHEN a pick is created, THE Pick System SHALL automatically register it for both FTD and ATTD scoring categories

### Requirement 2

**User Story:** As a user, I want to view all my submitted picks, so that I can track my predictions.

#### Acceptance Criteria

1. WHEN a user requests their picks, THE Pick System SHALL return all picks associated with that user's ID
2. WHEN displaying picks, THE Pick System SHALL include game information, player information, and submission timestamp
3. WHEN a user requests picks for a specific game, THE Pick System SHALL filter results to show only picks for that game
4. WHEN a user has no picks, THE Pick System SHALL return an empty list

### Requirement 3

**User Story:** As a user, I want to edit my pick before the game starts, so that I can change my prediction if needed.

#### Acceptance Criteria

1. WHEN a user updates a pick before kickoff, THE Pick System SHALL modify the pick record with the new player selection
2. WHEN a user updates a pick, THE Pick System SHALL update the modification timestamp
3. IF a user attempts to update a pick after kickoff, THEN THE Pick System SHALL reject the update and return an error message
4. WHEN a user updates a pick, THE Pick System SHALL preserve the original submission timestamp

### Requirement 4

**User Story:** As a user, I want to delete my pick before the game starts, so that I can remove a prediction I no longer want to make.

#### Acceptance Criteria

1. WHEN a user deletes a pick before kickoff, THE Pick System SHALL remove the pick record from the database
2. IF a user attempts to delete a pick after kickoff, THEN THE Pick System SHALL reject the deletion and return an error message
3. WHEN a user deletes a non-existent pick, THE Pick System SHALL return an error message

### Requirement 5

**User Story:** As a user, I want the system to prevent me from submitting duplicate picks, so that I don't accidentally make multiple predictions for one game.

#### Acceptance Criteria

1. WHEN a user attempts to submit a second pick for the same game, THE Pick System SHALL reject the submission and return an error message
2. WHEN checking for duplicates, THE Pick System SHALL consider only the combination of user ID and game ID
3. WHEN a user updates an existing pick, THE Pick System SHALL allow the modification without treating it as a duplicate

### Requirement 6

**User Story:** As a user, I want to search for players when making a pick, so that I can easily find and select the player I want to predict.

#### Acceptance Criteria

1. WHEN a user searches for a player by name, THE Pick System SHALL return matching players ordered by relevance
2. WHEN displaying player search results, THE Pick System SHALL include player name, team, and position
3. WHEN a user searches with an empty query, THE Pick System SHALL return an empty list
4. WHEN a user searches for a non-existent player, THE Pick System SHALL return an empty list

### Requirement 7

**User Story:** As a user, I want to see which games are available for picks, so that I can choose which games to make predictions for.

#### Acceptance Criteria

1. WHEN a user requests available games, THE Pick System SHALL return all scheduled games with kickoff times in the future
2. WHEN displaying available games, THE Pick System SHALL include home team, away team, kickoff time, and game week
3. WHEN a game's kickoff time has passed, THE Pick System SHALL exclude it from available games
4. WHEN displaying available games, THE Pick System SHALL order them by kickoff time ascending

### Requirement 8

**User Story:** As a user, I want to see my existing picks when viewing available games, so that I know which games I've already made predictions for.

#### Acceptance Criteria

1. WHEN a user views available games, THE Pick System SHALL indicate which games have existing picks
2. WHEN displaying existing picks with games, THE Pick System SHALL include the selected player name

### Requirement 9

**User Story:** As a system administrator, I want all pick operations to validate user authentication, so that only authorized users can manage picks.

#### Acceptance Criteria

1. WHEN an unauthenticated user attempts to create a pick, THE Pick System SHALL reject the request and return an authentication error
2. WHEN an unauthenticated user attempts to view picks, THE Pick System SHALL reject the request and return an authentication error
3. WHEN a user attempts to modify another user's pick, THE Pick System SHALL reject the request and return an authorization error
4. WHEN a user attempts to delete another user's pick, THE Pick System SHALL reject the request and return an authorization error
