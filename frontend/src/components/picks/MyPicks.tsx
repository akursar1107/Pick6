import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPicks, deletePick } from "@/lib/api/picks";
import { PickResponse } from "@/types/pick";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { format } from "date-fns";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";

interface MyPicksProps {
  onEditPick: (pick: PickResponse) => void;
}

export function MyPicks({ onEditPick }: MyPicksProps) {
  const [deletingPickId, setDeletingPickId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const {
    data: picks = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["picks"],
    queryFn: () => getPicks(),
  });

  // Show error toast when error occurs
  useEffect(() => {
    if (error) {
      const message = handleApiError(error);
      toast.error(message);
    }
  }, [error]);

  const deleteMutation = useMutation({
    mutationFn: deletePick,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["picks"] });
      queryClient.invalidateQueries({ queryKey: ["games", "available"] });
      toast.success("Pick deleted successfully!");
      setDeletingPickId(null);
    },
    onError: (error: unknown) => {
      const message = handleApiError(error);
      toast.error(message);
      setDeletingPickId(null);
    },
  });

  const handleDeleteClick = (pickId: string) => {
    if (deletingPickId === pickId) {
      // Confirm deletion
      deleteMutation.mutate(pickId);
    } else {
      // First click - show confirmation
      setDeletingPickId(pickId);
      // Auto-cancel after 3 seconds
      setTimeout(() => {
        setDeletingPickId(null);
      }, 3000);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">My Picks</h2>
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground gap-3">
          <Spinner size="lg" />
          <span>Loading picks...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">My Picks</h2>
        <div className="text-center py-8 text-destructive">
          Failed to load picks. Please try again.
        </div>
      </div>
    );
  }

  if (picks.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">My Picks</h2>
        <div className="text-center py-8 text-muted-foreground">
          You haven't made any picks yet. Select a game above to get started!
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">My Picks</h2>
      <div className="space-y-3">
        {picks.map((pick) => (
          <div
            key={pick.id}
            className="p-4 rounded-lg border border-input bg-card"
          >
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-sm sm:text-base">
                    {pick.game?.away_team} @ {pick.game?.home_team}
                  </span>
                  <span className="text-xs text-muted-foreground px-2 py-0.5 rounded-full bg-muted">
                    Week {pick.game?.week_number}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      pick.status === "pending"
                        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                        : pick.status === "win"
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                        : pick.status === "loss"
                        ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                        : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                    }`}
                  >
                    {pick.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm">
                  <span className="text-muted-foreground">Player: </span>
                  <span className="font-medium">
                    {pick.player?.name} ({pick.player?.team} •{" "}
                    {pick.player?.position})
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  Kickoff:{" "}
                  {pick.game?.kickoff_time &&
                    format(
                      new Date(pick.game.kickoff_time),
                      "EEE, MMM d • h:mm a"
                    )}
                </div>
                <div className="text-xs text-muted-foreground">
                  Submitted:{" "}
                  {format(
                    new Date(pick.pick_submitted_at),
                    "MMM d, yyyy • h:mm a"
                  )}
                </div>
              </div>
              <div className="flex gap-2 sm:flex-col sm:w-auto w-full">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEditPick(pick)}
                  disabled={deleteMutation.isPending}
                  className="flex-1 sm:flex-none sm:w-20"
                >
                  Edit
                </Button>
                <Button
                  variant={
                    deletingPickId === pick.id ? "destructive" : "outline"
                  }
                  size="sm"
                  onClick={() => handleDeleteClick(pick.id)}
                  disabled={deleteMutation.isPending}
                  className="flex-1 sm:flex-none sm:w-20"
                >
                  {deleteMutation.isPending && (
                    <Spinner size="sm" className="mr-2" />
                  )}
                  {deletingPickId === pick.id
                    ? "Confirm?"
                    : deleteMutation.isPending
                    ? "Deleting..."
                    : "Delete"}
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
