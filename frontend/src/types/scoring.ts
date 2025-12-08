// Scoring-related types based on the backend scoring schema

export interface UserScore {
  user_id: string;
  total_score: number;
  total_wins: number;
  total_losses: number;
  win_percentage: number;
}

export interface PickResult {
  id: string;
  user_id: string;
  game_id: string;
  player_id: string;
  status: "pending" | "win" | "loss" | "void";
  scored_at?: string;
  ftd_points: number;
  attd_points: number;
  total_points: number;
  is_manual_override: boolean;
  override_by_user_id?: string;
  override_at?: string;
  pick_submitted_at: string;
  created_at: string;
  updated_at?: string;
  // Related data
  player?: {
    id: string;
    name: string;
    team: string;
    position: string;
  };
  game?: {
    id: string;
    home_team: string;
    away_team: string;
    kickoff_time: string;
    week_number: number;
    status: string;
  };
  first_td_scorer?: {
    id: string;
    name: string;
    team: string;
    position: string;
  };
  all_td_scorers?: Array<{
    id: string;
    name: string;
    team: string;
    position: string;
  }>;
}

export interface GameResult {
  game_id: string;
  first_td_scorer_player_id?: string;
  all_td_scorer_player_ids: string[];
  scored_at?: string;
  is_manually_scored: boolean;
  picks_graded_count: number;
  // Related data
  first_td_scorer?: {
    id: string;
    name: string;
    team: string;
    position: string;
  };
  all_td_scorers?: Array<{
    id: string;
    name: string;
    team: string;
    position: string;
  }>;
  game?: {
    id: string;
    home_team: string;
    away_team: string;
    kickoff_time: string;
    week_number: number;
    status: string;
  };
}
