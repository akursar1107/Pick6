# Leaderboard User Guide

## Overview

The First6 Leaderboard shows how you rank against other participants based on your touchdown prediction performance. This guide will help you understand how to view standings, interpret statistics, and export data.

## Viewing the Leaderboard

### Accessing the Leaderboard

1. Navigate to the **Standings** page from the main navigation menu
2. The leaderboard will load automatically showing the current season standings

### Season vs Weekly View

The leaderboard offers two viewing modes:

#### Season Leaderboard (Default)

- Shows cumulative standings for the entire season
- Displays total points earned across all weeks
- Updates after each week's games are scored
- Best for tracking overall performance

#### Weekly Leaderboard

- Shows standings for a specific week only
- Use the week selector dropdown to choose a week (1-18)
- Displays points earned only in that week
- Best for comparing week-to-week performance

**To switch between views:**

1. Click the **Season** or **Weekly** tab at the top of the leaderboard
2. For weekly view, select a week from the dropdown menu

## Understanding the Leaderboard Columns

### Rank

- Your position in the standings (1st, 2nd, 3rd, etc.)
- Lower numbers are better
- Tied users show the same rank number

### Username / Display Name

- Your username or display name
- Click on any username to view detailed statistics

### Total Points

- Sum of all points earned from predictions
- FTD (First Touchdown) wins = 3 points each
- ATTD (Anytime Touchdown) wins = 1 point each

### FTD Points

- Points earned from First Touchdown predictions only
- Each correct FTD prediction = 3 points

### ATTD Points

- Points earned from Anytime Touchdown predictions only
- Each correct ATTD prediction = 1 point

### Wins

- Total number of correct predictions
- Includes both FTD and ATTD wins

### Losses

- Total number of incorrect predictions
- Includes both FTD and ATTD losses

### Pending

- Number of predictions still waiting for game results
- These don't affect your current ranking

### Win %

- Percentage of correct predictions
- Calculated as: (Wins / Total Graded Picks) × 100
- Higher percentages indicate better accuracy

### Tied Indicator

- Shows if you're tied with other users
- Tied users have the same total points and wins

## How Rankings Work

### Ranking Rules

Rankings are determined by the following criteria in order:

1. **Total Points** (Primary)

   - Users with more points rank higher
   - Points = (FTD wins × 3) + (ATTD wins × 1)

2. **Total Wins** (Tie-breaker)

   - If two users have equal points, the user with more wins ranks higher
   - This rewards accuracy over lucky high-value picks

3. **Tied Rank** (Final tie)
   - If two users have equal points AND equal wins, they receive the same rank
   - Both users are marked as "tied"

### Example Rankings

```
Rank  User      Points  Wins  Losses
1     Alice     45      15    3      (Most points)
2     Bob       42      14    4      (Fewer points than Alice)
3     Charlie   42      16    2      (Same points as Bob, but more wins)
4     David     39      13    5      (Fewer points)
5     Eve       39      13    5      (Tied with David - same points and wins)
5     Frank     39      13    5      (Also tied)
```

## Viewing User Statistics

### Opening User Stats

1. Click on any username in the leaderboard
2. A modal window will open showing detailed statistics

### Understanding User Stats

#### Overall Performance

- **Total Points**: Cumulative points for the season
- **Win-Loss Record**: Total wins vs losses (e.g., 15-3)
- **Win Percentage**: Success rate across all predictions
- **Current Rank**: Position in the season leaderboard

#### FTD Statistics

- **FTD Record**: First Touchdown wins vs losses
- **FTD Points**: Total points from FTD predictions
- **FTD Percentage**: Success rate for FTD predictions only

#### ATTD Statistics

- **ATTD Record**: Anytime Touchdown wins vs losses
- **ATTD Points**: Total points from ATTD predictions
- **ATTD Percentage**: Success rate for ATTD predictions only

#### Weekly Performance

- **Best Week**: Week with highest points earned
  - Shows week number, points, wins, losses, and rank
- **Worst Week**: Week with lowest points earned (excluding weeks with no picks)
  - Shows week number, points, wins, losses, and rank
- **Weekly Breakdown Chart**: Visual representation of points per week

#### Streaks

- **Current Streak**: Consecutive wins or losses from most recent pick
  - Example: "5 game win streak" or "2 game loss streak"
- **Longest Win Streak**: Best consecutive win streak this season
- **Longest Loss Streak**: Worst consecutive loss streak this season

## Finding Your Position

### Current User Highlighting

Your row in the leaderboard is automatically highlighted with a distinct color to help you quickly find your position.

### Scroll to Position

If you're not visible in the current viewport:

1. Look for the "Find Me" button (if available)
2. Click it to automatically scroll to your position
3. Your row will remain highlighted

## Sorting the Leaderboard

### Column Sorting

You can sort the leaderboard by any column:

1. Click on a column header (e.g., "Wins", "Win %")
2. The leaderboard will sort by that column
3. Click again to toggle between ascending and descending order
4. An arrow icon shows the current sort direction

### Important Notes

- Sorting by non-points columns still maintains tie-breaking rules
- The default sort is by rank (which follows the ranking rules)
- Sorting is temporary and resets when you refresh the page

## Exporting Leaderboard Data

### How to Export

1. Click the **Export** button in the leaderboard header
2. Choose your preferred format:

   - **CSV**: For spreadsheet applications (Excel, Google Sheets)
   - **JSON**: For programmatic analysis

3. The file will download automatically to your device

### Export Filenames

Files are automatically named based on the data:

- Season export: `leaderboard_season_2024.csv`
- Weekly export: `leaderboard_season_2024_week_5.csv`

### What's Included

The export includes all visible columns:

- Rank
- Username
- Display Name
- Total Points
- FTD Points
- ATTD Points
- Wins
- Losses
- Pending
- Win Percentage
- Is Tied

### Use Cases for Exports

- **Offline Analysis**: Analyze trends in spreadsheet software
- **Sharing**: Share standings with friends outside the platform
- **Record Keeping**: Keep historical records of weekly standings
- **Custom Visualizations**: Create your own charts and graphs

## Mobile Experience

### Mobile Optimizations

The leaderboard is fully responsive for mobile devices:

- **Priority Columns**: Rank, Username, and Total Points always visible
- **Expandable Rows**: Tap a row to see full details
- **Fixed Header**: Header stays visible while scrolling
- **Touch-Friendly**: Large tap targets for easy navigation

### Mobile Tips

1. Rotate to landscape for more columns
2. Tap usernames to view full statistics
3. Use the week selector dropdown for quick navigation
4. Swipe to scroll through long leaderboards

## Real-Time Updates

### Automatic Updates

The leaderboard updates automatically:

- **Polling**: Checks for updates every 30 seconds
- **On Focus**: Refreshes when you return to the tab
- **After Scoring**: Updates immediately when games are scored

### Manual Refresh

To manually refresh the leaderboard:

1. Look for the refresh icon button in the header
2. Click it to fetch the latest data
3. A loading indicator shows the update is in progress

### Update Indicators

- **Loading Spinner**: Shows when data is being fetched
- **Stale Data Warning**: Appears if data hasn't updated in a while
- **Success Toast**: Confirms when data is successfully refreshed

## Empty States

### No Data Scenarios

You may see empty states in certain situations:

#### "Season hasn't started yet"

- No users have graded picks yet
- Games haven't been scored
- **Action**: Submit your picks and wait for games to be scored

#### "No games this week"

- The selected week has no scheduled games
- **Action**: Select a different week

#### "Games in progress"

- All picks for the week are still pending
- Games haven't finished or been scored yet
- **Action**: Wait for games to complete and be scored

#### "No results found"

- Your current filters returned no data
- **Action**: Adjust your week selection or filters

## Frequently Asked Questions

### Why is my rank not changing?

- Rankings only update when games are scored
- If games are still in progress, your rank won't change
- Check the "Pending" column to see ungraded picks

### Why am I tied with another user?

- You have the same total points AND same number of wins
- Both criteria must match for a tie
- Ties are broken by total wins, not win percentage

### How often does the leaderboard update?

- Automatically every 30 seconds
- Immediately after games are scored
- When you manually refresh
- When you return to the tab

### Can I see historical leaderboards?

- Use the export feature to save weekly snapshots
- The system shows current season data only
- Past seasons may be available if configured by your admin

### What happens if I miss a week?

- Your season ranking continues to accumulate
- You'll have 0 points for that week in weekly view
- Missing weeks affect your total points but not your win percentage

### How is win percentage calculated?

- Formula: (Total Wins / Total Graded Picks) × 100
- Only includes graded picks (WIN or LOSS)
- Pending picks are not included in the calculation
- Rounded to 2 decimal places

## Tips for Success

1. **Check Weekly**: Review the weekly leaderboard to track recent performance
2. **Study Top Users**: Click on top-ranked users to see their strategies
3. **Monitor Streaks**: Keep an eye on your current streak
4. **Export Regularly**: Save weekly snapshots to track your progress
5. **Learn from Best/Worst Weeks**: Review your statistics to identify patterns

## Troubleshooting

### Leaderboard not loading

1. Check your internet connection
2. Try refreshing the page
3. Clear your browser cache
4. Contact your administrator if the issue persists

### Data looks incorrect

1. Wait for automatic refresh (30 seconds)
2. Try manual refresh button
3. Check if games have been scored
4. Verify your picks were submitted correctly

### Export not downloading

1. Check browser download settings
2. Ensure pop-ups are not blocked
3. Try a different browser
4. Check available disk space

## Support

If you encounter issues or have questions not covered in this guide:

- Contact your First6 administrator
- Check the system status page
- Review the FAQ section
- Submit a support ticket

---

**Last Updated**: December 2024
**Version**: 1.0
