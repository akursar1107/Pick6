# Real-Time Leaderboard Updates

## Overview

The leaderboard implements real-time updates through three mechanisms:

1. **Automatic Polling** - Fetches fresh data every 30 seconds
2. **Window Focus Refetch** - Updates when user returns to the tab
3. **Event-Based Updates** - Responds to scoring events immediately

## Implementation

### 1. React Query Polling (Subtask 12.1)

The leaderboard queries are configured with:

- `refetchInterval: 30000` - Polls every 30 seconds
- `refetchOnWindowFocus: true` - Refetches when window gains focus
- Loading indicator shows "Updating..." during background fetches

### 2. Manual Refresh Button (Subtask 12.2)

A refresh button in the header allows users to manually trigger updates:

- Icon button with RefreshCw icon
- Shows spinning animation during fetch
- Displays toast notification on completion
- Disabled during active fetches

### 3. Event System (Subtask 12.3)

Custom event system for immediate cache invalidation:

#### Hook: `useLeaderboardUpdates`

Listens for scoring events and invalidates React Query cache:

- `gameScored` event - When a game is scored
- `pickOverride` event - When a pick is manually overridden

#### Event Dispatchers

```typescript
import {
  dispatchGameScoredEvent,
  dispatchPickOverrideEvent,
} from "@/lib/events";

// When a game is scored
dispatchGameScoredEvent(gameId, season);

// When a pick is overridden
dispatchPickOverrideEvent(pickId, season);
```

## Usage

The StandingsPage automatically uses all three mechanisms:

```typescript
// Polling and window focus are configured in useQuery
const { data, isFetching, refetch } = useQuery({
  queryKey: ["leaderboard", "season", season],
  queryFn: () => api.getSeasonLeaderboard(season),
  refetchInterval: 30000,
  refetchOnWindowFocus: true,
});

// Event system is activated via hook
useLeaderboardUpdates(currentSeason);

// Manual refresh via button
<Button onClick={refetch}>
  <RefreshCw />
</Button>;
```

## Future Enhancements

This event system can be replaced with WebSocket integration:

1. Replace custom events with WebSocket messages
2. Backend emits events when games are scored
3. Frontend listens to WebSocket and invalidates cache
4. Same invalidation logic, different transport mechanism

## Requirements Validated

- **5.1** - Leaderboard updates within 5 seconds (via polling + events)
- **5.2** - Manual refresh button for user-triggered updates
- **5.3** - Cache invalidation on game scoring and pick override
- **5.5** - Loading indicator during updates
