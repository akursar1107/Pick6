import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Database,
  Calendar,
  TrendingUp,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface SchedulerJob {
  id: string;
  name: string;
  next_run_time: string | null;
  trigger: string;
}

interface SchedulerHealth {
  status: string;
  running: boolean;
  jobs: SchedulerJob[];
  timezone: string;
}

interface ScoringStatistics {
  picks_graded_7d: number;
  games_scored_7d: number;
  pending_picks: number;
  last_scoring_time: string | null;
  last_scored_game: string | null;
}

interface ScoringHealth {
  status: string;
  database_healthy: boolean;
  statistics: ScoringStatistics;
  issues: string[] | null;
}

interface SystemHealth {
  status: string;
  components: {
    database: string;
    scheduler: string;
  };
  timestamp: string;
}

const AdminMonitoringPage: React.FC = () => {
  // Fetch scheduler health
  const {
    data: schedulerHealth,
    isLoading: schedulerLoading,
    error: schedulerError,
  } = useQuery<SchedulerHealth>({
    queryKey: ["health", "scheduler"],
    queryFn: async () => {
      const response = await apiClient.get("/health/scheduler");
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch scoring health
  const {
    data: scoringHealth,
    isLoading: scoringLoading,
    error: scoringError,
  } = useQuery<ScoringHealth>({
    queryKey: ["health", "scoring"],
    queryFn: async () => {
      const response = await apiClient.get("/health/scoring");
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch system health
  const { data: systemHealth, isLoading: systemLoading } =
    useQuery<SystemHealth>({
      queryKey: ["health", "system"],
      queryFn: async () => {
        const response = await apiClient.get("/health/system");
        return response.data;
      },
      refetchInterval: 30000, // Refresh every 30 seconds
    });

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      healthy: {
        variant: "default" as const,
        icon: CheckCircle,
        color: "text-green-600",
      },
      degraded: {
        variant: "secondary" as const,
        icon: AlertCircle,
        color: "text-yellow-600",
      },
      unhealthy: {
        variant: "destructive" as const,
        icon: AlertCircle,
        color: "text-red-600",
      },
      stopped: {
        variant: "destructive" as const,
        icon: AlertCircle,
        color: "text-red-600",
      },
    };

    const config =
      statusConfig[status as keyof typeof statusConfig] ||
      statusConfig.unhealthy;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className={`h-3 w-3 ${config.color}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return "Never";
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const formatRelativeTime = (isoString: string | null) => {
    if (!isoString) return "Never";
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60)
      return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24)
      return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Monitoring</h1>
        <p className="text-muted-foreground">
          Monitor the health and status of the scoring system
        </p>
      </div>

      {/* System Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            System Overview
          </CardTitle>
          <CardDescription>Overall system health status</CardDescription>
        </CardHeader>
        <CardContent>
          {systemLoading ? (
            <Skeleton className="h-20 w-full" />
          ) : systemHealth ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">Overall Status</span>
                {getStatusBadge(systemHealth.status)}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="text-sm">Database</span>
                  {getStatusBadge(systemHealth.components.database)}
                </div>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="text-sm">Scheduler</span>
                  {getStatusBadge(systemHealth.components.scheduler)}
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Last checked: {formatDateTime(systemHealth.timestamp)}
              </p>
            </div>
          ) : (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>Failed to load system health</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Scheduler Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Scheduler Status
          </CardTitle>
          <CardDescription>Scheduled jobs and next run times</CardDescription>
        </CardHeader>
        <CardContent>
          {schedulerLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : schedulerError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Failed to load scheduler status
              </AlertDescription>
            </Alert>
          ) : schedulerHealth ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">Scheduler Status</span>
                {getStatusBadge(schedulerHealth.status)}
              </div>
              <div className="text-sm text-muted-foreground">
                Timezone: {schedulerHealth.timezone}
              </div>

              <div className="space-y-2">
                <h4 className="font-medium text-sm">Scheduled Jobs</h4>
                {schedulerHealth.jobs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No scheduled jobs
                  </p>
                ) : (
                  <div className="space-y-2">
                    {schedulerHealth.jobs.map((job) => (
                      <div key={job.id} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">
                            {job.name}
                          </span>
                          <Badge variant="outline">{job.id}</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground space-y-1">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-3 w-3" />
                            <span>
                              Next run: {formatDateTime(job.next_run_time)}
                            </span>
                          </div>
                          <div>Trigger: {job.trigger}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* Scoring Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Scoring Statistics
          </CardTitle>
          <CardDescription>
            Recent scoring activity and system metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {scoringLoading ? (
            <Skeleton className="h-60 w-full" />
          ) : scoringError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Failed to load scoring statistics
              </AlertDescription>
            </Alert>
          ) : scoringHealth ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">Scoring System Status</span>
                {getStatusBadge(scoringHealth.status)}
              </div>

              {scoringHealth.issues && scoringHealth.issues.length > 0 && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Issues Detected</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside space-y-1">
                      {scoringHealth.issues.map((issue, index) => (
                        <li key={index}>{issue}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="text-2xl font-bold">
                    {scoringHealth.statistics.picks_graded_7d}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Picks Graded (7d)
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-2xl font-bold">
                    {scoringHealth.statistics.games_scored_7d}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Games Scored (7d)
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-2xl font-bold">
                    {scoringHealth.statistics.pending_picks}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Pending Picks
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-xs font-medium mb-1">Last Scoring</div>
                  <div className="text-xs text-muted-foreground">
                    {formatRelativeTime(
                      scoringHealth.statistics.last_scoring_time
                    )}
                  </div>
                </div>
              </div>

              {scoringHealth.statistics.last_scored_game && (
                <div className="text-sm text-muted-foreground">
                  Last scored game: {scoringHealth.statistics.last_scored_game}
                </div>
              )}

              <div className="flex items-center gap-2 text-sm">
                <Database
                  className={`h-4 w-4 ${
                    scoringHealth.database_healthy
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                />
                <span>
                  Database:{" "}
                  {scoringHealth.database_healthy
                    ? "Connected"
                    : "Disconnected"}
                </span>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminMonitoringPage;
