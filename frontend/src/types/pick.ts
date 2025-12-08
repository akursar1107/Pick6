// Pick-related types based on the updated backend schema

export interface Player {
  id: string;
  name: string;
  team: string;
  position: string;
}

export interface Team {
  id: string;
  name: string;
  abbreviation: string;
  city: string;
}

export interface Game {
  id: string;
  home_team: string;
  away_team: string;
  kickoff_time: string;
  week_number: number;
  status: "scheduled" | "in_progress" | "completed" | "suspended";
  // Scoring fields
  first_td_scorer_player_id?: string;
  all_td_scorer_player_ids?: string[];
  scored_at?: string;
  is_manually_scored?: boolean;
}

export interface GameWithPick extends Game {
  user_pick?: {
    id: string;
    player_name: string;
    status?: "pending" | "win" | "loss" | "void";
    total_points?: number;
    ftd_points?: number;
    attd_points?: number;
  };
}

export interface Pick {
  id: string;
  user_id: string;
  game_id: string;
  player_id: string;
  status: "pending" | "win" | "loss" | "void";
  is_manual_override: boolean;
  settled_at?: string;
  pick_submitted_at: string;
  created_at: string;
  updated_at?: string;
  // Scoring fields
  scored_at?: string;
  ftd_points: number;
  attd_points: number;
  total_points: number;
  override_by_user_id?: string;
  override_at?: string;
  game?: Game;
  player?: Player;
}

export interface PickCreate {
  game_id: string;
  player_id: string;
}

export interface PickUpdate {
  player_id: string;
}

export interface PickResponse extends Pick {
  game: Game;
  player: Player;
}
