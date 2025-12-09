# Requirements Document: Admin Data Import Feature

## Introduction

This feature adds an "Import Data" button to the Admin Scoring Dashboard that allows administrators to import NFL season data from nflreadpy through a user-friendly interface. This eliminates the need to run command-line scripts and provides real-time feedback on the import process.

This implementation will be built as a new, clean service that can eventually replace the existing command-line import scripts (import_2024_data.py, import_2025_data.py), providing a more maintainable and user-friendly solution.

## Glossary

- **Admin Dashboard**: The administrative interface at `/admin/scoring` where admins manage game scoring and picks
- **nflreadpy**: Python library used to fetch NFL game data, schedules, and play-by-play information
- **Import Job**: A background task that fetches NFL data from nflreadpy and populates the database
- **Season Data**: NFL games, teams, players, and touchdown scorer information for a specific season
- **Grading**: The process of fetching play-by-play data to identify touchdown scorers for completed games
- **Import Status**: Real-time progress information about an ongoing import operation

## Requirements

### Requirement 1

**User Story:** As an admin, I want to import NFL season data from the dashboard, so that I can populate the database without using command-line tools.

#### Acceptance Criteria

1. WHEN an admin clicks the "Import Data" button on the Admin Scoring Dashboard THEN the system SHALL display an import configuration modal
2. WHEN the import modal opens THEN the system SHALL display options for season selection, week selection, and grading preference
3. WHEN an admin submits the import form THEN the system SHALL validate the input parameters before starting the import
4. WHEN the import parameters are valid THEN the system SHALL initiate a background import job and display a progress indicator
5. WHEN the import job completes successfully THEN the system SHALL display a success message with import statistics

### Requirement 2

**User Story:** As an admin, I want to select which NFL season and weeks to import, so that I can control the scope of data being imported.

#### Acceptance Criteria

1. WHEN the import modal displays THEN the system SHALL provide a dropdown to select the NFL season year
2. WHEN a season is selected THEN the system SHALL provide options to import all weeks or specific weeks
3. WHEN "specific weeks" is selected THEN the system SHALL display a multi-select input for week numbers
4. WHEN week numbers are entered THEN the system SHALL validate that weeks are between 1 and 18 for regular season
5. WHEN the user selects "all weeks" THEN the system SHALL import the entire season schedule

### Requirement 3

**User Story:** As an admin, I want to choose whether to grade games during import, so that I can fetch touchdown scorer data for completed games.

#### Acceptance Criteria

1. WHEN the import modal displays THEN the system SHALL provide a checkbox option to "Grade completed games"
2. WHEN "Grade completed games" is checked THEN the system SHALL fetch play-by-play data for completed games during import
3. WHEN grading is enabled THEN the system SHALL identify first touchdown scorers and all touchdown scorers
4. WHEN grading is disabled THEN the system SHALL only import game schedules and scores without touchdown data
5. WHEN grading encounters errors THEN the system SHALL continue importing other games and report errors separately

### Requirement 4

**User Story:** As an admin, I want to see real-time progress of the import operation, so that I know the import is working and can estimate completion time.

#### Acceptance Criteria

1. WHEN an import job starts THEN the system SHALL display a progress modal with current status
2. WHEN the import is processing THEN the system SHALL update progress information every 2 seconds
3. WHEN games are being imported THEN the system SHALL display the count of games processed
4. WHEN the import completes THEN the system SHALL display final statistics including teams created, players created, games imported, and games graded
5. WHEN the import fails THEN the system SHALL display error messages and allow the admin to retry

### Requirement 5

**User Story:** As an admin, I want the import to run as a background job, so that I can continue using the dashboard while data is being imported.

#### Acceptance Criteria

1. WHEN an import job is initiated THEN the system SHALL create a background task that runs asynchronously
2. WHEN the import is running THEN the system SHALL allow the admin to close the progress modal and continue using the dashboard
3. WHEN the admin closes the progress modal THEN the system SHALL continue the import in the background
4. WHEN the admin reopens the dashboard THEN the system SHALL display the status of any ongoing import jobs
5. WHEN multiple admins are logged in THEN the system SHALL prevent concurrent import jobs for the same season

### Requirement 6

**User Story:** As an admin, I want to see import history and logs, so that I can track what data has been imported and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the import modal opens THEN the system SHALL display a "Recent Imports" section showing the last 5 import operations
2. WHEN viewing recent imports THEN the system SHALL display the season, weeks imported, timestamp, status, and statistics for each import
3. WHEN an import fails THEN the system SHALL log error details that can be viewed by the admin
4. WHEN viewing import history THEN the system SHALL allow filtering by season and status
5. WHEN an import is in progress THEN the system SHALL display it at the top of the recent imports list with a "Running" status

### Requirement 7

**User Story:** As a developer, I want the import functionality to be built as a new, clean service implementation, so that we can deprecate the old command-line scripts and have a maintainable codebase.

#### Acceptance Criteria

1. WHEN the backend receives an import request THEN the system SHALL use a new NFLDataImportService class that is separate from the command-line scripts
2. WHEN importing data THEN the system SHALL implement clean, well-structured methods for creating teams, players, and games
3. WHEN grading games THEN the system SHALL implement touchdown identification logic using nflreadpy in a reusable service method
4. WHEN the new service is complete THEN the system SHALL allow deprecation of the old import_2024_data.py and import_2025_data.py scripts
5. WHEN the import completes THEN the system SHALL return structured statistics that can be easily consumed by the frontend

### Requirement 8

**User Story:** As an admin, I want to be notified if an import would overwrite existing data, so that I can make informed decisions about re-importing data.

#### Acceptance Criteria

1. WHEN an admin selects a season and weeks that already exist in the database THEN the system SHALL display a warning message
2. WHEN existing data is detected THEN the system SHALL show the count of games that would be updated versus created
3. WHEN the admin confirms the import THEN the system SHALL proceed with updating existing games and creating new ones
4. WHEN the admin cancels THEN the system SHALL close the modal without importing data
5. WHEN games are updated THEN the system SHALL preserve existing pick data and only update game scores and touchdown scorers

## Non-Functional Requirements

### Performance

- Import operations SHALL complete within 5 minutes for a full season import
- Progress updates SHALL be delivered to the client within 2 seconds of status changes
- The UI SHALL remain responsive during import operations

### Security

- Only authenticated admin users SHALL access the import functionality
- Import operations SHALL be logged with the admin user ID and timestamp
- The system SHALL prevent SQL injection and other security vulnerabilities in import parameters

### Reliability

- Import operations SHALL be idempotent (can be run multiple times safely)
- Failed imports SHALL not corrupt existing database data
- The system SHALL handle network failures gracefully and provide retry options

### Usability

- The import modal SHALL be intuitive and require minimal training
- Error messages SHALL be clear and actionable
- The progress indicator SHALL provide meaningful feedback to the user
