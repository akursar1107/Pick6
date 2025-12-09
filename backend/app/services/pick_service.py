"""Pick service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone
from app.db.models.pick import Pick, PickResult
from app.schemas.pick import PickCreate, PickUpdate
from app.core.exceptions import DuplicatePickError, GameLockedError, NotFoundError
from app.services.game_service import GameService
from app.services.player_service import PlayerService


class PickService:
    """Service for pick operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.game_service = GameService(db)
        self.player_service = PlayerService(db)

    async def check_duplicate_pick(self, user_id: UUID, game_id: UUID) -> bool:
        """
        Check if a pick already exists for the given user and game.

        Requirements: 5.1, 5.2

        Args:
            user_id: The user's ID
            game_id: The game's ID

        Returns:
            True if a duplicate pick exists, False otherwise
        """
        query = select(Pick).where(Pick.user_id == user_id, Pick.game_id == game_id)
        result = await self.db.execute(query)
        existing_pick = result.scalar_one_or_none()
        return existing_pick is not None

    async def validate_pick_timing(self, game_id: UUID) -> None:
        """
        Validate that a pick can be made/modified for the given game.
        Raises GameLockedError if the game's kickoff time has passed.

        Requirements: 1.5, 3.3, 4.2

        Args:
            game_id: The game's ID

        Raises:
            NotFoundError: If the game doesn't exist
            GameLockedError: If the game's kickoff time has passed
        """
        # Check if game exists
        game = await self.game_service.get_game_by_id(game_id)
        if not game:
            raise NotFoundError(f"Game with id {game_id} not found")

        # Check if game is locked
        is_locked = await self.game_service.is_game_locked(game_id)
        if is_locked:
            raise GameLockedError("Cannot modify pick after game kickoff")

    async def get_picks(
        self, user_id: Optional[UUID] = None, game_id: Optional[UUID] = None
    ) -> List[Pick]:
        """
        Get picks with optional filters, including related game and player data.

        This method is used by admin endpoints to fetch all picks with complete information.
        """
        from sqlalchemy.orm import selectinload
        from app.db.models.game import Game
        from app.db.models.player import Player

        # Build query with eager loading of relationships
        query = (
            select(Pick)
            .options(
                selectinload(Pick.game),
                selectinload(Pick.player),
                selectinload(Pick.user),
            )
            .order_by(Pick.pick_submitted_at.desc())
        )

        if user_id is not None:
            query = query.where(Pick.user_id == user_id)
        if game_id is not None:
            query = query.where(Pick.game_id == game_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_picks(
        self, user_id: UUID, game_id: Optional[UUID] = None
    ) -> List[Pick]:
        """
        Get picks for a user with optional game filter, including complete data.

        Requirements: 2.1, 2.2, 2.3, 2.4

        Args:
            user_id: The user's ID to filter picks
            game_id: Optional game ID to filter picks for a specific game

        Returns:
            List of Pick objects with joined game, player, and team data,
            ordered by pick_submitted_at descending
        """
        from sqlalchemy.orm import selectinload
        from app.db.models.game import Game
        from app.db.models.player import Player
        from app.db.models.team import Team

        # Build query with joins for complete data (Requirement 2.2)
        query = (
            select(Pick)
            .where(Pick.user_id == user_id)  # Requirement 2.1
            .join(Game, Pick.game_id == Game.id)
            .join(Player, Pick.player_id == Player.id)
            .join(Team, Player.team_id == Team.id)
            .order_by(
                Pick.pick_submitted_at.desc()
            )  # Order by submission time descending
        )

        # Add optional game filter (Requirement 2.3)
        if game_id is not None:
            query = query.where(Pick.game_id == game_id)

        result = await self.db.execute(query)
        picks = list(result.scalars().all())

        # Return empty list if no picks (Requirement 2.4)
        return picks

    async def get_pick_by_id(self, pick_id: UUID) -> Pick | None:
        """Get pick by ID"""
        result = await self.db.execute(select(Pick).where(Pick.id == pick_id))
        return result.scalar_one_or_none()

    async def create_pick(self, pick_data: PickCreate, user_id: UUID = None) -> Pick:
        """
        Create a new pick with validation.

        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2

        Args:
            pick_data: Pick creation data
            user_id: The authenticated user's ID

        Returns:
            The created Pick object

        Raises:
            NotFoundError: If game or player doesn't exist
            DuplicatePickError: If user already has a pick for this game
            GameLockedError: If game kickoff time has passed
        """
        # Verify game exists and validate timing (Requirement 1.5)
        await self.validate_pick_timing(pick_data.game_id)

        # Verify player exists (Requirement 1.4)
        player = await self.player_service.get_player_by_id(pick_data.player_id)
        if not player:
            raise NotFoundError(f"Player with id {pick_data.player_id} not found")

        # Check for duplicate pick (Requirements 5.1, 5.2)
        has_duplicate = await self.check_duplicate_pick(user_id, pick_data.game_id)
        if has_duplicate:
            raise DuplicatePickError(
                f"Pick already exists for user {user_id} and game {pick_data.game_id}"
            )

        # Create pick with PENDING status and capture submission timestamp
        # (Requirements 1.1, 1.2, 1.3)
        pick = Pick(
            user_id=user_id,  # Requirement 1.3
            game_id=pick_data.game_id,  # Requirement 1.4
            player_id=pick_data.player_id,  # Requirement 1.4
            status=PickResult.PENDING,  # Requirement 1.1
            pick_submitted_at=datetime.now(timezone.utc),  # Requirement 1.2
        )

        self.db.add(pick)
        await self.db.commit()
        await self.db.refresh(pick)
        return pick

    async def update_pick(
        self, pick_id: UUID, user_id: UUID, pick_update: PickUpdate
    ) -> Pick:
        """
        Update a pick with validation.

        Requirements: 3.1, 3.2, 3.3, 3.4, 9.3

        Args:
            pick_id: The pick's ID
            user_id: The authenticated user's ID
            pick_update: Pick update data

        Returns:
            The updated Pick object

        Raises:
            NotFoundError: If pick doesn't exist
            UnauthorizedError: If user doesn't own the pick
            GameLockedError: If game kickoff time has passed
        """
        from app.core.exceptions import UnauthorizedError

        # Get the pick
        pick = await self.get_pick_by_id(pick_id)
        if not pick:
            raise NotFoundError(f"Pick with id {pick_id} not found")

        # Ownership check - user_id must match (Requirement 9.3)
        if pick.user_id != user_id:
            raise UnauthorizedError(
                f"User {user_id} is not authorized to modify pick {pick_id}"
            )

        # Timing validation before update (Requirement 3.3)
        await self.validate_pick_timing(pick.game_id)

        # Verify new player exists if player_id is being updated
        if pick_update.player_id is not None:
            player = await self.player_service.get_player_by_id(pick_update.player_id)
            if not player:
                raise NotFoundError(f"Player with id {pick_update.player_id} not found")

        # Store original submission timestamp to verify it's preserved
        original_submitted_at = pick.pick_submitted_at

        # Update player_id (Requirement 3.1)
        if pick_update.player_id is not None:
            pick.player_id = pick_update.player_id

        # updated_at will be automatically updated by SQLAlchemy (Requirement 3.2)
        pick.updated_at = datetime.now(timezone.utc)

        # Preserve pick_submitted_at (Requirement 3.4)
        pick.pick_submitted_at = original_submitted_at

        await self.db.commit()
        await self.db.refresh(pick)
        return pick

    async def delete_pick(self, pick_id: UUID, user_id: UUID) -> None:
        """
        Delete a pick with validation.

        Requirements: 4.1, 4.2, 4.3, 9.4

        Args:
            pick_id: The pick's ID
            user_id: The authenticated user's ID

        Raises:
            NotFoundError: If pick doesn't exist (Requirement 4.3)
            UnauthorizedError: If user doesn't own the pick (Requirement 9.4)
            GameLockedError: If game kickoff time has passed (Requirement 4.2)
        """
        from app.core.exceptions import UnauthorizedError

        # Get the pick
        pick = await self.get_pick_by_id(pick_id)
        if not pick:
            raise NotFoundError(f"Pick with id {pick_id} not found")

        # Ownership check - user_id must match (Requirement 9.4)
        if pick.user_id != user_id:
            raise UnauthorizedError(
                f"User {user_id} is not authorized to delete pick {pick_id}"
            )

        # Timing validation before deletion (Requirement 4.2)
        await self.validate_pick_timing(pick.game_id)

        # Delete pick record from database (Requirement 4.1)
        await self.db.delete(pick)
        await self.db.commit()
