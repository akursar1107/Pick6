import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { LeaderboardTable } from "@/components/leaderboard/LeaderboardTable";
import { WeekSelector } from "@/components/leaderboard/WeekSelector";
import { UserStatsModal } from "@/components/leaderboard/UserStatsModal";
import { ExportButton } from "@/components/leaderboard/ExportButton";
import { EmptyState } from "@/components/leaderboard/EmptyState";
import { useAuthStore } from "@/stores/authStore";
import * as leaderboardApi from "@/lib/api/leaderboard";
import {
  AlertCircle,
  Calendar,
  ClipboardList,
  Loader2,
  Filter,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { useLeaderboardUpdates } from "@/hooks/useLeaderboardUpdates";

export default function StandingsPage() {
  const [activeTab, setActiveTab] = useState<"season" | "weekly">("season");
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedUsername, setSelectedUsername] = useState<string | undefined>(
    undefined
  );
  const currentSeason = new Date().getFullYear();
  const user = useAuthStore((state) => state.user);
  const { toast } = useToast();
  const navigate = useNavigate();

  // Listen for scoring events and invalidate cache
  useLeaderboardUpdates(currentSeason);

  // Fetch season leaderboard
  const {
    data: seasonData,
    isLoading: seasonLoading,
    error: seasonError,
    isFetching: seasonFetching,
    refetch: refetchSeason,
  } = useQuery({
    queryKey: ["leaderboard", "season", currentSeason],
    queryFn: () => leaderboardApi.getSeasonLeaderboard(currentSeason),
    enabled: activeTab === "season",
    refetchInterval: 30000, // Poll every 30 seconds
    refetchOnWindowFocus: true, // Refetch when window gains focus
  });

  // Fetch weekly leaderboard
  const {
    data: weeklyData,
    isLoading: weeklyLoading,
    error: weeklyError,
    isFetching: weeklyFetching,
    refetch: refetchWeekly,
  } = useQuery({
    queryKey: ["leaderboard", "week", currentSeason, selectedWeek],
    queryFn: () =>
      leaderboardApi.getWeeklyLeaderboard(currentSeason, selectedWeek!),
    enabled: activeTab === "weekly" && selectedWeek !== null,
    refetchInterval: 30000, // Poll every 30 seconds
    refetchOnWindowFocus: true, // Refetch when window gains focus
  });

  const handleUserClick = (userId: string) => {
    // Find the username from the current leaderboard data
    const currentData = activeTab === "season" ? seasonData : weeklyData;
    const userEntry = currentData?.find((entry) => entry.user_id === userId);
    setSelectedUserId(userId);
    setSelectedUsername(userEntry?.display_name || userEntry?.username);
  };

  const handleCloseModal = () => {
    setSelectedUserId(null);
    setSelectedUsername(undefined);
  };

  const handleManualRefresh = async () => {
    if (activeTab === "season") {
      await refetchSeason();
    } else {
      await refetchWeekly();
    }
    toast({
      title: "Leaderboard refreshed",
      description: "Latest standings have been loaded.",
    });
  };

  const handleExport = async (format: "csv" | "json") => {
    try {
      const week = activeTab === "weekly" ? selectedWeek : undefined;
      const blob = await leaderboardApi.exportLeaderboard(
        currentSeason,
        week ?? undefined,
        format
      );

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      // Generate filename
      const weekPart = week ? `_week_${week}` : "";
      const filename = `leaderboard_season_${currentSeason}${weekPart}.${format}`;
      link.download = filename;

      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Export successful",
        description: `Leaderboard exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Unable to export leaderboard. Please try again.",
        variant: "destructive",
      });
    }
  };

  const hasData = () => {
    if (activeTab === "season") {
      return seasonData && seasonData.length > 0;
    } else {
      return weeklyData && weeklyData.length > 0;
    }
  };

  const renderSeasonContent = () => {
    if (seasonLoading) {
      return (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      );
    }

    if (seasonError) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load season leaderboard. Please try again later.
          </AlertDescription>
        </Alert>
      );
    }

    if (!seasonData || seasonData.length === 0) {
      return (
        <EmptyState
          icon={ClipboardList}
          title="Season hasn't started yet"
          message="No picks have been graded yet. Be the first to submit your predictions and start competing!"
          action={{
            label: "Submit Picks",
            onClick: () => navigate("/picks"),
          }}
        />
      );
    }

    return (
      <LeaderboardTable
        entries={seasonData}
        currentUserId={user?.id}
        onUserClick={handleUserClick}
      />
    );
  };

  const renderWeeklyContent = () => {
    if (selectedWeek === null) {
      return (
        <EmptyState
          icon={Filter}
          title="Select a week"
          message="Please select a week from the dropdown above to view the weekly leaderboard."
        />
      );
    }

    if (weeklyLoading) {
      return (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      );
    }

    if (weeklyError) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load weekly leaderboard. Please try again later.
          </AlertDescription>
        </Alert>
      );
    }

    if (!weeklyData || weeklyData.length === 0) {
      // Show "no games" empty state
      return (
        <EmptyState
          icon={Calendar}
          title="No games this week"
          message={`Week ${selectedWeek} has no graded picks yet. Games may not have been played or picks are still pending.`}
          action={{
            label: "Submit Picks",
            onClick: () => navigate("/picks"),
          }}
        />
      );
    }

    // Check if all picks are pending (games in progress)
    const allPending = weeklyData.every(
      (entry) => entry.wins === 0 && entry.losses === 0 && entry.pending > 0
    );

    if (allPending) {
      return (
        <EmptyState
          icon={Loader2}
          title="Games in progress"
          message={`Week ${selectedWeek} games are currently being played. Check back soon for updated standings!`}
        />
      );
    }

    return (
      <LeaderboardTable
        entries={weeklyData}
        currentUserId={user?.id}
        onUserClick={handleUserClick}
      />
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-3xl">Leaderboard</CardTitle>
            {(seasonFetching || weeklyFetching) && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Updating...</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={(v: string) =>
              setActiveTab(v as "season" | "weekly")
            }
          >
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
              <TabsList>
                <TabsTrigger value="season">Season</TabsTrigger>
                <TabsTrigger value="weekly">Weekly</TabsTrigger>
              </TabsList>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                {activeTab === "weekly" && (
                  <WeekSelector
                    selectedWeek={selectedWeek}
                    onWeekChange={setSelectedWeek}
                    currentWeek={undefined} // TODO: Get current week from API or context
                  />
                )}
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleManualRefresh}
                  disabled={seasonFetching || weeklyFetching}
                  title="Refresh leaderboard"
                >
                  <RefreshCw
                    className={`h-4 w-4 ${
                      seasonFetching || weeklyFetching ? "animate-spin" : ""
                    }`}
                  />
                </Button>
                <ExportButton onExport={handleExport} disabled={!hasData()} />
              </div>
            </div>

            <TabsContent value="season" className="mt-0">
              {renderSeasonContent()}
            </TabsContent>

            <TabsContent value="weekly" className="mt-0">
              {renderWeeklyContent()}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* User Stats Modal */}
      <UserStatsModal
        userId={selectedUserId}
        username={selectedUsername}
        season={currentSeason}
        onClose={handleCloseModal}
      />
    </div>
  );
}
