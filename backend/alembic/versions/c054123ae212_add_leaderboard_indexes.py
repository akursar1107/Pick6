"""add_leaderboard_indexes

Revision ID: c054123ae212
Revises: dd889087ef87
Create Date: 2025-12-08 05:50:15.723490

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c054123ae212"
down_revision: Union[str, None] = "dd889087ef87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite index on picks (status, user_id) for efficient leaderboard queries
    op.create_index(
        "idx_picks_status_user", "picks", ["status", "user_id"], unique=False
    )

    # Create composite index on games (season_year, week_number) for efficient filtering
    op.create_index(
        "idx_games_season_week", "games", ["season_year", "week_number"], unique=False
    )


def downgrade() -> None:
    # Drop the indexes in reverse order
    op.drop_index("idx_games_season_week", table_name="games")
    op.drop_index("idx_picks_status_user", table_name="picks")
