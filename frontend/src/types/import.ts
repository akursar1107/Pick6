// Import feature types

export interface ImportConfig {
  season: number;
  weeks: number[] | "all";
  grade_games: boolean;
}

export interface ImportStats {
  teams_created: number;
  players_created: number;
  games_created: number;
  games_updated: number;
  games_graded: number;
  total_games: number;
}

export interface ImportProgress {
  status: "pending" | "running" | "completed" | "failed";
  current_step: string;
  games_processed: number;
  total_games: number;
  teams_created: number;
  players_created: number;
  games_created: number;
  games_updated: number;
  games_graded: number;
  errors: string[];
}

export interface ImportJob {
  id: string;
  season: number;
  weeks: number[] | null;
  grade_games: boolean;
  status: "pending" | "running" | "completed" | "failed";
  current_step: string | null;
  games_processed: number;
  total_games: number;
  teams_created: number;
  players_created: number;
  games_created: number;
  games_updated: number;
  games_graded: number;
  errors: string[];
  admin_user_id: string;
  started_at: string;
  completed_at: string | null;
}

export interface ImportStartRequest {
  season: number;
  weeks: number[] | "all";
  grade_games: boolean;
}

export interface ImportStartResponse {
  job_id: string;
  message: string;
  estimated_duration_minutes: number;
}

export interface ImportStatusResponse {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: ImportProgress | null;
  stats: ImportStats | null;
  started_at: string;
  completed_at: string | null;
  errors: string[];
}

export interface ImportHistoryItem {
  id: string;
  season: number;
  weeks: number[] | null;
  grade_games: boolean;
  status: "completed" | "failed" | "running" | "pending";
  started_at: string;
  completed_at: string | null;
  stats: ImportStats;
  admin_user_id: string;
}

export interface ImportHistoryResponse {
  imports: ImportHistoryItem[];
  total: number;
}

export interface ExistingDataCheckRequest {
  season: number;
  weeks: number[] | "all";
}

export interface ExistingDataCheckResponse {
  has_existing_data: boolean;
  existing_games_count: number;
  games_to_create: number;
  games_to_update: number;
  warning_message: string | null;
}
