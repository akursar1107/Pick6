// Leaderboard types matching backend schemas

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  display_name: string;
  total_points: number;
  ftd_points: number;
  attd_points: number;
  wins: number;
  losses: number;
  pending: number;
  win_percentage: number;
  is_tied: boolean;
}

export interface WeekPerformance {
  week: number;
  points: number;
  wins: number;
  losses: number;
  rank: number;
}

export interface Streak {
  type: "win" | "loss" | "none";
  count: number;
}

export interface UserStats {
  user_id: string;
  username: string;
  display_name: string;
  total_points: number;
  total_wins: number;
  total_losses: number;
  total_pending: number;
  win_percentage: number;
  current_rank: number;
  ftd_wins: number;
  ftd_losses: number;
  ftd_points: number;
  ftd_percentage: number;
  attd_wins: number;
  attd_losses: number;
  attd_points: number;
  attd_percentage: number;
  best_week?: WeekPerformance;
  worst_week?: WeekPerformance;
  weekly_breakdown: WeekPerformance[];
  current_streak: Streak;
  longest_win_streak: number;
  longest_loss_streak: number;
}
