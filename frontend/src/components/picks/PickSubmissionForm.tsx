import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPick, updatePick } from "@/lib/api/picks";
import { Player, GameWithPick, PickResponse } from "@/types/pick";
import { PlayerSearch } from "./PlayerSearch";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";

interface PickSubmissionFormProps {
  game?: GameWithPick;
  existingPick?: PickResponse;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function PickSubmissionForm({
  game,
  existingPick,
  onSuccess,
  onCancel,
}: PickSubmissionFormProps) {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(
    existingPick?.player || null
  );
  const [selectedGameId, setSelectedGameId] = useState<string>(
    game?.id || existingPick?.game_id || ""
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: createPick,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["picks"] });
      queryClient.invalidateQueries({ queryKey: ["games", "available"] });
      toast.success("Pick submitted successfully!");
      onSuccess?.();
    },
    onError: (error: unknown) => {
      const message = handleApiError(error);
      toast.error(message);
      setErrors({ submit: message });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      pickId,
      data,
    }: {
      pickId: string;
      data: { player_id: string };
    }) => updatePick(pickId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["picks"] });
      queryClient.invalidateQueries({ queryKey: ["games", "available"] });
      toast.success("Pick updated successfully!");
      onSuccess?.();
    },
    onError: (error: unknown) => {
      const message = handleApiError(error);
      toast.error(message);
      setErrors({ submit: message });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validation
    const newErrors: Record<string, string> = {};
    if (!selectedGameId) {
      newErrors.game = "Please select a game";
    }
    if (!selectedPlayer) {
      newErrors.player = "Please select a player";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Submit or update pick
    if (existingPick) {
      updateMutation.mutate({
        pickId: existingPick.id,
        data: { player_id: selectedPlayer!.id },
      });
    } else {
      createMutation.mutate({
        game_id: selectedGameId,
        player_id: selectedPlayer!.id,
      });
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold">
          {existingPick ? "Edit Pick" : "Make Your Pick"}
        </h2>
        {game && (
          <p className="text-sm text-muted-foreground mt-1">
            {game.away_team} @ {game.home_team} • Week {game.week_number}
          </p>
        )}
      </div>

      {!game && !existingPick && (
        <div className="space-y-2">
          <label
            htmlFor="game-select"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Select Game
          </label>
          <select
            id="game-select"
            value={selectedGameId}
            onChange={(e) => setSelectedGameId(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="">Select a game...</option>
            {/* Games will be populated by parent component */}
          </select>
          {errors.game && (
            <p className="text-sm text-destructive">{errors.game}</p>
          )}
        </div>
      )}

      <PlayerSearch
        onSelect={setSelectedPlayer}
        selectedPlayer={selectedPlayer}
      />
      {errors.player && (
        <p className="text-sm text-destructive">{errors.player}</p>
      )}

      {errors.submit && (
        <div className="p-3 rounded-md bg-destructive/10 border border-destructive">
          <p className="text-sm text-destructive">{errors.submit}</p>
        </div>
      )}

      <div className="flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
          {isLoading && <Spinner size="sm" className="mr-2" />}
          {isLoading
            ? "Submitting..."
            : existingPick
            ? "Update Pick"
            : "Submit Pick"}
        </Button>
      </div>
    </form>
  );
}
