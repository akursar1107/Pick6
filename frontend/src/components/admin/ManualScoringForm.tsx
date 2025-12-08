import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAvailableGames, searchPlayers } from "@/lib/api/picks";
import { manualScoreGame } from "@/lib/api/scores";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errors";
import { Player } from "@/types/pick";

export function ManualScoringForm() {
  const [selectedGameId, setSelectedGameId] = useState<string>("");
  const [firstTdScorerSearch, setFirstTdScorerSearch] = useState<string>("");
  const [firstTdScorer, setFirstTdScorer] = useState<Player | null>(null);
  const [allTdScorersSearch, setAllTdScorersSearch] = useState<string>("");
  const [allTdScorers, setAllTdScorers] = useState<Player[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [scoringResult, setScoringResult] = useState<{
    message: string;
    picks_graded: number;
  } | null>(null);

  const queryClient = useQueryClient();

  // Fetch available games
  const { data: games = [], isLoading: gamesLoading } = useQuery({
    queryKey: ["games", "available"],
    queryFn: getAvailableGames,
  });

  // Search for first TD scorer
  const { data: firstTdScorerResults = [], isLoading: firstTdSearchLoading } =
    useQuery({
      queryKey: ["players", "search", firstTdScorerSearch],
      queryFn: () => searchPlayers(firstTdScorerSearch),
      enabled: firstTdScorerSearch.length >= 2,
    });

  // Search for all TD scorers
  const { data: allTdScorersResults = [], isLoading: allTdSearchLoading } =
    useQuery({
      queryKey: ["players", "search", allTdScorersSearch],
      queryFn: () => searchPlayers(allTdScorersSearch),
      enabled: allTdScorersSearch.length >= 2,
    });

  // Manual scoring mutation
  const manualScoreMutation = useMutation({
    mutationFn: ({
      gameId,
      firstTdScorerId,
      allTdScorerIds,
    }: {
      gameId: string;
      firstTdScorerId: string | null;
      allTdScorerIds: string[];
    }) => manualScoreGame(gameId, firstTdScorerId, allTdScorerIds),
    onSuccess: (data) => {
      setScoringResult({
        message: data.message,
        picks_graded: data.picks_graded,
      });
      setShowResults(true);
      toast.success(
        `Game scored successfully! ${data.picks_graded} picks graded.`
      );

      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["games"] });
      queryClient.invalidateQueries({ queryKey: ["picks"] });
      queryClient.invalidateQueries({ queryKey: ["scores"] });
    },
    onError: (error) => {
      const message = handleApiError(error);
      toast.error(`Failed to score game: ${message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedGameId) {
      toast.error("Please select a game");
      return;
    }

    if (allTdScorers.length === 0) {
      toast.error("Please add at least one touchdown scorer");
      return;
    }

    manualScoreMutation.mutate({
      gameId: selectedGameId,
      firstTdScorerId: firstTdScorer?.id || null,
      allTdScorerIds: allTdScorers.map((p) => p.id),
    });
  };

  const handleAddTdScorer = (player: Player) => {
    if (!allTdScorers.find((p) => p.id === player.id)) {
      setAllTdScorers([...allTdScorers, player]);
      setAllTdScorersSearch("");
    }
  };

  const handleRemoveTdScorer = (playerId: string) => {
    setAllTdScorers(allTdScorers.filter((p) => p.id !== playerId));
  };

  const handleReset = () => {
    setSelectedGameId("");
    setFirstTdScorerSearch("");
    setFirstTdScorer(null);
    setAllTdScorersSearch("");
    setAllTdScorers([]);
    setShowResults(false);
    setScoringResult(null);
  };

  const selectedGame = games.find((g) => g.id === selectedGameId);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Manual Game Scoring</h3>
        <p className="text-sm text-muted-foreground">
          Manually score a game by selecting touchdown scorers. This will grade
          all pending picks for the selected game.
        </p>
      </div>

      {showResults && scoringResult ? (
        <div className="p-4 rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
          <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">
            Scoring Complete
          </h4>
          <p className="text-sm text-green-800 dark:text-green-200">
            {scoringResult.message}
          </p>
          <p className="text-sm text-green-800 dark:text-green-200 mt-1">
            Picks graded: {scoringResult.picks_graded}
          </p>
          <Button
            onClick={handleReset}
            variant="outline"
            size="sm"
            className="mt-3"
          >
            Score Another Game
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Game Selection */}
          <div className="space-y-2">
            <Label htmlFor="game-select">Select Game</Label>
            {gamesLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Spinner size="sm" />
                <span>Loading games...</span>
              </div>
            ) : (
              <select
                id="game-select"
                value={selectedGameId}
                onChange={(e) => setSelectedGameId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">-- Select a game --</option>
                {games.map((game) => (
                  <option key={game.id} value={game.id}>
                    {game.away_team} @ {game.home_team} - Week{" "}
                    {game.week_number}
                  </option>
                ))}
              </select>
            )}
            {selectedGame && (
              <p className="text-xs text-muted-foreground">
                Kickoff: {new Date(selectedGame.kickoff_time).toLocaleString()}
              </p>
            )}
          </div>

          {/* First TD Scorer */}
          <div className="space-y-2">
            <Label htmlFor="first-td-scorer">
              First Touchdown Scorer (Optional)
            </Label>
            {firstTdScorer ? (
              <div className="flex items-center justify-between p-2 rounded-md border border-input bg-muted">
                <span className="text-sm">
                  {firstTdScorer.name} - {firstTdScorer.team} (
                  {firstTdScorer.position})
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setFirstTdScorer(null);
                    setFirstTdScorerSearch("");
                  }}
                >
                  Clear
                </Button>
              </div>
            ) : (
              <div className="relative">
                <Input
                  id="first-td-scorer"
                  type="text"
                  placeholder="Search for player..."
                  value={firstTdScorerSearch}
                  onChange={(e) => setFirstTdScorerSearch(e.target.value)}
                />
                {firstTdSearchLoading && (
                  <div className="absolute right-3 top-3">
                    <Spinner size="sm" />
                  </div>
                )}
                {firstTdScorerSearch.length >= 2 &&
                  firstTdScorerResults.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-background border border-input rounded-md shadow-lg max-h-60 overflow-auto">
                      {firstTdScorerResults.map((player) => (
                        <button
                          key={player.id}
                          type="button"
                          onClick={() => {
                            setFirstTdScorer(player);
                            setFirstTdScorerSearch("");
                          }}
                          className="w-full text-left px-3 py-2 hover:bg-accent text-sm"
                        >
                          {player.name} - {player.team} ({player.position})
                        </button>
                      ))}
                    </div>
                  )}
              </div>
            )}
          </div>

          {/* All TD Scorers */}
          <div className="space-y-2">
            <Label htmlFor="all-td-scorers">
              All Touchdown Scorers (Required)
            </Label>
            {allTdScorers.length > 0 && (
              <div className="space-y-2 mb-2">
                {allTdScorers.map((player) => (
                  <div
                    key={player.id}
                    className="flex items-center justify-between p-2 rounded-md border border-input bg-muted"
                  >
                    <span className="text-sm">
                      {player.name} - {player.team} ({player.position})
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveTdScorer(player.id)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            )}
            <div className="relative">
              <Input
                id="all-td-scorers"
                type="text"
                placeholder="Search to add players..."
                value={allTdScorersSearch}
                onChange={(e) => setAllTdScorersSearch(e.target.value)}
              />
              {allTdSearchLoading && (
                <div className="absolute right-3 top-3">
                  <Spinner size="sm" />
                </div>
              )}
              {allTdScorersSearch.length >= 2 &&
                allTdScorersResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-background border border-input rounded-md shadow-lg max-h-60 overflow-auto">
                    {allTdScorersResults.map((player) => (
                      <button
                        key={player.id}
                        type="button"
                        onClick={() => handleAddTdScorer(player)}
                        className="w-full text-left px-3 py-2 hover:bg-accent text-sm"
                        disabled={allTdScorers.some((p) => p.id === player.id)}
                      >
                        {player.name} - {player.team} ({player.position})
                        {allTdScorers.some((p) => p.id === player.id) && (
                          <span className="ml-2 text-xs text-muted-foreground">
                            (Added)
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={
                !selectedGameId ||
                allTdScorers.length === 0 ||
                manualScoreMutation.isPending
              }
            >
              {manualScoreMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Scoring...
                </>
              ) : (
                "Score Game"
              )}
            </Button>
            <Button type="button" variant="outline" onClick={handleReset}>
              Reset
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
