import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAllPicksForAdmin } from "@/lib/api/picks";
import { overridePickScore } from "@/lib/api/scores";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";

export function PickOverrideForm() {
  const [selectedPickId, setSelectedPickId] = useState<string>("");
  const [status, setStatus] = useState<"win" | "loss">("win");
  const [ftdPoints, setFtdPoints] = useState<number>(0);
  const [attdPoints, setAttdPoints] = useState<number>(0);
  const [showResults, setShowResults] = useState(false);
  const [overrideResult, setOverrideResult] = useState<{
    message: string;
    pick_id: string;
    status: string;
    ftd_points: number;
    attd_points: number;
    total_points: number;
  } | null>(null);

  const queryClient = useQueryClient();

  // Fetch all picks (admin endpoint)
  const { data: picks = [], isLoading: picksLoading } = useQuery({
    queryKey: ["picks", "admin", "all"],
    queryFn: () => getAllPicksForAdmin(),
  });

  // Override mutation
  const overrideMutation = useMutation({
    mutationFn: ({
      pickId,
      status,
      ftdPoints,
      attdPoints,
    }: {
      pickId: string;
      status: "win" | "loss";
      ftdPoints: number;
      attdPoints: number;
    }) => overridePickScore(pickId, status, ftdPoints, attdPoints),
    onSuccess: (data) => {
      setOverrideResult(data);
      setShowResults(true);
      toast.success("Pick score overridden successfully!");

      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["picks"] });
      queryClient.invalidateQueries({ queryKey: ["scores"] });
    },
    onError: (error) => {
      const message = handleApiError(error);
      toast.error(`Failed to override pick: ${message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedPickId) {
      toast.error("Please select a pick");
      return;
    }

    // Validate points
    if (ftdPoints < 0 || ftdPoints > 3) {
      toast.error("FTD points must be between 0 and 3");
      return;
    }

    if (attdPoints < 0 || attdPoints > 1) {
      toast.error("ATTD points must be between 0 and 1");
      return;
    }

    overrideMutation.mutate({
      pickId: selectedPickId,
      status,
      ftdPoints,
      attdPoints,
    });
  };

  const handleReset = () => {
    setSelectedPickId("");
    setStatus("win");
    setFtdPoints(0);
    setAttdPoints(0);
    setShowResults(false);
    setOverrideResult(null);
  };

  const selectedPick = picks.find((p) => p.id === selectedPickId);

  // Update form when pick is selected
  const handlePickChange = (pickId: string) => {
    setSelectedPickId(pickId);
    const pick = picks.find((p) => p.id === pickId);
    if (pick) {
      setStatus(pick.status === "win" ? "win" : "loss");
      setFtdPoints(pick.ftd_points || 0);
      setAttdPoints(pick.attd_points || 0);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Override Pick Score</h3>
        <p className="text-sm text-muted-foreground">
          Manually override a pick's score and status. This will update the
          user's total score and create an audit trail.
        </p>
      </div>

      {showResults && overrideResult ? (
        <div className="p-4 rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
          <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">
            Override Complete
          </h4>
          <p className="text-sm text-green-800 dark:text-green-200">
            {overrideResult.message}
          </p>
          <div className="mt-2 space-y-1 text-sm text-green-800 dark:text-green-200">
            <p>Pick ID: {overrideResult.pick_id}</p>
            <p>Status: {overrideResult.status}</p>
            <p>FTD Points: {overrideResult.ftd_points}</p>
            <p>ATTD Points: {overrideResult.attd_points}</p>
            <p>Total Points: {overrideResult.total_points}</p>
          </div>
          <Button
            onClick={handleReset}
            variant="outline"
            size="sm"
            className="mt-3"
          >
            Override Another Pick
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Pick Selection */}
          <div className="space-y-2">
            <Label htmlFor="pick-select">Select Pick</Label>
            {picksLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Spinner size="sm" />
                <span>Loading picks...</span>
              </div>
            ) : (
              <select
                id="pick-select"
                value={selectedPickId}
                onChange={(e) => handlePickChange(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">-- Select a pick --</option>
                {picks.map((pick) => (
                  <option key={pick.id} value={pick.id}>
                    {pick.player?.name || "Unknown Player"} -{" "}
                    {pick.game?.away_team || "Unknown"} @{" "}
                    {pick.game?.home_team || "Unknown"} (Week{" "}
                    {pick.game?.week_number || "?"}) - Status: {pick.status}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Current Values Display */}
          {selectedPick && (
            <div className="p-3 rounded-md border border-input bg-muted space-y-1">
              <h4 className="text-sm font-semibold mb-2">Current Values</h4>
              <p className="text-xs text-muted-foreground">
                Player: {selectedPick.player?.name || "Unknown"}
              </p>
              <p className="text-xs text-muted-foreground">
                Game: {selectedPick.game?.away_team || "Unknown"} @{" "}
                {selectedPick.game?.home_team || "Unknown"}
              </p>
              <p className="text-xs text-muted-foreground">
                Status: {selectedPick.status}
              </p>
              <p className="text-xs text-muted-foreground">
                FTD Points: {selectedPick.ftd_points || 0}
              </p>
              <p className="text-xs text-muted-foreground">
                ATTD Points: {selectedPick.attd_points || 0}
              </p>
              <p className="text-xs text-muted-foreground">
                Total Points: {selectedPick.total_points || 0}
              </p>
              {selectedPick.is_manual_override && (
                <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                  ⚠️ This pick has been manually overridden
                </p>
              )}
            </div>
          )}

          {/* Status */}
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value as "win" | "loss")}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="win">Win</option>
              <option value="loss">Loss</option>
            </select>
          </div>

          {/* FTD Points */}
          <div className="space-y-2">
            <Label htmlFor="ftd-points">FTD Points (0 or 3)</Label>
            <Input
              id="ftd-points"
              type="number"
              min="0"
              max="3"
              step="1"
              value={ftdPoints}
              onChange={(e) => setFtdPoints(parseInt(e.target.value) || 0)}
            />
            <p className="text-xs text-muted-foreground">
              First Touchdown points: 0 (incorrect) or 3 (correct)
            </p>
          </div>

          {/* ATTD Points */}
          <div className="space-y-2">
            <Label htmlFor="attd-points">ATTD Points (0 or 1)</Label>
            <Input
              id="attd-points"
              type="number"
              min="0"
              max="1"
              step="1"
              value={attdPoints}
              onChange={(e) => setAttdPoints(parseInt(e.target.value) || 0)}
            />
            <p className="text-xs text-muted-foreground">
              Anytime Touchdown points: 0 (didn't score) or 1 (scored)
            </p>
          </div>

          {/* Total Points Display */}
          <div className="p-3 rounded-md border border-input bg-accent">
            <p className="text-sm font-medium">
              Total Points: {ftdPoints + attdPoints}
            </p>
          </div>

          {/* Submit Button */}
          <div className="flex gap-2">
            <Button
              type="submit"
              variant="destructive"
              disabled={!selectedPickId || overrideMutation.isPending}
            >
              {overrideMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Overriding...
                </>
              ) : (
                "Override Pick Score"
              )}
            </Button>
            <Button type="button" variant="outline" onClick={handleReset}>
              Reset
            </Button>
          </div>

          {/* Warning */}
          <div className="p-3 rounded-md border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950">
            <p className="text-xs text-amber-800 dark:text-amber-200">
              ⚠️ Warning: This action will override the pick's score and update
              the user's total score. An audit trail will be created with your
              admin ID and timestamp.
            </p>
          </div>
        </form>
      )}
    </div>
  );
}
