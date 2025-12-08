import { useQuery } from "@tanstack/react-query";
import { getUserScore } from "@/lib/api/scores";
import { Spinner } from "@/components/ui/spinner";
import { useEffect } from "react";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";

interface UserScoreCardProps {
  userId: string;
}

export function UserScoreCard({ userId }: UserScoreCardProps) {
  const {
    data: userScore,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["userScore", userId],
    queryFn: () => getUserScore(userId),
    enabled: !!userId,
  });

  // Show error toast when error occurs
  useEffect(() => {
    if (error) {
      const message = handleApiError(error);
      toast.error(message);
    }
  }, [error]);

  if (isLoading) {
    return (
      <div className="p-6 rounded-lg border border-input bg-card">
        <div className="flex items-center justify-center py-4">
          <Spinner size="md" />
        </div>
      </div>
    );
  }

  if (error || !userScore) {
    return (
      <div className="p-6 rounded-lg border border-input bg-card">
        <div className="text-center text-destructive">
          Failed to load score data
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-lg border border-input bg-card">
      <h3 className="text-lg font-semibold mb-4">Your Score</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-3xl font-bold text-primary">
            {userScore.total_score}
          </div>
          <div className="text-sm text-muted-foreground mt-1">Total Points</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">
            {userScore.total_wins}
          </div>
          <div className="text-sm text-muted-foreground mt-1">Wins</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-red-600 dark:text-red-400">
            {userScore.total_losses}
          </div>
          <div className="text-sm text-muted-foreground mt-1">Losses</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
            {(userScore.win_percentage * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-muted-foreground mt-1">Win Rate</div>
        </div>
      </div>
    </div>
  );
}
