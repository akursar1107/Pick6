import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchPlayers } from "@/lib/api/picks";
import { Player } from "@/types/pick";
import { cn } from "@/lib/utils";

interface PlayerSearchProps {
  onSelect: (player: Player) => void;
  selectedPlayer?: Player | null;
  className?: string;
}

export function PlayerSearch({
  onSelect,
  selectedPlayer,
  className,
}: PlayerSearchProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Fetch players based on debounced query
  const { data: players = [], isLoading } = useQuery({
    queryKey: ["players", "search", debouncedQuery],
    queryFn: () => searchPlayers(debouncedQuery),
    enabled: debouncedQuery.length > 0,
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setIsOpen(true);
  };

  const handleSelectPlayer = (player: Player) => {
    onSelect(player);
    setQuery("");
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    if (query.length > 0) {
      setIsOpen(true);
    }
  };

  const handleInputBlur = () => {
    // Delay to allow click on results
    setTimeout(() => setIsOpen(false), 200);
  };

  return (
    <div className={cn("relative", className)}>
      <div className="space-y-2">
        <label
          htmlFor="player-search"
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Search Player
        </label>
        <input
          id="player-search"
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          placeholder="Search by player name..."
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>

      {selectedPlayer && (
        <div className="mt-2 p-3 rounded-md border border-input bg-muted">
          <div className="text-sm font-medium">{selectedPlayer.name}</div>
          <div className="text-xs text-muted-foreground">
            {selectedPlayer.team} • {selectedPlayer.position}
          </div>
        </div>
      )}

      {isOpen && query.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-background border border-input rounded-md shadow-lg max-h-60 overflow-auto">
          {isLoading ? (
            <div className="p-4 text-sm text-muted-foreground text-center">
              Searching...
            </div>
          ) : players.length === 0 ? (
            <div className="p-4 text-sm text-muted-foreground text-center">
              No players found
            </div>
          ) : (
            <ul className="py-1">
              {players.map((player) => (
                <li key={player.id}>
                  <button
                    type="button"
                    onClick={() => handleSelectPlayer(player)}
                    className="w-full px-4 py-2 text-left hover:bg-accent hover:text-accent-foreground transition-colors"
                  >
                    <div className="text-sm font-medium">{player.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {player.team} • {player.position}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
