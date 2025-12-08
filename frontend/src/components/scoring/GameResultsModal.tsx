import { useQuery } from "@tanstack/react-query";
import { getGameResult } from "@/lib/api/scores";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { format } from "date-fns";
import { useEffect } from "react";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";

interface GameResultsModalProps {
  gameId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function GameResultsModal({
  gameId,
  isOpen,
  onClose,
}: GameResultsModalProps) {
  const {
    data: gameResult,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["gameResult", gameId],
    queryFn: () => getGameResult(gameId!),
    enabled: !!gameId && isOpen,
  });

  // Show error toast when error occurs
  useEffect(() => {
    if (error) {
      const message = handleApiError(error);
      toast.error(message);
    }
  }, [error]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Game Scoring Results</DialogTitle>
          <DialogDescription>
            View touchdown scorers and grading details for this game
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
          </div>
        )}

        {error && (
          <div className="text-center py-8 text-destructive">
            Failed to load game results
          </div>
        )}

        {gameResult && (
          <div className="space-y-6">
            {/* First TD Scorer */}
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-2">
                First Touchdown Scorer
              </h3>
              {gameResult.first_td_scorer ? (
                <div className="p-3 rounded-lg bg-accent">
                  <div className="font-medium">
                    {gameResult.first_td_scorer.name}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {gameResult.first_td_scorer.team} •{" "}
                    {gameResult.first_td_scorer.position}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground italic">
                  No touchdowns scored in this game
                </div>
              )}
            </div>

            {/* All TD Scorers */}
            {gameResult.all_td_scorers &&
              gameResult.all_td_scorers.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-muted-foreground mb-2">
                    All Touchdown Scorers ({gameResult.all_td_scorers.length})
                  </h3>
                  <div className="space-y-2">
                    {gameResult.all_td_scorers.map((player) => (
                      <div
                        key={player.id}
                        className="p-3 rounded-lg bg-accent/50"
                      >
                        <div className="font-medium">{player.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {player.team} • {player.position}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Grading Info */}
            <div className="pt-4 border-t space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Picks Graded:</span>
                <span className="font-medium">
                  {gameResult.picks_graded_count}
                </span>
              </div>
              {gameResult.scored_at && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Scored At:</span>
                  <span className="font-medium">
                    {format(
                      new Date(gameResult.scored_at),
                      "MMM d, yyyy • h:mm a"
                    )}
                  </span>
                </div>
              )}
              {gameResult.is_manually_scored && (
                <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
                  <span className="font-medium">⚠️ Manually Scored</span>
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
