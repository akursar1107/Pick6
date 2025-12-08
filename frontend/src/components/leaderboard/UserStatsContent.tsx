import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UserStats } from "@/types/leaderboard";
import { Trophy, TrendingUp, TrendingDown, Flame } from "lucide-react";
import { WeeklyPerformanceChart } from "./WeeklyPerformanceChart";

interface UserStatsContentProps {
  stats: UserStats;
}

export function UserStatsContent({ stats }: UserStatsContentProps) {
  const getStreakBadge = () => {
    if (
      stats.current_streak.type === "none" ||
      stats.current_streak.count === 0
    ) {
      return null;
    }

    const isWinStreak = stats.current_streak.type === "win";
    const variant = isWinStreak ? "default" : "destructive";

    return (
      <Badge variant={variant} className="text-sm">
        <Flame className="h-4 w-4 mr-1" />
        {stats.current_streak.count} {stats.current_streak.type} streak
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Overall Stats Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Overall Performance</CardTitle>
            {getStreakBadge()}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Points</p>
              <p className="text-2xl font-bold">{stats.total_points}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Record</p>
              <p className="text-2xl font-bold">
                {stats.total_wins}-{stats.total_losses}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Win %</p>
              <p className="text-2xl font-bold">
                {stats.win_percentage.toFixed(1)}%
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Current Rank</p>
              <p className="text-2xl font-bold flex items-center">
                <Trophy className="h-5 w-5 mr-1 text-yellow-500" />#
                {stats.current_rank}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* FTD and ATTD Stats */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* FTD Stats Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">First Touchdown (FTD)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Points</span>
                <span className="text-xl font-bold">{stats.ftd_points}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Record</span>
                <span className="text-xl font-bold">
                  {stats.ftd_wins}-{stats.ftd_losses}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Win %</span>
                <span className="text-xl font-bold">
                  {stats.ftd_percentage.toFixed(1)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ATTD Stats Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Anytime Touchdown (ATTD)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Points</span>
                <span className="text-xl font-bold">{stats.attd_points}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Record</span>
                <span className="text-xl font-bold">
                  {stats.attd_wins}-{stats.attd_losses}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Win %</span>
                <span className="text-xl font-bold">
                  {stats.attd_percentage.toFixed(1)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Best/Worst Week Display */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Best Week */}
        {stats.best_week && (
          <Card className="border-green-200 dark:border-green-900">
            <CardHeader>
              <CardTitle className="text-lg flex items-center text-green-700 dark:text-green-400">
                <TrendingUp className="h-5 w-5 mr-2" />
                Best Week
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Week</span>
                  <span className="text-lg font-bold">
                    Week {stats.best_week.week}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Points</span>
                  <span className="text-lg font-bold">
                    {stats.best_week.points}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Record</span>
                  <span className="text-lg font-bold">
                    {stats.best_week.wins}-{stats.best_week.losses}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Rank</span>
                  <span className="text-lg font-bold">
                    #{stats.best_week.rank}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Worst Week */}
        {stats.worst_week && (
          <Card className="border-red-200 dark:border-red-900">
            <CardHeader>
              <CardTitle className="text-lg flex items-center text-red-700 dark:text-red-400">
                <TrendingDown className="h-5 w-5 mr-2" />
                Worst Week
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Week</span>
                  <span className="text-lg font-bold">
                    Week {stats.worst_week.week}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Points</span>
                  <span className="text-lg font-bold">
                    {stats.worst_week.points}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Record</span>
                  <span className="text-lg font-bold">
                    {stats.worst_week.wins}-{stats.worst_week.losses}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Rank</span>
                  <span className="text-lg font-bold">
                    #{stats.worst_week.rank}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Streak Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Streak Records</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Longest Win Streak
              </p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {stats.longest_win_streak}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Longest Loss Streak
              </p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {stats.longest_loss_streak}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Weekly Performance Chart */}
      {stats.weekly_breakdown.length > 0 && (
        <WeeklyPerformanceChart
          weeklyData={stats.weekly_breakdown}
          bestWeek={stats.best_week?.week}
          worstWeek={stats.worst_week?.week}
        />
      )}
    </div>
  );
}
