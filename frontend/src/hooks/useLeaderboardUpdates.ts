import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

/**
 * Hook to handle leaderboard updates when scoring events occur.
 *
 * This hook provides a mechanism to invalidate the leaderboard cache
 * when games are scored. Currently uses a simple event-based approach
 * that can be extended to WebSocket integration in the future.
 *
 * Requirements: 5.1, 5.3
 */
export function useLeaderboardUpdates(season: number) {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Handler for game scored events
    const handleGameScored = (event: CustomEvent) => {
      const { season: scoredSeason } = event.detail;

      // Only invalidate if the scored game is from the current season
      if (scoredSeason === season) {
        // Invalidate all leaderboard queries for this season
        queryClient.invalidateQueries({
          queryKey: ["leaderboard", "season", season],
        });

        // Invalidate all weekly leaderboards for this season
        queryClient.invalidateQueries({
          queryKey: ["leaderboard", "week", season],
        });

        // Invalidate all user stats for this season
        queryClient.invalidateQueries({
          queryKey: ["user", "stats"],
        });
      }
    };

    // Handler for pick override events
    const handlePickOverride = (event: CustomEvent) => {
      const { season: overrideSeason } = event.detail;

      // Only invalidate if the override is from the current season
      if (overrideSeason === season) {
        // Invalidate all leaderboard queries
        queryClient.invalidateQueries({
          queryKey: ["leaderboard"],
        });

        // Invalidate user stats
        queryClient.invalidateQueries({
          queryKey: ["user", "stats"],
        });
      }
    };

    // Listen for custom events
    window.addEventListener("gameScored", handleGameScored as EventListener);
    window.addEventListener(
      "pickOverride",
      handlePickOverride as EventListener
    );

    // Cleanup listeners on unmount
    return () => {
      window.removeEventListener(
        "gameScored",
        handleGameScored as EventListener
      );
      window.removeEventListener(
        "pickOverride",
        handlePickOverride as EventListener
      );
    };
  }, [season, queryClient]);
}

/**
 * Utility function to dispatch a game scored event.
 * This can be called from anywhere in the app when a game is scored.
 *
 * @param gameId - The ID of the game that was scored
 * @param season - The season of the game
 */
export function dispatchGameScoredEvent(gameId: string, season: number) {
  const event = new CustomEvent("gameScored", {
    detail: { gameId, season },
  });
  window.dispatchEvent(event);
}

/**
 * Utility function to dispatch a pick override event.
 * This can be called from anywhere in the app when a pick is manually overridden.
 *
 * @param pickId - The ID of the pick that was overridden
 * @param season - The season of the pick
 */
export function dispatchPickOverrideEvent(pickId: string, season: number) {
  const event = new CustomEvent("pickOverride", {
    detail: { pickId, season },
  });
  window.dispatchEvent(event);
}
