"""Leaderboard service for calculating and caching user rankings"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, Integer
from typing import List, Optional, Dict, Tuple
from uuid import UUID
from collections import defaultdict
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game
from app.db.models.user import User
from app.schemas.leaderboard import (
    LeaderboardEntry,
    UserStats,
    WeekPerformance,
    Streak,
)
from app.core.config import settings
import redis.asyncio as redis
import json


class LeaderboardService:
    """Service for leaderboard operations"""

    def __init__(self, db: AsyncSession, cache: Optional[redis.Redis] = None):
        """
        Initialize leaderboard service

        Args:
            db: Database session
            cache: Optional Redis cache client
        """
        self.db = db
        self.cache = cache

    def _get_season_cache_key(self, season: int) -> str:
        """
        Generate cache key for season leaderboard

        Args:
            season: Season year

        Returns:
            Cache key string
        """
        return f"leaderboard:season:{season}"

    def _get_week_cache_key(self, season: int, week: int) -> str:
        """
        Generate cache key for weekly leaderboard

        Args:
            season: Season year
            week: Week number

        Returns:
            Cache key string
        """
        return f"leaderboard:week:{season}:{week}"

    def _get_user_stats_cache_key(
        self, user_id: UUID, season: Optional[int] = None
    ) -> str:
        """
        Generate cache key for user stats

        Args:
            user_id: User ID
            season: Optional season year

        Returns:
            Cache key string
        """
        if season is not None:
            return f"user:stats:{user_id}:{season}"
        return f"user:stats:{user_id}:all"

    def _serialize_leaderboard(self, entries: List[LeaderboardEntry]) -> str:
        """
        Serialize leaderboard entries to JSON string

        Args:
            entries: List of LeaderboardEntry objects

        Returns:
            JSON string
        """
        # Convert to dict with mode='json' to handle UUID serialization
        return json.dumps([entry.model_dump(mode="json") for entry in entries])

    def _deserialize_leaderboard(self, data: str) -> List[LeaderboardEntry]:
        """
        Deserialize JSON string to leaderboard entries

        Args:
            data: JSON string

        Returns:
            List of LeaderboardEntry objects
        """
        entries_data = json.loads(data)
        return [LeaderboardEntry(**entry) for entry in entries_data]

    def _serialize_user_stats(self, stats: UserStats) -> str:
        """
        Serialize user stats to JSON string

        Args:
            stats: UserStats object

        Returns:
            JSON string
        """
        # Convert to dict with mode='json' to handle UUID serialization
        return json.dumps(stats.model_dump(mode="json"))

    def _deserialize_user_stats(self, data: str) -> UserStats:
        """
        Deserialize JSON string to user stats

        Args:
            data: JSON string

        Returns:
            UserStats object
        """
        stats_data = json.loads(data)
        return UserStats(**stats_data)

    async def calculate_rankings(self, picks: List[Pick]) -> List[LeaderboardEntry]:
        """
        Calculate user rankings from a list of picks

        Args:
            picks: List of Pick objects (should be graded picks only)

        Returns:
            List of LeaderboardEntry objects sorted by rank
        """
        if not picks:
            return []

        # Group picks by user
        user_picks: Dict[UUID, List[Pick]] = defaultdict(list)
        for pick in picks:
            user_picks[pick.user_id].append(pick)

        # Calculate points for each user
        user_scores = []
        for user_id, user_pick_list in user_picks.items():
            # Get user info from first pick (all picks have same user)
            # We'll need to fetch user details separately
            ftd_points = sum(pick.ftd_points for pick in user_pick_list)
            attd_points = sum(pick.attd_points for pick in user_pick_list)
            wins = sum(1 for pick in user_pick_list if pick.status == PickResult.WIN)
            losses = sum(1 for pick in user_pick_list if pick.status == PickResult.LOSS)
            pending = sum(
                1 for pick in user_pick_list if pick.status == PickResult.PENDING
            )

            total_graded = wins + losses
            win_percentage = (wins / total_graded * 100) if total_graded > 0 else 0.0

            user_scores.append(
                {
                    "user_id": user_id,
                    "total_points": ftd_points + attd_points,
                    "ftd_points": ftd_points,
                    "attd_points": attd_points,
                    "wins": wins,
                    "losses": losses,
                    "pending": pending,
                    "win_percentage": round(win_percentage, 2),
                }
            )

        # Sort by total points (desc), then wins (desc)
        user_scores.sort(key=lambda x: (-x["total_points"], -x["wins"]))

        # Fetch user details for all users
        user_ids = [score["user_id"] for score in user_scores]
        result = await self.db.execute(select(User).where(User.id.in_(user_ids)))
        users = {user.id: user for user in result.scalars().all()}

        # Assign ranks with tie handling
        rankings = []
        for i, score in enumerate(user_scores):
            # Check if tied with previous
            if i > 0:
                prev = user_scores[i - 1]
                if (
                    score["total_points"] == prev["total_points"]
                    and score["wins"] == prev["wins"]
                ):
                    # Tied - use same rank
                    rank = rankings[-1].rank
                else:
                    # Not tied - use position
                    rank = i + 1
            else:
                rank = 1

            user = users.get(score["user_id"])
            if user:
                rankings.append(
                    LeaderboardEntry(
                        rank=rank,
                        user_id=score["user_id"],
                        username=user.username,
                        display_name=user.display_name or user.username,
                        total_points=score["total_points"],
                        ftd_points=score["ftd_points"],
                        attd_points=score["attd_points"],
                        wins=score["wins"],
                        losses=score["losses"],
                        pending=score["pending"],
                        win_percentage=score["win_percentage"],
                        is_tied=False,  # Will be set in second pass
                    )
                )

        # Second pass: mark all users in tie groups as tied
        for i in range(len(rankings)):
            # Check if this user is tied with previous or next
            is_tied_with_prev = i > 0 and rankings[i].rank == rankings[i - 1].rank
            is_tied_with_next = (
                i < len(rankings) - 1 and rankings[i].rank == rankings[i + 1].rank
            )
            if is_tied_with_prev or is_tied_with_next:
                # Create a new entry with is_tied=True
                rankings[i] = rankings[i].model_copy(update={"is_tied": True})

        return rankings

    async def get_season_leaderboard(self, season: int) -> List[LeaderboardEntry]:
        """
        Get season leaderboard for all users using optimized aggregation query

        Args:
            season: Season year

        Returns:
            List of LeaderboardEntry objects sorted by rank
        """
        # Check cache first
        if self.cache:
            cache_key = self._get_season_cache_key(season)
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return self._deserialize_leaderboard(cached_data)

        # Optimized query using database aggregation with GROUP BY
        # This reduces data transfer and leverages database indexes
        query = (
            select(
                User.id.label("user_id"),
                User.username,
                User.display_name,
                func.sum(Pick.ftd_points).label("ftd_points"),
                func.sum(Pick.attd_points).label("attd_points"),
                func.sum(func.cast(Pick.status == PickResult.WIN, Integer)).label(
                    "wins"
                ),
                func.sum(func.cast(Pick.status == PickResult.LOSS, Integer)).label(
                    "losses"
                ),
                func.sum(func.cast(Pick.status == PickResult.PENDING, Integer)).label(
                    "pending"
                ),
            )
            .select_from(User)
            .join(Pick, User.id == Pick.user_id)
            .join(Game, Pick.game_id == Game.id)
            .where(
                and_(
                    Game.season_year == season,
                    Pick.status.in_([PickResult.WIN, PickResult.LOSS]),
                )
            )
            .group_by(User.id, User.username, User.display_name)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Calculate derived fields and sort
        user_scores = []
        for row in rows:
            ftd_points = row.ftd_points or 0
            attd_points = row.attd_points or 0
            wins = row.wins or 0
            losses = row.losses or 0
            pending = row.pending or 0
            total_points = ftd_points + attd_points

            total_graded = wins + losses
            win_percentage = (wins / total_graded * 100) if total_graded > 0 else 0.0

            user_scores.append(
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "display_name": row.display_name or row.username,
                    "total_points": total_points,
                    "ftd_points": ftd_points,
                    "attd_points": attd_points,
                    "wins": wins,
                    "losses": losses,
                    "pending": pending,
                    "win_percentage": round(win_percentage, 2),
                }
            )

        # Sort by total points (desc), then wins (desc)
        user_scores.sort(key=lambda x: (-x["total_points"], -x["wins"]))

        # Assign ranks with tie handling
        rankings = []
        for i, score in enumerate(user_scores):
            # Check if tied with previous
            if i > 0:
                prev = user_scores[i - 1]
                if (
                    score["total_points"] == prev["total_points"]
                    and score["wins"] == prev["wins"]
                ):
                    # Tied - use same rank
                    rank = rankings[-1].rank
                else:
                    # Not tied - use position
                    rank = i + 1
            else:
                rank = 1

            rankings.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=score["user_id"],
                    username=score["username"],
                    display_name=score["display_name"],
                    total_points=score["total_points"],
                    ftd_points=score["ftd_points"],
                    attd_points=score["attd_points"],
                    wins=score["wins"],
                    losses=score["losses"],
                    pending=score["pending"],
                    win_percentage=score["win_percentage"],
                    is_tied=False,  # Will be set in second pass
                )
            )

        # Second pass: mark all users in tie groups as tied
        for i in range(len(rankings)):
            # Check if this user is tied with previous or next
            is_tied_with_prev = i > 0 and rankings[i].rank == rankings[i - 1].rank
            is_tied_with_next = (
                i < len(rankings) - 1 and rankings[i].rank == rankings[i + 1].rank
            )
            if is_tied_with_prev or is_tied_with_next:
                # Create a new entry with is_tied=True
                rankings[i] = rankings[i].model_copy(update={"is_tied": True})

        # Set cache with 5-minute TTL
        if self.cache:
            cache_key = self._get_season_cache_key(season)
            serialized_data = self._serialize_leaderboard(rankings)
            await self.cache.set(cache_key, serialized_data, ex=300)  # 5 minutes

        return rankings

    async def get_weekly_leaderboard(
        self, season: int, week: int
    ) -> List[LeaderboardEntry]:
        """
        Get weekly leaderboard for all users

        Args:
            season: Season year
            week: Week number

        Returns:
            List of LeaderboardEntry objects sorted by rank
        """
        # Check cache first
        if self.cache:
            cache_key = self._get_week_cache_key(season, week)
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return self._deserialize_leaderboard(cached_data)

        # Query picks for specific season and week (graded only)
        query = (
            select(Pick)
            .join(Game, Pick.game_id == Game.id)
            .where(
                and_(
                    Game.season_year == season,
                    Game.week_number == week,
                    Pick.status.in_([PickResult.WIN, PickResult.LOSS]),
                )
            )
        )

        result = await self.db.execute(query)
        picks = list(result.scalars().all())

        # Calculate rankings
        rankings = await self.calculate_rankings(picks)

        # Set cache with 5-minute TTL
        if self.cache:
            cache_key = self._get_week_cache_key(season, week)
            serialized_data = self._serialize_leaderboard(rankings)
            await self.cache.set(cache_key, serialized_data, ex=300)  # 5 minutes

        return rankings

    async def get_user_stats(
        self, user_id: UUID, season: Optional[int] = None
    ) -> UserStats:
        """
        Get detailed statistics for a user

        Args:
            user_id: User ID
            season: Optional season filter

        Returns:
            UserStats object with detailed statistics
        """
        # Check cache first
        if self.cache:
            cache_key = self._get_user_stats_cache_key(user_id, season)
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return self._deserialize_user_stats(cached_data)

        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Build query for user's picks
        query = (
            select(Pick)
            .join(Game, Pick.game_id == Game.id)
            .where(Pick.user_id == user_id)
        )

        # Add season filter if provided
        if season is not None:
            query = query.where(Game.season_year == season)

        # Only include graded picks for stats
        query = query.where(Pick.status.in_([PickResult.WIN, PickResult.LOSS]))

        result = await self.db.execute(query)
        picks = list(result.scalars().all())

        # Calculate overall stats
        total_wins = sum(1 for p in picks if p.status == PickResult.WIN)
        total_losses = sum(1 for p in picks if p.status == PickResult.LOSS)
        total_points = sum(p.ftd_points + p.attd_points for p in picks)
        ftd_points = sum(p.ftd_points for p in picks)
        attd_points = sum(p.attd_points for p in picks)

        total_graded = total_wins + total_losses
        win_percentage = (
            round((total_wins / total_graded) * 100, 2) if total_graded > 0 else 0.0
        )

        # Calculate FTD stats (picks where ftd_points > 0 or could have been FTD)
        # For simplicity, we'll count FTD wins as picks with ftd_points > 0
        ftd_wins = sum(1 for p in picks if p.ftd_points > 0)
        ftd_losses = sum(
            1 for p in picks if p.status == PickResult.LOSS and p.ftd_points == 0
        )
        ftd_total = ftd_wins + ftd_losses
        ftd_percentage = (
            round((ftd_wins / ftd_total) * 100, 2) if ftd_total > 0 else 0.0
        )

        # Calculate ATTD stats
        attd_wins = sum(1 for p in picks if p.attd_points > 0)
        attd_losses = sum(
            1 for p in picks if p.status == PickResult.LOSS and p.attd_points == 0
        )
        attd_total = attd_wins + attd_losses
        attd_percentage = (
            round((attd_wins / attd_total) * 100, 2) if attd_total > 0 else 0.0
        )

        # Get current rank from season leaderboard
        current_rank = 1
        if season is not None:
            leaderboard = await self.get_season_leaderboard(season)
            for entry in leaderboard:
                if entry.user_id == user_id:
                    current_rank = entry.rank
                    break

        # Calculate weekly performance breakdown
        weekly_breakdown = await self._calculate_weekly_breakdown(picks, user_id)

        # Find best and worst weeks
        best_week = None
        worst_week = None
        if weekly_breakdown:
            best_week = max(weekly_breakdown, key=lambda w: w.points)
            # Worst week excludes weeks with zero points
            weeks_with_points = [w for w in weekly_breakdown if w.points > 0]
            if weeks_with_points:
                worst_week = min(weeks_with_points, key=lambda w: w.points)

        # Calculate streaks
        current_streak = await self._calculate_current_streak(picks)
        longest_win_streak, longest_loss_streak = await self._calculate_longest_streaks(
            picks
        )

        # Include pending picks count
        pending_query = (
            select(func.count(Pick.id))
            .join(Game, Pick.game_id == Game.id)
            .where(
                and_(
                    Pick.user_id == user_id,
                    Pick.status == PickResult.PENDING,
                )
            )
        )
        if season is not None:
            pending_query = pending_query.where(Game.season_year == season)

        pending_result = await self.db.execute(pending_query)
        total_pending = pending_result.scalar() or 0

        user_stats = UserStats(
            user_id=user_id,
            username=user.username,
            display_name=user.display_name or user.username,
            total_points=total_points,
            total_wins=total_wins,
            total_losses=total_losses,
            total_pending=total_pending,
            win_percentage=win_percentage,
            current_rank=current_rank,
            ftd_wins=ftd_wins,
            ftd_losses=ftd_losses,
            ftd_points=ftd_points,
            ftd_percentage=ftd_percentage,
            attd_wins=attd_wins,
            attd_losses=attd_losses,
            attd_points=attd_points,
            attd_percentage=attd_percentage,
            best_week=best_week,
            worst_week=worst_week,
            weekly_breakdown=weekly_breakdown,
            current_streak=current_streak,
            longest_win_streak=longest_win_streak,
            longest_loss_streak=longest_loss_streak,
        )

        # Set cache with 5-minute TTL
        if self.cache:
            cache_key = self._get_user_stats_cache_key(user_id, season)
            serialized_data = self._serialize_user_stats(user_stats)
            await self.cache.set(cache_key, serialized_data, ex=300)  # 5 minutes

        return user_stats

    async def _calculate_weekly_breakdown(
        self, picks: List[Pick], user_id: UUID
    ) -> List[WeekPerformance]:
        """
        Calculate weekly performance breakdown

        Args:
            picks: List of graded picks
            user_id: User ID

        Returns:
            List of WeekPerformance objects
        """
        # Group picks by week and season
        weekly_picks: Dict[Tuple[int, int], List[Pick]] = defaultdict(list)

        # Need to fetch game info for each pick to get week number and season
        for pick in picks:
            game_result = await self.db.execute(
                select(Game).where(Game.id == pick.game_id)
            )
            game = game_result.scalar_one_or_none()
            if game:
                weekly_picks[(game.season_year, game.week_number)].append(pick)

        # Calculate stats for each week
        weekly_breakdown = []
        for (season, week), week_picks in sorted(weekly_picks.items()):
            points = sum(p.ftd_points + p.attd_points for p in week_picks)
            wins = sum(1 for p in week_picks if p.status == PickResult.WIN)
            losses = sum(1 for p in week_picks if p.status == PickResult.LOSS)

            # Get rank for this week by calculating weekly leaderboard
            try:
                weekly_leaderboard = await self.get_weekly_leaderboard(season, week)
                rank = 1
                for entry in weekly_leaderboard:
                    if entry.user_id == user_id:
                        rank = entry.rank
                        break
            except Exception:
                # If we can't get the leaderboard, default to rank 1
                rank = 1

            weekly_breakdown.append(
                WeekPerformance(
                    week=week, points=points, wins=wins, losses=losses, rank=rank
                )
            )

        return weekly_breakdown

    async def _calculate_current_streak(self, picks: List[Pick]) -> Streak:
        """
        Calculate current win/loss streak

        Args:
            picks: List of graded picks

        Returns:
            Streak object
        """
        if not picks:
            return Streak(type="none", count=0)

        # Need to get picks with game dates to order chronologically
        picks_with_dates = []
        for pick in picks:
            game_result = await self.db.execute(
                select(Game).where(Game.id == pick.game_id)
            )
            game = game_result.scalar_one_or_none()
            if game:
                picks_with_dates.append((pick, game.game_date))

        # Sort by game date descending (most recent first)
        picks_with_dates.sort(key=lambda x: x[1], reverse=True)

        if not picks_with_dates:
            return Streak(type="none", count=0)

        # Get most recent pick status
        most_recent_pick = picks_with_dates[0][0]
        if most_recent_pick.status == PickResult.WIN:
            streak_type = "win"
        elif most_recent_pick.status == PickResult.LOSS:
            streak_type = "loss"
        else:
            return Streak(type="none", count=0)

        # Count consecutive picks with same status
        count = 0
        for pick, _ in picks_with_dates:
            if pick.status == most_recent_pick.status:
                count += 1
            else:
                break

        return Streak(type=streak_type, count=count)

    async def _calculate_longest_streaks(self, picks: List[Pick]) -> Tuple[int, int]:
        """
        Calculate longest win and loss streaks

        Args:
            picks: List of graded picks

        Returns:
            Tuple of (longest_win_streak, longest_loss_streak)
        """
        if not picks:
            return (0, 0)

        # Need to get picks with game dates to order chronologically
        picks_with_dates = []
        for pick in picks:
            game_result = await self.db.execute(
                select(Game).where(Game.id == pick.game_id)
            )
            game = game_result.scalar_one_or_none()
            if game:
                picks_with_dates.append((pick, game.game_date))

        # Sort by game date ascending (oldest first)
        picks_with_dates.sort(key=lambda x: x[1])

        if not picks_with_dates:
            return (0, 0)

        longest_win_streak = 0
        longest_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0

        for pick, _ in picks_with_dates:
            if pick.status == PickResult.WIN:
                current_win_streak += 1
                current_loss_streak = 0
                longest_win_streak = max(longest_win_streak, current_win_streak)
            elif pick.status == PickResult.LOSS:
                current_loss_streak += 1
                current_win_streak = 0
                longest_loss_streak = max(longest_loss_streak, current_loss_streak)

        return (longest_win_streak, longest_loss_streak)

    async def invalidate_cache(
        self,
        season: int,
        week: Optional[int] = None,
        user_ids: Optional[List[UUID]] = None,
    ) -> None:
        """
        Invalidate leaderboard cache

        Args:
            season: Season year
            week: Optional week number
            user_ids: Optional list of user IDs to invalidate stats for
        """
        if not self.cache:
            return

        keys_to_delete = []

        # Invalidate season leaderboard
        season_key = self._get_season_cache_key(season)
        keys_to_delete.append(season_key)

        # Invalidate specific week if provided
        if week is not None:
            week_key = self._get_week_cache_key(season, week)
            keys_to_delete.append(week_key)

        # Invalidate user stats if user_ids provided
        if user_ids:
            for user_id in user_ids:
                # Invalidate both season-specific and all-time stats
                user_season_key = self._get_user_stats_cache_key(user_id, season)
                user_all_key = self._get_user_stats_cache_key(user_id, None)
                keys_to_delete.append(user_season_key)
                keys_to_delete.append(user_all_key)

        # Delete all keys in a single operation
        if keys_to_delete:
            await self.cache.delete(*keys_to_delete)

    async def invalidate_cache_for_game_scoring(self, game_id: UUID) -> None:
        """
        Invalidate cache when a game is scored

        Args:
            game_id: Game ID that was scored
        """
        if not self.cache:
            return

        # Get game details to determine season and week
        game_result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = game_result.scalar_one_or_none()
        if not game:
            return

        # Get all users who have picks for this game
        picks_result = await self.db.execute(
            select(Pick.user_id).where(Pick.game_id == game_id).distinct()
        )
        user_ids = [row[0] for row in picks_result.all()]

        # Invalidate caches
        await self.invalidate_cache(
            season=game.season_year,
            week=game.week_number,
            user_ids=user_ids,
        )

    async def invalidate_cache_for_pick_override(self, pick_id: UUID) -> None:
        """
        Invalidate cache when a pick is manually overridden

        Args:
            pick_id: Pick ID that was overridden
        """
        if not self.cache:
            return

        # Get pick and game details
        pick_result = await self.db.execute(select(Pick).where(Pick.id == pick_id))
        pick = pick_result.scalar_one_or_none()
        if not pick:
            return

        game_result = await self.db.execute(select(Game).where(Game.id == pick.game_id))
        game = game_result.scalar_one_or_none()
        if not game:
            return

        # Invalidate caches for this user, season, and week
        await self.invalidate_cache(
            season=game.season_year,
            week=game.week_number,
            user_ids=[pick.user_id],
        )

    async def invalidate_cache_batch(self, game_ids: List[UUID]) -> None:
        """
        Invalidate cache for multiple games in a single operation

        This is used when multiple games are scored simultaneously to avoid
        multiple recalculations and ensure efficient cache invalidation.

        Args:
            game_ids: List of game IDs that were scored
        """
        if not self.cache or not game_ids:
            return

        # Collect all affected cache keys
        keys_to_delete = set()
        seasons_weeks = set()

        # Get all games and their picks
        games_result = await self.db.execute(select(Game).where(Game.id.in_(game_ids)))
        games = games_result.scalars().all()

        # Get all users who have picks for these games
        picks_result = await self.db.execute(
            select(Pick.user_id, Game.season_year, Game.week_number)
            .join(Game, Pick.game_id == Game.id)
            .where(Game.id.in_(game_ids))
            .distinct()
        )
        picks_data = picks_result.all()

        # Collect unique seasons and weeks
        for game in games:
            seasons_weeks.add((game.season_year, game.week_number))

        # Collect user IDs by season
        user_ids_by_season = defaultdict(set)
        for user_id, season, week in picks_data:
            user_ids_by_season[season].add(user_id)

        # Build list of keys to delete
        for season, week in seasons_weeks:
            # Season leaderboard
            keys_to_delete.add(self._get_season_cache_key(season))
            # Weekly leaderboard
            keys_to_delete.add(self._get_week_cache_key(season, week))

        # User stats keys
        for season, user_ids in user_ids_by_season.items():
            for user_id in user_ids:
                keys_to_delete.add(self._get_user_stats_cache_key(user_id, season))
                keys_to_delete.add(self._get_user_stats_cache_key(user_id, None))

        # Delete all keys in single operation
        if keys_to_delete:
            await self.cache.delete(*list(keys_to_delete))
