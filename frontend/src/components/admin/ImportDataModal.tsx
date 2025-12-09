import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertTriangle, Loader2 } from "lucide-react";
import { ImportConfig } from "@/types/import";
import { useCheckExistingData } from "@/hooks/useImport";
import { toast } from "sonner";
import { getImportErrorToastMessage } from "@/lib/import-errors";

interface ImportDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportStart: (config: ImportConfig) => void;
}

export function ImportDataModal({
  isOpen,
  onClose,
  onImportStart,
}: ImportDataModalProps) {
  // Calculate current NFL season (September-February season)
  const getCurrentNFLSeason = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1; // 1-12
    // NFL season runs September (9) through February (2)
    // If we're in Jan-Aug, the current season is the previous year
    return month >= 9 ? year : year - 1;
  };

  const currentSeason = getCurrentNFLSeason();
  const [season, setSeason] = useState<number>(currentSeason);
  const [weekSelection, setWeekSelection] = useState<"all" | "specific">("all");
  const [selectedWeeks, setSelectedWeeks] = useState<number[]>([]);
  const [gradeGames, setGradeGames] = useState<boolean>(true);
  const [errors, setErrors] = useState<string[]>([]);
  const [showConfirmDialog, setShowConfirmDialog] = useState<boolean>(false);
  const [pendingConfig, setPendingConfig] = useState<ImportConfig | null>(null);

  const checkExistingDataMutation = useCheckExistingData();

  // Generate seasons from 2020 to current NFL season
  const seasons = Array.from(
    { length: currentSeason - 2020 + 1 },
    (_, i) => 2020 + i
  );
  const weeks = Array.from({ length: 18 }, (_, i) => i + 1);

  const handleWeekToggle = (week: number) => {
    setSelectedWeeks((prev) =>
      prev.includes(week) ? prev.filter((w) => w !== week) : [...prev, week]
    );
  };

  const validateForm = (): boolean => {
    const newErrors: string[] = [];

    if (season < 2020 || season > currentSeason) {
      newErrors.push(`Season must be between 2020 and ${currentSeason}`);
    }

    if (weekSelection === "specific" && selectedWeeks.length === 0) {
      newErrors.push("Please select at least one week");
    }

    if (
      weekSelection === "specific" &&
      selectedWeeks.some((w) => w < 1 || w > 18)
    ) {
      newErrors.push("Week numbers must be between 1 and 18");
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    const config: ImportConfig = {
      season,
      weeks:
        weekSelection === "all" ? "all" : selectedWeeks.sort((a, b) => a - b),
      grade_games: gradeGames,
    };

    // Check for existing data
    try {
      const result = await checkExistingDataMutation.mutateAsync({
        season: config.season,
        weeks: config.weeks,
      });

      if (result.has_existing_data) {
        // Show confirmation dialog
        setPendingConfig(config);
        setShowConfirmDialog(true);
      } else {
        // No existing data, proceed directly
        onImportStart(config);
      }
    } catch (error: unknown) {
      console.error("Error checking existing data:", error);

      // Show user-friendly error message
      const errorMessage = getImportErrorToastMessage(error);

      toast.warning("Could not check for existing data", {
        description: errorMessage + " You can still proceed with the import.",
        duration: 5000,
      });

      // Allow user to proceed anyway (fail open)
      // Don't block the import if the check fails
    }
  };

  const handleConfirmImport = () => {
    if (pendingConfig) {
      onImportStart(pendingConfig);
      setShowConfirmDialog(false);
      setPendingConfig(null);
    }
  };

  const handleCancelImport = () => {
    setShowConfirmDialog(false);
    setPendingConfig(null);
  };

  const handleClose = () => {
    setErrors([]);
    setShowConfirmDialog(false);
    setPendingConfig(null);
    onClose();
  };

  // Reset mutation state when modal closes
  useEffect(() => {
    if (!isOpen) {
      checkExistingDataMutation.reset();
    }
  }, [isOpen]);

  return (
    <>
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Import NFL Data</DialogTitle>
            <DialogDescription>
              Configure the import settings for NFL season data. This will fetch
              games, teams, and player information from nflreadpy.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Season Selection */}
            <div className="space-y-2">
              <Label htmlFor="season">Season</Label>
              <Select
                value={season.toString()}
                onValueChange={(value) => setSeason(parseInt(value))}
              >
                <SelectTrigger id="season">
                  <SelectValue placeholder="Select season" />
                </SelectTrigger>
                <SelectContent>
                  {seasons.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year} Season
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Week Selection */}
            <div className="space-y-2">
              <Label>Weeks</Label>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="all-weeks"
                    checked={weekSelection === "all"}
                    onCheckedChange={(checked) =>
                      setWeekSelection(checked ? "all" : "specific")
                    }
                  />
                  <Label
                    htmlFor="all-weeks"
                    className="text-sm font-normal cursor-pointer"
                  >
                    Import all weeks (1-18)
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="specific-weeks"
                    checked={weekSelection === "specific"}
                    onCheckedChange={(checked) =>
                      setWeekSelection(checked ? "specific" : "all")
                    }
                  />
                  <Label
                    htmlFor="specific-weeks"
                    className="text-sm font-normal cursor-pointer"
                  >
                    Select specific weeks
                  </Label>
                </div>

                {weekSelection === "specific" && (
                  <div className="ml-6 p-3 border rounded-md bg-muted/50">
                    <div className="grid grid-cols-6 gap-2">
                      {weeks.map((week) => (
                        <div key={week} className="flex items-center space-x-2">
                          <Checkbox
                            id={`week-${week}`}
                            checked={selectedWeeks.includes(week)}
                            onCheckedChange={() => handleWeekToggle(week)}
                          />
                          <Label
                            htmlFor={`week-${week}`}
                            className="text-sm font-normal cursor-pointer"
                          >
                            {week}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Grade Games Option */}
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="grade-games"
                  checked={gradeGames}
                  onCheckedChange={(checked) => setGradeGames(checked === true)}
                />
                <Label
                  htmlFor="grade-games"
                  className="text-sm font-normal cursor-pointer"
                >
                  Grade completed games
                </Label>
              </div>
              <p className="text-xs text-muted-foreground ml-6">
                Fetch play-by-play data to identify touchdown scorers for
                completed games
              </p>
            </div>

            {/* Error Messages */}
            {errors.length > 0 && (
              <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20">
                <ul className="text-sm text-destructive space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={checkExistingDataMutation.isPending}
            >
              {checkExistingDataMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Start Import
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog for Existing Data */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Existing Data Detected
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>{checkExistingDataMutation.data?.warning_message}</p>
              <div className="rounded-md bg-muted p-3 text-sm">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="font-medium">Existing games:</span>{" "}
                    {checkExistingDataMutation.data?.existing_games_count}
                  </div>
                  <div>
                    <span className="font-medium">To update:</span>{" "}
                    {checkExistingDataMutation.data?.games_to_update}
                  </div>
                  <div>
                    <span className="font-medium">To create:</span>{" "}
                    {checkExistingDataMutation.data?.games_to_create}
                  </div>
                </div>
              </div>
              <p className="text-sm font-medium">
                Do you want to proceed with the import?
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelImport}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmImport}>
              Proceed with Import
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
