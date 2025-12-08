/**
 * Event system for real-time updates across the application.
 *
 * This module provides a simple event-based system for triggering
 * cache invalidation and UI updates when data changes occur.
 *
 * Future Enhancement: This can be replaced with WebSocket integration
 * for true real-time updates from the server.
 */

export {
  dispatchGameScoredEvent,
  dispatchPickOverrideEvent,
} from "@/hooks/useLeaderboardUpdates";

/**
 * Usage Example:
 *
 * When a game is scored (e.g., in an admin panel or scoring page):
 * ```typescript
 * import { dispatchGameScoredEvent } from "@/lib/events";
 *
 * // After successfully scoring a game
 * dispatchGameScoredEvent(gameId, season);
 * ```
 *
 * When a pick is manually overridden:
 * ```typescript
 * import { dispatchPickOverrideEvent } from "@/lib/events";
 *
 * // After successfully overriding a pick
 * dispatchPickOverrideEvent(pickId, season);
 * ```
 *
 * The leaderboard page will automatically listen for these events
 * and refresh the data when they occur.
 */
