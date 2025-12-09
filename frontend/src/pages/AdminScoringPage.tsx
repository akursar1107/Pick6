import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getAvailableGames, getPicks } from "@/lib/api/picks";
import { ManualScoringForm } from "@/components/admin/ManualScoringForm";
import { PickOverrideForm } from "@/components/admin/PickOverrideForm";
import { ImportDataButton } from "@/components/admin/ImportDataButton";
import { ImportDataModal } from "@/components/admin/ImportDataModal";
import { ImportProgressModal } from "@/components/admin/ImportProgressModal";
import { ImportHistoryList } from "@/components/admin/ImportHistoryList";
import { Spinner } from "@/components/ui/spinner";
import { format } from "date-fns";
import { useStartImport } from "@/hooks/useImport";
import { ImportConfig, ImportStats } from "@/types/import";
import { toast } from "sonner";
import { getImportErrorToastMessage } from "@/lib/import-errors";

export default function AdminScoringPage() {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  // Fetch games for recent scoring activity
  const { data: games = [], isLoading: gamesLoading } = useQuery({
    queryKey: ["games", "available"],
    queryFn: getAvailableGames,
  });

  // Fetch picks for recent activity
  const { data: picks = [], isLoading: picksLoading } = useQuery({
    queryKey: ["picks", "all"],
    queryFn: () => getPicks(),
  });

  // Filter games pending scoring (completed but not scored)
  const gamesPendingScoring = games.filter(
    (game) => game.status === "completed" && !game.scored_at
  );

  // Filter recently scored games
  const recentlyScoredGames = games
    .filter((game) => game.scored_at)
    .sort(
      (a, b) =>
        new Date(b.scored_at!).getTime() - new Date(a.scored_at!).getTime()
    )
    .slice(0, 5);

  // Filter recently graded picks
  const recentlyGradedPicks = picks
    .filter((pick) => pick.scored_at)
    .sort(
      (a, b) =>
        new Date(b.scored_at!).getTime() - new Date(a.scored_at!).getTime()
    )
    .slice(0, 10);

  // Import mutation using custom hook
  const importMutation = useStartImport();

  const handleImportStart = (config: ImportConfig) => {
    importMutation.mutate(config, {
      onSuccess: (data) => {
        setCurrentJobId(data.job_id);
        setIsImportModalOpen(false);
        setIsProgressModalOpen(true);
        toast.success("Import started successfully", {
          description: `Estimated duration: ${data.estimated_duration_minutes} minutes`,
        });
      },
      onError: (error: any) => {
        const errorMessage = getImportErrorToastMessage(error);
        toast.error("Failed to start import", {
          description: errorMessage,
          duration: 5000,
        });
      },
    });
  };

  const handleImportComplete = (stats: ImportStats) => {
    // Refresh games list
    queryClient.invalidateQueries({ queryKey: ["games"] });
    queryClient.invalidateQueries({ queryKey: ["import-history"] });

    toast.success(
      `Import completed! Created ${stats.games_created} games, updated ${stats.games_updated} games.`
    );
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Admin Scoring Dashboard</h1>
          <p className="text-muted-foreground">
            Manually score games and override pick scores
          </p>
        </div>
        <ImportDataButton onClick={() => setIsImportModalOpen(true)} />
      </div>

      {/* Main Forms Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Manual Scoring Form */}
        <div className="p-6 rounded-lg border border-input bg-card">
          <ManualScoringForm />
        </div>

        {/* Pick Override Form */}
        <div className="p-6 rounded-lg border border-input bg-card">
          <PickOverrideForm />
        </div>
      </div>

      {/* Status Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Games Pending Scoring */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Games Pending Scoring</h2>
          {gamesLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner size="sm" />
              <span>Loading games...</span>
            </div>
          ) : gamesPendingScoring.length === 0 ? (
            <div className="p-4 rounded-lg border border-input bg-muted text-center text-sm text-muted-foreground">
              No games pending scoring
            </div>
          ) : (
            <div className="space-y-2">
              {gamesPendingScoring.map((game) => (
                <div
                  key={game.id}
                  className="p-3 rounded-lg border border-input bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-medium text-sm">
                      {game.away_team} @ {game.home_team}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Week {game.week_number} •{" "}
                      {format(new Date(game.kickoff_time), "MMM d, h:mm a")}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 w-fit">
                      {game.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Scoring Activity */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Recent Scoring Activity</h2>
          {gamesLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner size="sm" />
              <span>Loading activity...</span>
            </div>
          ) : recentlyScoredGames.length === 0 ? (
            <div className="p-4 rounded-lg border border-input bg-muted text-center text-sm text-muted-foreground">
              No recent scoring activity
            </div>
          ) : (
            <div className="space-y-2">
              {recentlyScoredGames.map((game) => (
                <div
                  key={game.id}
                  className="p-3 rounded-lg border border-input bg-card"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-medium text-sm">
                      {game.away_team} @ {game.home_team}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Week {game.week_number}
                    </span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        SCORED
                      </span>
                      {game.is_manually_scored && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                          MANUAL
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      Scored:{" "}
                      {format(new Date(game.scored_at!), "MMM d, h:mm a")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Import History */}
      <div className="mt-8">
        <ImportHistoryList limit={5} />
      </div>

      {/* Recently Graded Picks */}
      <div className="mt-8 space-y-4">
        <h2 className="text-xl font-semibold">Recently Graded Picks</h2>
        {picksLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner size="sm" />
            <span>Loading picks...</span>
          </div>
        ) : recentlyGradedPicks.length === 0 ? (
          <div className="p-4 rounded-lg border border-input bg-muted text-center text-sm text-muted-foreground">
            No recently graded picks
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-input">
                <tr className="text-left">
                  <th className="pb-2 font-semibold">Player</th>
                  <th className="pb-2 font-semibold">Game</th>
                  <th className="pb-2 font-semibold">Status</th>
                  <th className="pb-2 font-semibold">Points</th>
                  <th className="pb-2 font-semibold">Scored At</th>
                  <th className="pb-2 font-semibold">Override</th>
                </tr>
              </thead>
              <tbody>
                {recentlyGradedPicks.map((pick) => (
                  <tr key={pick.id} className="border-b border-input/50">
                    <td className="py-2">{pick.player?.name || "Unknown"}</td>
                    <td className="py-2">
                      {pick.game?.away_team || "?"} @{" "}
                      {pick.game?.home_team || "?"}
                    </td>
                    <td className="py-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          pick.status === "win"
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            : pick.status === "loss"
                            ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                            : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                        }`}
                      >
                        {pick.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2">
                      {pick.total_points || 0} ({pick.ftd_points || 0} FTD +{" "}
                      {pick.attd_points || 0} ATTD)
                    </td>
                    <td className="py-2 text-muted-foreground">
                      {pick.scored_at
                        ? format(new Date(pick.scored_at), "MMM d, h:mm a")
                        : "-"}
                    </td>
                    <td className="py-2">
                      {pick.is_manual_override ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                          YES
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          No
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Import Modals */}
      <ImportDataModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportStart={handleImportStart}
      />

      {currentJobId && (
        <ImportProgressModal
          jobId={currentJobId}
          isOpen={isProgressModalOpen}
          onClose={() => setIsProgressModalOpen(false)}
          onComplete={handleImportComplete}
        />
      )}
    </div>
  );
}
