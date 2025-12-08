import { apiClient } from "@/lib/api";
import { UserScore, PickResult, GameResult } from "@/types/scoring";

/**
 * Get user's total score and statistics
 * @param userId - The user's ID
 * @returns UserScore object with total score, wins, losses, and win percentage
 */
export async function getUserScore(userId: string): Promise<UserScore> {
  const response = await apiClient.get<UserScore>(`/scores/user/${userId}`);
  return response.data;
}

/**
 * Get pick result details including points breakdown
 * @param pickId - The pick's ID
 * @returns PickResult object with status, points, and actual scorers
 */
export async function getPickResult(pickId: string): Promise<PickResult> {
  const response = await apiClient.get<PickResult>(`/scores/pick/${pickId}`);
  return response.data;
}

/**
 * Get game scoring results including touchdown scorers
 * @param gameId - The game's ID
 * @returns GameResult object with first TD scorer, all TD scorers, and grading info
 */
export async function getGameResult(gameId: string): Promise<GameResult> {
  const response = await apiClient.get<GameResult>(`/scores/game/${gameId}`);
  return response.data;
}

/**
 * Manually score a game (admin only)
 * @param gameId - The game's ID
 * @param firstTdScorer - First TD scorer player ID (optional)
 * @param allTdScorers - All TD scorer player IDs
 * @returns Result with picks graded count
 */
export async function manualScoreGame(
  gameId: string,
  firstTdScorer: string | null,
  allTdScorers: string[]
): Promise<{ message: string; game_id: string; picks_graded: number }> {
  const response = await apiClient.post(`/scores/game/${gameId}/manual`, {
    first_td_scorer: firstTdScorer,
    all_td_scorers: allTdScorers,
  });
  return response.data;
}

/**
 * Override a pick's score (admin only)
 * @param pickId - The pick's ID
 * @param status - New status (win or loss)
 * @param ftdPoints - FTD points (0 or 3)
 * @param attdPoints - ATTD points (0 or 1)
 * @returns Updated pick information
 */
export async function overridePickScore(
  pickId: string,
  status: "win" | "loss",
  ftdPoints: number,
  attdPoints: number
): Promise<{
  message: string;
  pick_id: string;
  status: string;
  ftd_points: number;
  attd_points: number;
  total_points: number;
}> {
  const response = await apiClient.patch(`/scores/pick/${pickId}/override`, {
    status,
    ftd_points: ftdPoints,
    attd_points: attdPoints,
  });
  return response.data;
}
