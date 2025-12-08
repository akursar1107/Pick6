import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { LeaderboardEntry } from "@/types/leaderboard";
import { cn } from "@/lib/utils";

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
  currentUserId?: string;
  onUserClick?: (userId: string) => void;
}

type SortColumn =
  | "rank"
  | "username"
  | "total_points"
  | "wins"
  | "losses"
  | "win_percentage";
type SortDirection = "asc" | "desc";

export function LeaderboardTable({
  entries,
  currentUserId,
  onUserClick,
}: LeaderboardTableProps) {
  const [sortColumn, setSortColumn] = useState<SortColumn>("rank");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (userId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(userId)) {
      newExpanded.delete(userId);
    } else {
      newExpanded.add(userId);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      // Toggle direction
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      // New column, default to descending for numeric columns
      setSortColumn(column);
      setSortDirection(
        column === "username" || column === "rank" ? "asc" : "desc"
      );
    }
  };

  const sortedEntries = [...entries].sort((a, b) => {
    let aVal: string | number;
    let bVal: string | number;

    switch (sortColumn) {
      case "rank":
        aVal = a.rank;
        bVal = b.rank;
        break;
      case "username":
        aVal = a.username;
        bVal = b.username;
        break;
      case "total_points":
        aVal = a.total_points;
        bVal = b.total_points;
        break;
      case "wins":
        aVal = a.wins;
        bVal = b.wins;
        break;
      case "losses":
        aVal = a.losses;
        bVal = b.losses;
        break;
      case "win_percentage":
        aVal = a.win_percentage;
        bVal = b.win_percentage;
        break;
      default:
        aVal = a.rank;
        bVal = b.rank;
    }

    // Apply tie-breaking rules when values are equal
    if (aVal === bVal) {
      // Tie-break by points, then wins
      if (a.total_points !== b.total_points) {
        return sortDirection === "asc"
          ? a.total_points - b.total_points
          : b.total_points - a.total_points;
      }
      if (a.wins !== b.wins) {
        return sortDirection === "asc" ? a.wins - b.wins : b.wins - a.wins;
      }
      return 0;
    }

    // Normal sorting
    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortDirection === "asc"
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    return sortDirection === "asc"
      ? (aVal as number) - (bVal as number)
      : (bVal as number) - (aVal as number);
  });

  const SortIcon = ({ column }: { column: SortColumn }) => {
    if (sortColumn !== column) {
      return <ArrowUpDown className="ml-2 h-4 w-4" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="ml-2 h-4 w-4" />
    ) : (
      <ArrowDown className="ml-2 h-4 w-4" />
    );
  };

  return (
    <div className="rounded-md border overflow-x-auto">
      <div className="min-w-full">
        <Table>
          <TableHeader className="sticky top-0 bg-background z-10">
            <TableRow>
              <TableHead className="w-[60px] md:w-[80px]">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("rank")}
                  className="h-8 px-1 md:px-2 text-xs md:text-sm"
                >
                  Rank
                  <SortIcon column="rank" />
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort("username")}
                  className="h-8 px-1 md:px-2 text-xs md:text-sm"
                >
                  User
                  <SortIcon column="username" />
                </Button>
              </TableHead>
              <TableHead className="text-right">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("total_points")}
                  className="h-8 px-1 md:px-2 text-xs md:text-sm"
                >
                  Pts
                  <SortIcon column="total_points" />
                </Button>
              </TableHead>
              <TableHead className="text-right hidden lg:table-cell">
                FTD
              </TableHead>
              <TableHead className="text-right hidden lg:table-cell">
                ATTD
              </TableHead>
              <TableHead className="text-right hidden sm:table-cell">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("wins")}
                  className="h-8 px-1 md:px-2 text-xs md:text-sm"
                >
                  W
                  <SortIcon column="wins" />
                </Button>
              </TableHead>
              <TableHead className="text-right hidden sm:table-cell">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("losses")}
                  className="h-8 px-1 md:px-2 text-xs md:text-sm"
                >
                  L
                  <SortIcon column="losses" />
                </Button>
              </TableHead>
              <TableHead className="text-right hidden md:table-cell">
                <Button
                  variant="ghost"
                  onClick={() => handleSort("win_percentage")}
                  className="h-8 px-1 md:px-2 text-xs md:text-sm"
                >
                  Win %
                  <SortIcon column="win_percentage" />
                </Button>
              </TableHead>
              <TableHead className="w-[40px] sm:hidden"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedEntries.map((entry) => {
              const isExpanded = expandedRows.has(entry.user_id);
              return (
                <>
                  <TableRow
                    key={entry.user_id}
                    className={cn(
                      entry.user_id === currentUserId &&
                        "bg-primary/10 hover:bg-primary/15"
                    )}
                  >
                    <TableCell className="font-medium text-xs md:text-sm">
                      {entry.rank}
                      {entry.is_tied && "*"}
                    </TableCell>
                    <TableCell className="text-xs md:text-sm">
                      <button
                        onClick={() => onUserClick?.(entry.user_id)}
                        className="hover:underline text-left truncate max-w-[120px] md:max-w-none block"
                      >
                        {entry.display_name || entry.username}
                      </button>
                    </TableCell>
                    <TableCell className="text-right font-semibold text-xs md:text-sm">
                      {entry.total_points}
                    </TableCell>
                    <TableCell className="text-right hidden lg:table-cell text-xs md:text-sm">
                      {entry.ftd_points}
                    </TableCell>
                    <TableCell className="text-right hidden lg:table-cell text-xs md:text-sm">
                      {entry.attd_points}
                    </TableCell>
                    <TableCell className="text-right text-green-600 hidden sm:table-cell text-xs md:text-sm">
                      {entry.wins}
                    </TableCell>
                    <TableCell className="text-right text-red-600 hidden sm:table-cell text-xs md:text-sm">
                      {entry.losses}
                    </TableCell>
                    <TableCell className="text-right hidden md:table-cell text-xs md:text-sm">
                      {entry.win_percentage.toFixed(1)}%
                    </TableCell>
                    <TableCell className="sm:hidden">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleRow(entry.user_id)}
                        className="h-6 w-6 p-0"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                  {isExpanded && (
                    <TableRow
                      key={`${entry.user_id}-expanded`}
                      className="sm:hidden"
                    >
                      <TableCell colSpan={4} className="bg-muted/50 py-3">
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-muted-foreground">FTD:</span>{" "}
                            <span className="font-medium">
                              {entry.ftd_points}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">ATTD:</span>{" "}
                            <span className="font-medium">
                              {entry.attd_points}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Wins:</span>{" "}
                            <span className="font-medium text-green-600">
                              {entry.wins}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">
                              Losses:
                            </span>{" "}
                            <span className="font-medium text-red-600">
                              {entry.losses}
                            </span>
                          </div>
                          <div className="col-span-2">
                            <span className="text-muted-foreground">
                              Win %:
                            </span>{" "}
                            <span className="font-medium">
                              {entry.win_percentage.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
