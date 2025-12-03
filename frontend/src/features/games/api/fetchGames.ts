import { apiClient } from '@/lib/api'
import { Game } from '@/types/api-types'

export async function fetchGames(params?: {
  week?: number
  season?: number
  status?: string
}): Promise<Game[]> {
  const response = await apiClient.get<Game[]>('/games', { params })
  return response.data
}

export async function fetchGameById(gameId: string): Promise<Game> {
  const response = await apiClient.get<Game>(`/games/${gameId}`)
  return response.data
}

