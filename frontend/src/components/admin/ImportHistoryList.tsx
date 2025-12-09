import { useState } from "react";
import { format } from "date-fns";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useImportHistory } from "@/hooks/useImport";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ImportHistoryListProps {
  limit?: number;
}

export function ImportHistoryList({ limit = 10 }: ImportHistoryListProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [seasonFilter, setSeasonFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Fetch all history to get available seasons for filter dropdown
  const { data: allHistoryData } = useImportHistory({
    limit: 1000, // Large limit to get all unique seasons
  });

  // Fetch filtered history for display
  const { data: historyData, isLoading } = useImportHistory({
    limit,
    season: seasonFilter === "all" ? undefined : parseInt(seasonFilter),
    status: statusFilter === "all" ? undefined : statusFilter,
  });

  const imports = historyData?.imports || [];

  // Extract unique seasons from all import history data (not just filtered results)
  const seasons = Array.from(
    new Set((allHistoryData?.imports || []).map((imp) => imp.season))
  ).sort((a, b) => b - a); // Sort descending (most recent first)

  const getStatusBadge = (
    status: "completed" | "failed" | "running" | "pending"
  ) => {
    const variants = {
      completed:
        "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      running: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
      pending:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    };

    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${variants[status]}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const formatWeeks = (weeks: number[] | null) => {
    if (!weeks || weeks.length === 0) {
      return "All weeks";
    }
    if (weeks.length === 18) {
      return "All weeks (1-18)";
    }
    if (weeks.length <= 3) {
      return `Week${weeks.length > 1 ? "s" : ""} ${weeks.join(", ")}`;
    }
    return `${weeks.length} weeks`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Import History</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="gap-2"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="h-4 w-4" />
              Collapse
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4" />
              Expand
            </>
          )}
        </Button>
      </div>

      {isExpanded && (
        <>
          {/* Filters */}
          <div className="flex gap-4">
            <div className="flex-1">
              <Select value={seasonFilter} onValueChange={setSeasonFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by season" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Seasons</SelectItem>
                  {seasons.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year} Season
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* History Table */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : imports.length === 0 ? (
            <div className="p-8 rounded-lg border border-input bg-muted text-center text-sm text-muted-foreground">
              No import history found
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-input">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 border-b border-input">
                  <tr className="text-left">
                    <th className="p-3 font-semibold">Season</th>
                    <th className="p-3 font-semibold">Weeks</th>
                    <th className="p-3 font-semibold">Status</th>
                    <th className="p-3 font-semibold">Started</th>
                    <th className="p-3 font-semibold">Duration</th>
                    <th className="p-3 font-semibold">Statistics</th>
                  </tr>
                </thead>
                <tbody>
                  {imports.map((importJob) => {
                    const isRunning = importJob.status === "running";
                    const duration = importJob.completed_at
                      ? Math.round(
                          (new Date(importJob.completed_at).getTime() -
                            new Date(importJob.started_at).getTime()) /
                            1000 /
                            60
                        )
                      : null;

                    return (
                      <tr
                        key={importJob.id}
                        className={`border-b border-input/50 ${
                          isRunning ? "bg-blue-50/50 dark:bg-blue-950/20" : ""
                        }`}
                      >
                        <td className="p-3 font-medium">{importJob.season}</td>
                        <td className="p-3 text-muted-foreground">
                          {formatWeeks(importJob.weeks)}
                        </td>
                        <td className="p-3">
                          {getStatusBadge(importJob.status)}
                        </td>
                        <td className="p-3 text-muted-foreground">
                          {format(
                            new Date(importJob.started_at),
                            "MMM d, h:mm a"
                          )}
                        </td>
                        <td className="p-3 text-muted-foreground">
                          {duration !== null ? `${duration}m` : "-"}
                        </td>
                        <td className="p-3">
                          <div className="text-xs space-y-1">
                            <div>
                              <span className="text-muted-foreground">
                                Games:
                              </span>{" "}
                              {importJob.stats.games_created}C /{" "}
                              {importJob.stats.games_updated}U
                            </div>
                            <div>
                              <span className="text-muted-foreground">
                                Teams:
                              </span>{" "}
                              {importJob.stats.teams_created}
                              {" • "}
                              <span className="text-muted-foreground">
                                Players:
                              </span>{" "}
                              {importJob.stats.players_created}
                            </div>
                            {importJob.grade_games && (
                              <div>
                                <span className="text-muted-foreground">
                                  Graded:
                                </span>{" "}
                                {importJob.stats.games_graded}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
