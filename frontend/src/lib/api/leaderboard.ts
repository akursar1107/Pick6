import { apiClient } from "../api";
import { LeaderboardEntry, UserStats } from "../../types/leaderboard";

export const getSeasonLeaderboard = async (
  season: number
): Promise<LeaderboardEntry[]> => {
  const response = await apiClient.get(`/leaderboard/season/${season}`);
  return response.data;
};

export const getWeeklyLeaderboard = async (
  season: number,
  week: number
): Promise<LeaderboardEntry[]> => {
  const response = await apiClient.get(`/leaderboard/week/${season}/${week}`);
  return response.data;
};

export const getUserStats = async (
  userId: string,
  season?: number
): Promise<UserStats> => {
  const params = season ? { season } : {};
  const response = await apiClient.get(`/leaderboard/user/${userId}/stats`, {
    params,
  });
  return response.data;
};

export const exportLeaderboard = async (
  season: number,
  week?: number,
  format: "csv" | "json" = "csv"
): Promise<Blob> => {
  const params: Record<string, string | number> = { format };
  if (week) {
    params.week = week;
  }

  const response = await apiClient.get(`/leaderboard/export/${season}`, {
    params,
    responseType: "blob",
  });
  return response.data;
};
