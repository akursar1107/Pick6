# Frontend Testing Guide - Scoring System

## Overview

This guide provides step-by-step instructions for testing all frontend functionality of the scoring system.

## Prerequisites

- Frontend running at http://localhost:3000
- Backend API running at http://localhost:8000
- Test user account credentials
- Admin account credentials (for admin features)
- At least one game with picks in the database

## Testing Checklist

### 1. User Score Card Component ✓

**Location**: Displayed on user profile/dashboard

**Component**: `UserScoreCard.tsx`

**What to Test**:

- [ ] Score card displays correctly
- [ ] Total score shows correct value
- [ ] Wins count is accurate
- [ ] Losses count is accurate
- [ ] Win percentage calculated correctly
- [ ] Loading state displays while fetching
- [ ] Error state displays if API fails
- [ ] Card updates after new picks are graded

**Test Steps**:

1. Log in to the application
2. Navigate to your profile/dashboard
3. Verify the score card is visible
4. Check that all values are displayed
5. Refresh the page and verify data persists
6. Compare values with database/API response

**Expected Display**:

```
┌─────────────────────────┐
│   Your Score            │
├─────────────────────────┤
│ Total Points:    42     │
│ Wins:            10     │
│ Losses:          5      │
│ Win %:           66.7%  │
└─────────────────────────┘
```

**API Endpoint**: `GET /api/v1/scores/user/{user_id}`

**Test with curl**:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/scores/user/USER_ID
```

---

### 2. My Picks with Results

**Location**: `/picks` page

**Component**: `MyPicks.tsx` (enhanced with scoring)

**What to Test**:

- [ ] Picks list displays correctly
- [ ] Pick status badges show (✅ WIN / ❌ LOSS / ⏳ PENDING)
- [ ] Points earned displayed for winning picks
- [ ] FTD + ATTD breakdown visible
- [ ] Actual first TD scorer shown
- [ ] Tooltip shows all TD scorers
- [ ] Pending picks don't show results
- [ ] Filters work (all/pending/graded)
- [ ] Sorting works correctly

**Test Steps**:

1. Navigate to `/picks`
2. View your list of picks
3. Find a graded pick (status: win or loss)
4. Verify status badge is correct
5. Check points display (e.g., "4 pts (3 FTD + 1 ATTD)")
6. Hover over TD scorer info to see tooltip
7. Filter by status and verify results
8. Sort by date/points and verify order

**Expected Pick Display**:

```
┌──────────────────────────────────────┐
│ Chiefs vs Bills - Dec 7, 2024        │
├──────────────────────────────────────┤
│ Your Pick: Patrick Mahomes           │
│ Status: ✅ WIN                        │
│ Points: 4 pts (3 FTD + 1 ATTD)      │
│ First TD: Patrick Mahomes            │
│ All TDs: [hover for list]           │
└──────────────────────────────────────┘
```

---

### 3. Available Games with Scoring Indicators

**Location**: `/picks` page (available games section)

**Component**: `AvailableGames.tsx` (enhanced)

**What to Test**:

- [ ] Games list displays correctly
- [ ] Scored games show indicator
- [ ] User's result badge shows for scored games (WIN/LOSS)
- [ ] Points earned displayed for scored games
- [ ] Can click game to view results modal
- [ ] Unscored games don't show results
- [ ] Game status updates correctly

**Test Steps**:

1. Navigate to `/picks`
2. Scroll to available games section
3. Find a scored game
4. Verify scoring indicator is visible
5. Check your result badge (if you made a pick)
6. Verify points earned are displayed
7. Click on the game to open results modal

**Expected Game Display**:

```
┌──────────────────────────────────────┐
│ Chiefs vs Bills                      │
│ Dec 7, 2024 - 4:30 PM EST          │
│ Status: Final ✓ Scored              │
│ Your Result: ✅ WIN - 4 pts         │
│ [Click to view details]             │
└──────────────────────────────────────┘
```

---

### 4. Game Results Modal

**Location**: Opens when clicking on a scored game

**Component**: `GameResultsModal.tsx`

**What to Test**:

- [ ] Modal opens when clicking game
- [ ] Game details displayed correctly
- [ ] First TD scorer shown with player info
- [ ] All TD scorers list displayed
- [ ] Number of picks graded shown
- [ ] Scoring timestamp displayed
- [ ] Manual scoring indicator (if applicable)
- [ ] Close button works
- [ ] Click outside closes modal
- [ ] Loading state while fetching
- [ ] Error handling if API fails

**Test Steps**:

1. Click on a scored game
2. Verify modal opens
3. Check all information is displayed
4. Verify player names and details
5. Check timestamp format
6. Close modal with X button
7. Open again and close by clicking outside
8. Test with a game that has no TDs (edge case)

**Expected Modal Content**:

```
┌────────────────────────────────────────┐
│  Game Results                      [X] │
├────────────────────────────────────────┤
│  Chiefs vs Bills                       │
│  December 7, 2024                      │
│                                        │
│  First Touchdown Scorer:               │
│  🏈 Patrick Mahomes (QB, Chiefs)       │
│                                        │
│  All Touchdown Scorers:                │
│  • Patrick Mahomes (QB, Chiefs)        │
│  • Travis Kelce (TE, Chiefs)           │
│  • Josh Allen (QB, Bills)              │
│                                        │
│  Picks Graded: 25                      │
│  Scored At: Dec 7, 2024 8:45 PM       │
└────────────────────────────────────────┘
```

**API Endpoint**: `GET /api/v1/scores/game/{game_id}`

---

### 5. Admin Scoring Page

**Location**: `/admin/scoring`

**Components**: `AdminScoringPage.tsx`, `ManualScoringForm.tsx`, `PickOverrideForm.tsx`

**Requires**: Admin authentication

**What to Test**:

#### Manual Scoring Form

- [ ] Form displays correctly
- [ ] Game selection dropdown works
- [ ] Player search for first TD scorer works
- [ ] Multi-select for all TD scorers works
- [ ] Can select "No touchdowns" option
- [ ] Submit button triggers scoring
- [ ] Success message displays
- [ ] Results summary shown (picks graded count)
- [ ] Form resets after submission
- [ ] Error handling for invalid data
- [ ] Loading state during submission

**Test Steps**:

1. Log in as admin
2. Navigate to `/admin/scoring`
3. Select a game from dropdown
4. Search and select first TD scorer
5. Select all TD scorers (multi-select)
6. Click "Score Game" button
7. Verify success message
8. Check picks were graded (query API or database)
9. Test with "no touchdowns" scenario
10. Test error handling (invalid game ID)

#### Pick Override Form

- [ ] Form displays correctly
- [ ] Pick selection/search works
- [ ] Current pick values displayed
- [ ] Status dropdown works (win/loss)
- [ ] FTD points input works (0 or 3)
- [ ] ATTD points input works (0 or 1)
- [ ] Submit button triggers override
- [ ] Success message displays
- [ ] Audit trail recorded
- [ ] Form resets after submission
- [ ] Error handling for invalid data
- [ ] Loading state during submission

**Test Steps**:

1. On admin scoring page
2. Find pick override section
3. Search/select a pick
4. View current values
5. Change status to "win"
6. Set FTD points to 3
7. Set ATTD points to 1
8. Click "Override Score" button
9. Verify success message
10. Check pick was updated (query API)
11. Verify audit trail (override_at, override_by_user_id)

#### Recent Activity

- [ ] Recent scoring activity displayed
- [ ] Shows games scored recently
- [ ] Shows picks overridden recently
- [ ] Timestamps are correct
- [ ] Admin names shown for manual actions

---

### 6. Admin Monitoring Page

**Location**: `/admin/monitoring`

**Component**: `AdminMonitoringPage.tsx`

**Requires**: Admin authentication

**What to Test**:

- [ ] Page loads correctly
- [ ] Scheduler status displayed
- [ ] Next run times shown for all jobs
- [ ] Recent job executions listed
- [ ] Scoring statistics displayed
- [ ] Picks graded count (7 days)
- [ ] Games scored count (7 days)
- [ ] Pending picks count
- [ ] Last scoring timestamp
- [ ] Health status indicators (healthy/degraded/unhealthy)
- [ ] Error logs displayed (if any)
- [ ] Auto-refresh works (if implemented)
- [ ] Manual refresh button works

**Test Steps**:

1. Log in as admin
2. Navigate to `/admin/monitoring`
3. Verify scheduler status section
4. Check all three jobs are listed:
   - fetch_upcoming_games
   - grade_early_games
   - grade_late_games
5. Verify next run times are in the future
6. Check scoring statistics section
7. Verify all counts are displayed
8. Check health status indicators
9. Refresh page and verify data updates
10. Compare with API health endpoints

**Expected Display**:

```
┌────────────────────────────────────────┐
│  Scheduler Status                      │
├────────────────────────────────────────┤
│  Status: ✅ Healthy                     │
│  Running: Yes                          │
│                                        │
│  Scheduled Jobs:                       │
│  • Fetch Upcoming Games                │
│    Next Run: Dec 8, 2024 1:59 AM      │
│  • Grade Early Games                   │
│    Next Run: Dec 8, 2024 4:30 PM      │
│  • Grade Late Games                    │
│    Next Run: Dec 8, 2024 8:30 PM      │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Scoring Statistics (Last 7 Days)     │
├────────────────────────────────────────┤
│  Picks Graded: 150                     │
│  Games Scored: 12                      │
│  Pending Picks: 45                     │
│  Last Scoring: Dec 7, 2024 8:30 PM    │
│  Status: ✅ Healthy                     │
└────────────────────────────────────────┘
```

**API Endpoints**:

- `GET /api/v1/health/scheduler`
- `GET /api/v1/health/scoring` (admin only)

---

## Integration Testing Scenarios

### Scenario 1: Complete Scoring Flow

**Goal**: Test the entire flow from pick submission to viewing results

**Steps**:

1. Create a pick for an upcoming game
2. Wait for game to complete (or manually score via admin)
3. Verify pick status changes from pending to win/loss
4. Check points are awarded correctly
5. Verify user total score updated
6. View pick result details
7. View game results modal
8. Check leaderboard updated

### Scenario 2: Manual Scoring by Admin

**Goal**: Test admin manual scoring functionality

**Steps**:

1. Identify a completed game that hasn't been scored
2. Log in as admin
3. Navigate to `/admin/scoring`
4. Use manual scoring form
5. Select game and touchdown scorers
6. Submit scoring
7. Verify picks were graded
8. Check user scores updated
9. Verify game marked as manually scored
10. View results as regular user

### Scenario 3: Score Override

**Goal**: Test admin score override functionality

**Steps**:

1. Identify a graded pick
2. Note current status and points
3. Log in as admin
4. Navigate to `/admin/scoring`
5. Use pick override form
6. Change status and points
7. Submit override
8. Verify pick updated
9. Check user total score recalculated
10. Verify audit trail recorded
11. View updated result as regular user

### Scenario 4: Zero Touchdown Game

**Goal**: Test edge case of game with no touchdowns

**Steps**:

1. Create picks for a game
2. Manually score game with no touchdowns
3. Verify all picks marked as loss
4. Check all picks have 0 points
5. View game results modal (should show no TD scorers)
6. Verify user scores unchanged

### Scenario 5: Multiple Touchdowns by Same Player

**Goal**: Test that ATTD points only awarded once

**Steps**:

1. Create pick for a player
2. Manually score game where player scores 3 TDs
3. Verify pick gets 1 ATTD point (not 3)
4. If player scored first TD, verify 4 total points (3 FTD + 1 ATTD)
5. View game results showing all TDs

---

## API Testing (Supporting Frontend Tests)

### Get User Score

```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/scores/user/USER_ID
```

### Get Pick Result

```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/scores/pick/PICK_ID
```

### Get Game Result

```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/scores/game/GAME_ID
```

### Manual Score Game (Admin)

```bash
curl -X POST \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_td_scorer": "PLAYER_UUID",
    "all_td_scorers": ["PLAYER_UUID_1", "PLAYER_UUID_2"]
  }' \
  http://localhost:8000/api/v1/scores/game/GAME_ID/manual
```

### Override Pick Score (Admin)

```bash
curl -X PATCH \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "win",
    "ftd_points": 3,
    "attd_points": 1
  }' \
  http://localhost:8000/api/v1/scores/pick/PICK_ID/override
```

---

## Browser DevTools Testing

### Console Checks

1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Look for:
   - API call errors
   - Component rendering errors
   - State management issues
   - Network request failures

### Network Tab

1. Open Network tab
2. Filter by XHR/Fetch
3. Verify API calls:
   - Correct endpoints called
   - Proper authentication headers
   - Response status codes (200, 404, etc.)
   - Response data structure

### React DevTools

1. Install React DevTools extension
2. Inspect component tree
3. Check component props
4. Verify state updates
5. Monitor re-renders

---

## Common Issues and Solutions

### Issue: Score Card Not Displaying

**Symptoms**: Score card component doesn't show or shows loading forever

**Check**:

- API endpoint accessible: `GET /api/v1/scores/user/{user_id}`
- User ID is correct
- Authentication token is valid
- Network tab shows successful response
- Console for errors

**Solution**:

- Verify API is running
- Check authentication
- Verify user has picks in database

### Issue: Pick Results Not Showing

**Symptoms**: Picks don't show win/loss status or points

**Check**:

- Picks have been graded (scored_at is not null)
- Game has been scored
- API response includes scoring data
- Component is receiving correct props

**Solution**:

- Score the game (manually or wait for scheduled job)
- Verify database has scoring data
- Check API response structure

### Issue: Game Results Modal Empty

**Symptoms**: Modal opens but shows no touchdown data

**Check**:

- Game has been scored
- API endpoint returns data: `GET /api/v1/scores/game/{game_id}`
- Game has touchdown scorers (or is marked as zero TD game)

**Solution**:

- Score the game first
- Verify game data in database
- Check API response

### Issue: Admin Forms Not Working

**Symptoms**: Forms don't submit or show errors

**Check**:

- User has admin role
- Authentication token is valid
- API endpoints accessible
- Request payload is correct
- Console for errors

**Solution**:

- Verify admin authentication
- Check API is running
- Verify request format matches API expectations
- Check backend logs for errors

---

## Test Data Setup

### Create Test User

```sql
INSERT INTO users (id, email, username, password_hash, is_admin)
VALUES (
  gen_random_uuid(),
  'test@example.com',
  'testuser',
  '$2b$12$...', -- bcrypt hash of 'password'
  false
);
```

### Create Admin User

```sql
INSERT INTO users (id, email, username, password_hash, is_admin)
VALUES (
  gen_random_uuid(),
  'admin@example.com',
  'admin',
  '$2b$12$...', -- bcrypt hash of 'password'
  true
);
```

### Create Test Game

```sql
INSERT INTO games (id, external_id, home_team_id, away_team_id, kickoff_time, status)
VALUES (
  gen_random_uuid(),
  '2024_12_07_KC_BUF',
  (SELECT id FROM teams WHERE abbreviation = 'KC'),
  (SELECT id FROM teams WHERE abbreviation = 'BUF'),
  '2024-12-07 21:30:00',
  'final'
);
```

### Create Test Pick

```sql
INSERT INTO picks (id, user_id, game_id, player_id, status)
VALUES (
  gen_random_uuid(),
  (SELECT id FROM users WHERE username = 'testuser'),
  (SELECT id FROM games WHERE external_id = '2024_12_07_KC_BUF'),
  (SELECT id FROM players WHERE name = 'Patrick Mahomes'),
  'pending'
);
```

---

## Testing Checklist Summary

### User Features

- [ ] User score card displays correctly
- [ ] My picks show results (win/loss/pending)
- [ ] Points breakdown visible (FTD + ATTD)
- [ ] Available games show scoring indicators
- [ ] Game results modal works
- [ ] All data updates in real-time

### Admin Features

- [ ] Manual scoring form works
- [ ] Pick override form works
- [ ] Monitoring dashboard displays correctly
- [ ] Scheduler status visible
- [ ] Scoring statistics accurate
- [ ] Recent activity tracked

### Integration

- [ ] Complete scoring flow works end-to-end
- [ ] Manual scoring updates user scores
- [ ] Score overrides recalculate totals
- [ ] Edge cases handled (zero TDs, multiple TDs)
- [ ] Error handling works
- [ ] Loading states display correctly

### Performance

- [ ] Pages load quickly
- [ ] API calls are efficient
- [ ] No unnecessary re-renders
- [ ] Images/assets load properly
- [ ] Mobile responsive (if applicable)

---

## Next Steps

1. **Start with User Features**: Test score card and pick results
2. **Test Game Results Modal**: Verify all game data displays
3. **Test Admin Features**: Manual scoring and overrides
4. **Run Integration Scenarios**: Complete end-to-end flows
5. **Check Edge Cases**: Zero TDs, multiple TDs, errors
6. **Performance Testing**: Load times, responsiveness
7. **Cross-Browser Testing**: Chrome, Firefox, Safari, Edge
8. **Mobile Testing**: Responsive design (if applicable)

---

## Reporting Issues

When reporting issues, include:

- **Component**: Which component has the issue
- **Steps to Reproduce**: Exact steps to trigger the issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: Visual evidence
- **Console Errors**: Any errors in browser console
- **Network Tab**: API call details
- **Environment**: Browser, OS, screen size

---

**Happy Testing! 🧪**
