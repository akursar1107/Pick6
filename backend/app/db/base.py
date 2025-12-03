"""SQLAlchemy base model and metadata"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

# Base class for all models
class Base(DeclarativeBase):
    pass

# Import all models here for Alembic to discover them
# from app.db.models.user import User
# from app.db.models.game import Game
# from app.db.models.pick import Pick

