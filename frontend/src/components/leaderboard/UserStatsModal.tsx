import { useQuery } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import * as leaderboardApi from "@/lib/api/leaderboard";
import { UserStatsContent } from "./UserStatsContent";

interface UserStatsModalProps {
  userId: string | null;
  username?: string;
  season?: number;
  onClose: () => void;
}

export function UserStatsModal({
  userId,
  username,
  season,
  onClose,
}: UserStatsModalProps) {
  const currentSeason = season || new Date().getFullYear();

  const {
    data: userStats,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["user", "stats", userId, currentSeason],
    queryFn: () => leaderboardApi.getUserStats(userId!, currentSeason),
    enabled: userId !== null,
  });

  return (
    <Dialog
      open={userId !== null}
      onOpenChange={(open: boolean) => !open && onClose()}
    >
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {username || userStats?.display_name || "User"} Statistics
          </DialogTitle>
        </DialogHeader>

        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load user statistics. Please try again later.
            </AlertDescription>
          </Alert>
        )}

        {userStats && <UserStatsContent stats={userStats} />}
      </DialogContent>
    </Dialog>
  );
}
