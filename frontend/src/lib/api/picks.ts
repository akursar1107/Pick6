import { apiClient } from "@/lib/api";
import {
  PickCreate,
  PickUpdate,
  PickResponse,
  GameWithPick,
  Player,
} from "@/types/pick";

/**
 * Create a new pick for a game
 */
export async function createPick(data: PickCreate): Promise<PickResponse> {
  const response = await apiClient.post<PickResponse>("/picks", data);
  return response.data;
}

/**
 * Get all picks for the authenticated user
 * Optionally filter by game_id
 */
export async function getPicks(params?: {
  game_id?: string;
}): Promise<PickResponse[]> {
  const response = await apiClient.get<PickResponse[]>("/picks", { params });
  return response.data;
}

/**
 * Get a specific pick by ID
 */
export async function getPickById(pickId: string): Promise<PickResponse> {
  const response = await apiClient.get<PickResponse>(`/picks/${pickId}`);
  return response.data;
}

/**
 * Update an existing pick (change player selection)
 */
export async function updatePick(
  pickId: string,
  data: PickUpdate
): Promise<PickResponse> {
  const response = await apiClient.patch<PickResponse>(
    `/picks/${pickId}`,
    data
  );
  return response.data;
}

/**
 * Delete a pick before kickoff
 */
export async function deletePick(pickId: string): Promise<void> {
  await apiClient.delete(`/picks/${pickId}`);
}

/**
 * Get available games for picks (future kickoffs)
 */
export async function getAvailableGames(): Promise<GameWithPick[]> {
  const response = await apiClient.get<GameWithPick[]>("/games/available");
  return response.data;
}

/**
 * Search for players by name
 */
export async function searchPlayers(query: string): Promise<Player[]> {
  const response = await apiClient.get<Player[]>("/players/search", {
    params: { q: query },
  });
  return response.data;
}

/**
 * Get all picks in the system (admin only)
 * Used for admin override functionality
 */
export async function getAllPicksForAdmin(): Promise<PickResponse[]> {
  const response = await apiClient.get<PickResponse[]>("/scores/admin/picks");
  return response.data;
}

/**
 * Get all games in the database (admin only)
 * Used for admin manual scoring functionality
 */
export async function getAllGamesForAdmin(): Promise<GameWithPick[]> {
  const response = await apiClient.get<GameWithPick[]>("/games/admin/all");
  return response.data;
}
