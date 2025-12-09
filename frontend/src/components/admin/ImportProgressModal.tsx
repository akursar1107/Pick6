import { useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Spinner } from "@/components/ui/spinner";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { useImportStatus } from "@/hooks/useImport";
import { ImportStats } from "@/types/import";
import { toast } from "sonner";

interface ImportProgressModalProps {
  jobId: string;
  isOpen: boolean;
  onClose: () => void;
  onComplete: (stats: ImportStats) => void;
}

export function ImportProgressModal({
  jobId,
  isOpen,
  onClose,
  onComplete,
}: ImportProgressModalProps) {
  const { data: statusData, isLoading } = useImportStatus(jobId, {
    enabled: isOpen,
  });

  const status = statusData?.status || "pending";
  const progress = statusData?.progress;
  const stats = statusData?.stats;

  // Call onComplete when import finishes successfully
  useEffect(() => {
    if (status === "completed" && stats) {
      onComplete(stats);
    } else if (status === "failed") {
      // Show error toast when import fails
      const errorMessage =
        statusData?.errors?.[0] || "Import failed. Please try again.";
      toast.error(errorMessage);
    }
  }, [status, stats, statusData?.errors, onComplete]);

  const progressPercentage =
    progress && progress.total_games > 0
      ? Math.round((progress.games_processed / progress.total_games) * 100)
      : 0;

  const getStatusIcon = () => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-6 w-6 text-green-500" />;
      case "failed":
        return <XCircle className="h-6 w-6 text-destructive" />;
      case "running":
        return <Spinner size="sm" />;
      default:
        return <AlertCircle className="h-6 w-6 text-muted-foreground" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "completed":
        return "Import Completed Successfully";
      case "failed":
        return "Import Failed";
      case "running":
        return "Import In Progress";
      default:
        return "Import Pending";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStatusIcon()}
            {getStatusText()}
          </DialogTitle>
          <DialogDescription>
            {status === "running" &&
              "Importing NFL data. You can close this modal and the import will continue in the background."}
            {status === "completed" &&
              "The import has finished successfully. Check the statistics below."}
            {status === "failed" &&
              "The import encountered errors. Please check the error messages below."}
            {status === "pending" &&
              "The import is queued and will start soon."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Progress Bar */}
          {(status === "running" || status === "pending") && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Progress</span>
                <span className="font-medium">{progressPercentage}%</span>
              </div>
              <Progress value={progressPercentage} />
              <div className="text-sm text-muted-foreground">
                {progress?.games_processed || 0} / {progress?.total_games || 0}{" "}
                games processed
              </div>
            </div>
          )}

          {/* Current Step */}
          {status === "running" && progress?.current_step && (
            <div className="p-3 rounded-md bg-muted">
              <p className="text-sm font-medium mb-1">Current Step:</p>
              <p className="text-sm text-muted-foreground">
                {progress.current_step}
              </p>
            </div>
          )}

          {/* Statistics */}
          {(status === "completed" || (status === "running" && progress)) && (
            <div className="space-y-3">
              <p className="text-sm font-semibold">Statistics:</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-md bg-muted">
                  <p className="text-xs text-muted-foreground">Teams Created</p>
                  <p className="text-2xl font-bold">
                    {stats?.teams_created || progress?.teams_created || 0}
                  </p>
                </div>
                <div className="p-3 rounded-md bg-muted">
                  <p className="text-xs text-muted-foreground">
                    Players Created
                  </p>
                  <p className="text-2xl font-bold">
                    {stats?.players_created || progress?.players_created || 0}
                  </p>
                </div>
                <div className="p-3 rounded-md bg-muted">
                  <p className="text-xs text-muted-foreground">Games Created</p>
                  <p className="text-2xl font-bold">
                    {stats?.games_created || progress?.games_created || 0}
                  </p>
                </div>
                <div className="p-3 rounded-md bg-muted">
                  <p className="text-xs text-muted-foreground">Games Updated</p>
                  <p className="text-2xl font-bold">
                    {stats?.games_updated || progress?.games_updated || 0}
                  </p>
                </div>
                <div className="p-3 rounded-md bg-muted col-span-2">
                  <p className="text-xs text-muted-foreground">Games Graded</p>
                  <p className="text-2xl font-bold">
                    {stats?.games_graded || progress?.games_graded || 0}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error Messages */}
          {status === "failed" && (
            <div className="space-y-2">
              <p className="text-sm font-semibold text-destructive">Errors:</p>
              <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 max-h-40 overflow-y-auto">
                <ul className="text-sm text-destructive space-y-1">
                  {/* Show errors from progress */}
                  {progress?.errors && progress.errors.length > 0 ? (
                    progress.errors.map((error: string, index: number) => (
                      <li key={index}>• {error}</li>
                    ))
                  ) : /* Show errors from statusData */
                  statusData?.errors && statusData.errors.length > 0 ? (
                    statusData.errors.map((error: string, index: number) => (
                      <li key={index}>• {error}</li>
                    ))
                  ) : (
                    <li>• An unknown error occurred during import</li>
                  )}
                </ul>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                If the error persists, please check your network connection and
                try again.
              </p>
            </div>
          )}

          {/* Warning Messages for Running Imports with Errors */}
          {status === "running" &&
            progress?.errors &&
            progress.errors.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-semibold text-amber-600">
                  Warnings:
                </p>
                <div className="p-3 rounded-md bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 max-h-32 overflow-y-auto">
                  <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-1">
                    {progress.errors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
                <p className="text-xs text-muted-foreground">
                  Some games encountered errors but the import is continuing.
                </p>
              </div>
            )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          )}
        </div>

        <DialogFooter>
          {status === "running" && (
            <Button variant="outline" onClick={onClose}>
              Close (Continue in Background)
            </Button>
          )}
          {(status === "completed" || status === "failed") && (
            <Button onClick={onClose}>Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
