// Generated types from backend OpenAPI spec
// TODO: Generate these from backend OpenAPI schema

export interface User {
  id: string
  username: string
  email: string
  display_name?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface Game {
  id: string
  external_id: string
  season_year: number
  week_number: number
  game_type: string
  home_team_id: string
  away_team_id: string
  game_date: string
  kickoff_time: string
  status: 'scheduled' | 'in_progress' | 'completed' | 'suspended'
  first_td_scorer_player_id?: string
  final_score_home?: number
  final_score_away?: number
  created_at: string
  updated_at?: string
}

export interface Pick {
  id: string
  user_id: string
  game_id: string
  pick_type: 'FTD' | 'ATTD'
  player_id: string
  snapshot_odds?: string
  status: 'pending' | 'win' | 'loss' | 'void'
  is_manual_override: boolean
  settled_at?: string
  pick_submitted_at: string
  created_at: string
  updated_at?: string
}

