import { useState } from "react";
import { AvailableGames } from "@/components/picks/AvailableGames";
import { MyPicks } from "@/components/picks/MyPicks";
import { PickSubmissionForm } from "@/components/picks/PickSubmissionForm";
import { GameWithPick, PickResponse } from "@/types/pick";

export default function PicksPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedGame, setSelectedGame] = useState<GameWithPick | undefined>();
  const [editingPick, setEditingPick] = useState<PickResponse | undefined>();

  const handleMakePick = (game: GameWithPick) => {
    setSelectedGame(game);
    setEditingPick(undefined);
    setIsModalOpen(true);
  };

  const handleEditPickFromGame = (game: GameWithPick) => {
    // We need to fetch the full pick details
    // For now, we'll just open the modal with the game
    setSelectedGame(game);
    setEditingPick(undefined);
    setIsModalOpen(true);
  };

  const handleEditPickFromList = (pick: PickResponse) => {
    setEditingPick(pick);
    setSelectedGame(undefined);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedGame(undefined);
    setEditingPick(undefined);
  };

  const handleSuccess = () => {
    handleCloseModal();
  };

  return (
    <div className="container mx-auto px-4 py-4 sm:py-8 max-w-6xl">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2">
          Make Your Picks
        </h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          Select a player for each game. Your pick counts for both First
          Touchdown and Anytime Touchdown scoring.
        </p>
      </div>

      <div className="grid gap-6 sm:gap-8 lg:grid-cols-2">
        <div>
          <AvailableGames
            onMakePick={handleMakePick}
            onEditPick={handleEditPickFromGame}
          />
        </div>
        <div>
          <MyPicks onEditPick={handleEditPickFromList} />
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCloseModal}
          />
          {/* Modal Content */}
          <div className="relative bg-background rounded-lg shadow-lg p-4 sm:p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <PickSubmissionForm
              game={selectedGame}
              existingPick={editingPick}
              onSuccess={handleSuccess}
              onCancel={handleCloseModal}
            />
          </div>
        </div>
      )}
    </div>
  );
}
