import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAvailableGames } from "@/lib/api/picks";
import { GameWithPick } from "@/types/pick";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { format } from "date-fns";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";

interface AvailableGamesProps {
  onMakePick: (game: GameWithPick) => void;
  onEditPick: (game: GameWithPick) => void;
}

export function AvailableGames({
  onMakePick,
  onEditPick,
}: AvailableGamesProps) {
  const {
    data: games = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["games", "available"],
    queryFn: getAvailableGames,
    refetchInterval: 60000, // Refetch every minute
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
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Available Games</h2>
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground gap-3">
          <Spinner size="lg" />
          <span>Loading games...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Available Games</h2>
        <div className="text-center py-8 text-destructive">
          Failed to load games. Please try again.
        </div>
      </div>
    );
  }

  if (games.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Available Games</h2>
        <div className="text-center py-8 text-muted-foreground">
          No upcoming games available for picks.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Available Games</h2>
      <div className="space-y-3">
        {games.map((game) => (
          <div
            key={game.id}
            className="p-4 rounded-lg border border-input bg-card hover:bg-accent/50 transition-colors"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-base sm:text-lg">
                    {game.away_team} @ {game.home_team}
                  </span>
                  <span className="text-xs text-muted-foreground px-2 py-0.5 rounded-full bg-muted">
                    Week {game.week_number}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {format(new Date(game.kickoff_time), "EEE, MMM d • h:mm a")}
                </div>
                {game.user_pick && (
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs font-medium text-primary">
                      Your Pick:
                    </span>
                    <span className="text-sm font-medium">
                      {game.user_pick.player_name}
                    </span>
                  </div>
                )}
              </div>
              <div className="w-full sm:w-auto">
                {game.user_pick ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEditPick(game)}
                    className="w-full sm:w-auto"
                  >
                    Edit Pick
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => onMakePick(game)}
                    className="w-full sm:w-auto"
                  >
                    Make Pick
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
