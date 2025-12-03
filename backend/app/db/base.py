"""SQLAlchemy base model and metadata"""

from sqlalchemy.orm import DeclarativeBase

# Base class for all models
class Base(DeclarativeBase):
    pass

# Note: Model imports are NOT here to avoid circular imports
# Models are imported in alembic/env.py for migrations
# Models are imported in app/db/models/__init__.py for application use

